#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
L'usine à sprites de Jupire, en vrai : Blender + Cycles.

Elle fait exactement ce que `scripts/usine.gd` fait en miniature dans Godot —
photographier des volumes sous N angles en projection ORTHOGRAPHIQUE à une
inclinaison fixe — mais en path tracing, avec des arbres qui ont de vraies
branches, des feuilles translucides et une tache de contact au sol.

LE CONTRAT GÉOMÉTRIQUE (ne pas improviser, la caméra de jeu en dépend) :

  * projection ORTHOGRAPHIQUE, jamais perspective ;
  * inclinaison TILT = 36° au-dessus de l'horizon ;
  * 8 angles, azimut = a × 45° ;
  * pour un panneau de hauteur H (m) : taille verticale de la caméra = H·cos(36°),
    rapport largeur/hauteur de l'image = 1/cos(36°)  → 384 px de haut, 475 de large ;
  * la caméra vise (0,5 − marge)·H au-dessus de la base — 0,38·H à la marge
    nominale de 0,12 : le panneau va de −marge·H à (1−marge)·H, et la marge du
    bas reçoit la tache de contact ;
  * LA MARGE BASSE EST PAR PROP, calculée et déclarée dans le manifeste. En
    ortho inclinée, un déport horizontal de R vers la caméra descend de R·sin(t)
    à l'écran quand la marge n'offre que marge·H·cos(t) : il faut donc
    marge ≥ R·tan(t)/H. 0,12 convient à un chêne, pas à un sanglier, qui est
    plus long que haut. `fabriquer` mesure la descente réelle et résout
    échelle ↔ marge par point fixe ;
  * (0,0,0) est le PIED de l'objet — pas le centre de sa boîte : c'est ce point
    que Godot pose sur le terrain ;
  * fond transparent (PNG RGBA) ;
  * LE SOLEIL EST FIXE DANS LE MONDE pour les 8 angles. Il ne suit jamais la
    caméra. Sinon le côté éclairé tourne avec elle et tout l'éclairage ment.

REPÈRES. Godot est Y-haut, Blender est Z-haut : Blender(x, −z, y) = Godot(x, y, z).
En Blender, donc :
    caméra = (sin(az)·cos(t)·D, −cos(az)·cos(t)·D, sin(t)·D + 0,38·H)
    vers le soleil = (cos(el)·sin(azs), −cos(el)·cos(azs), sin(el))

Lancement :
    ~/blender-4.5.9-linux-x64/blender --background --python usine.py -- [options]
    (voir --aide, ou le README du dossier)

Tout est PROCÉDURAL : Blender 4.5 ne livre plus l'add-on Sapling, et aucun
asset CC0 n'était disponible au moment de l'écriture. Les arbres sont donc
construits par récursion (branches tubulaires + feuilles polygonales), les
matériaux par nœuds de bruit. Aucune texture externe n'est nécessaire.
"""

import argparse
import json
import math
import os
import random
import sys
import time

import bpy
import bmesh
from mathutils import Vector, Matrix, Quaternion
from mathutils import noise as bnoise
import numpy as np


# ───────────────────────────────────────────────────────────────────────────
#  LE CONTRAT — ces constantes sont partagées avec la caméra de jeu.
# ───────────────────────────────────────────────────────────────────────────

TILT = math.radians(36.0)   # inclinaison de la caméra au-dessus de l'horizon
ANGLES = 8                  # pas de 45°, la grille d'AoE2
HAUT_PX = 384               # hauteur de rendu ; la largeur en découle
MARGE_BAS = 0.12            # fraction du panneau réservée SOUS la ligne de sol
CENTRE = 0.38               # hauteur visée, en fraction de H (= (1−0,12+0,88)/2… soit 0,38)
SOL_AZ = 2.35               # azimut du soleil, radians — FIXE DANS LE MONDE
SOL_EL = 0.42               # élévation du soleil, radians
VARIANTES = 3

# nom → hauteur du panneau en mètres. Mêmes noms/hauteurs que Volumes.CATALOGUE,
# plus deux nouveautés (herbe_seche, tas_feuilles) demandées pour le sol.
CATALOGUE = {
    "chene_vert": 9.0,
    "chene_pubescent": 12.0,
    "buisson": 2.6,
    "rocher": 3.4,
    "herbe_seche": 0.8,
    "tas_feuilles": 0.6,
    # Animaux : hauteurs de panneau fixées par l'agent qui tient
    # Volumes.CATALOGUE côté Godot. Le panneau est plus grand que la bête
    # (elle est mise à sa TAILLE RÉELLE, pas étirée pour remplir), ce qui
    # laisse de la place au mouvement d'une pose à l'autre.
    "chevreuil": 2.0,
    "sanglier": 1.6,
    "oiseau": 2.2,
    "poisson": 1.0,
}

ORDRE = ["chene_vert", "chene_pubescent", "buisson", "rocher",
         "herbe_seche", "tas_feuilles",
         "chevreuil", "sanglier", "oiseau", "poisson"]

# Animaux : la « variante » n'est plus une forme mais une POSE prise dans le
# cycle d'animation du modèle riggé. Même échelle pour toutes les poses, sinon
# la bête change de taille en marchant.
ANIMAUX = {
    # nom : (fichier, taille réelle en m, action à jouer)
    #
    # L'action doit être nommée : à l'ouverture, ces .blend ont une action
    # « default » de longueur nulle assignée à l'armature. Sans la forcer, les
    # trois poses sortent identiques (constaté au rendu).
    "chevreuil": ("animaux/deer_female_blend/doe.blend", 1.15, "Run"),
    "sanglier": ("animaux/boar_blend/boar.blend", 0.95, "walk"),
    "oiseau": ("animaux/raven_blend/raven_0.blend", 0.55, "fly"),
    "poisson": ("animaux/esox_pike/esox.fbx", 0.75, "Swiming-Slow"),
}

# Modèles CC0 substituables au procédural, par nom de prop.
#
# VIDE À DESSEIN pour buisson et herbe_seche. Les touffes et buissons Poly Haven
# sont larges et plaqués au sol ; or à 36° d'inclinaison une empreinte de rayon R
# descend de 0,73·R SOUS la ligne de sol, et la marge basse ne vaut que 0,12·H.
# Mis au panneau, ces modèles tombaient à 25 % de leur taille (mesuré : la touffe
# faisait 2,4 cm de large dans un panneau de 80 cm). Le procédural, lui, est
# taillé pour le contrat. Remettre un chemin ici suffit à rebasculer.
MODELES = {}

RACINE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "..", ".."))
CC0 = os.path.join(RACINE, "assets", "cc0")
HDRI = os.path.join(CC0, "hdri", "kloofendal_43d_clear_puresky",
                    "kloofendal_43d_clear_puresky_2k.hdr")
ECORCE_CC0 = os.path.join(CC0, "textures", "jolcham_oak_bark_01")

# Le soleil de l'HDRI, MESURÉ sur le pixel le plus lumineux (2048 × 1024) :
# u = 0,6003 → azimut 0,6300 rad dans le repère de l'HDRI ; v = 0,7388 →
# élévation 0,750 rad (43°, ce que dit son nom). Notre contrat impose 0,42 rad.
# On fait donc deux choses : on tourne l'HDRI pour aligner les azimuts, et on
# ÉCRÊTE son disque solaire — sinon il porterait une seconde ombre, à 43°.
HDRI_AZ = 0.6300


# ───────────────────────────────────────────────────────────────────────────
#  Petits outils de maillage
# ───────────────────────────────────────────────────────────────────────────

def _repere(tangente, ref):
    """Repère orthonormé autour d'une tangente, transporté pour éviter la vrille."""
    t = tangente.normalized()
    u = ref - t * ref.dot(t)
    if u.length < 1e-5:
        secours = Vector((1.0, 0.0, 0.0)) if abs(t.x) < 0.9 else Vector((0.0, 1.0, 0.0))
        u = secours - t * secours.dot(t)
    u.normalize()
    v = t.cross(u)
    return u, v


def _tube(bm, pts, rayons, cotes=6, uv=None, ech_uv=1.0):
    """Bridge une suite d'anneaux le long d'une polyligne : une branche.
    Si `uv` est donné (couche UV du bmesh), déplie la branche en bande :
    u = tour de la branche, v = longueur d'arc en mètres × ech_uv. L'écorce
    photographiée garde ainsi son échelle réelle, quel que soit le rameau."""
    n = len(pts)
    if n < 2:
        return
    ref = Vector((1.0, 0.0, 0.0))
    anneaux = []
    arcs = [0.0]
    for i in range(1, n):
        arcs.append(arcs[-1] + (pts[i] - pts[i - 1]).length)
    for i, p in enumerate(pts):
        if i == 0:
            tg = pts[1] - pts[0]
        elif i == n - 1:
            tg = pts[-1] - pts[-2]
        else:
            tg = pts[i + 1] - pts[i - 1]
        if tg.length < 1e-6:
            tg = Vector((0.0, 0.0, 1.0))
        u, v = _repere(tg, ref)
        ref = u
        r = max(rayons[i], 1e-4)
        anneau = []
        for k in range(cotes):
            a = 2.0 * math.pi * k / cotes
            anneau.append(bm.verts.new(p + u * (r * math.cos(a)) + v * (r * math.sin(a))))
        anneaux.append(anneau)
    for i in range(n - 1):
        a, b = anneaux[i], anneaux[i + 1]
        circ = 2.0 * math.pi * max(rayons[i], 1e-4)
        for k in range(cotes):
            k2 = (k + 1) % cotes
            try:
                f = bm.faces.new((a[k], a[k2], b[k2], b[k]))
            except ValueError:
                continue
            if uv is not None:
                u0 = circ * k / cotes * ech_uv
                u1 = circ * (k + 1) / cotes * ech_uv
                v0 = arcs[i] * ech_uv
                v1 = arcs[i + 1] * ech_uv
                for lp, (uu, vv) in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
                    lp[uv].uv = (uu, vv)
    try:
        f = bm.faces.new(tuple(reversed(anneaux[0])))
        if uv is not None:
            for lp in f.loops:
                lp[uv].uv = (0.0, 0.0)
    except ValueError:
        pass


