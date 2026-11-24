# Jupire — comparaison des deux caméras, sur le vrai terrain de Balazuc.
#
# Les données viennent de proto-terrain (MNT LiDAR HD + BD TOPO), préparées par
# outils/convertir.py avec les réglages validés : lissage 5 m, aplatissement
# 0,85, creusement ×1,1, eau +0,5 m. L'éclairage (soleil direct, ombres
# portées, part de ciel visible) est cuit dans les couleurs de sommet : aucune
# lumière n'éclaire le terrain ni les sprites en jeu. C'est le modèle AoE2, et
# c'est ce qui tient la promesse « tourne sur du matériel modeste ».
#
# La question posée à l'écran, et elle seule :
#
#   MODE 1 — yaw VERROUILLÉ (AoE2 pur). Une seule orientation de caméra, donc
#            un seul angle de sprite par objet.
#   MODE 2 — yaw par PALIERS DE 45°. Huit orientations. Comme le pas de la
#            caméra est un multiple du pas des sprites, l'angle relatif reste
#            sur la grille : 8 images suffisent toujours. La rotation ne coûte
#            RIEN en nombre de sprites, seulement du temps de rendu à l'usine.
#
# Les deux sont en projection orthographique : le « 3D-2D iso » n'est pas
# l'objet du débat, le proto browser était déjà en ortho.

extends Node3D

const BUILD := "g3 · vie · 2026-09-23"
const DATA := "res://data/"

# 26,565° = atan(0.5), le 2:1 d'AoE2. 36° = le réglage validé au proto browser.
const TILTS := [26.565, 36.0, 45.0]
# Distance caméra fixe : en ortho elle ne change pas le cadrage, seulement la
# profondeur. La garder fixe permet de caler la brume atmosphérique dessus.
const DIST := 900.0

var meta: Dictionary
var n: int
var pas: float
var emprise: float
var alt := PackedFloat32Array()
var eau := PackedFloat32Array()

# état de la caméra
var verrouille := true
var az_i := 1                    # 8 paliers de 45° ; 1 = 45°, comme le proto
var tilt_i := 1
var portee := 150.0
var libre := false               # caméra libre ↔ collée au perso
var cible := Vector3.ZERO        # point visé en mode libre

# sprites
var planches := {}               # nom → [variante][angle] ; soleil dans le MONDE
var planches_faux := {}          # soleil collé à la caméra (le piège, touche L)
var soleil_monde := true
var mats := {}                   # nom → [variante][angle] de StandardMaterial3D
var groupes: Array = []          # { mi, nom, var, orient } pour le semis
var ruines: Array = []
var usine: Usine

# perso
var perso: MeshInstance3D
var p_pos := Vector3.ZERO
var p_dir := 0                   # 0..7, direction du regard dans le MONDE
var depart_gorge := Vector3.ZERO
var depart_plateau := Vector3.ZERO

# mesure
var masque_maintenant := false
var masque_temps := {true: 0.0, false: 0.0}
var total_temps := {true: 0.0, false: 0.0}
var gorge_bloques := 0
var gorge_moyenne := 0.0

var cam: Camera3D
var env: Environment
var terrain: MeshInstance3D
var mat_matiere: ShaderMaterial
var mat_plat: StandardMaterial3D
var hud: RichTextLabel

# eau
var riviere: Riviere
var noeud_eau: MeshInstance3D
var mat_eau: ShaderMaterial              # l'eau qui coule
var mat_eau_secours: StandardMaterial3D  # le matériau d'avant, gardé sous la main
var eau_shader := true

# vie et vent
var vie: Vie
var vent := 1.0
var mats_derive := {}                    # planches montées pour dériver en l'air
var litiere := 0

# Combien chaque essence se laisse plier. Le chiffre est une AMPLITUDE RELATIVE
# à la hauteur du panneau : sans ça un brin de 0,9 m et un peuplier de 16 m
# recevraient le même déplacement en mètres, et le brin ferait le grand écart.
const SOUPLESSE := {
	"chene_vert": 0.75, "chene_pubescent": 0.85, "peuplier": 1.30,
	"buisson": 1.05, "herbe_seche": 2.10, "feuilles": 0.45,
	"rocher": 0.0, "ruine": 0.0, "perso": 0.0,
}
# Le vent de la gorge remonte la vallée : direction unique, pour que la rafale
# traverse le paysage dans un sens lisible au lieu de faire du bruit.
const VENT_DIR := Vector2(0.82, -0.57)
var alerte: Label
var chargement: Label
var glisse := false
var auto := false                # tour automatique : les entrées sont ignorées


# ───────────────────────────────────────────────────────── démarrage
func _ready() -> void:
	_ecran_chargement()
	await get_tree().process_frame

	_charger()
	_batir_ciel()
	_batir_terrain()
	_batir_eau()

	var t0 := Time.get_ticks_msec()
	usine = Usine.new()
	add_child(usine)
	planches = await usine.fabriquer(deg_to_rad(TILTS[tilt_i]), true)
	print("usine : %d volumes × %d variantes × 8 angles en %d ms" % [
		planches.size(), Volumes.VARIANTES, Time.get_ticks_msec() - t0])

	_batir_materiaux()
	_choisir_departs()
	_semer_arbres()
	_semer_litiere()
	_poser_ruines()
	_poser_perso()
	_batir_camera()
	vie = Vie.new()
	vie.name = "Vie"
	add_child(vie)
	vie.demarrer(self, planches, riviere)
	_batir_hud()
	chargement.queue_free()
	_appliquer_angle()
	if "--auto" in OS.get_cmdline_user_args():
		auto = true
		_tour_automatique()


func _ecran_chargement() -> void:
	var cl := CanvasLayer.new()
	add_child(cl)
	chargement = Label.new()
	chargement.text = "Balazuc — construction du monde…"
	chargement.set_anchors_preset(Control.PRESET_CENTER)
	chargement.add_theme_font_size_override("font_size", 20)
	cl.add_child(chargement)


func _charger() -> void:
	meta = JSON.parse_string(FileAccess.get_file_as_string(DATA + "monde.json"))
	n = int(meta["n"])
	pas = float(meta["pas_m"])
	emprise = n * pas
	alt = FileAccess.get_file_as_bytes(DATA + "terrain.bin").to_float32_array()
	eau = FileAccess.get_file_as_bytes(DATA + "eau.bin").to_float32_array()
	assert(alt.size() == n * n, "terrain.bin ne correspond pas à monde.json")


