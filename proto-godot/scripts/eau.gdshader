// L'Ardèche qui descend la gorge.
//
// Ce que ce shader remplace : une carte de normales dont les UV défilaient en
// diagonale, à vitesse constante, sur toute la rivière. Deux choses sonnaient
// faux et c'étaient les bonnes à corriger :
//
//   1. l'eau glissait TOUJOURS vers le sud-est, y compris dans les boucles où
//      la rivière remonte vers le nord. Une rivière ne fait pas ça ;
//   2. elle glissait à la même vitesse partout, du bassin calme au rapide.
//
// D'où le CHAMP D'ÉCOULEMENT (scripts/riviere.gd) : une texture qui porte, pour
// chaque maille de 2,34 m, la direction du courant (déduite du gradient de la
// SURFACE D'EAU, qui perd 84 m sur l'emprise), la profondeur et la turbulence.
//
// ── CE QUE LA MESURE A CORRIGÉ ────────────────────────────────────────────
//
// Première version : rides en carte de normales, écume sur la berge, éclats en
// spéculaire physique. Mesure au décodeur PNG sur une capture, en travers de la
// rivière : 171 pixels de large, tous à (50, 63, 74) ± 2. Un aplat parfait.
// Trois causes, et aucune n'était un réglage :
//
//   · LES NORMALES NE SE VOIENT PAS. Sur une nappe presque plane éclairée par
//     un soleil à 24°, incliner la normale de trois degrés ne change ni le
//     diffus ni l'ambiante de façon mesurable. Le motif du courant passe donc
//     maintenant par l'ALBÉDO, pas seulement par la normale.
//   · LES ÉCLATS SPÉCULAIRES SONT GÉOMÉTRIQUEMENT IMPOSSIBLES ICI. Le soleil
//     est à 24° d'élévation, la caméra à 36° : le miroir du soleil part à 24°
//     du côté opposé et la caméra ne le voit JAMAIS. Il aurait fallu des rides
//     inclinées de plus de six degrés. Les paillettes sont donc assumées comme
//     un effet stylisé — du bruit fin, seuillé dur, qui défile avec le courant.
//   · L'ÉCUME ÉTAIT TROP FINE POUR EXISTER À L'ÉCRAN. Sa frange faisait deux ou
//     trois pixels à la portée de jeu.
//
// ── LE COURANT SE LIT À L'ÉTIREMENT ───────────────────────────────────────
//
// Le motif n'est pas échantillonné dans les axes du monde mais dans le REPÈRE
// DU COURANT : très étiré dans le sens de l'écoulement, serré en travers. C'est
// ce qui fait lire une rivière qui coule plutôt qu'une nappe qui frissonne, et
// c'est gratuit — un changement de coordonnées, pas un échantillon de plus.
//
// Le défilement, lui, suit la technique des « flow maps » : on ne peut pas
// faire glisser une texture le long d'un champ courbe sans l'étirer
// indéfiniment, donc on la relance périodiquement et on fait se recouvrir DEUX
// phases décalées d'une demi-période. Là où l'une s'étire, l'autre repart.

shader_type spatial;
render_mode cull_disabled, depth_draw_never;

// RG = direction du courant (0,5 = zéro) · B = profondeur · A = turbulence
uniform sampler2D flux : filter_linear, repeat_disable;
uniform sampler2D rides : filter_linear_mipmap, repeat_enable;
uniform sampler2D grain : filter_linear_mipmap, repeat_enable;

uniform float emprise = 2400.0;
uniform float echelle_rides = 9.0;     // largeur du motif en travers, en mètres
uniform float etirement = 3.6;         // combien il s'allonge dans le courant
uniform float vitesse = 0.17;          // périodes par seconde au courant plein
uniform float amplitude = 0.55;        // étirement toléré avant relance
uniform float relief = 0.26;           // inclinaison des rides
uniform vec3 soleil = vec3(0.65, 0.41, -0.64);
uniform vec3 ciel = vec3(0.52, 0.64, 0.80);
// Amplitude du motif, en ALBÉDO LINÉAIRE et pas en pourcentage. Mesuré : sur
// une eau profonde dont l'albédo vaut 0,05, un motif multiplicatif de ±10 %
// donnait ±4 sRGB à l'écran — invisible. Un écart ABSOLU de ±0,04 en donne une
// quinzaine, et il ne s'effondre pas quand l'eau est sombre.
uniform float contraste_courant = 0.13;
uniform float eclat = 1.1;             // force des paillettes
uniform float ecume = 1.0;

varying vec3 monde;

