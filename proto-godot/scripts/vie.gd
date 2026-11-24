# Ce qui bouge tout seul : les hardes, les vols, les poissons, les ronds.
#
# Une seule règle d'architecture ici, et elle vient du budget d'image : AUCUN
# animal n'est un nœud. Tout passe par des MultiMeshInstance3D — un par espèce —
# et l'angle de sprite de chaque bête voyage dans ses données d'instance
# (voir scripts/faune.gdshader). Une harde de huit chevreuils qui changent de
# cap en permanence coûte donc exactement un appel de dessin, comme un seul.
#
# L'autre règle vient de l'usine : les trois VARIANTES de chaque volume ne
# servent plus à casser la répétition mais à porter une POSE. Le chevreuil a une
# pose « tête baissée », l'oiseau trois positions d'aile, le poisson trois
# inclinaisons. C'est de l'animation à trois images, comme les sprites des
# années 90 — et elle ne coûte rien, puisque l'usine fabriquait déjà les trois.
#
# Les placeholders de scripts/volumes.gd tiennent la place des vrais sprites
# d'animaux fabriqués en parallèle : le jour où ils arrivent, seule la source
# des planches change, pas une ligne d'ici.

class_name Vie
extends Node3D

# Les espèces qui vivent ici passent par l'atlas et PAS par la table de
# matériaux du semis : monde.gd s'en sert pour ne pas leur fabriquer 24
# matériaux de végétation qui ne serviraient à rien.
const ESPECES := ["chevreuil", "sanglier", "oiseau", "poisson"]

const NB_HARDES := 8
const OISEAUX_PAR_VOL := 13
const NB_VOLS := 3
const POISSONS := 18          # emplacements ; trois ou quatre sautent à la fois
const ONDES := 40

# Au-delà, l'animal fuit. En deçà de FUITE_FIN il se calme.
const FUITE_RAYON := 34.0
const FUITE_FIN := 70.0

enum { BROUTE, MARCHE, FUITE }

var monde: Node3D
var riviere: Riviere
var mailles_bassin := PackedInt32Array()
var gn: int                   # copies locales : monde.n et monde.pas passent par
var gpas: float               # Variant, et k / Variant ne divise pas en entier
var gemprise: float

var hardes: Array = []        # { espece, ancre:Vector2, cap, territoire:Vector2, rayon }
var betes: Array = []         # { harde, pos:Vector2, y, cap, etat, minuteur, foulee, vitesse }
var vols: Array = []          # { centre:Vector2, y, sens }
var oiseaux: Array = []       # { vol, pos:Vector3, vit:Vector3, batt }
var poissons: Array = []      # { actif, depart:Vector3, dir:Vector2, t, duree, haut, attente }
var ondes: Array = []         # { pos:Vector3, age, duree, rayon }

var mm := {}                  # espèce → MultiMesh
var mats := {}                # espèce → ShaderMaterial
var mm_ondes: MultiMesh
var horloge := 0.0
var az_courant := 0
var _hasard := RandomNumberGenerator.new()


func demarrer(m: Node3D, planches: Dictionary, riv: Riviere) -> void:
	monde = m
	riviere = riv
	gn = int(m.n)
	gpas = float(m.pas)
	gemprise = float(m.emprise)
	_hasard.seed = 20260923
	mailles_bassin = riv.bassins
	for espece in ESPECES:
		_batir_multimesh(espece, planches)
	_batir_ondes()
	_peupler_hardes()
	_peupler_vols()
	_peupler_poissons()
	print("vie : %d bêtes en %d hardes · %d oiseaux en %d vols · %d poissons" % [
		betes.size(), hardes.size(), oiseaux.size(), vols.size(), poissons.size()])