# ───────────────────────────────────────────────────────── ciel & brume
func _batir_ciel() -> void:
	var we := WorldEnvironment.new()
	var e := Environment.new()
	var ciel := Sky.new()
	var psm := ProceduralSkyMaterial.new()
	psm.sky_top_color = Color(0.32, 0.47, 0.72)
	psm.sky_horizon_color = Color(0.76, 0.80, 0.79)
	psm.ground_horizon_color = Color(0.76, 0.80, 0.79)
	psm.ground_bottom_color = Color(0.30, 0.32, 0.27)
	ciel.sky_material = psm
	e.background_mode = Environment.BG_SKY
	e.sky = ciel
	e.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	e.ambient_light_energy = 0.9

	# La brume atmosphérique, c'est la doc 06 rendue littérale : « voir beaucoup
	# mais pas précisément ». En ortho, la profondeur à l'écran est linéaire du
	# bas vers le haut de l'image — une brume en profondeur donne donc pile la
	# perspective aérienne, et la fenêtre se recale sur le zoom à chaque image.
	# Éteinte par défaut : elle lave la matière et elle a brouillé deux
	# diagnostics de suite (j'ai comparé des captures avec et sans sans m'en
	# rendre compte). À rallumer sur F quand on juge l'ambiance, pas la matière.
	e.fog_enabled = false
	e.fog_mode = Environment.FOG_MODE_DEPTH
	e.fog_light_color = Color(0.70, 0.75, 0.78)
	e.fog_density = 0.30
	e.fog_depth_curve = 2.4
	e.fog_sky_affect = 0.0
	# Les deux portées de la doc 06, en mètres et en dur : net jusqu'à ~350 m
	# au-delà du perso, horizon fermé vers 3 km. Surtout PAS indexé sur le zoom
	# — sinon dézoomer embrumerait ce qu'on a sous le nez.
	e.fog_depth_begin = DIST + 350.0
	e.fog_depth_end = DIST + 3000.0
	we.environment = e
	add_child(we)
	env = e

	# Une seule lumière dans toute la scène, et elle ne sert QU'À l'eau : le
	# terrain et les sprites sont en non-éclairé, leur lumière est déjà cuite.
	var s := DirectionalLight3D.new()
	s.light_color = Color(1.0, 0.95, 0.84)
	s.light_energy = 1.15
	var d := Vector3(cos(Usine.SOL_EL) * sin(Usine.SOL_AZ), sin(Usine.SOL_EL),
					 cos(Usine.SOL_EL) * cos(Usine.SOL_AZ))
	s.look_at_from_position(d * 500.0, Vector3.ZERO, Vector3.UP)
	add_child(s)


# ───────────────────────────────────────────────────────── terrain
func _batir_terrain() -> void:
	var t0 := Time.get_ticks_msec()
	var coul := FileAccess.get_file_as_bytes(DATA + "couleurs.bin")
	var v := PackedVector3Array()
	var c := PackedColorArray()
	var nr := PackedVector3Array()
	v.resize(n * n)
	c.resize(n * n)
	nr.resize(n * n)
	for j in range(n):
		var b := j * n
		var z := j * pas
		var j0 := maxi(j - 1, 0) * n
		var j1 := mini(j + 1, n - 1) * n
		for i in range(n):
			var k := b + i
			v[k] = Vector3(i * pas, alt[k], z)
			c[k] = Color8(coul[k * 3], coul[k * 3 + 1], coul[k * 3 + 2])
			# la normale sert au shader : elle porte la macro-forme, sur
			# laquelle le micro-relief des textures viendra se greffer
			var i0 := maxi(i - 1, 0)
			var i1 := mini(i + 1, n - 1)
			var dx := (alt[b + i1] - alt[b + i0]) / ((i1 - i0) * pas)
			var dz := (alt[j1 + i] - alt[j0 + i]) / (2.0 * pas)
			nr[k] = Vector3(-dx, 1.0, -dz).normalized()
	var idx := PackedInt32Array()
	idx.resize((n - 1) * (n - 1) * 6)
	var p := 0
	for j in range(n - 1):
		var b := j * n
		for i in range(n - 1):
			var a := b + i
			idx[p] = a; idx[p + 1] = a + n; idx[p + 2] = a + 1
			idx[p + 3] = a + 1; idx[p + 4] = a + n; idx[p + 5] = a + n + 1
			p += 6

	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = v
	arr[Mesh.ARRAY_NORMAL] = nr
	arr[Mesh.ARRAY_COLOR] = c
	arr[Mesh.ARRAY_INDEX] = idx
	var m := ArrayMesh.new()
	m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)

	# Filet de sécurité : le matériau plat d'avant, sans shader. La session de
	# juillet a été perdue à cause d'un shader qui tombait en silence chez toi ;
	# tant que le shader n'est pas vérifié sur ta machine, X ramène celui-ci.
	mat_plat = StandardMaterial3D.new()
	mat_plat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat_plat.vertex_color_use_as_albedo = true
	mat_plat.cull_mode = BaseMaterial3D.CULL_DISABLED

	terrain = MeshInstance3D.new()
	terrain.mesh = m
	terrain.name = "Terrain"
	add_child(terrain)
	_batir_matiere()
	terrain.material_override = mat_matiere if mat_matiere != null else mat_plat
	print("terrain : %d sommets, %d triangles en %d ms" % [
		v.size(), idx.size() / 3, Time.get_ticks_msec() - t0])


# Les quatre matières tuilées + les deux cartes (mélange, lumière).
func _batir_matiere() -> void:
	var t0 := Time.get_ticks_msec()
	var sh := load("res://scripts/terrain.gdshader")
	if sh == null:
		push_warning("shader de terrain introuvable — on reste en aplat")
		return
	var mm := ShaderMaterial.new()
	mm.shader = sh
	for nom in ["falaise", "garrigue", "sousbois", "berge"]:
		for suf in ["col", "nrm"]:
			var img := Image.new()
			var chemin := "res://textures/%s_%s.jpg" % [nom, suf]
			if img.load(chemin) != OK:
				push_warning("texture absente : " + chemin)
				return
			img.generate_mipmaps()
			mm.set_shader_parameter("%s_%s" % [nom, suf],
				ImageTexture.create_from_image(img))

	# carte de mélange : un octet par matière et par maille de 2,34 m
	var oc := FileAccess.get_file_as_bytes(DATA + "couches.bin")
	var im := Image.create_from_data(n, n, false, Image.FORMAT_RGBA8, oc)
	mm.set_shader_parameter("melange", ImageTexture.create_from_image(im))

	# carte de lumière : soleil + ombres portées + part de ciel, cuits
	var lu := FileAccess.get_file_as_bytes(DATA + "lumiere.bin")
	var il := Image.create_from_data(n, n, false, Image.FORMAT_RGB8, lu)
	mm.set_shader_parameter("lumiere", ImageTexture.create_from_image(il))

	mm.set_shader_parameter("emprise", emprise)
	mm.set_shader_parameter("echelle_lum", float(meta.get("echelle_lum", 1.6)))
	mm.set_shader_parameter("soleil", Vector3(
		cos(Usine.SOL_EL) * sin(Usine.SOL_AZ), sin(Usine.SOL_EL),
		cos(Usine.SOL_EL) * cos(Usine.SOL_AZ)))
	mat_matiere = mm
	print("matières : 4 textures CC0 2K + mélange + lumière en %d ms" % [
		Time.get_ticks_msec() - t0])


