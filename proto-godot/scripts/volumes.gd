# Les volumes 3D que l'usine photographie.
#
# Volontairement grossiers : c'est l'argument. Un sprite affiché à 40 px de haut
# ne montre pas la qualité de la géométrie — c'est toute l'économie d'AoE2. Ces
# formes sont donc du placeholder assumé, remplaçables une par une par un modèle
# CC0 (Kenney, Quaternius, Poly Haven) ou un arbre de geometry nodes, SANS
# toucher au reste de la chaîne.
#
# Chaque volume a sa base à y = 0 et tient sous la hauteur annoncée au
# CATALOGUE (moins la marge du bas, réservée à la tache de contact).

class_name Volumes
extends RefCounted

# nom → hauteur du panneau, en mètres
const CATALOGUE := {
	"chene_vert": 9.0,
	"chene_pubescent": 12.0,
	"peuplier": 16.0,
	"buisson": 2.6,
	"rocher": 3.4,
	"ruine": 7.0,
	"perso": 2.0,
	# litière au sol : ce qui manquait pour que le sol ait une échelle entre
	# l'arbre et le caillou. Semé dense, c'est ce qui fait « ça grouille ».
	"herbe_seche": 0.9,
	"feuilles": 0.6,
	# faune. Les trois VARIANTES ne servent plus ici à casser la répétition mais
	# à porter une POSE : c'est l'animation la moins chère qui soit, puisque
	# l'usine les fabrique déjà toutes les trois.
	"chevreuil": 1.7,      # 0/1 = marche, 2 = tête baissée (broute)
	"sanglier": 1.2,       # idem
	"oiseau": 2.2,         # 0 = ailes hautes, 1 = à plat, 2 = ailes basses
	"poisson": 1.0,        # 0 = nez haut (montée), 1 = à plat, 2 = nez bas
}

# Ceux-là ne poussent pas : pas de tache de contact, pas de vent, et l'usine
# doit les cadrer sans marge de sol.
const EN_VOL := ["oiseau", "poisson"]

const MARGE_BAS := 0.12     # fraction du panneau réservée SOUS la ligne de sol
const VARIANTES := 3        # formes différentes par essence


# Une forêt de 30 000 fois le même arbre se voit immédiatement : l'œil attrape
# la répétition avant le détail. Trois formes par essence, tirées d'une graine
# stable, suffisent à casser le motif — et ça ne coûte que du temps de rendu.
static func batir(nom: String, variante := 0) -> Node3D:
	var r := RandomNumberGenerator.new()
	r.seed = hash(nom) + variante * 7919
	var n := Node3D.new()
	var f := 1.0 + (variante - 1) * 0.16        # une petite, une moyenne, une grande
	match nom:
		"chene_vert":
			_arbre(n, r, 7.6 * f, 3.4 * (2.0 - f), Color(0.15, 0.25, 0.12), Color(0.29, 0.24, 0.19))
		"chene_pubescent":
			_arbre(n, r, 10.2 * f, 4.2 * (2.0 - f), Color(0.26, 0.33, 0.15), Color(0.33, 0.28, 0.22))
		"peuplier":          _peuplier(n, r, f)
		"buisson":           _buisson(n, r, f)
		"rocher":            _rocher(n, r)
		"ruine":             _ruine(n, variante)
		"perso":             _perso(n)
		"herbe_seche":       _herbe_seche(n, r)
		"feuilles":          _tas_de_feuilles(n, r)
		"chevreuil":         _chevreuil(n, variante)
		"sanglier":          _sanglier(n, variante)
		"oiseau":            _oiseau(n, variante)
		"poisson":           _poisson(n, variante)
	return n


