# L'usine à sprites, en miniature.
#
# Elle fait à l'intérieur de Godot ce que Blender fera plus tard en batch :
# elle photographie des volumes 3D sous N angles, en projection ORTHOGRAPHIQUE
# et à l'inclinaison exacte de la caméra de jeu, et rend des textures.
#
# Trois choses s'y jouent, et ce sont elles qu'il faut voir à l'écran :
#
#   1. LE CONTRAT D'INCLINAISON. Le sprite n'est juste que si l'usine et la
#      caméra de jeu partagent le même angle. Change l'un sans l'autre et les
#      arbres ne posent plus sur le sol.
#   2. LE COÛT DES ANGLES. Passer de 1 à 8 angles, c'est la même boucle qui
#      tourne 8 fois : du temps de calcul, pas du travail d'artiste.
#   3. LE SOLEIL CUIT DANS LE MONDE. Si on fixe le soleil à la caméra au lieu
#      du monde, le côté éclairé suit la caméra quand elle pivote — l'éclairage
#      se met à mentir. Touche L dans le proto pour voir les deux.
#
# Géométrie, pour mémoire : en ortho inclinée de θ, un segment vertical de
# longueur H se projette sur H·cos(θ). Pour qu'une image remplisse exactement
# un panneau vertical de H de haut et H de large, il faut donc une caméra de
# taille H·cos(θ) et une image d'aspect 1/cos(θ).

class_name Usine
extends Node

const ANGLES := 8                       # pas de 45°, la grille d'AoE2
const HAUT_PX := 160                    # hauteur de rendu ; large marge de zoom

# Le soleil : mêmes valeurs que le proto browser (SOL_AZ 2.35, SOL_EL 0.42).
const SOL_AZ := 2.35
const SOL_EL := 0.42

var _vp: SubViewport
var _cam: Camera3D
var _porte: Node3D
var _lum: DirectionalLight3D


func _pret(tilt: float) -> void:
	_vp = SubViewport.new()
	_vp.own_world_3d = true
	_vp.transparent_bg = true
	_vp.msaa_3d = Viewport.MSAA_4X
	_vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
	add_child(_vp)

	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_CLEAR_COLOR
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	# Ciel d'Ardèche en plein jour : l'ambiante empêche les faces à l'ombre
	# d'être du noir mort. C'est ce qui donne l'air « peinture » de SC4.
	e.ambient_light_color = Color(0.62, 0.68, 0.78)
	e.ambient_light_energy = 0.55
	env.environment = e
	_vp.add_child(env)

	_lum = DirectionalLight3D.new()
	_lum.light_energy = 1.25
	_lum.light_color = Color(1.0, 0.96, 0.86)
	_vp.add_child(_lum)

	_cam = Camera3D.new()
	_cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	_cam.near = 0.05
	_cam.far = 400.0
	_vp.add_child(_cam)

	_porte = Node3D.new()          # le porte-objet : on y accroche le volume
	_vp.add_child(_porte)


# Fabrique toutes les planches. Retourne { nom: [8 textures] }.
#
# soleil_monde = true  → le soleil reste fixe dans le monde (le bon)
# soleil_monde = false → le soleil suit la caméra (le piège, touche L)
func fabriquer(tilt: float, soleil_monde: bool) -> Dictionary:
	if _vp == null:
		_pret(tilt)

	var aspect := 1.0 / cos(tilt)
	_vp.size = Vector2i(int(round(HAUT_PX * aspect)), HAUT_PX)

	var planches := {}
	for nom in Volumes.CATALOGUE:
		var haut: float = Volumes.CATALOGUE[nom]
		var formes := []
		for v in range(Volumes.VARIANTES):
			var vol: Node3D = Volumes.batir(nom, v)
			_porte.add_child(vol)
			var jeu: Array[Texture2D] = []
			for a in range(ANGLES):
				var az := TAU * float(a) / float(ANGLES)
				_viser(az, tilt, haut)
				if soleil_monde:
					_soleil(SOL_AZ, SOL_EL)
				else:
					_soleil(SOL_AZ + az, SOL_EL)   # le soleil collé à la caméra
				jeu.append(await _declic())
			_porte.remove_child(vol)
			vol.queue_free()
			formes.append(jeu)
		planches[nom] = formes
	return planches


func _viser(az: float, tilt: float, haut: float) -> void:
	# Taille = H·cos(tilt) : le panneau vertical de H de haut remplit l'image.
	_cam.size = haut * cos(tilt)
	var d := 80.0
	var cible := Vector3(0.0, haut * 0.5, 0.0)
	_cam.position = cible + Vector3(sin(az) * cos(tilt), sin(tilt), cos(az) * cos(tilt)) * d
	_cam.look_at(cible, Vector3.UP)


func _soleil(az: float, el: float) -> void:
	var dir := Vector3(cos(el) * sin(az), sin(el), cos(el) * cos(az))
	_lum.look_at_from_position(dir * 40.0, Vector3.ZERO, Vector3.UP)


func _declic() -> Texture2D:
	_vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	RenderingServer.force_draw(false)
	await RenderingServer.frame_post_draw
	var img := _vp.get_texture().get_image()
	return ImageTexture.create_from_image(img)
