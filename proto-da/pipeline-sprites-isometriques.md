# Pipeline sprites isométriques — jeu médiéval

_Noté le 17/11/2026. Référence de DA : Land & Liege (inspiration, pas clone)._

## Principe

Personne ne dessine. Des scripts Python assemblent des bâtiments 3D low-poly dans Blender, les rendent en vue isométrique, puis un second script les convertit en pixel art avec une palette fixe. Un agent IA écrit les fiches de bâtiments, lance les scripts, regarde le résultat et corrige. Mon rôle : choisir et valider.

Durée : ~1 jour pour monter le pipeline, puis ~10-15 min par bâtiment.

## La DA visée (observée sur les captures de Land & Liege)

- **Grain pixel uniforme** : bâtiments, arbres, clôtures et herbe ont la même taille de pixel, sans antialiasing, avec dithering.
- **Palette restreinte et désaturée** : verts olive, ocre du chaume, bruns, gris pierre, un seul bleu sarcelle pour l'eau.
- **Un seul soleil** : toutes les ombres portées partent dans la même direction.
- **Carte monde « maquette »** : vue inclinée, flou tilt-shift, ombres de nuages, brouillard de guerre gris, étiquettes parchemin avec écu et police onciale.
- **Variation temporelle** : quatre saisons par changement de palette, bâtiments construits par étapes.

Leur moteur n'est pas documenté. Ce qui est confirmé : terrain issu de données géographiques réelles, bâtiments isométriques en 4 rotations, plus de 200 bâtiments, pentes multipliées par 1,6 au-dessus de 300 m.

## Outils

| Outil | Rôle |
|---|---|
| Blender en ligne de commande (`blender -b -P script.py`) | Assemblage 3D et rendu, sans interface |
| Python + Pillow + numpy | Conversion pixel art, planches de sprites |
| Aseprite (facultatif) | Retouche manuelle des bâtiments phares |
| PixelLab (serveur MCP officiel) | Arbres, animaux, personnages, tuiles |
| Retro Diffusion (API, MCP) | Idem, styles `isometric` et `isometric_asset` |

Le serveur MCP Blender existe mais n'est pas nécessaire : la ligne de commande suffit et reste reproductible.

## Phase 1 — Fixer la DA (~2 h, décisions humaines)

Ces choix ne changent plus ensuite :

- **Projection** : dimétrique 2:1, caméra orthographique tournée de 60° en X et 45° en Z.
- **Échelle** : par exemple 1 m = 8 pixels, tuile au sol de 64×32 px. Une seule densité de pixel pour tout le jeu.
- **Soleil** : une direction unique (par exemple haut-gauche).
- **Palette** : 32 à 48 couleurs dans `palette.png`, prise sur Lospec ou proposée par l'agent.
- **Planche de référence** : 3 ou 4 bâtiments générés puis validés, qui servent d'étalon.

## Phase 2 — Kit de pièces 3D (~3 h)

Des fonctions Python Blender génèrent des pièces paramétriques : mur (longueur, hauteur, matériau), toit (pente, chaume ou tuile), colombage, porte, cheminée, clôture. Les matériaux sont des couleurs plates ou de petites textures bruitées, déjà dans la palette.

Un bâtiment est une fiche de données :

```json
{ "id": "chaumiere_01", "footprint": [2, 3],
  "walls": "torchis", "roof": { "type": "chaume", "pitch": 50 },
  "stages": ["fondations", "ossature", "complet"] }
```

L'agent écrit des fiches, pas de la géométrie : c'est ce qui permet d'atteindre 200 bâtiments.

## Phase 3 — Rendu isométrique (~1 h)

Le script charge une fiche, assemble les pièces, puis boucle sur 4 rotations (0°, 90°, 180°, 270°) et sur chaque étape de construction.

```python
cam.data.type = 'ORTHO'
cam.rotation_euler = (radians(60), 0, radians(45))
scene.render.film_transparent = True   # fond transparent
scene.render.filter_size = 0.01        # pas d'antialiasing
```

- Rendre directement à la résolution finale, jamais une grande image réduite ensuite.
- Rendre l'ombre portée dans une image séparée (plan au sol en « shadow catcher »), affichée en semi-transparence dans le jeu.