func _batir_eau() -> void:
	# Surface continue : on n'émet un quad que si ses QUATRE coins sont dans le
	# masque BD TOPO. Pas de plan unique — sur 2,4 km de gorge la rivière
	# descend, et convertir.py lui a calculé une altitude par maille.
	var rive := _distance_rive()
	riviere = Riviere.new()
	riviere.calculer(n, pas, eau, rive)
	var carte := PackedInt32Array()
	carte.resize(n * n)
	carte.fill(-1)
	var v := PackedVector3Array()
	var c := PackedColorArray()
	var uv := PackedVector2Array()
	var tg := PackedFloat32Array()
	var idx := PackedInt32Array()
	for j in range(n - 1):
		for i in range(n - 1):
			var k := j * n + i
			var q := [k, k + 1, k + n, k + n + 1]
			var ok := true
			for cc in q:
				if is_nan(eau[cc]):
					ok = false
					break
			if not ok:
				continue
			for cc in q:
				if carte[cc] < 0:
					carte[cc] = v.size()
					var x: float = (cc % n) * pas
					var z: float = (cc / n) * pas
					v.append(Vector3(x, eau[cc], z))
					uv.append(Vector2(x / emprise, z / emprise))
					c.append(_couleur_eau(rive[cc]))
					# surface plane : une tangente constante suffit, mais elle
					# est obligatoire — sans elle la carte de normales est ignorée
					tg.append_array([1.0, 0.0, 0.0, 1.0])
			idx.append_array([carte[k], carte[k + n], carte[k + 1],
							  carte[k + 1], carte[k + n], carte[k + n + 1]])
	if v.is_empty():
		push_warning("aucune eau dans le masque")
		return
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = v
	arr[Mesh.ARRAY_TEX_UV] = uv
	arr[Mesh.ARRAY_COLOR] = c
	arr[Mesh.ARRAY_TANGENT] = tg
	arr[Mesh.ARRAY_NORMAL] = _normales_hautes(v.size())
	arr[Mesh.ARRAY_INDEX] = idx
	var m := ArrayMesh.new()
	m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)

	# Le matériau d'avant, gardé EN SECOURS et accessible à la touche K. La
	# session de juillet a perdu l'eau parce qu'un ShaderMaterial tombait en
	# silence sous ANGLE ; le shader qui suit est donc à vérifier sur ta
	# machine, et tant qu'il ne l'est pas il faut pouvoir revenir en une touche.
	mat_eau_secours = StandardMaterial3D.new()
	mat_eau_secours.vertex_color_use_as_albedo = true
	mat_eau_secours.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat_eau_secours.roughness = 0.20
	mat_eau_secours.metallic = 0.0
	mat_eau_secours.metallic_specular = 0.55
	mat_eau_secours.normal_enabled = true
	mat_eau_secours.normal_texture = Riviere.rides()
	mat_eau_secours.normal_scale = 0.35
	mat_eau_secours.uv1_scale = Vector3(emprise / 9.0, emprise / 9.0, 1.0)
	mat_eau_secours.cull_mode = BaseMaterial3D.CULL_DISABLED

	var sh := load("res://scripts/eau.gdshader")
	if sh != null:
		mat_eau = ShaderMaterial.new()
		mat_eau.shader = sh
		mat_eau.set_shader_parameter("flux", riviere.texture)
		mat_eau.set_shader_parameter("rides", Riviere.rides())
		mat_eau.set_shader_parameter("grain", Riviere.grain())
		mat_eau.set_shader_parameter("emprise", emprise)
		mat_eau.set_shader_parameter("soleil", Vector3(
			cos(Usine.SOL_EL) * sin(Usine.SOL_AZ), sin(Usine.SOL_EL),
			cos(Usine.SOL_EL) * cos(Usine.SOL_AZ)))
	else:
		push_warning("shader d'eau introuvable — on reste sur le matériau de secours")
		eau_shader = false

	noeud_eau = MeshInstance3D.new()
	noeud_eau.mesh = m
	noeud_eau.material_override = mat_eau if eau_shader else mat_eau_secours
	noeud_eau.name = "Eau"
	add_child(noeud_eau)
	print("eau : %d sommets" % v.size())


func _normales_hautes(combien: int) -> PackedVector3Array:
	var nn := PackedVector3Array()
	nn.resize(combien)
	nn.fill(Vector3.UP)
	return nn


# Distance à la berge, en mètres, sur le masque d'eau (transformée de chanfrein
# en deux balayages). On NE PEUT PAS déduire la profondeur de la géométrie : le
# LiDAR a déjà la nappe dans le MNT, donc « altitude d'eau moins terrain » vaut
# ~0,5 m partout et la rivière sortait d'un seul bleu pâle. La largeur, elle,
# dit la vérité : au milieu c'est profond, au bord c'est un gué.
func _distance_rive() -> PackedFloat32Array:
	var d := PackedFloat32Array()
	d.resize(n * n)
	var INF := 1.0e9
	for k in range(n * n):
		d[k] = INF if not is_nan(eau[k]) else 0.0
	var dr := pas
	var di := pas * 1.41421
	for j in range(n):
		for i in range(n):
			var k := j * n + i
			if d[k] == 0.0:
				continue
			var m := d[k]
			if i > 0: m = minf(m, d[k - 1] + dr)
			if j > 0: m = minf(m, d[k - n] + dr)
			if i > 0 and j > 0: m = minf(m, d[k - n - 1] + di)
			if i < n - 1 and j > 0: m = minf(m, d[k - n + 1] + di)
			d[k] = m
	for j in range(n - 1, -1, -1):
		for i in range(n - 1, -1, -1):
			var k := j * n + i
			if d[k] == 0.0:
				continue
			var m := d[k]
			if i < n - 1: m = minf(m, d[k + 1] + dr)
			if j < n - 1: m = minf(m, d[k + n] + dr)
			if i < n - 1 and j < n - 1: m = minf(m, d[k + n + 1] + di)
			if i > 0 and j < n - 1: m = minf(m, d[k + n - 1] + di)
			d[k] = m
	return d


func _couleur_eau(rive: float) -> Color:
	var t := clampf(rive / 16.0, 0.0, 1.0)
	t = t * t * (3.0 - 2.0 * t)                    # transition douce
	var c := Color(0.42, 0.52, 0.48, 0.34).lerp(Color(0.05, 0.15, 0.21, 0.96), t)
	if rive < 3.0:                                 # frange claire, le gué
		c = c.lerp(Color(0.70, 0.76, 0.70, 0.26), 1.0 - rive / 3.0)
	return c


# ───────────────────────────────────────────────────────── sprites
# Les sprites passent d'un StandardMaterial3D à scripts/vegetation.gdshader.
# Ce que le shader doit rendre à l'identique, sous peine de perdre la forêt en
# croyant gagner le vent : le billboard fixé sur Y, le découpage alpha franc
# (qui permet de NE PAS trier 53 000 quads en profondeur), la nuance par
# instance du MultiMesh, et le non-éclairé. Ce qu'il ajoute : l'oscillation.
func _batir_materiaux() -> void:
	var src: Dictionary = planches if soleil_monde else planches_faux
	var sh := load("res://scripts/vegetation.gdshader")
	mats.clear()
	mats_derive.clear()
	for nom in src:
		if nom in Vie.ESPECES:
			continue                  # la faune a son propre atlas (vie.gd)
		var formes := []
		var formes_vol := []
		for v in range(src[nom].size()):
			var jeu: Array = []
			var jeu_vol: Array = []
			for a in range(Usine.ANGLES):
				jeu.append(_mat_sprite(sh, src[nom][v][a], nom, 0.0))
				if nom == "feuilles":
					jeu_vol.append(_mat_sprite(sh, src[nom][v][a], nom, 1.6))
			formes.append(jeu)
			formes_vol.append(jeu_vol)
		mats[nom] = formes
		if nom == "feuilles":
			mats_derive[nom] = formes_vol


func _mat_sprite(sh: Shader, planche: Texture2D, nom: String, tourbillon: float) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = sh
	m.set_shader_parameter("planche", planche)
	m.set_shader_parameter("hauteur", float(Volumes.CATALOGUE[nom]))
	m.set_shader_parameter("souplesse", float(SOUPLESSE.get(nom, 0.6)))
	m.set_shader_parameter("vent_dir", VENT_DIR)
	m.set_shader_parameter("vent_force", vent)
	m.set_shader_parameter("tourbillon", tourbillon)
	m.set_shader_parameter("seuil", 0.5)
	return m


# Le vent se coupe (touche V) : sans un A/B au même endroit on ne sait pas dire
# si l'oscillation aide la lecture du paysage ou si elle la brouille.
func _souffler(f: float) -> void:
	vent = f
	for table in [mats, mats_derive]:
		for nom in table:
			for formes in table[nom]:
				for m in formes:
					m.set_shader_parameter("vent_force", f)