# ───────────────────────────────────────────────────── planches et atlas
#
# Les 8 angles × 3 poses d'une espèce sont recollés dans UNE image. C'est la
# condition pour que tout le troupeau tienne dans un seul MultiMesh : un
# matériau ne porte qu'une texture, donc si l'angle devait changer de matériau,
# il faudrait re-répartir les bêtes entre 24 MultiMesh à chaque image.
func atlas(planches: Dictionary, espece: String) -> ImageTexture:
	var jeux: Array = planches[espece]
	var m0: Image = (jeux[0][0] as Texture2D).get_image()
	m0.convert(Image.FORMAT_RGBA8)
	var l := m0.get_width()
	var h := m0.get_height()
	var img := Image.create(l * Usine.ANGLES, h * Volumes.VARIANTES, false, Image.FORMAT_RGBA8)
	for v in range(jeux.size()):
		for a in range(Usine.ANGLES):
			var im: Image = (jeux[v][a] as Texture2D).get_image()
			im.convert(Image.FORMAT_RGBA8)
			img.blit_rect(im, Rect2i(0, 0, l, h), Vector2i(a * l, v * h))
	return ImageTexture.create_from_image(img)


# Appelé quand l'usine refait les planches (touche T ou L) : seule la texture
# change, les bêtes continuent leur vie.
func recharger(planches: Dictionary) -> void:
	for espece in mats:
		mats[espece].set_shader_parameter("atlas", atlas(planches, espece))


func _batir_multimesh(espece: String, planches: Dictionary) -> void:
	var h: float = Volumes.CATALOGUE[espece]
	var q := QuadMesh.new()
	q.size = Vector2(h, h)
	q.center_offset = Vector3(0, h * (0.5 - Volumes.MARGE_BAS), 0)
	var mat := ShaderMaterial.new()
	mat.shader = load("res://scripts/faune.gdshader")
	mat.set_shader_parameter("atlas", atlas(planches, espece))
	mat.set_shader_parameter("grille", Vector2(Usine.ANGLES, Volumes.VARIANTES))
	q.material = mat
	var combien: int = {"chevreuil": 64, "sanglier": 48, "oiseau": NB_VOLS * OISEAUX_PAR_VOL,
						"poisson": POISSONS}[espece]
	var m := MultiMesh.new()
	m.transform_format = MultiMesh.TRANSFORM_3D
	m.use_colors = true
	m.use_custom_data = true
	m.mesh = q
	m.instance_count = combien
	for i in range(combien):
		m.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ZERO), Vector3.ZERO))
		m.set_instance_custom_data(i, Color(0, 0, 0, 0))
	var mi := MultiMeshInstance3D.new()
	mi.multimesh = m
	mi.name = "Faune_" + espece
	# Sans boîte explicite, tout le troupeau disparaît dès que l'origine du
	# MultiMesh sort du champ — le même piège que pour le semis.
	mi.custom_aabb = AABB(Vector3.ZERO, Vector3(gemprise, 500, gemprise))
	add_child(mi)
	mm[espece] = m
	mats[espece] = mat


func _batir_ondes() -> void:
	var p := PlaneMesh.new()
	p.size = Vector2(1, 1)
	var mat := ShaderMaterial.new()
	mat.shader = load("res://scripts/ondes.gdshader")
	p.material = mat
	var m := MultiMesh.new()
	m.transform_format = MultiMesh.TRANSFORM_3D
	m.use_colors = true
	m.mesh = p
	m.instance_count = ONDES
	for i in range(ONDES):
		m.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ZERO), Vector3.ZERO))
		m.set_instance_color(i, Color(1, 1, 1, 0))
		ondes.append({"age": 1e9, "duree": 1.0, "rayon": 1.0, "pos": Vector3.ZERO})
	var mi := MultiMeshInstance3D.new()
	mi.multimesh = m
	mi.name = "Ondes"
	mi.custom_aabb = AABB(Vector3.ZERO, Vector3(gemprise, 500, gemprise))
	add_child(mi)
	mm_ondes = m


