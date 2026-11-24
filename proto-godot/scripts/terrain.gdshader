// Terrain de Balazuc : quatre matières tuilées, mélangées par une carte de
// poids, multipliées par un éclairage cuit hors ligne.
//
// Pourquoi ce chemin plutôt qu'une grande texture cuite : une image de 8192²
// sur 2,4 km donne 30 cm par pixel — à la portée de jeu, c'est encore un aplat.
// Ici la matière est tuilée, donc le détail vaut ~2 cm par pixel, et la carte
// de mélange (1024², une valeur tous les 2,3 m) ne porte QUE la répartition.
// Détail fin et macro-structure sont deux problèmes séparés, à deux résolutions.
//
// L'éclairage n'est PAS calculé ici : ombres portées et part de ciel visible
// sont cuites par outils/convertir.py. Le shader ne rajoute que le micro-relief
// des cartes de normales — la différence entre la normale du terrain et celle
// de la matière. Sans cette soustraction, on éclairerait deux fois.

shader_type spatial;
render_mode cull_disabled, unshaded;

uniform sampler2D melange : filter_linear, repeat_disable;
uniform sampler2D lumiere : filter_linear, repeat_disable;

uniform sampler2D falaise_col : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D garrigue_col : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D sousbois_col : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D berge_col : source_color, filter_linear_mipmap, repeat_enable;

uniform sampler2D falaise_nrm : filter_linear_mipmap, repeat_enable;
uniform sampler2D garrigue_nrm : filter_linear_mipmap, repeat_enable;
uniform sampler2D sousbois_nrm : filter_linear_mipmap, repeat_enable;
uniform sampler2D berge_nrm : filter_linear_mipmap, repeat_enable;

uniform float emprise = 2400.0;
// mètres couverts par une tuile. Grand exprès : le motif se répète tous les
// N mètres, et à 6 px/m une tuile de 8 m se verrait battre comme un damier.
uniform vec4 tuiles = vec4(34.0, 26.0, 22.0, 16.0);
uniform vec3 soleil = vec3(0.65, 0.41, -0.64);
uniform float echelle_lum = 1.6;
uniform float force_relief = 1.1;

// Les textures CC0 sont photographiées à plat, chacune avec sa propre
// exposition : brutes, le calcaire fait champ de neige à côté d'une garrigue
// qui fait labour. Ces teintes les ramènent dans une seule lumière — c'est le
// travail d'étalonnage, et il se fait ici, pas dans les fichiers sources.
uniform vec3 teinte_falaise = vec3(0.80, 0.77, 0.70);
uniform vec3 teinte_garrigue = vec3(0.96, 1.00, 0.74);
uniform vec3 teinte_sousbois = vec3(0.82, 0.86, 0.62);
// La berge a été étalonnée à la mesure, et c'est elle qui tenait tout le
// paysage en otage. Gravel023 est décrite à la source comme « bright, light,
// white pebbles » : à teinte 0,90 elle sortait à sRGB 191 quand le sous-bois
// est à 95, un rapport de deux, et elle couvre 10,8 % de l'emprise. Résultat :
// 27 % de l'image en nappe blanche, qu'on lisait comme de la neige. Un galet de
// rivière sec au soleil n'est pas plus clair qu'un calcaire — et surtout, il ne
// doit pas l'être PLUS que la falaise, qui est le sujet du paysage.
uniform vec3 teinte_berge = vec3(0.47, 0.49, 0.46);
uniform float saturation = 0.88;
uniform float exposition = 2.10;
// Contraste appliqué en linéaire : les textures CC0 sont plates par
// construction (éclairage neutre au tournage), et la mesure a montré toute la
// scène coincée entre sRGB 43 et 115. Sans ça, une journée d'été en Ardèche
// ressemble à un jour de brouillard.
uniform float contraste = 1.28;
// Épaule de compression : sans elle, une falaise calcaire en plein soleil
// sature à blanc et perd toute sa matière — c'est ce qu'on voyait au premier
// essai. Ici les hautes lumières se tassent au lieu d'être coupées.
uniform float epaule = 0.22;

varying vec3 monde;
varying vec3 normale_monde;

void vertex() {
	monde = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	normale_monde = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

// Projection triplanaire : sur une paroi verticale, une texture projetée par
// le haut s'étire en traînées. On projette donc selon les trois axes et on
// pondère par la normale. Réservé à la falaise — c'est la seule matière qui
// tienne sur du vertical, et trois échantillons coûtent trois fois plus cher.
vec3 triplan(sampler2D t, vec3 p, vec3 nn, float ech) {
	vec3 b = abs(nn);
	b = b * b * b * b;
	b /= (b.x + b.y + b.z);
	return texture(t, p.zy / ech).rgb * b.x
		 + texture(t, p.xz / ech).rgb * b.y
		 + texture(t, p.xy / ech).rgb * b.z;
}

void fragment() {
	vec2 uvm = monde.xz / emprise;
	vec4 w = texture(melange, uvm);
	w /= max(w.r + w.g + w.b + w.a, 0.001);

	vec3 col = triplan(falaise_col, monde, normale_monde, tuiles.x) * teinte_falaise * w.r
			 + texture(garrigue_col, monde.xz / tuiles.y).rgb * teinte_garrigue * w.g
			 + texture(sousbois_col, monde.xz / tuiles.z).rgb * teinte_sousbois * w.b
			 + texture(berge_col, monde.xz / tuiles.w).rgb * teinte_berge * w.a;
	col = mix(vec3(dot(col, vec3(0.299, 0.587, 0.114))), col, saturation);

	vec3 dn = (texture(falaise_nrm, monde.xz / tuiles.x).rgb * 2.0 - 1.0) * w.r
			+ (texture(garrigue_nrm, monde.xz / tuiles.y).rgb * 2.0 - 1.0) * w.g
			+ (texture(sousbois_nrm, monde.xz / tuiles.z).rgb * 2.0 - 1.0) * w.b
			+ (texture(berge_nrm, monde.xz / tuiles.w).rgb * 2.0 - 1.0) * w.a;

	// micro-relief SEUL : on ne garde que l'écart à l'éclairage déjà cuit
	vec3 nn = normalize(normale_monde + vec3(dn.x, 0.0, -dn.y) * force_relief);
	float nd0 = max(dot(normale_monde, soleil), 0.0);
	float nd1 = max(dot(nn, soleil), 0.0);
	float micro = clamp(1.0 + (nd1 - nd0) * 0.8, 0.75, 1.25);

	vec3 lum = texture(lumiere, uvm).rgb * echelle_lum;
	vec3 sortie = pow(max(col * lum * micro, vec3(0.0)), vec3(contraste)) * exposition;
	ALBEDO = sortie / (1.0 + sortie * epaule);
}