func _quad(nom: String) -> QuadMesh:
	var h: float = Volumes.CATALOGUE[nom]
	var q := QuadMesh.new()
	q.size = Vector2(h, h)
	q.center_offset = Vector3(0, h * (0.5 - Volumes.MARGE_BAS), 0)
	return q


func _semer_arbres() -> void:
	var vers := {
		"ripisylve": "peuplier", "chene_vert": "chene_vert",
		"chene_pubescent": "chene_pubescent", "garrigue": "buisson",
		"rocher": "rocher", "pelouse": "buisson", "eau": "buisson",
	}
	var noms: Array = meta["noms"]
	var octets := FileAccess.get_file_as_bytes(DATA + "arbres.bin")
	var nb := octets.size() / 14
	# On range chaque arbre par (essence, variante, ORIENTATION dans le monde).
	# L'orientation vient de la position, donc elle est stable : un arbre garde
	# la même face au même endroit, partie après partie.
	var lots := {}
	for t in range(nb):
		var o := t * 14
		var x := octets.decode_float(o)
		var z := octets.decode_float(o + 4)
		var esp := int(octets.decode_u8(o + 8))
		var ech := octets.decode_float(o + 9)
		var vari := int(octets.decode_u8(o + 13)) % Volumes.VARIANTES
		var vol: String = vers.get(noms[esp], "buisson")
		var graine := hash(Vector2i(int(x * 4.0), int(z * 4.0)))
		var orient: int = graine % Usine.ANGLES
		var cle := "%s|%d|%d" % [vol, vari, orient]
		if not lots.has(cle):
			lots[cle] = []
		lots[cle].append([x, altitude_en(x, z), z, ech, float(graine % 1000) / 1000.0])

	var total := _poser_lots(lots)
	print("semis : %d arbres en %d lots (essence × variante × orientation)" % [
		total, groupes.size()])
	_semer_cailloux()


# Les pentes nues du LiDAR sortent en aplat : le semis n'y met rien parce qu'il
# n'y pousse rien. Un éboulis et quelques touffes suffisent à leur rendre une
# échelle — et ils réutilisent le volume « rocher », fabriqué depuis le début
# mais jamais semé.
func _semer_cailloux() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 20260923
	var lots := {}
	var maille := 7.5
	var g := int(emprise / maille)
	for j in range(g):
		for i in range(g):
			var x := (i + rng.randf()) * maille
			var z := (j + rng.randf()) * maille
			var pen := _pente(x, z)
			if pen < 15.0 or not _sec(x, z):
				continue
			if rng.randf() > clampf((pen - 15.0) / 20.0, 0.0, 1.0) * 0.85:
				continue
			var nom := "rocher" if rng.randf() < 0.62 else "buisson"
			var vari := rng.randi() % Volumes.VARIANTES
			var orient := rng.randi() % Usine.ANGLES
			var cle := "%s|%d|%d" % [nom, vari, orient]
			if not lots.has(cle):
				lots[cle] = []
			lots[cle].append([x, altitude_en(x, z), z,
				rng.randf_range(0.55, 1.35), rng.randf()])
	var total := _poser_lots(lots)
	print("éboulis : %d cailloux et touffes sur les pentes nues" % total)


func _poser_lots(lots: Dictionary, derive := false) -> int:
	var total := 0
	for cle in lots:
		var bout: PackedStringArray = cle.split("|")
		var nom := bout[0]
		var vari := int(bout[1])
		var orient := int(bout[2])
		var liste: Array = lots[cle]
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.use_colors = true
		mm.mesh = _quad(nom)
		mm.instance_count = liste.size()
		for i in range(liste.size()):
			var a: Array = liste[i]
			var b := Basis().scaled(Vector3(a[3], a[3], a[3]))
			mm.set_instance_transform(i, Transform3D(b, Vector3(a[0], a[1], a[2])))
			# nuance par instance : un vert un peu plus clair ou plus jaune.
			# C'est ce qui empêche la forêt d'être une tache uniforme.
			var g: float = a[4]
			mm.set_instance_color(i, Color(0.86 + g * 0.30, 0.90 + g * 0.20, 0.84 + g * 0.26))
		var mi := MultiMeshInstance3D.new()
		mi.multimesh = mm
		mi.name = "Semis_" + cle.replace("|", "_")
		# Sans boîte explicite, Godot culle la forêt entière dès que l'origine
		# du MultiMesh sort du champ.
		mi.custom_aabb = AABB(Vector3.ZERO, Vector3(emprise, 400, emprise))
		add_child(mi)
		groupes.append({"mi": mi, "nom": nom, "var": vari, "orient": orient,
						"derive": derive})
		total += liste.size()
	return total


# Herbe sèche, tas de feuilles, feuilles en l'air.
#
# Le sol du proto s'arrêtait à l'arbre et au caillou : entre les deux, la
# texture tuilée toute seule. Or c'est l'échelle intermédiaire qui dit au
# regard à quelle distance il se trouve — sans elle une garrigue à 40 m et une
# garrigue à 400 m se ressemblent.
#
# La répartition ne se devine pas : elle se LIT dans couches.bin, la carte de
# mélange que le shader de terrain utilise déjà. Là où le sol est garrigue, on
# sème des touffes sèches ; là où il est litière de sous-bois, des feuilles.
# Semer à l'aveugle aurait mis de la paille sur le calcaire nu.
func _semer_litiere() -> void:
	var t0 := Time.get_ticks_msec()
	var oc := FileAccess.get_file_as_bytes(DATA + "couches.bin")
	var rng := RandomNumberGenerator.new()
	rng.seed = 424242
	var lots := {}
	var vol := {}
	var maille := 5.2
	var g := int(emprise / maille)
	for j in range(g):
		for i in range(g):
			var x := (i + rng.randf()) * maille
			var z := (j + rng.randf()) * maille
			var k := clampi(int(z / pas), 0, n - 1) * n + clampi(int(x / pas), 0, n - 1)
			if not _sec(x, z):
				continue
			var garrigue := oc[k * 4 + 1] / 255.0
			var sousbois := oc[k * 4 + 2] / 255.0
			var nom := ""
			if garrigue > 0.30 and rng.randf() < garrigue * 0.72:
				nom = "herbe_seche"
			elif sousbois > 0.34 and rng.randf() < sousbois * 0.34:
				nom = "feuilles"
			else:
				continue
			if _pente(x, z) > 38.0:
				continue
			var vari := rng.randi() % Volumes.VARIANTES
			var orient := rng.randi() % Usine.ANGLES
			var cle := "%s|%d|%d" % [nom, vari, orient]
			if not lots.has(cle):
				lots[cle] = []
			lots[cle].append([x, altitude_en(x, z), z,
				rng.randf_range(0.7, 1.6), rng.randf()])
			# quelques feuilles décollent : elles tourbillonnent au-dessus du tas
			if nom == "feuilles" and rng.randf() < 0.055:
				var cv := "feuilles|%d|%d" % [vari, orient]
				if not vol.has(cv):
					vol[cv] = []
				vol[cv].append([x, altitude_en(x, z) + rng.randf_range(0.6, 2.4), z,
					rng.randf_range(0.5, 1.0), rng.randf()])
	litiere = _poser_lots(lots)
	var envol := _poser_lots(vol, true)
	print("litière : %d touffes et tas + %d feuilles en l\'air (%d ms)" % [
		litiere, envol, Time.get_ticks_msec() - t0])


