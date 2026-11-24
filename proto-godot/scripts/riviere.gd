# Le champ d'écoulement de l'Ardèche.
#
# La question à laquelle ce fichier répond est : DANS QUEL SENS coule l'eau, en
# chaque point de la rivière ? Le proto n'avait pas de réponse — il faisait
# défiler une texture en diagonale, partout pareil. Or la gorge fait des boucles :
# sur la moitié du parcours, « en diagonale » c'est à contre-courant.
#
# La réponse est dans les données, et elle était déjà là : convertir.py calcule
# une altitude de surface d'eau PAR MAILLE, et cette surface perd 84 m entre
# l'amont et l'aval de l'emprise. L'eau descend la pente de sa propre surface —
# c'est la définition d'un écoulement. Le gradient de `eau.bin` donne donc la
# direction du courant, gratuitement.
#
# Trois précautions, chacune payée par un essai raté :
#
#   · LISSER la surface avant d'en prendre le gradient. Brute, elle est en
#     marches d'escalier (le MNT est quantifié) et le gradient part dans tous
#     les sens d'une maille à l'autre.
#   · LISSER ENSUITE le champ de directions lui-même. Une rivière de 40 m de
#     large doit couler d'un seul tenant ; sans ce deuxième lissage les deux
#     rives partent en sens contraire là où la surface est plate.
#   · NE PAS NORMALISER là où la pente est nulle. Une longueur de vecteur
#     inférieure à 1 dit au shader « ici, ça dort » — c'est ce qui distingue un
#     bassin d'un rapide, et on perdrait l'information en normalisant tout.

class_name Riviere
extends RefCounted

# Au-delà de cette pente de surface, on considère le courant à plein régime.
# Mesuré sur les données : pente médiane 0,63 %, neuvième décile 3,7 %.
const PENTE_PLEINE := 0.020
# Largeur au-delà de laquelle on est « au milieu », en mètres.
const PROFOND_M := 14.0

var n: int
var pas: float
var dirx := PackedFloat32Array()
var dirz := PackedFloat32Array()
var prof := PackedFloat32Array()
var turb := PackedFloat32Array()
var texture: ImageTexture
var bassins := PackedInt32Array()      # mailles assez larges pour un poisson


func calculer(nn: int, ppas: float, eau: PackedFloat32Array,
		rive: PackedFloat32Array) -> void:
	n = nn
	pas = ppas
	var t0 := Time.get_ticks_msec()
	var total := n * n

	# On ne travaille QUE sur les mailles d'eau : 5 % de la carte. Tout le reste
	# du fichier serait du temps perdu à lisser du vide.
	var mailles := PackedInt32Array()
	for k in range(total):
		if not is_nan(eau[k]):
			mailles.append(k)

	# Les décalages de voisinage sont sortis des boucles : un littéral de
	# tableau à l'intérieur, c'est une allocation par maille et par passe —
	# 260 000 allocations pour rien sur le seul lissage des directions.
	var croix := [-1, 1, -n, n]
	var carre := [-1, 1, -n, n, -n - 1, -n + 1, n - 1, n + 1]

	# ── 1. lisser la surface d'eau ────────────────────────────────────────
	var z := PackedFloat32Array()
	z.resize(total)
	for k in mailles:
		z[k] = eau[k]
	var tampon := z.duplicate()
	for _passe in range(3):
		for k in mailles:
			var s := z[k]
			var c := 1.0
			for d in croix:
				var v: int = k + d
				if v >= 0 and v < total and not is_nan(eau[v]):
					s += z[v]
					c += 1.0
			tampon[k] = s / c
		for k in mailles:
			z[k] = tampon[k]

	# ── 2. gradient : l'eau descend ───────────────────────────────────────
	dirx.resize(total)
	dirz.resize(total)
	prof.resize(total)
	turb.resize(total)
	var pente := PackedFloat32Array()
	pente.resize(total)
	for k in mailles:
		var i := k % n
		var j := k / n
		var gx := _derivee(z, eau, k, 1, i > 0, i < n - 1)
		var gz := _derivee(z, eau, k, n, j > 0, j < n - 1)
		dirx[k] = -gx
		dirz[k] = -gz
		pente[k] = sqrt(gx * gx + gz * gz)

	# ── 3. lisser le champ de directions ──────────────────────────────────
	# Cinq passes : à 2,34 m la maille, ça porte le lissage à une dizaine de
	# mètres, soit l'ordre de grandeur de la largeur de la rivière.
	var tx := dirx.duplicate()
	var tz := dirz.duplicate()
	for _passe in range(5):
		for k in mailles:
			var sx := dirx[k] * 2.0
			var sz := dirz[k] * 2.0
			var c := 2.0
			for d in carre:
				var v: int = k + d
				if v >= 0 and v < total and not is_nan(eau[v]):
					sx += dirx[v]
					sz += dirz[v]
					c += 1.0
			tx[k] = sx / c
			tz[k] = sz / c
		for k in mailles:
			dirx[k] = tx[k]
			dirz[k] = tz[k]

	# ── 4. normaliser, mais garder la mollesse des bassins ────────────────
	var lisse_p := _lisser_scalaire(pente, eau, mailles, 3, croix)
	for k in mailles:
		var l := sqrt(dirx[k] * dirx[k] + dirz[k] * dirz[k])
		# La force du courant vient de la pente LISSÉE, pas de la longueur du
		# vecteur : après cinq passes de moyenne, deux directions opposées se
		# sont annulées et la longueur ne veut plus rien dire.
		var force: float = clampf(lisse_p[k] / PENTE_PLEINE, 0.0, 1.0)
		force = sqrt(force)                     # la vitesse suit la racine de la pente
		if l > 1e-7:
			dirx[k] = dirx[k] / l * force
			dirz[k] = dirz[k] / l * force
		else:
			dirx[k] = 0.0
			dirz[k] = 0.0
		prof[k] = clampf(rive[k] / PROFOND_M, 0.0, 1.0)
		# Un rapide, c'est de l'eau qui accélère ET qui se resserre. Les deux
		# vont ensemble sur le terrain, et les additionner évite de marquer en
		# écume un torrent large et calme.
		turb[k] = clampf(force * (0.55 + 0.75 * (1.0 - prof[k])), 0.0, 1.0)
		if rive[k] > 8.0:
			bassins.append(k)
	turb = _lisser_scalaire(turb, eau, mailles, 2, croix)

	texture = _texture(mailles, total, croix)
	print("rivière : %d mailles d'eau, %d bassins pour les poissons (%d ms)" % [
		mailles.size(), bassins.size(), Time.get_ticks_msec() - t0])


