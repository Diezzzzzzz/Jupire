# Technique

## Direction artistique : sprites pré-rendus sur terrain 3D

Le « charme SimCity 4 » = **hybride** :
- **Terrain** = vraie 3D (mesh + textures) → relief, pentes.
- **Objets** (bâtiments, arbres, ruines, perso, animaux) = **sprites pré-rendus** :
  modélisés en 3D, « photographiés » sous un angle dimétrique fixe, aplatis en 2D.
  Le pré-calcul donne ombres douces / détails riches → la patte.

Piège : un sprite aplati n'est correct **que sous l'angle de rendu**. Solution =
**sprites multi-angles** (rendre chaque objet sous N angles : 4 = SC4, 8 = AoE2/Diablo).
Caméra qui tourne par **paliers** (swap du bon sprite), pan + zoom libres.
→ navigation sans casser la DA. Le coût se déplace vers le **pipeline d'assets**
(rendre chaque prop sous 8 angles en batch via Blender).

## Moteur : Godot 4

- Gratuit, open-source, pas de royalties.
- Excellent 2.5D : `Sprite3D` / `AnimatedSprite3D` posés sur terrain 3D = modèle SC4.
- Export **natif** (Windows/Mac/Linux, léger) **et** web (HTML5) depuis le même projet.
- **API multijoueur haut niveau** intégrée (`MultiplayerSynchronizer`, RPC).

Note perf : un jeu à base de sprites est **GPU-cheap** → « tourne sur énormément
de PC » est garanti par l'approche elle-même. Le vrai mur n'est pas le rendu mais
le **réseau** (serveur autoritaire, synchro, anti-triche, latence).

## Terrain réel

- **MNT / DEM** = grille d'altitudes.
  - **IGN RGE ALTI** (France) : 1–5 m, gratuit. Référence pour Balazuc.
  - (Alternatives mondiales : Copernicus DEM 30 m, AWS Terrain Tiles, SRTM.)
- Pipeline :
  1. Bounding box autour de Balazuc (~44.51° N, 4.37° E), quelques km².
  2. Récupérer + découper le DEM (**QGIS** ou `gdal`) → **heightmap PNG 16-bit**.
  3. Importer dans Godot via le plugin **Terrain3D** (import heightmap, LOD,
     collision auto). Alternative : HTerrain (Zylann).
  4. Collision générée → le perso marche dessus.
- **Échelle** : décider tôt un facteur monde (1 unité Godot = X mètres), l'appliquer
  partout (terrain, perso, vitesse, caméra). Sinon tout est à refaire.

## Habillage du monde (forêts, rivières, ruines)

Source « où sont les choses » :
- **OpenStreetMap** : `waterway` (rivières), `natural=wood` / `landuse=forest`, lacs.
- **IGN BD TOPO / BD FORÊT** (France) : hydrographie + végétation très détaillées.

Approches à combiner :
- **Données réelles** = macro (cette zone est forêt, ici coule la rivière).
- **Procédural** = micro (position/densité exacte des arbres).

### Le bâti → des ruines (idée clé)

On garde **quelques** polygones `building` choisis à la main. Au lieu de poser une
maison, ils servent de **données de placement de ruines** :
- **position** (où était le bâtiment),
- **forme** du polygone (pans de mur le long des arêtes),
- **orientation**.
Recouvertes de lierre/mousse (overlays sprites), végétation qui pousse dedans.

### Performance forêts : instancing obligatoire

Une forêt = des milliers d'arbres. **Jamais** d'objets individuels. Utiliser
**`MultiMeshInstance3D`** (milliers de copies en un appel GPU). Arbres = sprites
multi-angles instanciés → forêt façon AoE2, magnifique et quasi gratuite.

### Rivières

Lignes `waterway` → mesh le long de la spline (ou creuser le terrain) + **shader
d'eau stylisée**.

## Animaux = chantier à part (plus tard)

Pas de la donnée à importer mais de l'**IA/gameplay** : spawn, comportement
(errer, brouter, fuir), troupeaux (**boids**), animations sprite multi-angles.
Premier jalon réaliste : **un seul animal** qui erre et fuit le joueur.