func _poser_ruines() -> void:
	# Huit ruines en couronne autour du point de départ, une par orientation du
	# monde. En mode PALIERS, les huit cases de la planche servent en même temps
	# à l'écran : c'est la démonstration que l'objet ORIENTÉ a besoin des 8
	# angles, là où l'arbre s'en passerait.
	for i in range(Usine.ANGLES):
		var a := TAU * float(i) / float(Usine.ANGLES) + 0.4
		var p := _terre_ferme(depart_gorge + Vector3(cos(a), 0, sin(a)) * 52.0)
		var mi := MeshInstance3D.new()
		mi.mesh = _quad("ruine")
		mi.position = p
		mi.custom_aabb = AABB(Vector3(-8, -8, -8), Vector3(16, 24, 16))
		add_child(mi)
		ruines.append({"noeud": mi, "orient": i, "var": i % Volumes.VARIANTES})


# Pousse un point jusqu'à un sol SEC et pas trop pentu. Sans ça, les ruines de
# la couronne tombaient dans la rivière — les « bâtiments dans l'eau ».
func _terre_ferme(p: Vector3) -> Vector3:
	var c := Vector2(clampf(p.x, 30, emprise - 30), clampf(p.z, 30, emprise - 30))
	for essai in range(70):
		if _sec(c.x, c.y) and _pente(c.x, c.y) < 22.0:
			break
		# spirale : on s'éloigne en tournant, donc on trouve la berge la plus
		# proche au lieu de sauter à l'autre bout de la carte
		var a := essai * 2.39996            # angle d'or, répartition régulière
		var r := 12.0 + essai * 3.0
		c = Vector2(clampf(p.x + cos(a) * r, 30, emprise - 30),
					clampf(p.z + sin(a) * r, 30, emprise - 30))
	return Vector3(c.x, altitude_en(c.x, c.y), c.y)


func _sec(x: float, z: float) -> bool:
	var r := 9.0
	for dz in [-r, 0.0, r]:
		for dx in [-r, 0.0, r]:
			var i := clampi(int((x + dx) / pas), 0, n - 1)
			var j := clampi(int((z + dz) / pas), 0, n - 1)
			if not is_nan(eau[j * n + i]):
				return false
	return true


func _pente(x: float, z: float) -> float:
	var d := 4.0
	var dx := (altitude_en(x + d, z) - altitude_en(x - d, z)) / (2.0 * d)
	var dz := (altitude_en(x, z + d) - altitude_en(x, z - d)) / (2.0 * d)
	return rad_to_deg(atan(sqrt(dx * dx + dz * dz)))


func _poser_perso() -> void:
	perso = MeshInstance3D.new()
	perso.mesh = _quad("perso")
	perso.custom_aabb = AABB(Vector3(-3, -3, -3), Vector3(6, 8, 6))
	add_child(perso)
	p_pos = depart_gorge
	p_pos.y = altitude_en(p_pos.x, p_pos.z)
	cible = p_pos


# Choisir les deux points de vue par la MESURE, pas à l'œil. La session de
# juillet a déraillé à force de juger sur impression ; ici, on compte.
func _choisir_departs() -> void:
	var t0 := Time.get_ticks_msec()
	var meilleur := -1
	var basse := 1e9
	var haut := -1e9
	var marge := int(260.0 / pas)
	var saut := maxi(1, int(18.0 / pas))
	var teste := 0
	var somme := 0
	for j in range(marge, n - marge, saut):
		for i in range(marge, n - marge, saut):
			var k := j * n + i
			if not is_nan(eau[k]):
				continue
			var p := Vector3(i * pas, alt[k], j * pas)
			if alt[k] > haut:
				haut = alt[k]
				depart_plateau = p
			if not _pres_de_leau(i, j):
				continue
			var bloques := 0
			for a in range(Usine.ANGLES):
				if _masque_depuis(p, a):
					bloques += 1
			teste += 1
			somme += bloques
			# le point le plus enfermé QUI GARDE une échappée : c'est là que la
			# rotation fait une différence visible
			if bloques <= 6 and (bloques > meilleur or (bloques == meilleur and alt[k] < basse)):
				meilleur = bloques
				basse = alt[k]
				depart_gorge = p
	gorge_bloques = meilleur
	if teste > 0:
		gorge_moyenne = float(somme) / float(teste)
	print("départs : %d points de berge testés, %.2f palier(s) masqué(s) en moyenne, meilleur %d/8 (%d ms)" % [
		teste, gorge_moyenne, meilleur, Time.get_ticks_msec() - t0])


func _pres_de_leau(i: int, j: int) -> bool:
	var r := maxi(2, int(14.0 / pas))
	for dj in [-r, 0, r]:
		for di in [-r, 0, r]:
			var jj := clampi(j + dj, 0, n - 1)
			var ii := clampi(i + di, 0, n - 1)
			if not is_nan(eau[jj * n + ii]):
				return true
	return false


# ───────────────────────────────────────────────────────── caméra & HUD
func _batir_camera() -> void:
	cam = Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.near = 1.0
	cam.far = DIST * 2.4
	cam.size = portee
	add_child(cam)
	cam.current = true


func _placer_camera() -> void:
	var tilt := deg_to_rad(TILTS[tilt_i])
	var az := TAU * float(az_i) / float(Usine.ANGLES)
	cam.size = portee
	var c := (cible if libre else p_pos) + Vector3(0, 1.0, 0)
	cam.position = c + Vector3(sin(az) * cos(tilt), sin(tilt), cos(az) * cos(tilt)) * DIST
	cam.look_at(c, Vector3.UP)


func _batir_hud() -> void:
	var cl := CanvasLayer.new()
	add_child(cl)
	var fond := ColorRect.new()
	fond.color = Color(0.055, 0.067, 0.047, 0.88)
	fond.size = Vector2(458, 516)
	cl.add_child(fond)
	hud = RichTextLabel.new()
	hud.bbcode_enabled = true
	hud.fit_content = true
	hud.scroll_active = false
	hud.position = Vector2(14, 12)
	hud.size = Vector2(430, 496)
	hud.add_theme_font_size_override("normal_font_size", 13)
	hud.add_theme_font_size_override("bold_font_size", 13)
	cl.add_child(hud)

	alerte = Label.new()
	alerte.add_theme_font_size_override("font_size", 26)
	alerte.add_theme_color_override("font_color", Color(1, 0.35, 0.3))
	alerte.set_anchors_preset(Control.PRESET_CENTER_TOP)
	alerte.position = Vector2(-220, 26)
	alerte.size = Vector2(440, 40)
	alerte.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	alerte.visible = false
	cl.add_child(alerte)


# ───────────────────────────────────────────────────────── boucle
func _process(dt: float) -> void:
	if cam == null:
		return
	_bouger(dt)
	_placer_camera()
	if not eau_shader and mat_eau_secours != null:
		# Le matériau de secours n'a pas de champ d'écoulement : il ne sait que
		# faire glisser ses UV, toujours dans le même sens. C'est justement ce
		# que le shader remplace.
		var t := Time.get_ticks_msec() / 1000.0
		mat_eau_secours.uv1_offset = Vector3(t * 0.011, t * 0.028, 0.0)
	if vie != null:
		vie.maj(dt, az_i, p_pos)
	masque_maintenant = _masque_depuis(p_pos, az_i)
	total_temps[verrouille] += dt
	if masque_maintenant:
		masque_temps[verrouille] += dt
	alerte.visible = masque_maintenant and not libre
	alerte.text = "PERSO MASQUÉ PAR LE RELIEF"
	_hud()


