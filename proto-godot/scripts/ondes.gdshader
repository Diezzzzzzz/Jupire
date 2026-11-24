// Le rond dans l'eau.
//
// Deux anneaux concentriques sur un quad posé à plat : l'onde de tête, nette,
// et son sillage, plus mou et en retard. C'est ce décalage qui fait lire un
// rond qui S'ÉLARGIT plutôt qu'un cercle qui grossit.
//
// Le rayon et l'effacement viennent du CPU (scripts/vie.gd), pas d'un temps de
// naissance rangé dans les données d'instance : il n'y a jamais plus d'une
// vingtaine de ronds vivants, et une vingtaine de transformations par image ne
// se mesure pas, alors qu'un temps absolu quantifié sur 8 bits, si.

shader_type spatial;
render_mode cull_disabled, unshaded, shadows_disabled, depth_draw_never;

uniform float largeur = 0.16;     // épaisseur de l'anneau, en fraction du rayon
uniform vec3 teinte = vec3(0.93, 0.96, 0.95);

void fragment() {
	float r = length(UV - 0.5) * 2.0;
	float a = smoothstep(1.0, 1.0 - largeur, r) * smoothstep(1.0 - largeur * 2.0, 1.0 - largeur, r);
	float b = smoothstep(0.66, 0.50, r) * smoothstep(0.30, 0.50, r) * 0.45;
	ALBEDO = teinte;
	ALPHA = (a + b) * COLOR.a;
}