# ───────────────────────────────────────────────────── peuplement
func _peupler_hardes() -> void:
	# Les hardes ne sont pas semées au hasard sur la carte : elles vivent dans
	# le fond de gorge, là où le joueur se tient. Une harde à 800 m derrière une
	# crête est du calcul perdu.
	for i in range(NB_HARDES):
		var espece := "chevreuil" if i % 3 != 2 else "sanglier"
		var c := _terrain_vivable(Vector2(
			_hasard.randf_range(120.0, gemprise - 120.0),
			_hasard.randf_range(120.0, gemprise - 120.0)))
		hardes.append({"espece": espece, "ancre": c, "cap": _hasard.randf_range(0, TAU),
					   "territoire": c, "rayon": _hasard.randf_range(90.0, 180.0)})
		var combien := _hasard.randi_range(3, 7) if espece == "sanglier" else _hasard.randi_range(4, 8)
		for j in range(combien):
			var p := c + Vector2(_hasard.randf_range(-14, 14), _hasard.randf_range(-14, 14))
			betes.append({"harde": i, "pos": p, "y": monde.altitude_en(p.x, p.y),
						  "cap": _hasard.randf_range(0, TAU), "etat": BROUTE,
						  "minuteur": _hasard.randf_range(1.0, 6.0), "foulee": _hasard.randf(),
						  "vitesse": 0.0})


func _peupler_vols() -> void:
	# Les vols tournent au-dessus de la RIVIÈRE : c'est là que la gorge s'ouvre,
	# donc là qu'on les voit passer entre les parois. Un vol posé au hasard
	# finissait invariablement à raser un plateau boisé.
	for i in range(NB_VOLS):
		var k: int = mailles_bassin[_hasard.randi() % maxi(1, mailles_bassin.size())]
		var c := Vector2((k % gn) * gpas, (k / gn) * gpas)
		var y: float = monde.altitude_en(c.x, c.y) + _hasard.randf_range(55.0, 95.0)
		vols.append({"centre": c, "y": y, "sens": 1.0 if i % 2 == 0 else -1.0})
		for j in range(OISEAUX_PAR_VOL):
			var a := TAU * float(j) / OISEAUX_PAR_VOL
			var r := _hasard.randf_range(25.0, 70.0)
			var p := Vector3(c.x + cos(a) * r, y + _hasard.randf_range(-12, 12), c.y + sin(a) * r)
			oiseaux.append({"vol": i, "pos": p,
							"vit": Vector3(-sin(a), 0, cos(a)) * 12.0,
							"batt": _hasard.randf_range(0, TAU)})


func _peupler_poissons() -> void:
	for i in range(POISSONS):
		poissons.append({"actif": false, "attente": _hasard.randf_range(1.0, 18.0),
						 "depart": Vector3.ZERO, "dir": Vector2.RIGHT, "t": 0.0,
						 "duree": 1.0, "haut": 1.5})


func _terrain_vivable(p: Vector2) -> Vector2:
	for essai in range(60):
		if monde.est_sec(p.x, p.y) and monde.pente_en(p.x, p.y) < 24.0:
			return p
		var a := essai * 2.39996
		var r := 25.0 + essai * 14.0
		p = Vector2(clampf(p.x + cos(a) * r, 60.0, gemprise - 60.0),
					clampf(p.y + sin(a) * r, 60.0, gemprise - 60.0))
	return p


# ───────────────────────────────────────────────────── boucle
func maj(dt: float, az_i: int, perso: Vector3) -> void:
	horloge += dt
	az_courant = az_i
	# Le pas est borné : après un passage par l'usine (touche T), dt vaut
	# plusieurs secondes et les hardes se téléportaient à l'autre bout de la
	# carte, les oiseaux dans la roche.
	var d := minf(dt, 0.1)
	_maj_hardes(d, perso)
	_maj_oiseaux(d)
	_maj_poissons(d, perso)
	_maj_ondes(d)


# L'index de sprite est l'angle RELATIF entre l'objet et la caméra, exactement
# comme pour les arbres. Le modèle regarde vers -Z, donc son lacet vaut le cap
# moins un demi-tour : d'où le +4 (quatre huitièmes).
func _case(cap: float) -> float:
	var h := int(round(cap / (TAU / Usine.ANGLES)))
	var rel := (az_courant - h + 4 + Usine.ANGLES * 4) % Usine.ANGLES
	return float(rel) / float(Usine.ANGLES)