func _bouger(dt: float) -> void:
	var d := Vector2.ZERO
	if Input.is_key_pressed(KEY_Z): d.y -= 1
	if Input.is_key_pressed(KEY_S): d.y += 1
	if Input.is_key_pressed(KEY_Q): d.x -= 1
	if Input.is_key_pressed(KEY_D): d.x += 1
	if d == Vector2.ZERO:
		return
	d = d.normalized()
	# On se déplace dans le repère de l'ÉCRAN : « haut » avance vers le haut de
	# l'image quel que soit le palier. Sinon, pivoter désoriente la marche.
	var az := TAU * float(az_i) / float(Usine.ANGLES)
	var av := Vector3(-sin(az), 0, -cos(az))
	var dr := Vector3(cos(az), 0, -sin(az))
	var v := (av * -d.y + dr * d.x).normalized()
	var rapide := Input.is_key_pressed(KEY_SHIFT)
	if libre:
		# en caméra libre, on survole : la vitesse suit le zoom, sinon on rampe
		# quand on est dézoomé et on fuse quand on est près du sol
		var vit: float = portee * (2.4 if rapide else 0.8)
		cible += v * vit * dt
		cible.x = clampf(cible.x, 0, emprise - pas)
		cible.z = clampf(cible.z, 0, emprise - pas)
		cible.y = altitude_en(cible.x, cible.z)
	else:
		p_pos += v * (14.0 if rapide else 5.0) * dt
		p_pos.x = clampf(p_pos.x, 0, emprise - pas)
		p_pos.z = clampf(p_pos.z, 0, emprise - pas)
		p_pos.y = altitude_en(p_pos.x, p_pos.z)
		p_dir = int(round(atan2(v.x, v.z) / (TAU / Usine.ANGLES))) % Usine.ANGLES
		_appliquer_angle()


func _appliquer_angle() -> void:
	# Un sprite est choisi par l'angle RELATIF entre l'objet et la caméra.
	# Comme le pas de la caméra (45°) est un multiple du pas des sprites (45°),
	# cet angle relatif reste sur la grille : 8 images suffisent, toujours.
	#
	# Le SENS de cet angle relatif, lui, était inversé, et ça ne se voyait pas
	# tant que rien ne marchait dans une direction connue : l'usine photographie
	# le volume depuis l'azimut a·45°, donc un objet tourné de Δ se regarde sous
	# l'image (azimut_caméra − Δ), pas (Δ − azimut_caméra). Sur un arbre dont le
	# lacet est tiré au hasard, les deux se valent. Sur le perso — et maintenant
	# sur les hardes — l'un des deux fait marcher les bêtes à reculons.
	for g in groupes:
		var rel: int = (az_i - int(g["orient"]) + Usine.ANGLES * 2) % Usine.ANGLES
		var table: Dictionary = mats_derive if g.get("derive", false) else mats
		g["mi"].material_override = table[g["nom"]][int(g["var"])][rel]
	for r in ruines:
		var rel: int = (az_i - int(r["orient"]) + Usine.ANGLES * 2) % Usine.ANGLES
		r["noeud"].material_override = mats["ruine"][int(r["var"])][rel]
	if perso != null:
		# Le modèle regarde vers −Z : son lacet vaut donc son cap moins un
		# demi-tour, d'où les quatre huitièmes ajoutés.
		var rel: int = (az_i - p_dir + 4 + Usine.ANGLES * 2) % Usine.ANGLES
		perso.material_override = mats["perso"][0][rel]
		perso.position = p_pos


# Le relief passe-t-il entre la caméra et ce point, sous ce palier ?
# C'est la mesure de toute la question : en yaw verrouillé, on ne peut pas
# tourner autour de la falaise, on subit l'orientation qu'on a.
func _masque_depuis(pos: Vector3, palier: int) -> bool:
	var tilt := deg_to_rad(TILTS[tilt_i])
	var az := TAU * float(palier) / float(Usine.ANGLES)
	var b := pos + Vector3(0, 1.6, 0)
	var dir := Vector3(sin(az) * cos(tilt), sin(tilt), cos(az) * cos(tilt))
	for s in range(1, 180):
		var p := b + dir * (s * 5.0)
		if p.x < 0 or p.z < 0 or p.x >= emprise or p.z >= emprise:
			return false
		if altitude_en(p.x, p.z) > p.y + 0.6:
			return true
	return false


var _cache_pos := Vector3(-1e9, 0, 0)
var _cache_bloques := 0

# Combien des 8 paliers sont masqués à l'endroit où l'on se tient ? C'est le
# chiffre qui tranche : s'il vaut 0 partout, le yaw verrouillé ne coûte rien.
func _bloques_ici() -> int:
	if p_pos.distance_to(_cache_pos) < 3.0:
		return _cache_bloques
	_cache_pos = p_pos
	_cache_bloques = 0
	for a in range(Usine.ANGLES):
		if _masque_depuis(p_pos, a):
			_cache_bloques += 1
	return _cache_bloques


# Ce que vie.gd a besoin de savoir du monde, et rien de plus : où est le sol,
# où il est sec, où il est trop raide, et à quelle hauteur est la nappe d'eau.
func est_sec(x: float, z: float) -> bool:
	return _sec(x, z)


func pente_en(x: float, z: float) -> float:
	return _pente(x, z)


# NAN hors de l'eau : c'est la convention de eau.bin, et elle dit exactement
# « il n'y a pas de surface ici », ce qu'un 0 ne dirait pas.
func niveau_eau(x: float, z: float) -> float:
	var i := clampi(int(x / pas), 0, n - 1)
	var j := clampi(int(z / pas), 0, n - 1)
	return eau[j * n + i]


func altitude_en(x: float, z: float) -> float:
	var fx := clampf(x / pas, 0, n - 1.001)
	var fz := clampf(z / pas, 0, n - 1.001)
	var i := int(fx)
	var j := int(fz)
	var u := fx - i
	var v := fz - j
	var k := j * n + i
	return (alt[k] * (1 - u) + alt[k + 1] * u) * (1 - v) \
		 + (alt[k + n] * (1 - u) + alt[k + n + 1] * u) * v


# Le point du sol sous le curseur. En ortho, le rayon est parallèle à l'axe de
# vue : on avance dessus jusqu'à passer sous le terrain, puis on affine.
func _point_sol(ecran: Vector2) -> Vector3:
	var o := cam.project_ray_origin(ecran)
	var d := cam.project_ray_normal(ecran)
	var t := 0.0
	var pas_m := 8.0
	for s in range(400):
		var p := o + d * t
		if p.x >= 0 and p.z >= 0 and p.x < emprise and p.z < emprise:
			if p.y <= altitude_en(p.x, p.z):
				# dichotomie sur le dernier segment, sinon on pose l'objet en
				# marche d'escalier
				var a := t - pas_m
				var b := t
				for _i in range(12):
					var m := (a + b) * 0.5
					var q := o + d * m
					if q.y <= altitude_en(q.x, q.z):
						b = m
					else:
						a = m
				var r := o + d * b
				return Vector3(r.x, altitude_en(r.x, r.z), r.z)
		t += pas_m
	return Vector3(-1, 0, 0)