static func _mat(c: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = 0.95
	m.metallic_specular = 0.1
	return m


static func _poser(parent: Node3D, maille: Mesh, mat: Material, t: Transform3D) -> void:
	var mi := MeshInstance3D.new()
	mi.mesh = maille
	mi.material_override = mat
	mi.transform = t
	parent.add_child(mi)


# Tache de contact sous l'objet. Ce n'est PAS une ombre portée : à 24° de
# hauteur de soleil, la vraie ombre ferait 20 m et sortirait du panneau. C'est
# l'assombrissement du pied, ce que fait AoE2. Elle est décalée à l'opposé du
# soleil, dans le MONDE — donc elle tourne correctement avec les 8 angles.
static func _contact(n: Node3D, rayon: float) -> void:
	var d := CylinderMesh.new()
	d.top_radius = rayon
	d.bottom_radius = rayon
	d.height = 0.02
	d.radial_segments = 16
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(0.05, 0.06, 0.04, 0.42)
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	var dec := Vector3(-sin(Usine.SOL_AZ), 0.0, -cos(Usine.SOL_AZ)) * rayon * 0.45
	_poser(n, d, m, Transform3D(Basis(), Vector3(0, 0.02, 0) + dec))


static func _arbre(n: Node3D, r: RandomNumberGenerator, haut: float, large: float,
		feuille: Color, bois: Color) -> void:
	_contact(n, large * 0.55)
	var tronc := CylinderMesh.new()
	tronc.top_radius = haut * 0.022
	tronc.bottom_radius = haut * 0.042
	tronc.height = haut * 0.45
	tronc.radial_segments = 7
	_poser(n, tronc, _mat(bois), Transform3D(Basis(), Vector3(0, haut * 0.225, 0)))

	# Houppier : des masses décentrées, plus claires en haut, plus sombres en
	# bas. Ce dégradé fait tout le volume — un houppier d'une seule couleur
	# rend une boule plate. L'asymétrie, elle, est VOULUE : c'est elle qui rend
	# les 8 angles distinguables. Un arbre symétrique donnerait 8 images
	# identiques et cacherait la question posée.
	var haute := _mat(feuille.lightened(0.22))
	var basse := _mat(feuille.darkened(0.30))
	var moyenne := _mat(feuille)
	var boules := 9
	for i in range(boules):
		var s := SphereMesh.new()
		var ray: float = large * r.randf_range(0.26, 0.44)
		s.radius = ray
		s.height = ray * 2.0 * r.randf_range(0.72, 1.0)
		s.radial_segments = 9
		s.rings = 6
		var a := TAU * float(i) / float(boules) + r.randf_range(-0.35, 0.35)
		var d := large * r.randf_range(0.05, 0.40)
		var t: float = r.randf_range(0.0, 1.0)
		var y: float = haut * lerpf(0.46, 0.92, t)
		var m: StandardMaterial3D = basse if t < 0.33 else (moyenne if t < 0.66 else haute)
		var b := Basis().scaled(Vector3(1.0, r.randf_range(0.70, 0.92), 1.0))
		_poser(n, s, m, Transform3D(b, Vector3(cos(a) * d, y, sin(a) * d)))

	# une branche basse d'un seul côté : repère d'orientation très lisible
	var br := CylinderMesh.new()
	br.top_radius = haut * 0.012
	br.bottom_radius = haut * 0.025
	br.height = large * 0.7
	br.radial_segments = 5
	var bb := Basis(Vector3.FORWARD, deg_to_rad(64.0))
	_poser(n, br, _mat(bois), Transform3D(bb, Vector3(large * 0.24, haut * 0.5, 0)))


static func _peuplier(n: Node3D, r: RandomNumberGenerator, f := 1.0) -> void:
	_contact(n, 1.4)
	var haut := 13.6 * f
	var tronc := CylinderMesh.new()
	tronc.top_radius = 0.1
	tronc.bottom_radius = 0.26
	tronc.height = haut
	tronc.radial_segments = 7
	_poser(n, tronc, _mat(Color(0.38, 0.35, 0.28)), Transform3D(Basis(), Vector3(0, haut * 0.5, 0)))
	var mf := _mat(Color(0.34, 0.44, 0.22))
	for i in range(6):
		var s := SphereMesh.new()
		var ray := r.randf_range(0.9, 1.5)
		s.radius = ray
		s.height = ray * 3.1
		s.radial_segments = 8
		s.rings = 5
		var a := TAU * float(i) / 6.0
		_poser(n, s, mf, Transform3D(Basis(),
			Vector3(cos(a) * 0.75, haut * r.randf_range(0.42, 0.80), sin(a) * 0.75)))


static func _buisson(n: Node3D, r: RandomNumberGenerator, f := 1.0) -> void:
	_contact(n, 0.85 * f)
	var mf := _mat(Color(0.33, 0.34, 0.19))
	var mh := _mat(Color(0.44, 0.44, 0.24))
	for i in range(6):
		var s := SphereMesh.new()
		var ray: float = r.randf_range(0.34, 0.66) * f
		s.radius = ray
		s.height = ray * 1.4
		s.radial_segments = 8
		s.rings = 5
		var y: float = r.randf_range(0.25, 0.85) * f
		_poser(n, s, mh if y > 0.55 * f else mf, Transform3D(Basis(), Vector3(
			r.randf_range(-0.55, 0.55) * f, y, r.randf_range(-0.55, 0.55) * f)))


static func _rocher(n: Node3D, r: RandomNumberGenerator) -> void:
	_contact(n, 1.2)
	var m := _mat(Color(0.56, 0.54, 0.47))
	for i in range(3):
		var b := BoxMesh.new()
		b.size = Vector3(r.randf_range(0.8, 2.0), r.randf_range(0.6, 1.6), r.randf_range(0.8, 1.8))
		var base := Basis(Vector3.UP, r.randf_range(0, TAU)) * Basis(Vector3.RIGHT, r.randf_range(-0.35, 0.35))
		_poser(n, b, m, Transform3D(base, Vector3(
			r.randf_range(-0.5, 0.5), b.size.y * 0.42, r.randf_range(-0.5, 0.5))))


# LE démonstrateur du débat. Un mur en L : fortement asymétrique, ORIENTÉ dans
# le monde. Un arbre peut se contenter d'un seul rendu ; ce mur-là, non : c'est
# lui qui exige les 8 angles dès que la caméra tourne.
static func _ruine(n: Node3D, variante := 0) -> void:
	_contact(n, 3.0)
	var r := RandomNumberGenerator.new()
	r.seed = 4242 + variante * 131
	var pierre := _mat(Color(0.55, 0.52, 0.44))
	var pierre2 := _mat(Color(0.47, 0.45, 0.39))
	var mousse := _mat(Color(0.30, 0.36, 0.22))
	var long := BoxMesh.new()
	long.size = Vector3(6.0 + variante, 2.6, 0.75)
	_poser(n, long, pierre, Transform3D(Basis(), Vector3(0.6, 1.3, -2.1)))
	var pignon := BoxMesh.new()
	pignon.size = Vector3(0.75, 5.2 - variante * 0.7, 4.4)
	_poser(n, pignon, pierre2, Transform3D(Basis(), Vector3(-2.3, pignon.size.y * 0.5, 0.0)))
	var reste := BoxMesh.new()
	reste.size = Vector3(1.6, 1.1, 0.7)
	_poser(n, reste, pierre, Transform3D(Basis(Vector3.UP, 0.22), Vector3(2.4, 0.55, 1.6)))
	# blocs tombés, du côté opposé au pignon : deuxième repère d'orientation
	for i in range(3):
		var bloc := BoxMesh.new()
		bloc.size = Vector3(r.randf_range(0.6, 1.2), r.randf_range(0.4, 0.8), r.randf_range(0.5, 1.0))
		_poser(n, bloc, pierre2, Transform3D(Basis(Vector3.UP, r.randf_range(-0.8, 0.8)),
			Vector3(r.randf_range(2.0, 3.6), bloc.size.y * 0.5, r.randf_range(-1.6, 1.8))))
	# la végétation reprend la ruine (doc 03 : lierre et mousse dans les pierres)
	for i in range(4):
		var s := SphereMesh.new()
		var ray := r.randf_range(0.4, 0.9)
		s.radius = ray
		s.height = ray * 1.3
		s.radial_segments = 7
		s.rings = 4
		_poser(n, s, mousse, Transform3D(Basis(), Vector3(
			r.randf_range(-2.6, 2.8), r.randf_range(0.3, 2.6), r.randf_range(-2.4, 1.8))))


static func _perso(n: Node3D) -> void:
	_contact(n, 0.42)
	var corps := CapsuleMesh.new()
	corps.radius = 0.22
	corps.height = 1.35
	corps.radial_segments = 10
	_poser(n, corps, _mat(Color(0.78, 0.36, 0.22)), Transform3D(Basis(), Vector3(0, 0.78, 0)))
	var tete := SphereMesh.new()
	tete.radius = 0.15
	tete.height = 0.3
	tete.radial_segments = 10
	tete.rings = 6
	_poser(n, tete, _mat(Color(0.86, 0.72, 0.56)), Transform3D(Basis(), Vector3(0, 1.58, 0)))
	# nez : le perso regarde vers -Z (avant de Godot). C'est ce qui rend la
	# direction lisible, donc ce qui exige 8 images et pas une.
	var nez := BoxMesh.new()
	nez.size = Vector3(0.1, 0.1, 0.22)
	_poser(n, nez, _mat(Color(0.94, 0.84, 0.66)), Transform3D(Basis(), Vector3(0, 1.55, -0.2)))


# ───────────────────────────────────────────────── litière au sol
#
# Ce qui manquait au sol : entre l'arbre de 9 m et le caillou de 3 m, rien. Les
# pentes du LiDAR sortaient donc en aplat de texture, et l'œil n'avait aucune
# échelle intermédiaire à quoi s'accrocher. L'herbe sèche et les tas de feuilles
# sont semés par MILLIERS — c'est leur nombre qui fait l'effet, pas leur forme.

static func _herbe_seche(n: Node3D, r: RandomNumberGenerator) -> void:
	# Une touffe = des brins qui divergent depuis un même point. Ce sont eux
	# que le shader de vent pliera le plus : souplesse maximale.
	var paille := _mat(Color(0.74, 0.66, 0.40))
	var paille2 := _mat(Color(0.58, 0.51, 0.28))
	var sec := _mat(Color(0.46, 0.42, 0.24))
	for i in range(16):
		var b := BoxMesh.new()
		var h := r.randf_range(0.30, 0.78)
		b.size = Vector3(0.022, h, 0.022)
		var a := TAU * float(i) / 16.0 + r.randf_range(-0.3, 0.3)
		var pen := r.randf_range(0.12, 0.62)      # les brins s'ouvrent en gerbe
		var base := Basis(Vector3.UP, a) * Basis(Vector3.RIGHT, pen)
		var m: StandardMaterial3D = sec if i % 3 == 0 else (paille if h > 0.55 else paille2)
		_poser(n, b, m, Transform3D(base, Vector3(
			cos(a) * 0.04, h * 0.5 * cos(pen), sin(a) * 0.04)))


static func _tas_de_feuilles(n: Node3D, r: RandomNumberGenerator) -> void:
	# Des disques presque plats, posés à plat les uns sur les autres. Vu de
	# 36° au-dessus, c'est exactement la lecture d'un tas de feuilles mortes.
	var tons := [Color(0.52, 0.34, 0.17), Color(0.62, 0.45, 0.22),
				 Color(0.41, 0.28, 0.15), Color(0.68, 0.53, 0.28)]
	for i in range(11):
		var d := CylinderMesh.new()
		var ray := r.randf_range(0.07, 0.15)
		d.top_radius = ray
		d.bottom_radius = ray * r.randf_range(0.5, 0.9)
		d.height = 0.012
		d.radial_segments = 5
		var base := Basis(Vector3.UP, r.randf_range(0, TAU)) \
				  * Basis(Vector3.RIGHT, r.randf_range(-0.5, 0.5))
		_poser(n, d, _mat(tons[i % tons.size()]), Transform3D(base, Vector3(
			r.randf_range(-0.22, 0.22), 0.012 + i * 0.011, r.randf_range(-0.22, 0.22))))


# ───────────────────────────────────────────────── faune
#
# Tous les animaux regardent vers -Z, comme le perso : c'est la convention de
# l'avant dans Godot, et c'est elle que monde.gd traduit en index de sprite.
# Les VARIANTES ne cassent plus la répétition, elles portent une POSE — l'usine
# les fabriquait déjà toutes les trois, l'animation ne coûte donc rien de plus.

static func _patte(n: Node3D, m: Material, x: float, z: float, h: float, ray: float,
		avance: float) -> void:
	var p := CylinderMesh.new()
	p.top_radius = ray
	p.bottom_radius = ray * 0.7
	p.height = h
	p.radial_segments = 5
	# la patte pivote autour de l'épaule : c'est ce balancement qui, d'une
	# variante à l'autre, fait lire la marche
	var base := Basis(Vector3.RIGHT, avance)
	_poser(n, p, m, Transform3D(base, Vector3(x, h * 0.5, z + sin(avance) * h * 0.4)))


static func _chevreuil(n: Node3D, variante := 0) -> void:
	_contact(n, 0.5)
	var r := RandomNumberGenerator.new()
	r.seed = 7001 + variante
	var robe := _mat(Color(0.56, 0.38, 0.23))
	var ventre := _mat(Color(0.74, 0.65, 0.52))
	var sombre := _mat(Color(0.30, 0.21, 0.14))
	var broute := variante == 2
	var bal: float = [0.35, -0.35, 0.05][variante]

	var corps := CapsuleMesh.new()
	corps.radius = 0.21
	corps.height = 1.02
	corps.radial_segments = 8
	corps.rings = 3
	# capsule couchée le long de l'axe Z : l'animal est plus long que haut
	_poser(n, corps, robe, Transform3D(Basis(Vector3.RIGHT, PI * 0.5), Vector3(0, 0.78, 0)))
	var vt := CapsuleMesh.new()
	vt.radius = 0.15
	vt.height = 0.86
	vt.radial_segments = 7
	vt.rings = 3
	_poser(n, vt, ventre, Transform3D(Basis(Vector3.RIGHT, PI * 0.5), Vector3(0, 0.66, 0.02)))

	# cou et tête : relevés en marche, plongés au sol quand il broute
	var cou_pen := 1.15 if broute else -0.55
	var cou := CylinderMesh.new()
	cou.top_radius = 0.065
	cou.bottom_radius = 0.11
	cou.height = 0.42
	cou.radial_segments = 6
	var cb := Basis(Vector3.RIGHT, cou_pen)
	var cpos := Vector3(0, 0.92, -0.48) + cb * Vector3(0, 0.21, 0)
	_poser(n, cou, robe, Transform3D(cb, cpos))
	var tete := CapsuleMesh.new()
	tete.radius = 0.075
	tete.height = 0.30
	tete.radial_segments = 6
	tete.rings = 3
	var tpos := Vector3(0, 0.92, -0.48) + cb * Vector3(0, 0.46, 0)
	_poser(n, tete, robe, Transform3D(cb * Basis(Vector3.RIGHT, 0.9), tpos))
	# oreilles : deux virgules claires, le repère d'avant le plus lisible
	for s in [-1.0, 1.0]:
		var o := BoxMesh.new()
		o.size = Vector3(0.04, 0.13, 0.07)
		_poser(n, o, ventre, Transform3D(Basis(Vector3.FORWARD, s * 0.5),
			tpos + Vector3(s * 0.08, 0.09, 0.03)))
	# miroir blanc de la croupe : le repère d'ARRIÈRE, tout aussi nécessaire
	var miroir := SphereMesh.new()
	miroir.radius = 0.15
	miroir.height = 0.24
	miroir.radial_segments = 7
	miroir.rings = 4
	_poser(n, miroir, _mat(Color(0.90, 0.88, 0.80)), Transform3D(Basis(), Vector3(0, 0.86, 0.50)))

	_patte(n, sombre, -0.13, -0.32, 0.62, 0.035, bal)
	_patte(n, sombre, 0.13, -0.32, 0.62, 0.035, -bal)
	_patte(n, sombre, -0.14, 0.34, 0.64, 0.040, -bal)
	_patte(n, sombre, 0.14, 0.34, 0.64, 0.040, bal)


static func _sanglier(n: Node3D, variante := 0) -> void:
	_contact(n, 0.48)
	var soie := _mat(Color(0.23, 0.19, 0.16))
	var soie2 := _mat(Color(0.33, 0.28, 0.23))
	var bal: float = [0.30, -0.30, 0.0][variante]
	var groin := 0.40 if variante == 2 else 0.62      # nez au sol quand il fouille

	# masse trapue, épaules plus hautes que la croupe : c'est LA silhouette
	var corps := SphereMesh.new()
	corps.radius = 0.36
	corps.height = 0.62
	corps.radial_segments = 9
	corps.rings = 6
	_poser(n, corps, soie, Transform3D(Basis().scaled(Vector3(0.78, 1.0, 1.35)),
		Vector3(0, 0.50, 0.06)))
	var epaule := SphereMesh.new()
	epaule.radius = 0.30
	epaule.height = 0.58
	epaule.radial_segments = 8
	epaule.rings = 5
	_poser(n, epaule, soie2, Transform3D(Basis().scaled(Vector3(0.82, 1.0, 0.9)),
		Vector3(0, 0.56, -0.26)))
	# tête en coin, prolongée du groin : la pointe avant du triangle
	var tete := BoxMesh.new()
	tete.size = Vector3(0.24, 0.26, 0.42)
	_poser(n, tete, soie, Transform3D(Basis(Vector3.RIGHT, 0.25), Vector3(0, groin, -0.60)))
	var gr := CylinderMesh.new()
	gr.top_radius = 0.07
	gr.bottom_radius = 0.09
	gr.height = 0.16
	gr.radial_segments = 6
	_poser(n, gr, soie2, Transform3D(Basis(Vector3.RIGHT, PI * 0.5),
		Vector3(0, groin - 0.06, -0.82)))
	_patte(n, soie, -0.16, -0.26, 0.34, 0.045, bal)
	_patte(n, soie, 0.16, -0.26, 0.34, 0.045, -bal)
	_patte(n, soie, -0.17, 0.26, 0.32, 0.048, -bal)
	_patte(n, soie, 0.17, 0.26, 0.32, 0.048, bal)


static func _oiseau(n: Node3D, variante := 0) -> void:
	# Un rapace planant, pas un moineau : dans la gorge de l'Ardèche ce sont les
	# vautours et les milans qu'on voit tourner. Deux mètres d'envergure, c'est
	# aussi la seule taille qui reste lisible à 6 pixels par mètre.
	var pen: float = [0.55, 0.02, -0.38][variante]          # le battement, en trois temps
	var plume := _mat(Color(0.19, 0.17, 0.15))
	var plume2 := _mat(Color(0.34, 0.30, 0.25))
	var corps := CapsuleMesh.new()
	corps.radius = 0.09
	corps.height = 0.60
	corps.radial_segments = 7
	corps.rings = 3
	_poser(n, corps, plume, Transform3D(Basis(Vector3.RIGHT, PI * 0.5), Vector3(0, 1.1, 0)))
	var tete := SphereMesh.new()
	tete.radius = 0.07
	tete.height = 0.14
	tete.radial_segments = 6
	tete.rings = 4
	_poser(n, tete, plume2, Transform3D(Basis(), Vector3(0, 1.13, -0.32)))
	for s in [-1.0, 1.0]:
		var aile := BoxMesh.new()
		aile.size = Vector3(0.92, 0.035, 0.30)
		# l'aile pivote autour de l'épaule : le dièdre fait toute la lecture
		var b := Basis(Vector3.FORWARD, -s * pen)
		_poser(n, aile, plume, Transform3D(b,
			Vector3(s * 0.52, 1.1 + sin(pen) * 0.46, -0.02)))
		var bout := BoxMesh.new()
		bout.size = Vector3(0.30, 0.03, 0.16)
		_poser(n, bout, plume2, Transform3D(b,
			Vector3(s * 1.02, 1.1 + sin(pen) * 0.90, 0.06)))
	var queue := BoxMesh.new()
	queue.size = Vector3(0.24, 0.03, 0.34)
	_poser(n, queue, plume2, Transform3D(Basis(), Vector3(0, 1.09, 0.42)))


static func _poisson(n: Node3D, variante := 0) -> void:
	# Le saut se lit à l'INCLINAISON, pas au détail : nez haut à la montée, à
	# plat au sommet, nez bas à la retombée. monde.gd choisit la variante
	# d'après la vitesse verticale — trois images pour une parabole.
	var pen: float = [-0.62, 0.0, 0.62][variante]
	var dos := _mat(Color(0.28, 0.34, 0.31))
	var flanc := _mat(Color(0.74, 0.78, 0.76))
	var b := Basis(Vector3.RIGHT, pen)
	var corps := CapsuleMesh.new()
	corps.radius = 0.088
	corps.height = 0.52
	corps.radial_segments = 8
	corps.rings = 3
	_poser(n, corps, flanc, Transform3D(b * Basis(Vector3.RIGHT, PI * 0.5).scaled(
		Vector3(0.62, 1.0, 1.0)), Vector3(0, 0.5, 0)))
	var ligne := CapsuleMesh.new()
	ligne.radius = 0.055
	ligne.height = 0.46
	ligne.radial_segments = 7
	ligne.rings = 3
	_poser(n, ligne, dos, Transform3D(b * Basis(Vector3.RIGHT, PI * 0.5).scaled(
		Vector3(0.55, 1.0, 1.0)), Vector3(0, 0.5, 0) + b * Vector3(0, 0.05, 0)))
	var queue := BoxMesh.new()
	queue.size = Vector3(0.025, 0.24, 0.20)
	_poser(n, queue, dos, Transform3D(b, Vector3(0, 0.5, 0) + b * Vector3(0, 0, 0.34)))
	var nageoire := BoxMesh.new()
	nageoire.size = Vector3(0.02, 0.13, 0.16)
	_poser(n, nageoire, dos, Transform3D(b, Vector3(0, 0.5, 0) + b * Vector3(0, 0.11, 0.02)))