func _maj_hardes(dt: float, perso: Vector3) -> void:
	for h in hardes:
		# l'ancre dérive lentement dans son territoire : c'est elle qui fait que
		# la harde se DÉPLACE au lieu de tourner en rond sur place
		h["cap"] += _hasard.randf_range(-1.0, 1.0) * dt * 0.7
		var a: float = h["cap"]
		var na: Vector2 = h["ancre"] + Vector2(sin(a), cos(a)) * 2.2 * dt
		var t: Vector2 = h["territoire"]
		if na.distance_to(t) > float(h["rayon"]):
			h["cap"] = atan2(t.x - na.x, t.y - na.y)
		else:
			h["ancre"] = na

	var m: MultiMesh = mm["chevreuil"]
	var ms: MultiMesh = mm["sanglier"]
	var ic := 0
	var isa := 0
	for b in betes:
		var h: Dictionary = hardes[b["harde"]]
		var p: Vector2 = b["pos"]
		var d2 := Vector2(perso.x, perso.z).distance_to(p)

		b["minuteur"] = float(b["minuteur"]) - dt
		if d2 < FUITE_RAYON:
			# Fuir DROIT à l'opposé, sans hésiter : c'est ce qui rend la
			# présence du joueur lisible. Une bête qui « réfléchit » se lit
			# comme un bug de navigation.
			b["etat"] = FUITE
			b["minuteur"] = 3.5
			b["cap"] = atan2(p.x - perso.x, p.y - perso.z)
		elif float(b["minuteur"]) <= 0.0:
			if b["etat"] == FUITE and d2 < FUITE_FIN:
				b["minuteur"] = 1.5
			elif b["etat"] == BROUTE:
				b["etat"] = MARCHE
				b["minuteur"] = _hasard.randf_range(2.0, 7.0)
				var vers: Vector2 = h["ancre"] + Vector2(
					_hasard.randf_range(-16, 16), _hasard.randf_range(-16, 16))
				b["cap"] = atan2(vers.x - p.x, vers.y - p.y)
			else:
				b["etat"] = BROUTE
				b["minuteur"] = _hasard.randf_range(3.0, 11.0)

		var vit := 0.0
		match int(b["etat"]):
			FUITE: vit = 9.5
			MARCHE: vit = 1.35
			_: vit = 0.0
		# rappel vers la harde : sans lui les bêtes s'éparpillent en une heure
		if vit > 0.0 and b["etat"] != FUITE:
			var vers_ancre := atan2(float(h["ancre"].x) - p.x, float(h["ancre"].y) - p.y)
			if p.distance_to(h["ancre"]) > 26.0:
				b["cap"] = lerp_angle(float(b["cap"]), vers_ancre, 0.9 * dt * 3.0)

		if vit > 0.0:
			var c: float = b["cap"]
			var np := p + Vector2(sin(c), cos(c)) * vit * dt
			np.x = clampf(np.x, 20.0, gemprise - 20.0)
			np.y = clampf(np.y, 20.0, gemprise - 20.0)
			# L'eau et la falaise renvoient. Un chevreuil qui traverse la rivière
			# ou grimpe une paroi verticale annule tout le travail d'ancrage.
			if monde.est_sec(np.x, np.y) and monde.pente_en(np.x, np.y) < 30.0:
				b["pos"] = np
				b["foulee"] = fmod(float(b["foulee"]) + vit * dt * 0.7, 2.0)
			else:
				b["cap"] = float(b["cap"]) + PI * 0.55
			p = b["pos"]
		b["y"] = monde.altitude_en(p.x, p.y)
		b["vitesse"] = vit

		# pose : tête baissée à l'arrêt, sinon les deux temps de la foulée
		var pose := 2 if vit == 0.0 else (0 if float(b["foulee"]) < 1.0 else 1)
		var ech := 1.0 + (0.12 if b["harde"] % 2 == 0 else -0.06)
		var tr := Transform3D(Basis().scaled(Vector3(ech, ech, ech)),
							  Vector3(p.x, float(b["y"]), p.y))
		var cd := Color(_case(float(b["cap"])), float(pose) / float(Volumes.VARIANTES), 1.0, 0.0)
		if h["espece"] == "chevreuil":
			if ic >= m.instance_count:
				continue
			m.set_instance_transform(ic, tr)
			m.set_instance_custom_data(ic, cd)
			m.set_instance_color(ic, Color(1, 1, 1))
			ic += 1
		else:
			if isa >= ms.instance_count:
				continue
			ms.set_instance_transform(isa, tr)
			ms.set_instance_custom_data(isa, cd)
			ms.set_instance_color(isa, Color(1, 1, 1))
			isa += 1