# ───────────────────────────────────────────────────────── entrées
func _unhandled_input(e: InputEvent) -> void:
	# Pendant le tour automatique, la fenêtre reste sensible à la souris : un
	# cran de molette parasite a suffi à faire passer une capture de 110 m de
	# portée à 1831 m, et à la rendre incomparable aux précédentes. Une capture
	# de vérification ne vaut que si ses conditions sont fixées.
	if auto:
		return
	if e is InputEventMouseButton:
		if e.pressed and e.button_index == MOUSE_BUTTON_WHEEL_UP:
			portee = maxf(28.0, portee * 0.88)
		elif e.pressed and e.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			portee = minf(2600.0, portee / 0.88)
		elif e.button_index == MOUSE_BUTTON_RIGHT or e.button_index == MOUSE_BUTTON_MIDDLE:
			glisse = e.pressed
		elif e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
			var p := _point_sol(e.position)
			if p.x >= 0:
				p_pos = p
				_appliquer_angle()
				if not libre:
					cible = p_pos
	elif e is InputEventMouseMotion and glisse:
		# glisser à la souris : on convertit les pixels en mètres via la portée,
		# puis on projette sur le plan du sol selon l'azimut courant
		var mm := e as InputEventMouseMotion
		var m_par_px := portee / float(get_viewport().get_visible_rect().size.y)
		var az := TAU * float(az_i) / float(Usine.ANGLES)
		var dr := Vector3(cos(az), 0, -sin(az))
		var av := Vector3(-sin(az), 0, -cos(az))
		var tilt := deg_to_rad(TILTS[tilt_i])
		var dep: Vector3 = dr * (-mm.relative.x * m_par_px) \
				 + av * (mm.relative.y * m_par_px / maxf(0.25, sin(tilt)))
		if not libre:
			libre = true
			cible = p_pos
		cible += dep
		cible.x = clampf(cible.x, 0, emprise - pas)
		cible.z = clampf(cible.z, 0, emprise - pas)
		cible.y = altitude_en(cible.x, cible.z)

	if not (e is InputEventKey and e.pressed and not e.echo):
		return
	match e.keycode:
		KEY_1:
			verrouille = true
			az_i = 1
			_appliquer_angle()
		KEY_2:
			verrouille = false
		KEY_A:
			if not verrouille:
				az_i = (az_i + 1) % Usine.ANGLES
				_appliquer_angle()
		KEY_E:
			if not verrouille:
				az_i = (az_i + Usine.ANGLES - 1) % Usine.ANGLES
				_appliquer_angle()
		KEY_G:
			libre = not libre
			if libre:
				cible = p_pos
		KEY_F:
			env.fog_enabled = not env.fog_enabled
		KEY_X:
			# bascule matières tuilées ↔ aplat de secours
			if mat_matiere != null:
				terrain.material_override = mat_plat \
					if terrain.material_override == mat_matiere else mat_matiere
		KEY_T:
			tilt_i = (tilt_i + 1) % TILTS.size()
			await _refaire_planches()
		KEY_K:
			# Retour au matériau d'eau d'avant. C'est la précaution de juillet :
			# un shader qui tombe en silence chez toi doit se contourner en une
			# touche, pas en une session.
			if mat_eau != null:
				eau_shader = not eau_shader
				noeud_eau.material_override = mat_eau if eau_shader else mat_eau_secours
		KEY_V:
			_souffler(0.0 if vent > 0.5 else 1.0)
		KEY_L:
			soleil_monde = not soleil_monde
			await _refaire_planches()
		KEY_B:
			p_pos = depart_gorge
			p_pos.y = altitude_en(p_pos.x, p_pos.z)
			cible = p_pos
			libre = false
		KEY_H:
			p_pos = depart_plateau
			p_pos.y = altitude_en(p_pos.x, p_pos.z)
			cible = p_pos
			libre = false
		KEY_R:
			masque_temps = {true: 0.0, false: 0.0}
			total_temps = {true: 0.0, false: 0.0}
		KEY_F12:
			_capture()
		KEY_ESCAPE:
			get_tree().quit()


# Refabrique les planches : changer l'inclinaison OU le soleil oblige à
# repasser par l'usine. C'est le contrat entre l'usine et la caméra — un sprite
# n'est juste que sous l'angle où il a été photographié.
func _refaire_planches() -> void:
	chargement = Label.new()
	chargement.text = "usine à sprites…"
	chargement.set_anchors_preset(Control.PRESET_CENTER)
	var cl := CanvasLayer.new()
	cl.add_child(chargement)
	add_child(cl)
	await get_tree().process_frame
	var jeu := await usine.fabriquer(deg_to_rad(TILTS[tilt_i]), soleil_monde)
	if soleil_monde:
		planches = jeu
	else:
		planches_faux = jeu
	_batir_materiaux()
	if vie != null:
		vie.recharger(jeu)
	_appliquer_angle()
	cl.queue_free()


# Le budget d'image, mesuré et pas ressenti. On chauffe d'abord (les premières
# images après un déplacement paient le streaming des textures et le tri), PUIS
# on compte des images pendant une fenêtre de temps fixe. Sans la chauffe, le
# compteur du HUD annonce 12 fps sur une scène qui en tient 40.
func _bench(nom: String, ou: Vector3) -> void:
	p_pos = ou
	p_pos.y = altitude_en(p_pos.x, p_pos.z)
	cible = p_pos
	_appliquer_angle()
	# Sans couper la synchro verticale on mesure 60 fps sur tout et on ne voit
	# jamais venir la marge qui s'épuise. On veut le coût réel de l'image.
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	for _i in range(45):
		await get_tree().process_frame
	var t0 := Time.get_ticks_usec()
	var images := 0
	while Time.get_ticks_usec() - t0 < 2_000_000:
		await get_tree().process_frame
		images += 1
	var dt := (Time.get_ticks_usec() - t0) / 1_000_000.0
	print("FPS %s : %.1f  (%d images en %.2f s)" % [nom, images / dt, images, dt])


func _capture(nom := "") -> void:
	var img := get_viewport().get_texture().get_image()
	var dir := ProjectSettings.globalize_path("res://captures")
	DirAccess.make_dir_recursive_absolute(dir)
	if nom == "":
		nom = "%s_%s" % ["verrouille" if verrouille else "paliers",
			Time.get_datetime_string_from_system().replace(":", "-")]
	var chemin := dir + "/" + nom + ".png"
	img.save_png(chemin)
	print("capture : ", chemin)


