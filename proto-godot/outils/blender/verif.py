#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contrôle visuel des sprites. À lancer avec le Python de Blender (numpy inclus) :

  blender --background --python verif.py -- <png…> --sortie planche.png

Compose les PNG RGBA sur un gris moyen et trace les repères du contrat :
  · ligne ROUGE  = le sol de l'objet (z=0), à 0,88 de haut du panneau ;
  · ligne BLEUE  = axe vertical du panneau ;
  · cadre VERT   = l'emprise utile (le panneau de H × H vu à 36°).
Affiche aussi, pour chaque image, la boîte des pixels opaques en fractions de
panneau : c'est la mesure qui dit si l'objet déborde ou s'il flotte.
"""
import sys, os, math, json
import numpy as np

TILT = math.radians(36.0)
MARGE_BAS = 0.12


def lire(chemin):
    import bpy
    img = bpy.data.images.load(chemin)
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]  # haut→bas
    bpy.data.images.remove(img)
    return a


MARGE = MARGE_BAS


def mesurer(a, seuil=0.25):
    """Boîte des pixels dont alpha > `seuil`, en fraction de panneau, PLUS la
    ligne de base du tronc.

    La distinction est le point qui prête à confusion : le contrat place la
    BASE DE L'OBJET à 12 % du bord inférieur, pas le pixel opaque le plus bas.
    Vu à 36° d'inclinaison, tout ce qui est devant le tronc descend dans l'image
    de tan(36°) × sa distance — un houppier de 3,4 m de rayon occupe donc
    légitimement 2,5 m de panneau SOUS sa propre ligne de sol. On mesure donc
    séparément le pied du tronc, dans la bande centrale de l'image."""
    h, w, _ = a.shape
    al = a[:, :, 3]
    m = al > seuil
    if not m.any():
        return None
    ys, xs = np.where(m)
    sol = (1.0 - MARGE) * h                # ligne z=0 en pixels depuis le haut
    # pied du tronc : bas de la colonne opaque centrale (bande de ±2 % de large)
    b = max(2, int(w * 0.02))
    bande = al[:, w // 2 - b:w // 2 + b + 1] > 0.5
    lignes = np.where(bande.any(axis=1))[0]
    pied = int(lignes.max()) if len(lignes) else -1
    return dict(z_bas=(sol - ys.max()) / h, z_haut=(sol - ys.min()) / h,
                x_g=(xs.min() - w / 2.0) / w, x_d=(xs.max() - w / 2.0) / w,
                lum=float(a[:, :, :3][m].mean()), couv=float(m.mean()),
                l_haut=int(ys.min()), l_bas=int(ys.max()), pied=pied,
                sol=sol, h=h,
                coins=float(np.max([al[0, 0], al[0, -1], al[-1, 0], al[-1, -1]])))


def composer(a, fond=(0.45, 0.47, 0.50)):
    h, w, _ = a.shape
    al = a[:, :, 3:4]
    rgb = a[:, :, :3] * al + np.array(fond, dtype=np.float32) * (1.0 - al)
    return np.clip(rgb, 0, 1)


def reperes(rgb):
    h, w, _ = rgb.shape
    sol = int(round((1.0 - MARGE) * h))
    rgb[max(0, min(sol, h - 1) - 1):min(sol + 1, h), :] = (0.9, 0.1, 0.1)
    c = w // 2
    rgb[::6, c:c + 1] = (0.2, 0.4, 1.0)
    rgb[0:1, :] = rgb[h - 1:h, :] = (0.1, 0.8, 0.2)
    rgb[:, 0:1] = rgb[:, w - 1:w] = (0.1, 0.8, 0.2)
    return rgb


def main():
    import bpy
    argv = sys.argv[sys.argv.index("--") + 1:]
    sortie = "planche.png"
    if "--sortie" in argv:
        i = argv.index("--sortie")
        sortie = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    cols = 4
    if "--cols" in argv:
        i = argv.index("--cols")
        cols = int(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    global MARGE
    if "--marge" in argv:
        i = argv.index("--marge")
        MARGE = float(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    brut = "--brut" in argv
    argv = [x for x in argv if x != "--brut"]

    vign = []
    for c in argv:
        a = lire(c)
        m = mesurer(a)
        if m:
            print("%-30s lignes %3d..%3d | pied tronc %3d (attendu %3.0f, soit "
                  "%.1f%% du bas) | z[%+.3f..%+.3f] x[%+.3f..%+.3f] lum %.3f "
                  "couv %.1f%% coins a=%.3f"
                  % (os.path.basename(os.path.dirname(c)) + "/" + os.path.basename(c),
                     m["l_haut"], m["l_bas"], m["pied"], m["sol"],
                     (m["h"] - m["pied"]) / m["h"] * 100,
                     m["z_bas"], m["z_haut"], m["x_g"], m["x_d"], m["lum"],
                     m["couv"] * 100, m["coins"]))
        else:
            print("%-42s VIDE" % c)
        r = composer(a)
        if not brut:
            r = reperes(r)
        vign.append(r)

    if not vign:
        return
    hh = max(v.shape[0] for v in vign)
    ww = max(v.shape[1] for v in vign)
    lignes = (len(vign) + cols - 1) // cols
    planche = np.zeros((lignes * hh, cols * ww, 4), dtype=np.float32)
    planche[:, :, 3] = 1.0
    for i, v in enumerate(vign):
        r, c = divmod(i, cols)
        planche[r * hh:r * hh + v.shape[0], c * ww:c * ww + v.shape[1], :3] = v

    img = bpy.data.images.new("planche", cols * ww, lignes * hh, alpha=True)
    img.pixels = planche[::-1].ravel().tolist()
    img.file_format = "PNG"
    img.filepath_raw = os.path.abspath(sortie)
    # sRGB : sans ça la planche sort délavée et on juge mal la luminosité
    img.save()
    print("planche →", sortie)


if __name__ == "__main__":
    main()