## Phase 4 — Conversion pixel art (~2 h)

1. Alpha binaire : chaque pixel est opaque ou transparent.
2. Réduction à la palette fixe avec dithering ordonné (matrice de Bayer).
3. Contour sombre optionnel d'1 pixel sur la silhouette.
4. Assemblage en planche de sprites + JSON (point d'ancrage, emprise en tuiles, rotation, étape).

Saisons : une table de correspondance de couleurs par saison (verts → ocres → blanc), sans re-rendre.

## Phase 5 — L'agent `sprite-forge` (~2 h)

Un skill contient la bible de DA, le catalogue des pièces et la procédure. Pour chaque demande (« un moulin à eau ») :

1. écrire la fiche JSON à partir du kit ;
2. lancer rendu + conversion ;
3. comparer la planche produite à la planche de référence (silhouette, proportions, lisibilité, palette) ;
4. corriger et relancer, 3 itérations au maximum ;
5. présenter le lot pour validation.

Pièce manquante (une roue de moulin) : l'agent l'ajoute au kit comme nouvelle fonction.

## Mon rôle

- Choisir la palette parmi des propositions.
- Valider la planche de référence par remarques (« toit trop plat », « trop sombre »).
- Trier les lots : accepter, refuser, commenter.

La retouche à la main est facultative. Sans elle, le rendu est propre et cohérent mais un peu mécanique ; un pixel artist freelance peut reprendre plus tard les 10-20 sprites les plus visibles.

## Hors pipeline et limites

- **Arbres, animaux, personnages** : formes organiques, à générer avec PixelLab ou Retro Diffusion puis à repasser par la phase 4 pour forcer la palette.
- **Terrain** : chantier séparé (données d'altitude, hillshade, texture d'herbe).
- **Bâtiments uniques** (château, cathédrale) : modélisation dédiée, le kit ne suffit pas.
- Aucun pipeline « sprites iso » clé en main n'existe : la boucle rotations + planche est à scripter.
- Retro Diffusion : 10 requêtes par minute, perspectives parfois incohérentes.

## Carte : du Sud-Ardèche à la Méditerranée

Oui, c'est largement faisable, même à l'échelle 1:1.

| Zone | Surface réelle | Surface en jeu à 1:2 |
|---|---|---|
| Angleterre entière (Land & Liege, d'après leur site) | ~130 000 km² | ~32 500 km² |
| Moitié de l'Angleterre | ~65 000 km² | ~16 000 km² |
| Aubenas → Le Grau-du-Roi, bande de 100 km de large | ~13 000 km² | ~3 250 km² |

- Distance Aubenas → mer : ~120 km à vol d'oiseau (Vallon-Pont-d'Arc → mer : ~100 km).
- La bande couvre les gorges de l'Ardèche, les Cévennes orientales, Alès, Uzès, Nîmes, la Camargue et Aigues-Mortes (port royal médiéval du XIIIe siècle).
- À 1:2, la carte est environ 10 fois plus petite que la leur ; à 1:1, elle reste plus petite que leur monde en jeu.
- À 1:1 avec des cellules de 10 m : ~130 millions de cellules, à découper en morceaux chargés à la demande.
- Données : un seul pays, donc moins de sources qu'eux. RGE ALTI et BD TOPO (IGN), Corine Land Cover, géologie BRGM.

## Sources

- Land & Liege, site officiel : https://landandliege.com/
- Article Shazoo : https://shazoo.ru/2026/11/10/193765/solo-razrabotcik-sozdaet-srednevekovuiu-mmo-na-tocnoi-karte-britanii-mir-sobran-iz-realnyx-dannyx-s-kletkami-10-na-10-metrov
- PixelLab MCP : https://www.pixellab.ai/vibe-coding
- Retro Diffusion, exemples d'API : https://github.com/Retro-Diffusion/api-examples
- Blender MCP : https://mcpservers.org/es/servers/ahujasid/blender-mcp
- Retour d'expérience Claude + Blender : https://medium.com/@creativeaininja/claude-drives-blender-through-mcp-now-heres-what-actually-changes-684f28f78c7b