# Boids, version courte : séparation, alignement, cohésion — plus un rappel
# TANGENTIEL autour du centre du vol, qui est ce qui fait tourner la ronde. Sans
# ce quatrième terme les trois règles classiques donnent un banc qui part tout
# droit et quitte la carte en vingt secondes.
func _maj_oiseaux(dt: float) -> void:
	var m: MultiMesh = mm["oiseau"]
	var centres := []
	var vitesses := []
	for v in vols:
		centres.append(Vector3.ZERO)
		vitesses.append(Vector3.ZERO)
	for o in oiseaux:
		centres[o["vol"]] += o["pos"]
		vitesses[o["vol"]] += o["vit"]
	for i in range(vols.size()):
		centres[i] /= float(OISEAUX_PAR_VOL)
		vitesses[i] /= float(OISEAUX_PAR_VOL)

	for i in range(oiseaux.size()):
		var o: Dictionary = oiseaux[i]
		var v: Dictionary = vols[o["vol"]]
		var p: Vector3 = o["pos"]
		var acc := Vector3.ZERO

		acc += (centres[o["vol"]] - p) * 0.35
		acc += (vitesses[o["vol"]] - o["vit"]) * 0.55
		var sep := Vector3.ZERO
		for j in range(oiseaux.size()):
			if j == i or oiseaux[j]["vol"] != o["vol"]:
				continue
			var d: Vector3 = p - oiseaux[j]["pos"]
			var l := d.length()
			if l < 9.0 and l > 0.01:
				sep += d / (l * l) * 14.0
		acc += sep

		# la ronde : une force perpendiculaire au rayon, dans le plan horizontal
		var r := Vector3(p.x - v["centre"].x, 0.0, p.z - v["centre"].y)
		var rl := r.length()
		if rl > 0.5:
			var tang := Vector3(-r.z, 0.0, r.x).normalized() * float(v["sens"])
			acc += tang * 9.0
			acc += -r / rl * (rl - 55.0) * 0.12

		# plafond et plancher : on plane AU-DESSUS du relief, jamais dedans
		var sol: float = monde.altitude_en(p.x, p.z)
		var vise: float = maxf(float(v["y"]), sol + 45.0)
		acc.y += (vise - p.y) * 0.55

		var vit: Vector3 = o["vit"] + acc * dt
		var vl := vit.length()
		vit = vit / maxf(vl, 0.001) * clampf(vl, 9.0, 17.0)
		o["vit"] = vit
		o["pos"] = p + vit * dt

		# battement : trois positions d'aile, à contretemps d'un oiseau à l'autre
		o["batt"] = fmod(float(o["batt"]) + dt * 5.5, TAU)
		var s := sin(float(o["batt"]))
		var pose := 0 if s > 0.45 else (2 if s < -0.45 else 1)
		var cap := atan2(vit.x, vit.z)
		m.set_instance_transform(i, Transform3D(Basis(),
			o["pos"] - Vector3(0, Volumes.CATALOGUE["oiseau"] * (0.5 - Volumes.MARGE_BAS), 0)))
		m.set_instance_custom_data(i, Color(_case(cap), float(pose) / float(Volumes.VARIANTES), 1.0, 0.0))
		m.set_instance_color(i, Color(1, 1, 1))