# Profil d'une feuille dans son plan local : x le long du pétiole, y en travers.
# Six sommets suffisent — à 384 px une feuille fait 2 à 8 px, c'est la silhouette
# du paquet qui compte, pas le lobe.
PROFIL_FEUILLE = [(0.00, 0.00), (0.22, 0.34), (0.58, 0.44),
                  (1.00, 0.00), (0.58, -0.44), (0.22, -0.34)]


def _feuille(bm, origine, axe, normale, longueur, largeur):
    """Pose une feuille polygonale (6 sommets) dans le repère (axe, normale)."""
    a = axe.normalized()
    n = normale - a * normale.dot(a)
    if n.length < 1e-5:
        return
    n.normalize()
    c = a.cross(n)
    vs = []
    for x, y in PROFIL_FEUILLE:
        vs.append(bm.verts.new(origine + a * (x * longueur) + c * (y * largeur)))
    try:
        bm.faces.new(vs)
    except ValueError:
        pass


def _objet(nom, bm, materiaux, lisse=True):
    """Transforme un bmesh en objet de la scène."""
    me = bpy.data.meshes.new(nom)
    bm.to_mesh(me)
    bm.free()
    if lisse:
        for p in me.polygons:
            p.use_smooth = True
    for m in materiaux:
        me.materials.append(m)
    ob = bpy.data.objects.new(nom, me)
    bpy.context.collection.objects.link(ob)
    return ob


# ───────────────────────────────────────────────────────────────────────────
#  Matériaux — tout par nœuds, aucune texture sur disque
# ───────────────────────────────────────────────────────────────────────────

def _mat_neuf(nom):
    m = bpy.data.materials.new(nom)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    sortie = nt.nodes.new("ShaderNodeOutputMaterial")
    sortie.location = (600, 0)
    return m, nt, sortie


def _img(chemin, non_couleur=False):
    im = bpy.data.images.load(chemin, check_existing=True)
    if non_couleur:
        im.colorspace_settings.name = "Non-Color"
    return im