# ───────────────────────────────────────────────────────── HUD
func _hud() -> void:
	var tilt: float = TILTS[tilt_i]
	var exag := tan(deg_to_rad(90.0 - tilt))
	var pc := func(v: bool) -> String:
		if total_temps[v] < 0.5:
			return "—"
		return "%d %%" % round(100.0 * masque_temps[v] / total_temps[v])
	var angles_utiles := 1 if verrouille else Usine.ANGLES
	var t := "[b]Balazuc — les deux caméras[/b]\n"
	t += "[color=#6b6a5e]build %s · MNT LiDAR HD · ortho[/color]\n\n" % BUILD
	if verrouille:
		t += "[color=#e8c07a][b]MODE 1 — yaw VERROUILLÉ[/b][/color]  (AoE2 pur)\n"
		t += "[color=#8f8d80]aucune rotation possible[/color]\n"
	else:
		t += "[color=#9ad07a][b]MODE 2 — paliers de 45°[/b][/color]\n"
		t += "[color=#8f8d80]A / E pour pivoter · palier %d/8 (%d°)[/color]\n" % [
			az_i, az_i * 45]
	t += "\nangles de sprite utilisés : [b]%d / 8[/b]\n" % angles_utiles
	t += "images par objet : [b]%d[/b] × %d variantes  [color=#6b6a5e](temps GPU, pas de travail d'artiste)[/color]\n" % [
		angles_utiles, Volumes.VARIANTES]
	t += "\ninclinaison %.1f° · pentes perçues ×%.2f  [color=#6b6a5e](T pour changer)[/color]\n" % [tilt, exag]
	t += "portée %.0f m · caméra [b]%s[/b]\n" % [portee, "libre" if libre else "sur le perso"]
	t += "\n[b]perso masqué par le relief[/b]\n"
	t += "  ici, sous [b]%d des 8 paliers[/b]  [color=#6b6a5e](moyenne de berge : %.1f/8)[/color]\n" % [
		_bloques_ici(), gorge_moyenne]
	t += "  temps masqué — verrouillé : [b]%s[/b]  paliers : [b]%s[/b]\n" % [
		pc.call(true), pc.call(false)]
	t += "\nsoleil cuit dans : [b]%s[/b]\n" % ("le monde ✓" if soleil_monde else "la caméra ✗ (l'éclairage ment)")
	t += "brume atmosphérique : [b]%s[/b]  [color=#6b6a5e](F)[/color]\n" % (
		"oui" if env.fog_enabled else "non")
	t += "eau : [b]%s[/b]  [color=#6b6a5e](K)[/color] · vent : [b]%s[/b]  [color=#6b6a5e](V)[/color]\n" % [
		"courant + écume" if eau_shader else "secours (UV qui glissent)",
		"oui" if vent > 0.5 else "non"]
	t += "\n[color=#8f8d80]1/2 mode · A/E pivoter · T inclinaison · L soleil\n"
	t += "G caméra libre ↔ perso · ZQSD déplacer (Maj = vite)\n"
	t += "clic droit glisser = déplacer la vue · clic gauche = poser le perso\n"
	t += "B fond de gorge · H belvédère · molette zoom\n"
	t += "K eau · V vent · R compteurs · F12 capture · Échap quitter[/color]\n"
	if vie != null:
		t += "\n[color=#7d9a6b]%d bêtes en %d hardes · %d rapaces · %d poissons[/color]\n" % [
			vie.betes.size(), vie.hardes.size(), vie.oiseaux.size(), vie.poissons.size()]
	t += "[color=#6b6a5e]%d arbres + %d touffes en %d lots · %.0f fps[/color]" % [
		meta["n_arbres"], litiere, groupes.size(), Engine.get_frames_per_second()]
	hud.text = t


# ───────────────────────────────────────────────────────── tour automatique
func _tour_automatique() -> void:
	# Lancé avec « -- --auto » : prend les captures et quitte. Sert à regarder
	# le résultat sans avoir à te déranger.
	await get_tree().create_timer(0.6).timeout
	for etape in [["gorge", true, 1], ["gorge", false, 3], ["gorge", false, 5],
				  ["plateau", true, 1], ["plateau", false, 3]]:
		p_pos = depart_gorge if etape[0] == "gorge" else depart_plateau
		p_pos.y = altitude_en(p_pos.x, p_pos.z)
		cible = p_pos
		verrouille = etape[1]
		az_i = etape[2]
		_appliquer_angle()
		await get_tree().create_timer(0.4).timeout
		_capture("%s_%s_az%d" % [etape[0], "verrouille" if etape[1] else "paliers", etape[2]])
	# Une capture cadrée sur la rivière : le fond de gorge choisi par la mesure
	# n'a pas toujours d'eau à l'image, et c'est pourtant l'eau qu'on vient
	# juger. Sans cette vue-là on conclut sur un plan où il n'y a rien à voir.
	if riviere != null and not riviere.bassins.is_empty():
		# On vise le bassin le plus AGITÉ, pas un bassin au hasard : c'est là que
		# l'écume et le courant ont quelque chose à montrer. Viser au milieu de
		# la liste tombait sur une eau morte et ne prouvait rien.
		# ...et le plus agité parmi les mailles LARGES et loin du bord de carte.
		# Le premier essai visait le maximum absolu de turbulence : il tombait
		# sur un ruisseau de trois mètres à l'extrême bord de l'emprise, et la
		# capture ne montrait pas l'Ardèche.
		var k := riviere.bassins[0]
		var pire := -1.0
		var marge := int(300.0 / pas)
		for c in riviere.bassins:
			var ci := c % n
			var cj := c / n
			if ci < marge or cj < marge or ci > n - marge or cj > n - marge:
				continue
			if riviere.prof[c] < 0.95:          # rive à plus de 13 m : le lit principal
				continue
			if riviere.turb[c] > pire:
				pire = riviere.turb[c]
				k = c
		# caméra LIBRE et cible SUR l'eau : pousser le point sur la terre ferme
		# éloignait le cadre de la rivière qu'on vient justement regarder
		libre = true
		cible = Vector3((k % n) * pas, 0.0, (k / n) * pas)
		cible.y = altitude_en(cible.x, cible.z)
		verrouille = false
		az_i = 1
		portee = 110.0
		_appliquer_angle()
		await get_tree().create_timer(1.4).timeout
		_capture("riviere_pres")
		portee = 220.0
		await get_tree().create_timer(0.8).timeout
		_capture("riviere_loin")
		portee = 150.0
		libre = false

	# ── vent : un A/B qui se MESURE ────────────────────────────────────────
	# Une capture fixe ne peut pas montrer un balancement. Ce qu'on peut
	# montrer, c'est que deux images prises au même endroit à une seconde
	# d'intervalle DIFFÈRENT quand le vent souffle, et pas quand il est coupé.
	# C'est la seule preuve qu'une capture sait donner d'un mouvement.
	libre = true
	cible = depart_gorge
	cible.y = altitude_en(cible.x, cible.z)
	portee = 70.0
	_souffler(1.0)
	await get_tree().create_timer(0.6).timeout
	_capture("vent_a")
	await get_tree().create_timer(0.9).timeout
	_capture("vent_b")
	_souffler(0.0)
	await get_tree().create_timer(0.6).timeout
	_capture("sansvent_a")
	await get_tree().create_timer(0.9).timeout
	_capture("sansvent_b")
	_souffler(1.0)

	# ── faune : on va la chercher ──────────────────────────────────────────
	# Les hardes vivent où le terrain le permet, pas devant la caméra. Sans
	# aller au-dessus de l'une d'elles, aucune capture ne prouverait qu'elles
	# existent, encore moins qu'elles broutent ou qu'elles fuient.
	if vie != null and not vie.hardes.is_empty():
		var h: Dictionary = vie.hardes[0]
		cible = Vector3(h["ancre"].x, 0.0, h["ancre"].y)
		cible.y = altitude_en(cible.x, cible.z)
		portee = 42.0
		await get_tree().create_timer(1.0).timeout
		_capture("faune_loin")
		# le perso débarque au milieu de la harde : elle doit détaler
		p_pos = cible
		_appliquer_angle()
		await get_tree().create_timer(1.6).timeout
		_capture("faune_fuite")
	portee = 150.0
	libre = false

	await _bench("gorge", depart_gorge)
	await _bench("plateau", depart_plateau)
	# La même vue avec et sans brume, pour distinguer ce qui vient du sol de ce
	# qui vient de l'air — sans A/B au même endroit on corrige la mauvaise chose.
	p_pos = depart_gorge
	p_pos.y = altitude_en(p_pos.x, p_pos.z)
	cible = p_pos
	verrouille = false
	az_i = 5
	_appliquer_angle()
	env.fog_enabled = false
	await get_tree().create_timer(0.5).timeout
	_capture("ab_sans_brume")
	env.fog_enabled = true
	await get_tree().create_timer(0.5).timeout
	_capture("ab_avec_brume")
	env.fog_enabled = false
	get_tree().quit()