# Le saut : une parabole d'une seconde, au-dessus d'une maille profonde et PRÈS
# DU JOUEUR. Semés sur les 2,4 km de rivière, les poissons sautaient toujours
# hors champ — le plus joli système du monde ne sert à rien s'il est invisible.
func _maj_poissons(dt: float, perso: Vector3) -> void:
	var m: MultiMesh = mm["poisson"]
	var hp: float = Volumes.CATALOGUE["poisson"] * (0.5 - Volumes.MARGE_BAS)
	for i in range(poissons.size()):
		var f: Dictionary = poissons[i]
		if not f["actif"]:
			f["attente"] = float(f["attente"]) - dt
			if float(f["attente"]) <= 0.0:
				if not _lancer_saut(f, perso):
					f["attente"] = _hasard.randf_range(1.0, 3.0)
			m.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ZERO), Vector3.ZERO))
			m.set_instance_custom_data(i, Color(0, 0, 0, 0))
			continue

		f["t"] = float(f["t"]) + dt
		var u: float = float(f["t"]) / float(f["duree"])
		if u >= 1.0:
			var d0: Vector3 = f["depart"]
			var fin := d0 + Vector3(f["dir"].x, 0, f["dir"].y) * float(f["duree"]) * 3.2
			_onde(fin, 5.0, 2.6)
			_onde(fin, 3.0, 1.8)
			f["actif"] = false
			f["attente"] = _hasard.randf_range(6.0, 26.0)
			m.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ZERO), Vector3.ZERO))
			m.set_instance_custom_data(i, Color(0, 0, 0, 0))
			continue

		var dep: Vector3 = f["depart"]
		var avance := Vector3(f["dir"].x, 0, f["dir"].y) * float(f["duree"]) * 3.2 * u
		# parabole : 4·h·u·(1−u) culmine à h au milieu et retombe à zéro
		var y := 4.0 * float(f["haut"]) * u * (1.0 - u)
		var p := dep + avance + Vector3(0, y, 0)
		var monte := (0.5 - u)          # >0 en montée, <0 en retombée
		var pose := 0 if monte > 0.16 else (2 if monte < -0.16 else 1)
		var cap := atan2(f["dir"].x, f["dir"].y)
		m.set_instance_transform(i, Transform3D(Basis(), p - Vector3(0, hp, 0)))
		m.set_instance_custom_data(i, Color(_case(cap), float(pose) / float(Volumes.VARIANTES), 1.0, 0.0))
		m.set_instance_color(i, Color(1, 1, 1))


func _lancer_saut(f: Dictionary, perso: Vector3) -> bool:
	if mailles_bassin.is_empty():
		return false
	for essai in range(40):
		var k: int = mailles_bassin[_hasard.randi() % mailles_bassin.size()]
		var x := (k % gn) * gpas
		var z := (k / gn) * gpas
		if Vector2(x - perso.x, z - perso.z).length() > 130.0:
			continue
		var niveau: float = monde.niveau_eau(x, z)
		if is_nan(niveau):
			continue
		# le poisson saute DANS LE SENS DU COURANT, avec un écart : c'est ce
		# petit accord avec l'eau qui fait qu'on ne le lit pas comme un jouet
		var d := Vector2(riviere.dirx[k], riviere.dirz[k])
		if d.length() < 0.05:
			d = Vector2(_hasard.randf_range(-1, 1), _hasard.randf_range(-1, 1))
		d = d.normalized().rotated(_hasard.randf_range(-0.8, 0.8))
		f["actif"] = true
		f["depart"] = Vector3(x, niveau, z)
		f["dir"] = d
		f["t"] = 0.0
		f["duree"] = _hasard.randf_range(0.85, 1.25)
		f["haut"] = _hasard.randf_range(1.1, 2.3)
		_onde(Vector3(x, niveau, z), 3.4, 2.0)
		return true
	return false


func _onde(p: Vector3, rayon: float, duree: float) -> void:
	for o in ondes:
		if float(o["age"]) < float(o["duree"]):
			continue
		o["pos"] = p + Vector3(0, 0.07, 0)      # juste au-dessus de la nappe
		o["age"] = 0.0
		o["duree"] = duree
		o["rayon"] = rayon
		return


func _maj_ondes(dt: float) -> void:
	for i in range(ondes.size()):
		var o: Dictionary = ondes[i]
		var age := float(o["age"])
		if age >= float(o["duree"]):
			continue
		age += dt
		o["age"] = age
		var u := clampf(age / float(o["duree"]), 0.0, 1.0)
		# le rond s'élargit vite puis ralentit, et s'efface en fin de course
		var r: float = float(o["rayon"]) * (0.18 + 0.82 * sqrt(u))
		var a := (1.0 - u) * (1.0 - u) * 0.85
		mm_ondes.set_instance_transform(i, Transform3D(
			Basis().scaled(Vector3(r * 2.0, 1.0, r * 2.0)), o["pos"]))
		mm_ondes.set_instance_color(i, Color(1, 1, 1, a))
		if u >= 1.0:
			mm_ondes.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ZERO), Vector3.ZERO))
