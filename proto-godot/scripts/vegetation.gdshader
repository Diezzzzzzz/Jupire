// Végétation : le billboard d'avant, plus le vent.
//
// Ce shader REMPLACE un StandardMaterial3D en BILLBOARD_FIXED_Y + alpha
// scissor + couleur par instance. Les trois doivent survivre à l'identique,
// sinon on perd la forêt en même temps qu'on gagne le vent :
//
//   · le billboard fixé sur Y est recopié du code que Godot génère lui-même
//     pour BILLBOARD_FIXED_Y + keep_scale — pas une approximation ;
//   · le `discard` sous seuil vaut l'alpha scissor : le sprite s'écrit dans le
//     tampon de profondeur comme un solide, donc 53 000 quads n'ont PAS besoin
//     d'être triés ;
//   · COLOR porte la nuance par instance du MultiMesh.
//
// Le vent, lui, tient en une idée : le pied ne bouge pas, la cime oui. Le
// déplacement est appliqué sur VERTEX.x, c'est-à-dire l'axe HORIZONTAL DU
// PANNEAU — donc l'axe droite-gauche de l'écran après billboard. L'arbre se
// balance dans le plan de l'image, ce qui est exactement ce que fait un sprite
// 2D peint à la main, et ça ne coûte pas un pixel de plus.

shader_type spatial;
render_mode cull_disabled, unshaded, shadows_disabled;

uniform sampler2D planche : source_color, filter_linear_mipmap, repeat_disable;
uniform float seuil = 0.5;

// hauteur du PANNEAU en mètres : sans elle l'amplitude serait en unités de
// quad, et un chêne de 12 m se balancerait autant qu'une touffe de 0,9 m.
uniform float hauteur = 9.0;
// 0 = minéral (rocher, ruine, perso : rien ne bouge), 1 = feuillu, 2 = brin sec
uniform float souplesse = 1.0;
uniform vec2 vent_dir = vec2(0.80, 0.60);
uniform float vent_force = 1.0;
// rayon du tourbillon, en mètres : réservé aux feuilles qui dérivent en l'air.
// À 0 l'objet est planté dans le sol et ne fait que se pencher.
uniform float tourbillon = 0.0;

varying vec3 nuance;

// Bruit d'entier : il ne sert qu'à décaler la PHASE de chaque touffe. Sans lui
// toute la garrigue oscille en même temps et l'œil voit une nappe respirer.
float grain(vec2 p) {
	return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

void vertex() {
	vec3 ancre = MODEL_MATRIX[3].xyz;
	float ph = grain(floor(ancre.xz * 3.0)) * 6.2831853;

	// Front de rafale : une onde lente qui TRAVERSE la gorge. C'est elle qui
	// fait la différence entre « ça vibre » et « il y a du vent » — le vent
	// réel arrive par bouffées, et on doit voir la bouffée passer.
	vec2 vd = normalize(vent_dir);
	float rafale = 0.45 + 0.55 * sin(0.21 * TIME - dot(ancre.xz, vd) * 0.0075);
	rafale = rafale * rafale;                      // les creux sont plus longs

	// Prise au vent : nulle au pied, maximale en cime. L'usine cadre le volume
	// entre y = 0 et y = hauteur, donc le BAS DU QUAD est la ligne de sol, et
	// UV.y vaut 1 en bas pour un QuadMesh.
	float haut = 1.0 - UV.y;
	float prise = haut * haut;

	float osc = sin(1.7 * TIME + ph) * 0.62 + sin(3.9 * TIME + ph * 1.7) * 0.38;
	float d = osc * prise * souplesse * (0.30 + 0.70 * rafale) * vent_force * hauteur * 0.055;
	VERTEX.x += d;
	VERTEX.y -= abs(d) * 0.22;      // une cime qui se penche perd de la hauteur

	if (tourbillon > 0.0) {
		// Feuille en l'air : elle tourne dans une bulle autour de son ancre, et
		// ne s'en éloigne jamais. C'est VOULU — le shader ignore l'altitude du
		// terrain, une feuille qui dérive loin finirait sous la roche.
		float t = TIME * (0.55 + 0.5 * grain(ancre.xz)) + ph;
		ancre.x += sin(t) * tourbillon;
		ancre.z += cos(t * 0.77) * tourbillon;
		ancre.y += (0.55 + 0.45 * sin(t * 1.9)) * tourbillon * 1.4;
	}

	// BILLBOARD_FIXED_Y + keep_scale, tels que Godot les génère.
	mat4 mv = VIEW_MATRIX * mat4(
		vec4(normalize(cross(vec3(0.0, 1.0, 0.0), INV_VIEW_MATRIX[2].xyz)), 0.0),
		vec4(0.0, 1.0, 0.0, 0.0),
		vec4(normalize(cross(INV_VIEW_MATRIX[0].xyz, vec3(0.0, 1.0, 0.0))), 0.0),
		vec4(ancre, 1.0));
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
	vec4 t = texture(planche, UV);
	if (t.a < seuil) {
		discard;
	}
	ALBEDO = t.rgb * nuance;
	ALPHA = 1.0;
}