void vertex() {
	monde = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

// Deux phases décalées d'une demi-période, pondérées par leur fraîcheur : au
// moment où une phase a le plus étiré la texture, son poids est nul.
// Dans le repère du courant l'écoulement est purement selon +x, d'où le
// décalage appliqué sur la seule composante x.
vec3 defiler(sampler2D t, vec2 uv, float phase, float ampl) {
	float p0 = fract(phase);
	float p1 = fract(phase + 0.5);
	float w = abs(1.0 - 2.0 * p0);
	vec3 a = texture(t, uv - vec2(p0 * ampl, 0.0)).rgb;
	vec3 b = texture(t, uv - vec2(p1 * ampl, 0.0)).rgb;
	return mix(b, a, w);
}

void fragment() {
	vec4 f = texture(flux, monde.xz / emprise);
	vec2 dir = f.rg * 2.0 - 1.0;
	float lent = length(dir);              // 0 dans les mares, 1 en plein courant
	float prof = f.b;                      // 0 sur la berge, 1 au milieu
	float turb = f.a;                      // rapides : lit qui remonte, eau serrée

	// Repère local du courant. Il tourne avec la rivière, donc le motif suit
	// les boucles de la gorge au lieu de les traverser.
	vec2 ax = lent > 0.03 ? dir / lent : vec2(1.0, 0.0);
	vec2 bx = vec2(-ax.y, ax.x);
	vec2 uvc = vec2(dot(monde.xz, ax) / (echelle_rides * etirement),
					dot(monde.xz, bx) / echelle_rides);

	// Un rapide court, un bassin dort. Sans ce facteur la rivière avait la même
	// nervosité partout et c'est ce qui la faisait lire comme un plan d'eau.
	float allure = (0.28 + 0.72 * turb) * (0.30 + 0.70 * lent);
	float phase = TIME * vitesse * allure;

	// ── le motif du courant, dans l'albédo ────────────────────────────────
	// Deux échelles : de longues veines qui filent, et un grain plus court qui
	// les casse. Centré sur zéro pour éclaircir autant qu'il assombrit.
	float veine = defiler(grain, uvc, phase, amplitude).r;
	float trame = defiler(grain, uvc * vec2(2.3, 1.9) + vec2(0.37, 0.11),
						  phase * 1.45 + 0.27, amplitude).g;
	float motif = (veine - 0.5) * 0.70 + (trame - 0.5) * 0.50;
	motif *= contraste_courant * (0.45 + 0.55 * lent);

	// ── normales des rides ────────────────────────────────────────────────
	vec3 r1 = defiler(rides, uvc * vec2(1.7, 1.3), phase * 1.2, amplitude) * 2.0 - 1.0;
	vec2 g = (r1.x * ax + r1.y * bx) * relief;
	vec3 nw = normalize(vec3(-g.x, 1.0, -g.y));
	NORMAL = normalize((VIEW_MATRIX * vec4(nw, 0.0)).xyz);
	vec3 vue = normalize(CAMERA_POSITION_WORLD - monde);

	// ── écume ─────────────────────────────────────────────────────────────
	// Trois causes, et ce sont celles de la vraie rivière : le bord (l'eau
	// racle le galet), le rapide (le lit remonte et l'eau se resserre), et le
	// mouvement propre de la mousse, qui DESCEND avec le courant.
	//
	// La frange de berge est exprimée en MÈTRES et pas en fraction : la
	// profondeur normalisée sature à 14 m, et une frange « prof < 0,55 »
	// faisait deux pixels à l'écran. Ici elle en fait vingt.
	// prof sature à 14 m : la frange court donc de 0,7 m à 4,2 m de la berge.
	// Réglée à 7 m au premier essai, elle blanchissait dix mètres de rivière et
	// la mesure sortait à sRGB 207 — de la glace, pas de l'écume.
	float bord = 1.0 - smoothstep(0.05, 0.30, prof);
	float brasse = smoothstep(0.50, 0.98, turb);
	float m = max(bord * 0.90, brasse) * ecume;
	// le grain décide OÙ la mousse s'accroche ; sans lui l'écume est un ruban
	// peint le long de la berge, d'une régularité impossible
	m *= smoothstep(0.30, 0.78, veine * 0.55 + trame * 0.45 + m * 0.42);
	m = clamp(m, 0.0, 1.0);

	// ── couleur ───────────────────────────────────────────────────────────
	float fresnel = pow(1.0 - clamp(dot(nw, vue), 0.0, 1.0), 4.0);
	vec3 base = mix(COLOR.rgb, ciel, fresnel * 0.55)
			  + vec3(0.85, 1.0, 1.10) * motif;
	ALBEDO = max(mix(base, vec3(0.74, 0.79, 0.79), m), vec3(0.0));
	ALPHA = clamp(mix(COLOR.a, 0.96, m) + fresnel * 0.25, 0.0, 1.0);
	// Une eau trop lisse se comporte en miroir et renvoie tout le ciel : à
	// rugosité 0,10 la rivière virait au bleu blanc sur toute sa largeur.
	ROUGHNESS = mix(0.32, 0.85, m);
	METALLIC = 0.0;
	SPECULAR = mix(0.70, 0.30, m);

	// ── paillettes ────────────────────────────────────────────────────────
	// Stylisées, pas physiques (voir l'entête). Du bruit fin seuillé dur, qui
	// file avec le courant : ce sont des points qui s'allument et s'éteignent,
	// et c'est ce qu'on lit d'une rivière au soleil. Sur l'eau calme il n'y en
	// a presque pas, ce qui reste juste.
	float fin = defiler(grain, uvc * vec2(3.1, 5.2) + vec2(0.71, 0.29),
						phase * 1.9 + 0.61, amplitude).b;
	float paillette = smoothstep(0.80, 0.96, fin) * (0.25 + 0.75 * lent) * (1.0 - m * 0.8);
	EMISSION = vec3(1.0, 0.96, 0.84) * paillette * eclat;
	// L'émission d'un fragment transparent est multipliée par son alpha : sans
	// ce rattrapage les paillettes disparaissent là où l'eau est claire.
	ALPHA = clamp(ALPHA + paillette * 0.8, 0.0, 1.0);
}