# Dérivée centrée quand les deux voisins sont dans l'eau, décentrée sinon. Sans
# ce soin, la berge — où un seul côté existe — sortait un gradient énorme et
# fabriquait une couronne de faux rapides tout le long de la rivière.
func _derivee(z: PackedFloat32Array, eau: PackedFloat32Array, k: int, d: int,
		peut_moins: bool, peut_plus: bool) -> float:
	var a := k - d
	var b := k + d
	var oa: bool = peut_moins and not is_nan(eau[a])
	var ob: bool = peut_plus and not is_nan(eau[b])
	if oa and ob:
		return (z[b] - z[a]) / (2.0 * pas)
	if ob:
		return (z[b] - z[k]) / pas
	if oa:
		return (z[k] - z[a]) / pas
	return 0.0


func _lisser_scalaire(src: PackedFloat32Array, eau: PackedFloat32Array,
		mailles: PackedInt32Array, passes: int, croix: Array) -> PackedFloat32Array:
	var total := n * n
	var a := src.duplicate()
	var b := src.duplicate()
	for _p in range(passes):
		for k in mailles:
			var s := a[k]
			var c := 1.0
			for d in croix:
				var v: int = k + d
				if v >= 0 and v < total and not is_nan(eau[v]):
					s += a[v]
					c += 1.0
			b[k] = s / c
		var t := a
		a = b
		b = t
	return a


# RG = direction (0,5 = immobile) · B = profondeur · A = turbulence.
#
# La texture déborde de deux mailles sur la terre ferme : le maillage d'eau
# s'arrête pile au bord du masque, et sans ce débord le filtrage bilinéaire va
# chercher la valeur neutre hors rivière — une frange morte et immobile tout le
# long des berges, exactement là où l'œil regarde.
#
# On ne balaie PAS le million de mailles : on part du bord de l'eau et on
# n'avance que sur le front. Le balayage complet coûtait quelques secondes de
# chargement pour un résultat identique.
func _texture(mailles: PackedInt32Array, total: int, croix: Array) -> ImageTexture:
	var rempli := PackedByteArray()
	rempli.resize(total)
	for k in mailles:
		rempli[k] = 1
	var dx := dirx.duplicate()
	var dz := dirz.duplicate()
	var pf := prof.duplicate()
	var tb := turb.duplicate()
	var front := mailles.duplicate()
	var deborde := PackedInt32Array()
	for _passe in range(2):
		var candidats := {}
		for k in front:
			for d in croix:
				var v: int = k + d
				if v >= 0 and v < total and rempli[v] == 0:
					candidats[v] = true
		var suivant := PackedInt32Array()
		for v in candidats:
			var sx := 0.0
			var sz := 0.0
			var sp := 0.0
			var st := 0.0
			var c := 0.0
			for d in croix:
				var w: int = v + d
				if w >= 0 and w < total and rempli[w] != 0:
					sx += dx[w]; sz += dz[w]; sp += pf[w]; st += tb[w]; c += 1.0
			if c > 0.0:
				dx[v] = sx / c; dz[v] = sz / c; pf[v] = sp / c; tb[v] = st / c
				suivant.append(v)
		for v in suivant:
			rempli[v] = 1
			deborde.append(v)
		front = suivant

	# Fond neutre : direction nulle, aucune profondeur, aucune turbulence. On ne
	# peint ensuite que les ~60 000 mailles qui portent quelque chose, au lieu
	# d'écrire les quatre millions d'octets de la carte entière.
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	img.fill(Color8(128, 128, 0, 0))
	for lot in [mailles, deborde]:
		for k in lot:
			img.set_pixel(k % n, k / n, Color(
				clampf(dx[k] * 0.5 + 0.5, 0.0, 1.0),
				clampf(dz[k] * 0.5 + 0.5, 0.0, 1.0),
				clampf(pf[k], 0.0, 1.0),
				clampf(tb[k], 0.0, 1.0)))
	return ImageTexture.create_from_image(img)