def mat_ecorce_photo(nom, dossier, prefixe, teinte=(1.0, 1.0, 1.0), force_nrm=1.0):
    """Écorce à partir d'un jeu Poly Haven (diff / nor_gl / arm packé).
    L'ARM contient AO en rouge, rugosité en vert, métal en bleu."""
    m, nt, sortie = _mat_neuf(nom)
    uvn = nt.nodes.new("ShaderNodeUVMap")
    uvn.location = (-1000, 0)
    uvn.uv_map = "UVMap"

    diff = nt.nodes.new("ShaderNodeTexImage")
    diff.location = (-760, 220)
    diff.image = _img(os.path.join(dossier, prefixe + "_diff_2k.jpg"))
    diff.extension = "REPEAT"
    nt.links.new(uvn.outputs["UV"], diff.inputs["Vector"])

    arm = nt.nodes.new("ShaderNodeTexImage")
    arm.location = (-760, -60)
    arm.image = _img(os.path.join(dossier, prefixe + "_arm_2k.jpg"), True)
    nt.links.new(uvn.outputs["UV"], arm.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    sep.location = (-540, -60)
    nt.links.new(arm.outputs["Color"], sep.inputs["Color"])

    nrm = nt.nodes.new("ShaderNodeTexImage")
    nrm.location = (-760, -360)
    nrm.image = _img(os.path.join(dossier, prefixe + "_nor_gl_2k.jpg"), True)
    nt.links.new(uvn.outputs["UV"], nrm.inputs["Vector"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.location = (-540, -360)
    nm.inputs["Strength"].default_value = force_nrm
    nt.links.new(nrm.outputs["Color"], nm.inputs["Color"])

    tin = nt.nodes.new("ShaderNodeMixRGB")
    tin.location = (-500, 220)
    tin.blend_type = "MULTIPLY"
    tin.inputs["Fac"].default_value = 1.0
    tin.inputs["Color2"].default_value = (*teinte, 1.0)
    nt.links.new(diff.outputs["Color"], tin.inputs["Color1"])

    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.location = (0, 0)
    p.inputs["Specular IOR Level"].default_value = 0.25
    nt.links.new(tin.outputs["Color"], p.inputs["Base Color"])
    nt.links.new(sep.outputs["Green"], p.inputs["Roughness"])
    nt.links.new(nm.outputs["Normal"], p.inputs["Normal"])
    nt.links.new(p.outputs["BSDF"], sortie.inputs["Surface"])
    return m


def mat_ecorce(nom, teinte_claire, teinte_sombre, echelle=9.0):
    """Écorce : bruit étiré verticalement (crevasses) + relief par bump."""
    m, nt, sortie = _mat_neuf(nom)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    coord.location = (-900, 0)
    mapg = nt.nodes.new("ShaderNodeMapping")
    mapg.location = (-720, 0)
    mapg.inputs["Scale"].default_value = (3.0, 3.0, 0.32)  # étirement vertical
    nt.links.new(coord.outputs["Object"], mapg.inputs["Vector"])

    bruit = nt.nodes.new("ShaderNodeTexNoise")
    bruit.location = (-540, 100)
    bruit.inputs["Scale"].default_value = echelle
    bruit.inputs["Detail"].default_value = 8.0
    bruit.inputs["Roughness"].default_value = 0.62
    nt.links.new(mapg.outputs["Vector"], bruit.inputs["Vector"])

    fin = nt.nodes.new("ShaderNodeTexNoise")
    fin.location = (-540, -160)
    fin.inputs["Scale"].default_value = echelle * 7.0
    fin.inputs["Detail"].default_value = 6.0
    nt.links.new(mapg.outputs["Vector"], fin.inputs["Vector"])

    rampe = nt.nodes.new("ShaderNodeValToRGB")
    rampe.location = (-330, 100)
    rampe.color_ramp.elements[0].position = 0.34
    rampe.color_ramp.elements[0].color = (*teinte_sombre, 1.0)
    rampe.color_ramp.elements[1].position = 0.66
    rampe.color_ramp.elements[1].color = (*teinte_claire, 1.0)
    nt.links.new(bruit.outputs["Fac"], rampe.inputs["Fac"])

    bump = nt.nodes.new("ShaderNodeBump")
    bump.location = (-150, -220)
    bump.inputs["Strength"].default_value = 0.55
    bump.inputs["Distance"].default_value = 0.03
    nt.links.new(bruit.outputs["Fac"], bump.inputs["Height"])

    bump2 = nt.nodes.new("ShaderNodeBump")
    bump2.location = (20, -260)
    bump2.inputs["Strength"].default_value = 0.25
    nt.links.new(fin.outputs["Fac"], bump2.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bump2.inputs["Normal"])

    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.location = (260, 0)
    p.inputs["Roughness"].default_value = 0.88
    p.inputs["Specular IOR Level"].default_value = 0.22
    nt.links.new(rampe.outputs["Color"], p.inputs["Base Color"])
    nt.links.new(bump2.outputs["Normal"], p.inputs["Normal"])
    nt.links.new(p.outputs["BSDF"], sortie.inputs["Surface"])
    return m


def mat_feuille(nom, vert_a, vert_b, translucide, brillance=0.35, part_trans=0.30):
    """Feuille : diffus + translucide. C'est la translucidité qui fait le feuillage
    vivant — sans elle les faces à contre-jour sont du noir mort."""
    m, nt, sortie = _mat_neuf(nom)
    m.use_backface_culling = False

    coord = nt.nodes.new("ShaderNodeTexCoord")
    coord.location = (-900, 0)
    bruit = nt.nodes.new("ShaderNodeTexNoise")
    bruit.location = (-720, 0)
    bruit.inputs["Scale"].default_value = 3.2   # variation à l'échelle du paquet
    bruit.inputs["Detail"].default_value = 3.0
    nt.links.new(coord.outputs["Object"], bruit.inputs["Vector"])

    rampe = nt.nodes.new("ShaderNodeValToRGB")
    rampe.location = (-520, 0)
    rampe.color_ramp.elements[0].position = 0.30
    rampe.color_ramp.elements[0].color = (*vert_a, 1.0)
    rampe.color_ramp.elements[1].position = 0.72
    rampe.color_ramp.elements[1].color = (*vert_b, 1.0)
    nt.links.new(bruit.outputs["Fac"], rampe.inputs["Fac"])

    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.location = (-200, 160)
    p.inputs["Roughness"].default_value = 0.42
    p.inputs["Specular IOR Level"].default_value = brillance
    nt.links.new(rampe.outputs["Color"], p.inputs["Base Color"])

    tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
    tr.location = (-200, -140)
    tr.inputs["Color"].default_value = (*translucide, 1.0)

    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.location = (200, 0)
    mix.inputs["Fac"].default_value = part_trans
    nt.links.new(p.outputs["BSDF"], mix.inputs[1])
    nt.links.new(tr.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], sortie.inputs["Surface"])
    return m


def mat_calcaire(nom):
    """Calcaire d'Ardèche : gris-crème mouchetée, lichen jaune-vert dans les creux."""
    m, nt, sortie = _mat_neuf(nom)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    coord.location = (-1000, 0)

    gros = nt.nodes.new("ShaderNodeTexNoise")
    gros.location = (-820, 150)
    gros.inputs["Scale"].default_value = 2.4
    gros.inputs["Detail"].default_value = 8.0
    gros.inputs["Roughness"].default_value = 0.58
    nt.links.new(coord.outputs["Object"], gros.inputs["Vector"])

    grain = nt.nodes.new("ShaderNodeTexVoronoi")
    grain.location = (-820, -160)
    grain.feature = "F1"
    grain.inputs["Scale"].default_value = 26.0
    nt.links.new(coord.outputs["Object"], grain.inputs["Vector"])

    rampe = nt.nodes.new("ShaderNodeValToRGB")
    rampe.location = (-600, 150)
    rampe.color_ramp.elements[0].position = 0.34
    rampe.color_ramp.elements[0].color = (0.085, 0.080, 0.068, 1.0)
    rampe.color_ramp.elements[1].position = 0.72
    rampe.color_ramp.elements[1].color = (0.285, 0.270, 0.232, 1.0)
    nt.links.new(gros.outputs["Fac"], rampe.inputs["Fac"])

    # lichen : masque serré sur les hautes valeurs d'un troisième bruit
    lich = nt.nodes.new("ShaderNodeTexNoise")
    lich.location = (-820, -420)
    lich.inputs["Scale"].default_value = 6.5
    lich.inputs["Detail"].default_value = 5.0
    nt.links.new(coord.outputs["Object"], lich.inputs["Vector"])
    mlich = nt.nodes.new("ShaderNodeValToRGB")
    mlich.location = (-600, -420)
    mlich.color_ramp.elements[0].position = 0.50
    mlich.color_ramp.elements[1].position = 0.68
    nt.links.new(lich.outputs["Fac"], mlich.inputs["Fac"])

    melange = nt.nodes.new("ShaderNodeMixRGB")
    melange.location = (-330, 60)
    melange.blend_type = "MIX"
    melange.inputs["Color2"].default_value = (0.115, 0.125, 0.055, 1.0)
    nt.links.new(rampe.outputs["Color"], melange.inputs["Color1"])
    nt.links.new(mlich.outputs["Color"], melange.inputs["Fac"])

    bump = nt.nodes.new("ShaderNodeBump")
    bump.location = (-150, -250)
    bump.inputs["Strength"].default_value = 0.45
    nt.links.new(grain.outputs["Distance"], bump.inputs["Height"])
    bump2 = nt.nodes.new("ShaderNodeBump")
    bump2.location = (20, -300)
    bump2.inputs["Strength"].default_value = 0.35
    nt.links.new(gros.outputs["Fac"], bump2.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bump2.inputs["Normal"])

    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.location = (280, 0)
    p.inputs["Roughness"].default_value = 0.80
    p.inputs["Specular IOR Level"].default_value = 0.30
    nt.links.new(melange.outputs["Color"], p.inputs["Base Color"])
    nt.links.new(bump2.outputs["Normal"], p.inputs["Normal"])
    nt.links.new(p.outputs["BSDF"], sortie.inputs["Surface"])
    return m


def mat_paille(nom):
    """Herbe sèche : paille claire, franchement translucide (elle s'allume à contre-jour)."""
    m, nt, sortie = _mat_neuf(nom)
    m.use_backface_culling = False
    coord = nt.nodes.new("ShaderNodeTexCoord")
    coord.location = (-900, 0)
    bruit = nt.nodes.new("ShaderNodeTexNoise")
    bruit.location = (-720, 0)
    bruit.inputs["Scale"].default_value = 5.0
    nt.links.new(coord.outputs["Object"], bruit.inputs["Vector"])
    rampe = nt.nodes.new("ShaderNodeValToRGB")
    rampe.location = (-520, 0)
    rampe.color_ramp.elements[0].position = 0.32
    rampe.color_ramp.elements[0].color = (0.32, 0.25, 0.12, 1.0)
    rampe.color_ramp.elements[1].position = 0.70
    rampe.color_ramp.elements[1].color = (0.74, 0.62, 0.33, 1.0)
    nt.links.new(bruit.outputs["Fac"], rampe.inputs["Fac"])
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.location = (-200, 160)
    p.inputs["Roughness"].default_value = 0.55
    nt.links.new(rampe.outputs["Color"], p.inputs["Base Color"])
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
    tr.location = (-200, -140)
    tr.inputs["Color"].default_value = (0.82, 0.70, 0.38, 1.0)
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.location = (200, 0)
    mix.inputs["Fac"].default_value = 0.42
    nt.links.new(p.outputs["BSDF"], mix.inputs[1])
    nt.links.new(tr.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], sortie.inputs["Surface"])
    return m


def mat_terre(nom):
    """Terre de sous-bois, pour la butte sous le tas de feuilles."""
    m, nt, sortie = _mat_neuf(nom)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    coord.location = (-700, 0)
    bruit = nt.nodes.new("ShaderNodeTexNoise")
    bruit.location = (-520, 0)
    bruit.inputs["Scale"].default_value = 14.0
    bruit.inputs["Detail"].default_value = 6.0
    nt.links.new(coord.outputs["Object"], bruit.inputs["Vector"])
    rampe = nt.nodes.new("ShaderNodeValToRGB")
    rampe.location = (-330, 0)
    rampe.color_ramp.elements[0].color = (0.10, 0.075, 0.05, 1.0)
    rampe.color_ramp.elements[1].color = (0.26, 0.19, 0.12, 1.0)
    nt.links.new(bruit.outputs["Fac"], rampe.inputs["Fac"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.location = (-150, -200)
    bump.inputs["Strength"].default_value = 0.4
    nt.links.new(bruit.outputs["Fac"], bump.inputs["Height"])
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.location = (200, 0)
    p.inputs["Roughness"].default_value = 0.95
    nt.links.new(rampe.outputs["Color"], p.inputs["Base Color"])
    nt.links.new(bump.outputs["Normal"], p.inputs["Normal"])
    nt.links.new(p.outputs["BSDF"], sortie.inputs["Surface"])
    return m


def mat_contact():
    """Le disque attrape-ombre. Diffus au centre, transparent au bord : l'ombre
    captée s'éteint AVANT la lisière du disque, donc pas d'arc de coupe visible.

    Ce n'est pas l'ombre portée complète — à 24° de hauteur de soleil, celle d'un
    chêne de 9 m ferait 20 m et sortirait vingt fois du panneau. C'est la tache de
    contact, ce que fait AoE2 : l'assombrissement du pied, plus la vraie pénombre
    calculée par Cycles sur les deux premiers mètres.
    """
    m, nt, sortie = _mat_neuf("contact")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    coord.location = (-800, 0)
    sep = nt.nodes.new("ShaderNodeVectorMath")
    sep.location = (-620, 0)
    sep.operation = "LENGTH"
    nt.links.new(coord.outputs["Object"], sep.inputs[0])
    rampe = nt.nodes.new("ShaderNodeValToRGB")
    rampe.location = (-430, 0)
    rampe.color_ramp.interpolation = "EASE"
    rampe.color_ramp.elements[0].position = 0.22   # opaque jusqu'à 22 % du rayon
    rampe.color_ramp.elements[0].color = (0, 0, 0, 1)
    rampe.color_ramp.elements[1].position = 0.94   # éteint avant le bord
    rampe.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(sep.outputs["Value"], rampe.inputs["Fac"])

    dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
    dif.location = (-150, 140)
    dif.inputs["Color"].default_value = (0.26, 0.24, 0.18, 1.0)
    trp = nt.nodes.new("ShaderNodeBsdfTransparent")
    trp.location = (-150, -100)
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.location = (200, 0)
    nt.links.new(rampe.outputs["Color"], mix.inputs["Fac"])
    nt.links.new(dif.outputs["BSDF"], mix.inputs[1])
    nt.links.new(trp.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], sortie.inputs["Surface"])
    return m


# ───────────────────────────────────────────────────────────────────────────
#  Les arbres : récursion branches + feuilles
# ───────────────────────────────────────────────────────────────────────────

class ReglesArbre:
    """Le jeu de règles d'une essence. C'est ici qu'on distingue un chêne vert
    (dense, ramassé, sempervirent) d'un chêne pubescent (ouvert, tortueux)."""

    def __init__(self, **kw):
        self.prof_max = 4
        self.enfants = (3, 4)
        self.ratio_long = 0.70
        self.ratio_rayon = 0.62
        self.angle = (0.55, 1.05)      # écart au parent, radians
        self.sinuosite = 0.16
        self.gravite = -0.05           # >0 redresse, <0 fait retomber
        self.phototropisme = 0.10      # tire les rameaux vers le haut
        self.effilement = 0.45
        self.tronc_h = 0.34            # part de la hauteur avant la 1re fourche
        self.tronc_r = 0.035           # rayon du tronc / hauteur
        self.depart = (2, 3)           # fourches à la tête du tronc
        self.feuille_l = 0.11
        self.feuille_r = 0.55          # largeur / longueur
        self.feuilles_par_rameau = 6   # points de bouquet le long d'un rameau
        self.par_rosette = 4           # feuilles par bouquet
        self.plancher = 0.34           # pas de feuilles sous cette part de H
        self.prof_feuilles = 2         # feuilles à partir de prof_max − n
        self.__dict__.update(kw)


def _rameaux(pousses, feuilles_pos, base, direction, longueur, rayon, prof, rg, R):
    """Trace une branche puis ses filles. Remplit `pousses` (polylignes) et
    `feuilles_pos` (origine, axe) pour les rameaux terminaux."""
    segs = 6 if prof == 0 else max(2, 5 - prof // 2)
    d = direction.normalized()
    p = base.copy()
    pts = [p.copy()]
    rayons = [rayon]
    # Biais vertical : phototropisme en bas (les charpentières montent), gravité
    # en haut (les rameaux fins retombent). C'est ce dégradé qui arrondit le
    # houppier ; un biais constant donne une araignée.
    part = prof / max(1, R.prof_max)
    biais = R.gravite * part + R.phototropisme * (1.0 - part)
    for s in range(segs):
        gigue = Vector((rg.gauss(0, 1), rg.gauss(0, 1), rg.gauss(0, 1))) * R.sinuosite
        d = (d + gigue + Vector((0.0, 0.0, biais))).normalized()
        p = p + d * (longueur / segs)
        # Rien ne pousse sous terre. Sans cette butée, une branche retombante du
        # chêne pubescent (gravité −0,18) descendait à 1,19 m SOUS la base —
        # mesuré —, ce qui gonflait la marge basse du panneau de 0,12 à 0,264
        # pour rien, et rognait l'arbre d'autant.
        if p.z < 0.0:
            p.z = 0.0
            d = Vector((d.x, d.y, abs(d.z) * 0.35 + 0.05)).normalized()
        pts.append(p.copy())
        rayons.append(rayon * (1.0 - (s + 1) / segs * R.effilement))
    cotes = 8 if prof == 0 else (6 if prof == 1 else (4 if prof <= 3 else 3))
    pousses.append((pts, rayons, cotes))

    # Feuillage : sur les rameaux des dernières générations, en rosettes.
    # Les feuilles de chêne poussent en bouquets au bout des pousses, pas une
    # par une — c'est le bouquet qui fait la masse lisible à 300 px.
    if prof >= R.prof_max - R.prof_feuilles:
        n = R.feuilles_par_rameau + (3 if prof == R.prof_max else 0)
        for i in range(n):
            t = 0.25 + 0.75 * (i + 0.5) / n     # rien sur le premier quart
            k = min(len(pts) - 2, int(t * (len(pts) - 1)))
            u = t * (len(pts) - 1) - k
            org = pts[k].lerp(pts[k + 1], u)
            for _ in range(R.par_rosette):
                axe = Vector((rg.gauss(0, 1), rg.gauss(0, 1), rg.gauss(0, 0.9) + 0.30))
                if axe.length < 1e-4:
                    axe = Vector((0, 0, 1))
                ecart = Vector((rg.gauss(0, 1), rg.gauss(0, 1), rg.gauss(0, 1)))
                ecart = ecart * (R.feuille_l * 0.35 / max(ecart.length, 1e-4))
                feuilles_pos.append((org + ecart, axe.normalized()))

    if prof >= R.prof_max:
        return
    nb = rg.randint(*R.enfants)
    for i in range(nb):
        t = rg.uniform(0.38, 1.0)
        k = min(len(pts) - 2, int(t * (len(pts) - 1)))
        frac = t * (len(pts) - 1) - k
        org = pts[k].lerp(pts[k + 1], frac)
        # Le rayon de la fille se déduit du rayon LOCAL du parent à l'attache,
        # pas de son rayon de départ : sinon les jonctions gonflent.
        r_local = rayons[k] * (1.0 - frac) + rayons[k + 1] * frac
        tg = (pts[k + 1] - pts[k]).normalized()
        a = 2.0 * math.pi * (i + rg.uniform(-0.25, 0.25)) / nb
        ouv = rg.uniform(*R.angle)
        uu, vv = _repere(tg, Vector((1.0, 0.0, 0.0)))
        lat = uu * math.cos(a) + vv * math.sin(a)
        nd = (tg * math.cos(ouv) + lat * math.sin(ouv)).normalized()
        _rameaux(pousses, feuilles_pos, org, nd,
                 longueur * R.ratio_long * rg.uniform(0.82, 1.15),
                 r_local * R.ratio_rayon * rg.uniform(0.88, 1.08),
                 prof + 1, rg, R)


def batir_arbre(nom, graine, R, mat_bois, mat_feuilles, hauteur_cible):
    """Construit un arbre complet et le renvoie comme deux objets (bois, feuilles)."""
    rg = random.Random(graine)
    pousses, feuilles_pos = [], []

    h_tronc = hauteur_cible * R.tronc_h
    r_tronc = hauteur_cible * R.tronc_r
    # Le tronc : segmenté et légèrement penché, il n'est jamais un cylindre droit.
    d0 = Vector((rg.gauss(0, 0.09), rg.gauss(0, 0.09), 1.0)).normalized()
    _rameaux(pousses, feuilles_pos, Vector((0.0, 0.0, 0.0)), d0,
             h_tronc, r_tronc, 0, rg, R)

    # Les grosses charpentières repartent de la tête du tronc.
    tete_pts, tete_r, _ = pousses[0]
    for i in range(rg.randint(*R.depart)):
        a = 2.0 * math.pi * (i + rg.uniform(-0.2, 0.2)) / R.depart[1]
        ouv = rg.uniform(0.35, 0.8)
        tg = (tete_pts[-1] - tete_pts[-2]).normalized()
        uu, vv = _repere(tg, Vector((1.0, 0.0, 0.0)))
        lat = uu * math.cos(a) + vv * math.sin(a)
        nd = (tg * math.cos(ouv) + lat * math.sin(ouv)).normalized()
        _rameaux(pousses, feuilles_pos, tete_pts[-1], nd,
                 hauteur_cible * 0.30 * rg.uniform(0.85, 1.15),
                 tete_r[-1] * rg.uniform(0.62, 0.82), 1, rg, R)

    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    for pts, rayons, cotes in pousses:
        _tube(bm, pts, rayons, cotes, uv, ech_uv=1.4)
    bois = _objet(nom + "_bois", bm, [mat_bois])

    # On coupe le feuillage bas : un chêne adulte porte son houppier au-dessus
    # du tronc, et c'est la silhouette « tronc visible + dôme » qui le rend
    # lisible à 300 px de haut.
    h_reelle = max((p.z for pts, _, _ in pousses for p in pts), default=hauteur_cible)
    seuil = h_reelle * R.plancher
    feuilles_pos = [f for f in feuilles_pos if f[0].z > seuil] or feuilles_pos

    bmf = bmesh.new()
    for org, axe in feuilles_pos:
        L = R.feuille_l * rg.uniform(0.75, 1.3)
        nrm = Vector((rg.gauss(0, 1), rg.gauss(0, 1), rg.gauss(0, 1)))
        if nrm.length < 1e-4:
            nrm = Vector((0, 0, 1))
        _feuille(bmf, org, axe, nrm, L, L * R.feuille_r)
    feuillage = _objet(nom + "_feuilles", bmf, [mat_feuilles], lisse=False)
    return [bois, feuillage]


# ───────────────────────────────────────────────────────────────────────────
#  Les autres objets
# ───────────────────────────────────────────────────────────────────────────

def batir_rocher(nom, graine, mat, hauteur_cible):
    """Bloc de calcaire : icosphère bruitée puis tranchée par des plans —
    le calcaire casse en dièdres, pas en boules."""
    rg = random.Random(graine)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0)

    # aplatissement général : un bloc est plus large que haut
    # Un bloc large et bas serait rogné par le bas du panneau (la marge basse
    # ne vaut que 0,12·H, et l'empreinte au sol mange 0,73 × son rayon). On
    # taille donc un bloc dressé, ce que fait le calcaire de la gorge.
    ech = Vector((rg.uniform(0.70, 0.95), rg.uniform(0.62, 0.88), rg.uniform(1.25, 1.75)))
    for v in bm.verts:
        v.co = Vector((v.co.x * ech.x, v.co.y * ech.y, v.co.z * ech.z))

    # relief fractal
    dec = Vector((rg.uniform(0, 30), rg.uniform(0, 30), rg.uniform(0, 30)))
    for v in bm.verts:
        n1 = bnoise.noise(v.co * 1.3 + dec)
        n2 = bnoise.noise(v.co * 3.8 + dec * 1.7)
        n3 = bnoise.noise(v.co * 9.5 + dec * 2.3)
        n4 = bnoise.noise(v.co * 22.0 + dec * 3.1)
        v.co += v.normal * (n1 * 0.30 + n2 * 0.13 + n3 * 0.05 + n4 * 0.018)

    # 5 à 8 tranches planes : les faces de clivage
    for _ in range(rg.randint(9, 13)):
        n = Vector((rg.gauss(0, 1), rg.gauss(0, 1), rg.gauss(0, 0.75))).normalized()
        d = rg.uniform(0.50, 0.90)
        for v in bm.verts:
            ecart = v.co.dot(n) - d
            if ecart > 0.0:
                v.co -= n * ecart

    # poser la base à Z=0 et bien à plat
    zmin = min(v.co.z for v in bm.verts)
    for v in bm.verts:
        v.co.z -= zmin
        if v.co.z < 0.04:
            v.co.z *= 0.35

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # Ombrage plat assumé : à 5 120 facettes pour 3,4 m de bloc, une facette fait
    # ~10 px. C'est exactement le grain d'un calcaire cassé — le lisser le
    # transformerait en galet.
    return [_objet(nom, bm, [mat], lisse=False)]


def batir_buisson(nom, graine, mat_bois, mat_feuilles, hauteur_cible):
    """Buisson de garrigue : plusieurs tiges partant du sol, feuillage compact.
    C'est un chêne kermès / ciste : dense, bas, coriace."""
    rg = random.Random(graine)
    R = ReglesArbre(prof_max=5, enfants=(3, 4), ratio_long=0.68, ratio_rayon=0.66,
                    angle=(0.55, 1.15), sinuosite=0.24, gravite=-0.04,
                    phototropisme=0.16, effilement=0.42, plancher=0.04,
                    feuille_l=0.055, feuille_r=0.62, feuilles_par_rameau=5,
                    par_rosette=5, prof_feuilles=3)
    pousses, feuilles = [], []
    for i in range(rg.randint(4, 6)):
        a = 2.0 * math.pi * i / 5.0 + rg.uniform(-0.4, 0.4)
        ouv = rg.uniform(0.18, 0.55)
        d = Vector((math.sin(ouv) * math.cos(a), math.sin(ouv) * math.sin(a), math.cos(ouv)))
        org = Vector((math.cos(a) * 0.06, math.sin(a) * 0.06, 0.0)) * hauteur_cible
        _rameaux(pousses, feuilles, org, d,
                 hauteur_cible * rg.uniform(0.32, 0.46),
                 hauteur_cible * rg.uniform(0.022, 0.033), 0, rg, R)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    for pts, rayons, cotes in pousses:
        _tube(bm, pts, rayons, cotes, uv, ech_uv=4.0)
    bois = _objet(nom + "_bois", bm, [mat_bois])
    bmf = bmesh.new()
    for org, axe in feuilles:
        L = R.feuille_l * rg.uniform(0.7, 1.35)
        _feuille(bmf, org, axe,
                 Vector((rg.gauss(0, 1), rg.gauss(0, 1), rg.gauss(0, 1))), L, L * R.feuille_r)
    feuillage = _objet(nom + "_feuilles", bmf, [mat_feuilles], lisse=False)
    return [bois, feuillage]


def batir_herbe(nom, graine, mat, hauteur_cible):
    """Touffe d'herbe sèche : des lames effilées qui s'ouvrent en gerbe et
    retombent. Chaque lame est une bande de 4 quads, ça suffit largement."""
    rg = random.Random(graine)
    bm = bmesh.new()
    nb = rg.randint(520, 660)
    for _ in range(nb):
        a = rg.uniform(0, 2 * math.pi)
        rad = rg.uniform(0.0, 0.20) * hauteur_cible
        org = Vector((math.cos(a) * rad, math.sin(a) * rad, 0.0))
        L = hauteur_cible * rg.uniform(0.55, 1.05)
        larg = hauteur_cible * rg.uniform(0.008, 0.016)
        ouv = rg.uniform(0.08, 0.48)          # écart à la verticale au départ
        dh = Vector((math.cos(a + rg.gauss(0, 0.5)), math.sin(a + rg.gauss(0, 0.5)), 0.0))
        d = (Vector((0, 0, 1)) * math.cos(ouv) + dh * math.sin(ouv)).normalized()
        cote = Vector((-d.y, d.x, 0.0))
        if cote.length < 1e-4:
            cote = Vector((1, 0, 0))
        cote.normalize()
        segs = 4
        p = org.copy()
        prec = None
        courbe = rg.uniform(0.30, 1.15)        # combien la lame retombe
        for s in range(segs + 1):
            t = s / segs
            w = larg * (1.0 - t) ** 0.7
            dd = (d + Vector((0, 0, -courbe * t))).normalized()
            if s > 0:
                p = p + dd * (L / segs)
            va = bm.verts.new(p - cote * w)
            vb = bm.verts.new(p + cote * w)
            if prec is not None:
                try:
                    bm.faces.new((prec[0], prec[1], vb, va))
                except ValueError:
                    pass
            prec = (va, vb)
    return [_objet(nom, bm, [mat], lisse=False)]


def batir_tas_feuilles(nom, graine, mat_terre_, mat_feuilles, hauteur_cible):
    """Tas de feuilles mortes : une butte de terre couverte de feuilles posées
    à plat, avec quelques-unes redressées sur les bords."""
    rg = random.Random(graine)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    # Rayon ≈ hauteur : à 36° d'inclinaison l'empreinte au sol coûte 0,73 × son
    # rayon SOUS la ligne de sol, et la marge basse ne vaut que 0,12·H. Une
    # galette large serait rognée net par le bas du panneau.
    rayon = hauteur_cible * 0.95
    for v in bm.verts:
        v.co = Vector((v.co.x * rayon, v.co.y * rayon, v.co.z * hauteur_cible * 1.05))
        n = bnoise.noise(v.co * 2.0 + Vector((graine % 17, 3.0, 7.0)))
        v.co += Vector((0, 0, n * hauteur_cible * 0.12))
    # on coupe tout ce qui passe sous 0 : il reste une butte
    verts_bas = [v for v in bm.verts if v.co.z < 0.0]
    for v in verts_bas:
        v.co.z = 0.0
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    butte = _objet(nom + "_butte", bm, [mat_terre_], lisse=True)

    bmf = bmesh.new()
    for _ in range(rg.randint(900, 1200)):
        a = rg.uniform(0, 2 * math.pi)
        u = math.sqrt(rg.uniform(0, 1))
        r = u * rayon * 0.98
        # hauteur de la butte au rayon r (approximée par la même ellipsoïde)
        z = hauteur_cible * 1.05 * math.sqrt(max(0.0, 1.0 - (r / rayon) ** 2))
        org = Vector((math.cos(a) * r, math.sin(a) * r, z + hauteur_cible * 0.02))
        axe = Vector((rg.gauss(0, 1), rg.gauss(0, 1), rg.gauss(0, 0.35)))
        nrm = Vector((rg.gauss(0, 0.45), rg.gauss(0, 0.45), 1.0))
        L = hauteur_cible * rg.uniform(0.20, 0.38)
        _feuille(bmf, org, axe, nrm, L, L * 0.62)
    tapis = _objet(nom + "_feuilles", bmf, [mat_feuilles], lisse=False)
    return [butte, tapis]


# ───────────────────────────────────────────────────────────────────────────
#  Import des assets CC0 (voir README pour les sources et les licences)
# ───────────────────────────────────────────────────────────────────────────

def _racines(avant):
    """Les objets apparus depuis l'instantané `avant`, sans leurs enfants."""
    neufs = [o for o in bpy.data.objects if o.name not in avant]
    return neufs


def importer_gltf(chemin, graine=0):
    """Importe un glTF Poly Haven et renvoie ses objets. On lui donne une
    rotation aléatoire autour de Z : trois variantes du même buisson ne doivent
    pas être trois fois la même silhouette."""
    avant = {o.name for o in bpy.data.objects}
    bpy.ops.import_scene.gltf(filepath=chemin)
    objets = _racines(avant)
    rg = random.Random(graine)
    porte = bpy.data.objects.new("porte_import", None)
    bpy.context.collection.objects.link(porte)
    for o in objets:
        if o.parent is None:
            o.parent = porte
            o.matrix_parent_inverse = Matrix.Identity(4)
    porte.rotation_euler = (0.0, 0.0, rg.uniform(0.0, 2.0 * math.pi))
    bpy.context.view_layer.update()
    return [porte] + objets


def _mat_depuis_image(nom, image, rugosite=0.72):
    """Un Principled tout simple autour d'une texture diffuse."""
    m, nt, sortie = _mat_neuf(nom)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.location = (-400, 0)
    tex.image = image
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.location = (0, 0)
    p.inputs["Roughness"].default_value = rugosite
    p.inputs["Specular IOR Level"].default_value = 0.30
    nt.links.new(tex.outputs["Color"], p.inputs["Base Color"])
    nt.links.new(p.outputs["BSDF"], sortie.inputs["Surface"])
    return m


def importer_anime(chemin, pose, nb_poses, action=None, graine=0):
    """Importe un modèle riggé et le fige sur une pose de son cycle d'animation.

    « Variante » veut dire POSE pour les animaux : les trois images d'un même
    angle sont trois instants de la marche, pas trois individus.

    Deux pièges, tous deux constatés au rendu :
      · ces .blend embarquent leurs propres lampes, leur caméra et un sol —
        importés tels quels, ils écrasaient notre éclairage (les bêtes
        sortaient blanches à 0,8 de luminance) ;
      · leurs matériaux sont du Blender Internal, que Blender 4 ne sait plus
        convertir : on les reconstruit à partir des images du fichier.
    """
    avant = {o.name for o in bpy.data.objects}
    objets = []
    images = []
    if chemin.lower().endswith(".blend"):
        with bpy.data.libraries.load(chemin, link=False) as (src, dst):
            dst.objects = list(src.objects)
            dst.actions = list(src.actions)
            dst.images = list(src.images)
        images = [i for i in dst.images if i is not None and i.size[0] > 4]
        for o in dst.objects:
            if o is None:
                continue
            if o.type not in {"MESH", "ARMATURE"} or o.name.lower().startswith("plane"):
                bpy.data.objects.remove(o, do_unlink=True)
                continue
            bpy.context.collection.objects.link(o)
            objets.append(o)
        # on force l'action voulue sur l'armature
        if action:
            act = bpy.data.actions.get(action)
            for o in objets:
                if o.type == "ARMATURE" and act is not None:
                    if o.animation_data is None:
                        o.animation_data_create()
                    o.animation_data.action = act
        # matériaux : une image par maillage, appariée par le nom
        for o in objets:
            if o.type != "MESH" or not images:
                continue
            choix = images[0]
            for im in images:
                if o.name.lower().split(".")[0] in im.name.lower():
                    choix = im
                    break
            m = _mat_depuis_image(o.name + "_mat", choix)
            o.data.materials.clear()
            o.data.materials.append(m)
    else:
        bpy.ops.import_scene.fbx(filepath=chemin)
        neufs = [o for o in bpy.data.objects if o.name not in avant]
        mailles = [o for o in neufs if o.type == "MESH"]
        garde = set()
        if mailles:
            principal = max(mailles, key=lambda o: len(o.data.vertices))
            garde.add(principal.name)
        garde |= {o.name for o in neufs if o.type == "ARMATURE"}
        objets = []
        for o in neufs:
            if o.name in garde:
                objets.append(o)
            else:
                bpy.data.objects.remove(o, do_unlink=True)
        # Le matériau FBX du brochet (Esox-Shdr + « Projection material ») sort
        # quasi noir sous Cycles (0,03 de luminance mesurée). On le remplace par
        # un Principled sur sa diffuse, comme pour les .blend.
        tex = os.path.join(os.path.dirname(chemin), "tex")
        if os.path.isdir(tex):
            jpgs = sorted(f for f in os.listdir(tex)
                          if f.lower().endswith((".png", ".jpg")))
            if jpgs:
                im = _img(os.path.join(tex, jpgs[0]))
                for o in objets:
                    if o.type == "MESH":
                        o.data.materials.clear()
                        o.data.materials.append(_mat_depuis_image(o.name + "_mat", im, 0.35))
        if action:
            act = next((a for a in bpy.data.actions if action.lower() in a.name.lower()
                        and not a.name.lower().startswith("camera")), None)
            for o in objets:
                if o.type == "ARMATURE" and act is not None:
                    if o.animation_data is None:
                        o.animation_data_create()
                    o.animation_data.action = act

    # Étendue de l'animation : union des actions réellement posées.
    d, f = 1e9, -1e9
    for o in objets:
        ad = o.animation_data
        if ad and ad.action:
            a, b = ad.action.frame_range
            if b > a:
                d, f = min(d, a), max(f, b)
    if d > f:
        d, f = 1.0, 1.0
    t = pose / max(1, nb_poses)          # on évite la dernière image, = la 1re
    bpy.context.scene.frame_set(int(round(d + (f - d) * t)))

    porte = bpy.data.objects.new("porte_anime", None)
    bpy.context.collection.objects.link(porte)
    for o in objets:
        if o.parent is None:
            o.parent = porte
            o.matrix_parent_inverse = Matrix.Identity(4)
    bpy.context.view_layer.update()
    return [porte] + objets


def _sans_ombre_arriere(objets):
    """Les feuillages importés sont souvent des plans à alpha : sans
    « transparent shadows » ils projettent des ombres carrées."""
    vus = set()
    for o in objets:
        if o.type != "MESH":
            continue
        for sl in o.material_slots:
            m = sl.material
            if m is None or m.name in vus:
                continue
            vus.add(m.name)
            m.use_backface_culling = False
            if hasattr(m, "shadow_method"):
                m.shadow_method = "CLIP"


# ───────────────────────────────────────────────────────────────────────────
#  Fabrique : nom + variante → liste d'objets, déjà mis à l'échelle du panneau
# ───────────────────────────────────────────────────────────────────────────

def _materiaux():
    return {
        # Écorce photographiée (Poly Haven « Jolcham Oak Bark 01 », CC0) dépliée
        # à l'échelle réelle. Le chêne vert est teinté plus sombre et plus gris
        # que le pubescent, comme dans la nature.
        "ecorce_vert": (mat_ecorce_photo("ecorce_chene_vert", ECORCE_CC0,
                                         "jolcham_oak_bark_01", (0.62, 0.60, 0.60), 1.1)
                        if os.path.isdir(ECORCE_CC0) else
                        mat_ecorce("ecorce_chene_vert", (0.105, 0.092, 0.076), (0.028, 0.026, 0.024), 11.0)),
        "ecorce_pub": (mat_ecorce_photo("ecorce_chene_pub", ECORCE_CC0,
                                        "jolcham_oak_bark_01", (0.90, 0.86, 0.80), 1.0)
                       if os.path.isdir(ECORCE_CC0) else
                       mat_ecorce("ecorce_chene_pub", (0.150, 0.133, 0.108), (0.040, 0.036, 0.031), 9.0)),
        "ecorce_buis": mat_ecorce("ecorce_buisson", (0.130, 0.110, 0.080), (0.036, 0.031, 0.024), 18.0),
        # chêne vert : feuille coriace, vert sombre, revers glauque
        "feuille_vert": mat_feuille("feuille_chene_vert", (0.028, 0.055, 0.020),
                                    (0.075, 0.135, 0.048), (0.34, 0.46, 0.16),
                                    brillance=0.45, part_trans=0.40),
        # chêne pubescent : vert plus clair et plus jaune, feuille fine
        "feuille_pub": mat_feuille("feuille_chene_pub", (0.055, 0.095, 0.028),
                                   (0.155, 0.215, 0.062), (0.48, 0.58, 0.19),
                                   brillance=0.28, part_trans=0.48),
        "feuille_buis": mat_feuille("feuille_buisson", (0.045, 0.070, 0.024),
                                    (0.125, 0.150, 0.050), (0.38, 0.42, 0.15),
                                    brillance=0.40, part_trans=0.40),
        "feuille_morte": mat_feuille("feuille_morte", (0.19, 0.105, 0.042),
                                     (0.40, 0.235, 0.095), (0.44, 0.26, 0.10),
                                     brillance=0.20, part_trans=0.30),
        "calcaire": mat_calcaire("calcaire"),
        "paille": mat_paille("paille"),
        "terre": mat_terre("terre"),
    }


# Facteur de taille par variante : une petite, une moyenne, une grande.
# Bornée à 1,0 pour que la plus grande remplisse tout juste le panneau.
FACTEUR = (0.80, 0.905, 1.0)


def fabriquer(nom, variante, mats, nb_variantes=3, echelle_imposee=None,
              marge_imposee=None):
    """Construit (ou importe) l'objet, puis le met au panneau.

    Renvoie (objets, rayon_contact, k) — k est l'homothétie appliquée, qu'on
    réutilise telle quelle pour les autres poses d'un animal : sinon la bête
    change de taille d'une pose à l'autre."""
    H = CATALOGUE[nom]
    graine = (abs(hash(nom)) % 100000) + variante * 7919
    plafond = H * (1.0 - MARGE_BAS)
    cible_h = plafond * FACTEUR[min(variante, len(FACTEUR) - 1)]

    if nom in ANIMAUX:
        rel, taille, action = ANIMAUX[nom]
        objets = importer_anime(os.path.join(CC0, rel), variante, nb_variantes,
                                action, graine)
        _sans_ombre_arriere(objets)
        cible_h = taille          # taille RÉELLE, pas « remplir le panneau »
    elif nom in MODELES and os.path.isfile(os.path.join(CC0, MODELES[nom][variante % 3])):
        objets = importer_gltf(os.path.join(CC0, MODELES[nom][variante % 3]), graine)
        _sans_ombre_arriere(objets)
    elif nom == "chene_vert":
        # Chêne vert : tronc court, houppier dense et arrondi, feuille petite
        # et coriace. Six générations : c'est ce qu'il faut pour que la masse se
        # ferme sans que les rameaux deviennent des tuyaux.
        R = ReglesArbre(prof_max=6, enfants=(3, 4), ratio_long=0.74, ratio_rayon=0.68,
                        angle=(0.50, 1.00), sinuosite=0.17, gravite=-0.10,
                        phototropisme=0.22, effilement=0.35,
                        tronc_h=0.26, tronc_r=0.040, plancher=0.30,
                        depart=(3, 4), feuille_l=0.115, feuille_r=0.52,
                        feuilles_par_rameau=6, par_rosette=5, prof_feuilles=3)
        objets = batir_arbre(nom, graine, R, mats["ecorce_vert"], mats["feuille_vert"], cible_h)
    elif nom == "chene_pubescent":
        # Chêne pubescent : plus haut, plus ouvert, branches tortueuses,
        # feuillage plus clair et moins serré — on voit à travers.
        R = ReglesArbre(prof_max=6, enfants=(3, 4), ratio_long=0.78, ratio_rayon=0.70,
                        angle=(0.70, 1.40), sinuosite=0.30, gravite=-0.18,
                        phototropisme=0.24, effilement=0.40,
                        tronc_h=0.40, tronc_r=0.034, plancher=0.40,
                        depart=(2, 3), feuille_l=0.17, feuille_r=0.62,
                        feuilles_par_rameau=6, par_rosette=4, prof_feuilles=3)
        objets = batir_arbre(nom, graine, R, mats["ecorce_pub"], mats["feuille_pub"], cible_h)
    elif nom == "buisson":
        objets = batir_buisson(nom, graine, mats["ecorce_buis"], mats["feuille_buis"], cible_h)
    elif nom == "rocher":
        objets = batir_rocher(nom, graine, mats["calcaire"], cible_h)
    elif nom == "herbe_seche":
        objets = batir_herbe(nom, graine, mats["paille"], cible_h)
    elif nom == "tas_feuilles":
        objets = batir_tas_feuilles(nom, graine, mats["terre"], mats["feuille_morte"], cible_h)
    else:
        raise ValueError("objet inconnu : " + nom)

    # ── mise au panneau ──────────────────────────────────────────────────
    # On ne peut PAS cadrer sur la boîte 3D : en projection ortho inclinée, un
    # point proche de la caméra DESCEND dans l'image de tan(36°) × sa distance.
    # Un houppier large déborde donc par le haut d'un côté et par le bas de
    # l'autre, selon l'azimut. Et les coins bas-larges de la boîte n'existent
    # pas (pas de feuilles au ras du sol sous le bord du houppier). On projette
    # donc les VRAIS sommets, sur les 8 azimuts, et on applique l'homothétie
    # qui fait tenir le pire cas dans [−0,12·H ; +0,88·H] × [−H/2 ; +H/2].
    co = _sommets(objets)
    # ANCRAGE. Le point (0, 0, 0) du panneau est le PIED de l'objet : c'est lui
    # que Godot posera sur le terrain. Les constructeurs procéduraux plantent
    # déjà le tronc là ; il ne faut surtout pas les recentrer.
    #
    # Deux erreurs mesurées avant d'arriver là :
    #   · caler z sur le sommet le plus BAS remontait tout l'arbre de la hauteur
    #     du rameau le plus retombant → pied à 14,1 % du bas au lieu de 12 % ;
    #   · centrer x/y sur la boîte décalait le tronc hors de l'axe, et comme en
    #     ortho inclinée un déport horizontal de d fait monter l'image de
    #     tan(36°)·d, la ligne de sol se mettait à bouger d'un angle à l'autre
    #     (+0,010·H à l'azimut 0, −0,037·H à 45°).
    # Un houppier asymétrique sort donc décentré dans le panneau : c'est juste,
    # un vrai chêne l'est aussi.
    if nom in ANIMAUX or nom in MODELES:
        cx = 0.5 * (co[:, 0].min() + co[:, 0].max())
        cy = 0.5 * (co[:, 1].min() + co[:, 1].max())
        cz = co[:, 2].min()
    else:
        cx = cy = cz = 0.0
    co = co - np.array([cx, cy, cz])
    s_haut, s_bas, h_max = _projeter(co)

    fige = echelle_imposee is not None
    cible = cible_h if nom in ANIMAUX else plafond * FACTEUR[min(variante, len(FACTEUR) - 1)]

    # MARGE BASSE, calculée et non plus constante.
    #
    # En ortho inclinée de t, un déport horizontal de R vers la caméra descend à
    # l'écran de R·sin(t), quand la marge n'offre que marge·H·cos(t). Il faut
    # donc  marge ≥ R·tan(t)/H. À 36° avec marge 0,12 ça plafonne le rayon à
    # 0,165·H : parfait pour un arbre, absurde pour un sanglier, qui est plus
    # long que haut. On calcule donc la marge dont chaque prop a besoin, avec
    # 10 % de sécurité, et on la déclare dans le manifeste.
    #
    # L'échelle et la marge se déterminent l'une l'autre (la marge dépend du
    # rayon, qui dépend de l'échelle, qui dépend de la marge) : trois tours de
    # point fixe suffisent largement à converger.
    # La borne théorique 1,1·R·tan(t)/H suppose que TOUT le rayon horizontal
    # touche le sol. C'est vrai d'un sanglier, faux d'un arbre : son houppier
    # est large mais haut, donc sa projection vers le bas est rattrapée par sa
    # hauteur. Mesuré sur le chêne vert, elle réservait 0,328·H pour un besoin
    # réel de 0,107·H — un tiers de panneau perdu. On prend donc la descente
    # RÉELLE de la géométrie, s_bas, qui est la même grandeur mesurée au lieu
    # d'être majorée, plus 6 % de sécurité.
    # Si la marge est imposée (passe 2 : toutes les variantes d'un prop
    # partagent le même panneau, donc la marge la plus exigeante des trois), on
    # ne résout plus rien — on cadre dedans. Sans ça, la plus petite variante se
    # recadrait sur SA marge, plus faible, et son sommet sortait par le haut du
    # panneau réellement utilisé.
    marge = MARGE_BAS if marge_imposee is None else marge_imposee
    k = echelle_imposee if fige else 1.0
    for _ in range(1 if marge_imposee is not None else 6):
        if not fige:
            k = (cible_h if nom in ANIMAUX
                 else H * (1.0 - marge) * FACTEUR[min(variante, len(FACTEUR) - 1)])
            k = k / max(s_haut, 1e-4)
            k = min(k, (H * 0.5 * 0.98) / max(h_max, 1e-4))
            k = min(k, (H * (1.0 - marge)) / max(s_haut, 1e-4))
        if marge_imposee is not None:
            break
        marge_v = MARGE_BAS
        if s_bas < 0.0:
            marge_v = max(marge_v, 1.06 * abs(s_bas) * k / H)
        marge_v = min(marge_v, 0.55)      # au-delà, le panneau ne sert plus à rien
        if abs(marge_v - marge) < 5e-4:
            marge = marge_v
            break
        marge = marge_v
    debord = max(0.0, abs(s_bas) * k - H * marge) if s_bas < 0 else 0.0
    if debord > 1e-4:
        print("    ! %s v%d : %.1f px de débordement sous le panneau"
              % (nom, variante, debord / H * HAUT_PX))

    # Le porte-objet : c'est lui qui porte l'homothétie et le recalage. On ne
    # touche pas aux maillages, ce qui laisse fonctionner les armatures.
    porte = bpy.data.objects.new("panneau_" + nom, None)
    bpy.context.collection.objects.link(porte)
    for o in objets:
        if o.parent is None:
            o.parent = porte
            o.matrix_parent_inverse = Matrix.Identity(4)
    porte.scale = (k, k, k)
    porte.location = (-cx * k, -cy * k, -cz * k)
    bpy.context.view_layer.update()

    # À 36° d'inclinaison, un disque de rayon R descend de tan(36°)·R sous la
    # ligne de sol. Pour que la tache tienne dans la marge, il faut
    # R ≤ marge·H / tan(36°). Au-delà elle serait coupée net par le bord
    # inférieur, et ça se verrait comme un trait.
    rayon_max = H * marge / math.tan(TILT)
    rayon_contact = max(1e-3, min(h_max * k * 1.15, rayon_max))
    return [porte] + objets, rayon_contact, k, marge


def _sommets(objets):
    """Tous les sommets, en coordonnées monde, dans un tableau numpy (n, 3).
    Passe par le graphe de dépendances : un maillage déformé par une armature
    n'a PAS ses sommets posés dans `mesh.vertices`."""
    dg = bpy.context.evaluated_depsgraph_get()
    lots = []
    for ob in objets:
        if ob.type not in {"MESH", "CURVE", "SURFACE", "FONT"}:
            continue
        oe = ob.evaluated_get(dg)
        try:
            me = oe.to_mesh()
        except RuntimeError:
            continue
        n = len(me.vertices)
        if n:
            brut = np.empty(n * 3, dtype=np.float64)
            me.vertices.foreach_get("co", brut)
            m = np.array(oe.matrix_world.to_4x4()).reshape(4, 4)
            lots.append(brut.reshape(n, 3) @ m[:3, :3].T + m[:3, 3])
        oe.to_mesh_clear()
    return np.vstack(lots) if lots else np.zeros((1, 3))


def _projeter(co):
    """Ordonnée écran extrême (haut, bas) et demi-largeur extrême, sur les 8
    azimuts. L'ordonnée écran est déjà divisée par cos(TILT), donc comparable
    à une hauteur monde : on la compare directement à 0,88·H et −0,12·H."""
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    tt = math.tan(TILT)
    s_haut, s_bas, h_max = -1e9, 1e9, 0.0
    for a in range(ANGLES):
        az = 2.0 * math.pi * a / ANGLES
        ca, sa = math.cos(az), math.sin(az)
        sv = z + tt * (-x * sa + y * ca)
        s_haut = max(s_haut, float(sv.max()))
        s_bas = min(s_bas, float(sv.min()))
        h_max = max(h_max, float(np.abs(x * ca + y * sa).max()))
    return s_haut, s_bas, h_max


# ───────────────────────────────────────────────────────────────────────────
#  La scène : ciel, soleil, sol de rebond, disque de contact, caméra
# ───────────────────────────────────────────────────────────────────────────

def dir_soleil():
    """Vecteur unitaire VERS le soleil, dans le repère Blender."""
    return Vector((math.cos(SOL_EL) * math.sin(SOL_AZ),
                   -math.cos(SOL_EL) * math.cos(SOL_AZ),
                   math.sin(SOL_EL)))


def monter_scene(force_soleil=3.6, force_ciel=1.80, ciel_hdri=True):
    sc = bpy.context.scene

    # ── le ciel ──────────────────────────────────────────────────────────
    # Fixe dans le monde, comme le soleil : c'est la même règle. Si le ciel
    # tournait avec la caméra, les reflets et l'ambiante mentiraient aussi.
    monde = bpy.data.worlds.new("ciel_ardeche")
    sc.world = monde
    monde.use_nodes = True
    nt = monde.node_tree
    nt.nodes.clear()
    sortie = nt.nodes.new("ShaderNodeOutputWorld")
    sortie.location = (400, 0)
    fond = nt.nodes.new("ShaderNodeBackground")
    fond.location = (200, 0)
    fond.inputs["Strength"].default_value = force_ciel
    nt.links.new(fond.outputs["Background"], sortie.inputs["Surface"])

    if ciel_hdri and os.path.isfile(HDRI):
        coord = nt.nodes.new("ShaderNodeTexCoord")
        coord.location = (-800, 0)
        mapg = nt.nodes.new("ShaderNodeMapping")
        mapg.location = (-620, 0)
        # rotation mesurée : on amène l'azimut du soleil de l'HDRI sur le nôtre
        cible = math.atan2(math.cos(SOL_EL) * -math.cos(SOL_AZ),
                           math.cos(SOL_EL) * math.sin(SOL_AZ))
        mapg.inputs["Rotation"].default_value[2] = cible - HDRI_AZ
        nt.links.new(coord.outputs["Generated"], mapg.inputs["Vector"])
        env = nt.nodes.new("ShaderNodeTexEnvironment")
        env.location = (-420, 0)
        env.image = _img(HDRI)
        nt.links.new(mapg.outputs["Vector"], env.inputs["Vector"])
        # écrêtage : le disque solaire de cet HDRI culmine à 1,1 × 10⁵ et il est
        # à 43°. On le ramène sous le seuil pour qu'il ne porte pas une seconde
        # ombre — la lumière directe vient de NOTRE soleil, à 0,42 rad.
        clamp = nt.nodes.new("ShaderNodeMath")
        clamp.location = (-220, -160)
        clamp.operation = "MINIMUM"
        clamp.inputs[1].default_value = 6.0
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        sep.location = (-220, 120)
        nt.links.new(env.outputs["Color"], sep.inputs["Color"])
        lum = nt.nodes.new("ShaderNodeMath")
        lum.location = (-40, 200)
        lum.operation = "MAXIMUM"
        nt.links.new(sep.outputs["Red"], lum.inputs[0])
        nt.links.new(sep.outputs["Green"], lum.inputs[1])
        lum2 = nt.nodes.new("ShaderNodeMath")
        lum2.location = (-40, 40)
        lum2.operation = "MAXIMUM"
        nt.links.new(lum.outputs["Value"], lum2.inputs[0])
        nt.links.new(sep.outputs["Blue"], lum2.inputs[1])
        nt.links.new(lum2.outputs["Value"], clamp.inputs[0])
        fac = nt.nodes.new("ShaderNodeMath")
        fac.location = (0, -300)
        fac.operation = "DIVIDE"
        fac.use_clamp = False
        nt.links.new(clamp.outputs["Value"], fac.inputs[0])
        maxi = nt.nodes.new("ShaderNodeMath")
        maxi.location = (-220, -320)
        maxi.operation = "MAXIMUM"
        maxi.inputs[1].default_value = 1e-4
        nt.links.new(lum2.outputs["Value"], maxi.inputs[0])
        nt.links.new(maxi.outputs["Value"], fac.inputs[1])
        mul = nt.nodes.new("ShaderNodeVectorMath")
        mul.location = (40, -60)
        mul.operation = "SCALE"
        nt.links.new(env.outputs["Color"], mul.inputs[0])
        nt.links.new(fac.outputs["Value"], mul.inputs["Scale"])
        nt.links.new(mul.outputs["Vector"], fond.inputs["Color"])
    else:
        ciel = nt.nodes.new("ShaderNodeTexSky")
        ciel.location = (-400, 0)
        ciel.sky_type = "NISHITA"
        ciel.sun_disc = False          # le disque solaire est joué par la lampe Sun
        ciel.sun_elevation = SOL_EL
        ciel.sun_rotation = math.atan2(-math.cos(SOL_AZ), math.sin(SOL_AZ))
        ciel.altitude = 250.0
        ciel.air_density = 1.0
        ciel.dust_density = 1.6
        ciel.ozone_density = 1.0
        nt.links.new(ciel.outputs["Color"], fond.inputs["Color"])

    # ── le soleil ────────────────────────────────────────────────────────
    ld = bpy.data.lights.new("soleil", "SUN")
    ld.energy = force_soleil
    ld.color = (1.0, 0.94, 0.82)
    # 0,5° (le vrai diamètre du Soleil) donne un bord d'ombre au couteau qui se
    # lit comme une planche. 2,8° adoucit la pénombre sans toucher à l'azimut.
    ld.angle = math.radians(2.8)
    soleil = bpy.data.objects.new("soleil", ld)
    bpy.context.collection.objects.link(soleil)
    d = dir_soleil()
    soleil.location = d * 120.0
    # une lampe Sun éclaire selon son −Z : on l'oriente vers l'origine
    soleil.rotation_mode = "QUATERNION"
    soleil.rotation_quaternion = Vector((0.0, 0.0, -1.0)).rotation_difference(-d)

    # ── sol de rebond : invisible à la caméra, mais il renvoie la lumière ──
    # C'est lui qui empêche le dessous des houppiers d'être noir. La garrigue
    # sèche renvoie beaucoup, et chaud.
    me = bpy.data.meshes.new("sol_rebond")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=200.0)
    bm.to_mesh(me)
    bm.free()
    m, ntm, sm = _mat_neuf("sol_rebond")
    p = ntm.nodes.new("ShaderNodeBsdfDiffuse")
    p.inputs["Color"].default_value = (0.32, 0.28, 0.19, 1.0)
    ntm.links.new(p.outputs["BSDF"], sm.inputs["Surface"])
    me.materials.append(m)
    sol = bpy.data.objects.new("sol_rebond", me)
    sol.location = (0, 0, -0.004)
    bpy.context.collection.objects.link(sol)
    sol.visible_camera = False
    sol.visible_shadow = False     # il ne doit pas s'ombrer lui-même sur le disque
    sol.visible_glossy = False

    # ── disque de contact : attrape-ombre à bord fondu ───────────────────
    med = bpy.data.meshes.new("contact")
    bmd = bmesh.new()
    bmesh.ops.create_circle(bmd, cap_ends=True, segments=48, radius=1.0)
    bmd.to_mesh(med)
    bmd.free()
    med.materials.append(mat_contact())
    disque = bpy.data.objects.new("contact", med)
    bpy.context.collection.objects.link(disque)
    disque.is_shadow_catcher = True

    # ── caméra ───────────────────────────────────────────────────────────
    cd = bpy.data.cameras.new("cam")
    cd.type = "ORTHO"
    cd.sensor_fit = "VERTICAL"     # ortho_scale = extension VERTICALE = H·cos(t)
    cd.clip_start = 1.0
    cd.clip_end = 1000.0
    cam = bpy.data.objects.new("cam", cd)
    bpy.context.collection.objects.link(cam)
    sc.camera = cam

    return cam, disque, soleil


def assainir(chemin, seuil=0.04):
    """Remet à zéro les alphas résiduels. Le débruiteur laisse un voile de
    quelques millièmes sur tout le cadre (mesuré : 0,024 dans les coins). Sans
    conséquence avec une découpe à 0,5, mais ça salit les bords en mélange
    alpha, et ça gonfle le PNG."""
    img = bpy.data.images.load(chemin)
    n = img.size[0] * img.size[1] * 4
    px = np.empty(n, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(-1, 4)
    faible = px[:, 3] < seuil
    px[faible] = 0.0
    img.pixels.foreach_set(px.ravel())
    img.file_format = "PNG"
    img.filepath_raw = chemin
    img.save()
    bpy.data.images.remove(img)


def viser(cam, az, H, marge=MARGE_BAS):
    """Place la caméra pour l'angle `az` et le panneau de hauteur H. C'EST LE CONTRAT.

    Le panneau va de −marge·H à (1−marge)·H : son centre est donc à
    (0,5 − marge)·H au-dessus de la base. Avec la marge nominale de 0,12 on
    retrouve bien les 0,38·H du contrat."""
    D = 120.0
    centre = (0.5 - marge) * H
    cible = Vector((0.0, 0.0, centre))
    cam.data.ortho_scale = H * math.cos(TILT)
    cam.location = Vector((math.sin(az) * math.cos(TILT) * D,
                           -math.cos(az) * math.cos(TILT) * D,
                           math.sin(TILT) * D + centre))
    direction = cible - cam.location
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = direction.to_track_quat("-Z", "Y")


def reglages_rendu(echantillons, haut_px, gpu=True):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    largeur = int(round(haut_px / math.cos(TILT)))
    sc.render.resolution_x = largeur
    sc.render.resolution_y = haut_px
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.color_depth = "8"
    sc.render.image_settings.compression = 20
    # Vue « Standard » : le jeu fait son propre rendu de tons. Un AgX ici
    # délaverait les sprites et Godot ne pourrait pas le rattraper.
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0

    c = sc.cycles
    c.samples = echantillons
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.012
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    c.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    # Le cœur d'un houppier n'est sombre que si la lumière y rebondit : à 4
    # rebonds diffus il sortait uniforme et plastique.
    c.max_bounces = 14
    c.diffuse_bounces = 8
    c.glossy_bounces = 2
    c.transmission_bounces = 4
    c.transparent_max_bounces = 8
    c.volume_bounces = 0
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.use_fast_gi = False
    c.film_exposure = 1.0

    peripherique = "CPU"
    if gpu:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for essai in ("OPTIX", "CUDA"):
            try:
                prefs.compute_device_type = essai
            except TypeError:
                continue
            prefs.get_devices()
            trouves = [d for d in prefs.devices if d.type == essai]
            if trouves:
                for d in prefs.devices:
                    d.use = (d.type == essai)
                c.device = "GPU"
                peripherique = "%s (%s)" % (essai, trouves[0].name)
                break
        else:
            c.device = "CPU"
    else:
        c.device = "CPU"
    return peripherique, largeur


# ───────────────────────────────────────────────────────────────────────────
#  Boucle principale
# ───────────────────────────────────────────────────────────────────────────

def _oublier(objets):
    """Retire les objets ET leurs enfants — un import glTF ou .blend en accroche
    tout un arbre, et les laisser gonflerait la scène jusqu'au manque de VRAM."""
    aret = set()
    pile = list(objets)
    while pile:
        o = pile.pop()
        if o is None or o.name in aret:
            continue
        aret.add(o.name)
        pile.extend(list(o.children))
    for nom in aret:
        ob = bpy.data.objects.get(nom)
        if ob is not None:
            bpy.data.objects.remove(ob, do_unlink=True)
    for bloc in (bpy.data.meshes, bpy.data.armatures):
        for d in list(bloc):
            if d.users == 0:
                bloc.remove(d)


def vider_objets():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(prog="usine.py", description="Usine à sprites Jupire")
    ap.add_argument("--sortie", default=None, help="dossier textures/sprites")
    ap.add_argument("--props", default=None, help="liste séparée par des virgules")
    ap.add_argument("--variantes", type=int, default=VARIANTES)
    ap.add_argument("--angles", type=int, default=ANGLES)
    ap.add_argument("--echantillons", type=int, default=160)
    ap.add_argument("--haut-px", type=int, default=HAUT_PX, dest="haut_px")
    ap.add_argument("--cpu", action="store_true", help="forcer le CPU")
    ap.add_argument("--sans-contact", action="store_true", dest="sans_contact",
                    help="rendre sans la tache de contact (contrôle du cadrage)")
    ap.add_argument("--ciel", default="hdri", choices=("hdri", "nishita"),
                    help="HDRI Poly Haven écrêté (défaut) ou ciel Nishita calculé")
    ap.add_argument("--pas-de-manifeste", action="store_true", dest="sans_manifeste")
    args = ap.parse_args(argv)

    racine = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          "..", ".."))
    sortie = args.sortie or os.path.join(racine, "textures", "sprites")
    os.makedirs(sortie, exist_ok=True)

    props = [p.strip() for p in args.props.split(",")] if args.props else list(ORDRE)
    for p in props:
        if p not in CATALOGUE:
            raise SystemExit("objet inconnu : " + p)

    vider_objets()
    peripherique, largeur = reglages_rendu(args.echantillons, args.haut_px, gpu=not args.cpu)
    cam, disque, soleil = monter_scene(ciel_hdri=(args.ciel == 'hdri'))
    mats = _materiaux()

    print("=" * 62)
    print("USINE JUPIRE — Cycles sur %s" % peripherique)
    print("  image %d × %d px   tilt %.1f°   %d angles   %d échantillons"
          % (largeur, args.haut_px, math.degrees(TILT), args.angles, args.echantillons))
    print("=" * 62)

    manifeste = {
        "tilt_deg": round(math.degrees(TILT), 4),
        "angles": args.angles,
        "soleil_az": SOL_AZ,
        "soleil_el": SOL_EL,
        "marge_bas": MARGE_BAS,
        "haut_px": args.haut_px,
        "props": {},
    }

    t_total = time.time()
    n_img = 0
    for nom in props:
        H = CATALOGUE[nom]
        os.makedirs(os.path.join(sortie, nom), exist_ok=True)
        images = []
        marges = []
        echelle = None
        # Passe 1 : construire chaque variante juste pour connaître sa marge.
        # Le panneau est le même pour toutes (Godot pose un quad par prop), donc
        # la visée doit utiliser la marge la plus exigeante des trois. La
        # construction est bien plus rapide que le rendu, la passe se paie.
        for v in range(args.variantes):
            objets, rc, k, marge = fabriquer(nom, v, mats, args.variantes, echelle)
            if nom in ANIMAUX and echelle is None:
                echelle = k
            marges.append(marge)
            _oublier(objets)
        marge = round(max(marges), 4)

        for v in range(args.variantes):
            t0 = time.time()
            objets, rc, k, _m = fabriquer(nom, v, mats, args.variantes, echelle, marge)
            disque.scale = (rc, rc, 1.0)
            disque.location = (0.0, 0.0, -20.0 if args.sans_contact else 0.0)
            tris = sum(len(o.data.polygons) for o in objets if o.type == "MESH")
            jeu = []
            for a in range(args.angles):
                az = 2.0 * math.pi * a / args.angles
                viser(cam, az, H, marge)
                chemin = os.path.join(sortie, nom, "v%d_a%d.png" % (v, a))
                bpy.context.scene.render.filepath = chemin
                bpy.ops.render.render(write_still=True)
                assainir(chemin)
                jeu.append("%s/v%d_a%d.png" % (nom, v, a))
                n_img += 1
            images.append(jeu)
            _oublier(objets)
            print("  %-16s v%d  %5d faces  %6.1f s" % (nom, v, tris, time.time() - t0))
        # Une seule marge pour les N variantes d'un prop : le jeu place un
        # quad par prop, pas par variante. On prend la plus exigeante.
        marge_prop = marge if marges else MARGE_BAS
        manifeste["props"][nom] = {
            "hauteur_m": H,
            "marge_bas": marge_prop,
            "variantes": args.variantes,
            # pour les animaux la variante est une POSE du cycle d'animation,
            # pour le reste c'est une forme différente du même objet
            "variante_est": "pose" if nom in ANIMAUX else "forme",
            "images": images,
        }

    if not args.sans_manifeste:
        chemin_m = os.path.join(sortie, "manifeste.json")
        anc = {}
        if os.path.exists(chemin_m):
            try:
                with open(chemin_m, "r", encoding="utf-8") as f:
                    anc = json.load(f).get("props", {})
            except Exception:
                anc = {}
        anc.update(manifeste["props"])
        manifeste["props"] = {k: anc[k] for k in ORDRE if k in anc}
        with open(chemin_m, "w", encoding="utf-8") as f:
            json.dump(manifeste, f, indent=1, ensure_ascii=False)
        print("manifeste → %s" % chemin_m)

    dt = time.time() - t_total
    print("=" * 62)
    print("%d images en %.1f s  (%.2f s/image)  sur %s"
          % (n_img, dt, dt / max(n_img, 1), peripherique))


if __name__ == "__main__":
    main()
