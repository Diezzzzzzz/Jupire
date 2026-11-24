// Faune : le même billboard que la végétation, mais l'angle change À CHAQUE
// IMAGE.
//
// C'est la seule différence, et elle commande tout le reste. Un arbre garde son
// orientation pour toujours : on peut donc ranger les arbres en un MultiMesh
// par (angle × variante) et changer de matériau quand la caméra pivote. Un
// chevreuil qui marche, non — il change de cap en permanence, et le trier dans
// 24 MultiMesh à chaque image serait absurde.
//
// Donc : les 8 angles × 3 poses tiennent dans UN atlas, et chaque instance dit
// quelle case elle veut par INSTANCE_CUSTOM. Une harde entière = un MultiMesh,
// un matériau, un appel de dessin, quel que soit le cap de chacun.
//
//   INSTANCE_CUSTOM.x = colonne (angle relatif), NORMALISÉE : indice / 8
//   INSTANCE_CUSTOM.y = ligne   (pose),          NORMALISÉE : indice / 3
//   INSTANCE_CUSTOM.z = opacité (0 = instance rangée hors champ)
//
// Les indices passent normalisés pour ne rien supposer du format de stockage
// des données d'instance : que Godot les garde en flottant ou les quantifie sur
// 8 bits, un multiple de 1/8 retombe sur le bon entier après arrondi.

shader_type spatial;
render_mode cull_disabled, unshaded, shadows_disabled;

uniform sampler2D atlas : source_color, filter_linear, repeat_disable;
uniform vec2 grille = vec2(8.0, 3.0);
uniform float seuil = 0.5;

varying vec2 uva;
varying vec3 nuance;
varying float opacite;

void vertex() {
	vec2 case_ = floor(INSTANCE_CUSTOM.xy * grille + 0.5);
	// On rentre d'un demi-texel dans la case : sans ça le filtrage linéaire va
	// chercher la case voisine sur le bord et un chevreuil hérite de l'aile du
	// vautour d'à côté.
	vec2 marge = 0.5 / (vec2(textureSize(atlas, 0)) / grille);
	uva = (case_ + mix(marge, 1.0 - marge, UV)) / grille;
	opacite = INSTANCE_CUSTOM.z;

	// BILLBOARD_FIXED_Y + keep_scale, tels que Godot les génère.
	mat4 mv = VIEW_MATRIX * mat4(
		vec4(normalize(cross(vec3(0.0, 1.0, 0.0), INV_VIEW_MATRIX[2].xyz)), 0.0),
		vec4(0.0, 1.0, 0.0, 0.0),
		vec4(normalize(cross(INV_VIEW_MATRIX[0].xyz, vec3(0.0, 1.0, 0.0))), 0.0),
		MODEL_MATRIX[3]);
	mv = mv * mat4(
		vec4(length(MODEL_MATRIX[0].xyz), 0.0, 0.0, 0.0),
		vec4(0.0, length(MODEL_MATRIX[1].xyz), 0.0, 0.0),
		vec4(0.0, 0.0, length(MODEL_MATRIX[2].xyz), 0.0),
		vec4(0.0, 0.0, 0.0, 1.0));
	MODELVIEW_MATRIX = mv;
	MODELVIEW_NORMAL_MATRIX = mat3(mv);

	nuance = COLOR.rgb;
}

void fragment() {
	vec4 t = texture(atlas, uva);
	// Le seuil monte quand l'instance s'efface : une bête qu'on range hors
	// champ disparaît par les bords au lieu de clignoter d'un coup.
	if (t.a * opacite < seuil) {
		discard;
	}
	ALBEDO = t.rgb * nuance;
	ALPHA = 1.0;
}