# ── textures procédurales ────────────────────────────────────────────────
#
# Fabriquées ici et pas chargées : elles doivent être RACCORDABLES (le shader
# les répète tous les 7 m sur 2,4 km de rivière), et une texture raccordable se
# calcule en trois lignes alors qu'elle se trouve difficilement.

# Carte de normales des rides : somme de trois ondes de directions et de
# périodes premières entre elles, dérivée en différences finies cycliques.
static func rides(T := 128) -> ImageTexture:
	var h := PackedFloat32Array()
	h.resize(T * T)
	for j in range(T):
		for i in range(T):
			var a := TAU * (i * 3.0 + j * 1.0) / T
			var b := TAU * (i * -2.0 + j * 4.0) / T
			var c := TAU * (i * 5.0 + j * -3.0) / T
			var d := TAU * (i * 7.0 + j * 6.0) / T
			h[j * T + i] = sin(a) * 0.46 + sin(b) * 0.30 + sin(c) * 0.15 + sin(d) * 0.09
	var img := Image.create(T, T, false, Image.FORMAT_RGB8)
	for j in range(T):
		for i in range(T):
			var gx := h[j * T + (i + 1) % T] - h[j * T + (i + T - 1) % T]
			var gy := h[((j + 1) % T) * T + i] - h[((j + T - 1) % T) * T + i]
			var nv := Vector3(-gx, -gy, 1.4).normalized()
			img.set_pixel(i, j, Color(nv.x * 0.5 + 0.5, nv.y * 0.5 + 0.5, nv.z * 0.5 + 0.5))
	img.generate_mipmaps()
	return ImageTexture.create_from_image(img)


# Grain d'écume : du bruit de valeur raccordable, à trois octaves. Les taches
# doivent être GROSSES et molles — un bruit fin ferait du grésillement blanc,
# pas de la mousse.
static func grain(T := 128) -> ImageTexture:
	var img := Image.create(T, T, false, Image.FORMAT_RGB8)
	var couches := []
	for octave in [4, 9, 19]:
		couches.append(_valeur(T, octave, 1000 + octave))
	for j in range(T):
		for i in range(T):
			var k := j * T + i
			var r: float = couches[0][k] * 0.55 + couches[1][k] * 0.30 + couches[2][k] * 0.15
			var g: float = couches[1][k] * 0.60 + couches[2][k] * 0.40
			img.set_pixel(i, j, Color(r, g, couches[2][k]))
	img.generate_mipmaps()
	return ImageTexture.create_from_image(img)


static func _valeur(T: int, cellules: int, graine: int) -> PackedFloat32Array:
	var r := RandomNumberGenerator.new()
	r.seed = graine
	var g := PackedFloat32Array()
	g.resize(cellules * cellules)
	for k in range(cellules * cellules):
		g[k] = r.randf()
	var out := PackedFloat32Array()
	out.resize(T * T)
	for j in range(T):
		for i in range(T):
			var fx: float = float(i) / float(T) * float(cellules)
			var fz: float = float(j) / float(T) * float(cellules)
			var i0 := int(fx) % cellules
			var j0 := int(fz) % cellules
			var i1 := (i0 + 1) % cellules
			var j1 := (j0 + 1) % cellules
			var u: float = fx - floor(fx)
			var v: float = fz - floor(fz)
			u = u * u * (3.0 - 2.0 * u)
			v = v * v * (3.0 - 2.0 * v)
			out[j * T + i] = lerpf(lerpf(g[j0 * cellules + i0], g[j0 * cellules + i1], u),
								   lerpf(g[j1 * cellules + i0], g[j1 * cellules + i1], u), v)
	return out
