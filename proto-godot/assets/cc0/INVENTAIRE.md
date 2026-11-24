# Inventaire des assets CC0 — Jupire (gorge de Balazuc)

Voir `LICENCES.md` pour les détails de licence/source/taille de chaque asset.

## Utilisable tel quel

| Asset | Chemin | Remarque |
|---|---|---|
| Buissons garrigue (shrub_02, shrub_04) | `vegetation/shrub_02/`, `vegetation/shrub_04/` | glTF PBR prêt à l'emploi, générique mais convaincant pour de la garrigue basse. |
| Touffes d'herbe (grass_medium_01/02) | `vegetation/grass_medium_01/`, `vegetation/grass_medium_02/` | glTF PBR, alpha sur les brins, prêt à l'emploi. |
| Végétation stylisée (Common Tree, Bush, Willow, Plant, Grass, Pine Tree, Rock Moss) | `vegetation/quaternius_nature_pack/` | FBX low-poly à couleurs vertex (aucune texture externe nécessaire). Alternative légère si la direction artistique va vers du stylisé plutôt que du PBR réaliste. |
| Écorce de chêne (texture) | `textures/jolcham_oak_bark_01/` | JPG 2K, prêt à appliquer sur tronc. |
| Herbe sèche (texture sol) | `textures/withered_grass/` | JPG 2K, prêt à l'emploi pour un sol de garrigue. |
| Feuilles mortes au sol (texture) | `textures/forest_leaves_03/` | JPG 2K, prêt à l'emploi en sous-bois. |
| Feuille avec canal alpha (Leaf001) | `textures/leaf001_alpha/` | JPG 2K avec carte Opacity séparée (alpha), utilisable directement pour une carte de feuillage. |
| HDRI ciel d'été dégagé | `hdri/kloofendal_43d_clear_puresky/` | HDR 2K, midi, ciel dégagé haute contraste — prêt pour l'éclairage indirect Cycles. |
| Mouton | `animaux/quaternius_farm/Sheep.fbx` | FBX prêt, pose statique (à vérifier si une marche est incluse dans le rig). |
| Renard | `animaux/quaternius_pack5/Red Fox.fbx` | FBX prêt, pose statique. |
| Oiseau générique / poisson générique (secours) | `animaux/quaternius_pack5/bird.fbx`, `animaux/quaternius_pack5/Fish.fbx` | FBX très simples, en secours si les versions détaillées (corbeau, brochet) ne conviennent pas. |
| Poisson de rivière — brochet (Esox) | `animaux/esox_pike/esox.fbx` + `tex/` | FBX riggé et animé (idle, nage lente, nage rapide, 60 fps), textures PBR incluses. Le plus abouti des animaux livrés. |

## Demande du travail

| Asset | Chemin | Travail nécessaire | Estimation |
|---|---|---|---|
| Sanglier | `animaux/boar_blend/boar.blend` | Riggé + animé (marche, attaque) mais livré en `.blend`. Soit Godot importe le `.blend` nativement (Blender installé sur la machine de dev, import direct dans l'éditeur), soit export manuel en glTF/FBX depuis Blender. | ~10 min |
| Chevreuil/cerf | `animaux/deer_female_blend/doe.blend`, `animaux/old_deer_male_blend/deer1.blend` | Idem : riggés + animés, en `.blend`. Export à faire vers glTF/FBX si l'import natif Blender n'est pas configuré. | ~10-15 min chacun |
| Corvidé (corbeau) | `animaux/raven_blend/raven_0.blend` | Riggé, anim de vol de démo, en `.blend`. Même remarque export. | ~10 min |
| Arbre feuillu (approximation chêne) | `vegetation/tree_small_02/` | C'est un arbre africain (Burkea africana / wild syringa), pas un chêne. Silhouette généraliste correcte pour un feuillu moyen, mais pas typée chêne vert/pubescent. Piste concrète : remplacer ses textures tronc/feuilles par `textures/jolcham_oak_bark_01/` et `textures/leaf001_alpha/` pour le rapprocher visuellement d'un chêne méditerranéen. Modèle lourd (111 Mo) — à garder seulement si la direction artistique est réaliste/PBR. | ~30-45 min de retexturage dans Blender |
| Buisson sec (Wild Rooibos Bush) | `vegetation/wild_rooibos_bush/` | Espèce sud-africaine (fynbos du Karoo), pas méditerranéenne, mais silhouette de buisson sec très proche d'un ciste ou d'un romarin de garrigue. Utilisable en l'état comme remplissage, idéal si retexturé/reteinté plus tard. | Optionnel |

## Non trouvé / écarté (avec piste)

| Besoin | Statut | Piste concrète |
|---|---|---|
| Genévrier (buisson conique de garrigue) | Non trouvé en CC0 | Aucun modèle dédié sur Poly Haven, ambientCG, Kenney ou dans les packs Quaternius explorés. Piste : partir de `vegetation/quaternius_nature_pack/Bush_1.fbx` ou `Bush_2.fbx` et le resculpter en forme conique dans Blender (~20 min), ou surveiller les mises à jour de Poly Haven (nouveaux modèles ajoutés régulièrement). |
| Chèvre (en plus du mouton) | Non cherchée spécifiquement | La consigne acceptait « mouton ou chèvre » ; le mouton (Sheep.fbx) couvre le besoin. Si une chèvre précise est voulue, aucune n'a été localisée en CC0 lors de cette recherche — à relancer sur Quaternius/Poly Haven si besoin. |
| Chêne méditerranéen réaliste (modèle dédié) | Écarté | Les meilleurs résultats Sketchfab (« Low Poly Oak Tree » by Aroy, « Lowpoly Oak Tree » by Mongze) sont en **CC-BY** (attribution obligatoire) — non conformes à la consigne CC0 stricte, donc écartés sans téléchargement. Voir plus haut la piste de retexturage de `tree_small_02`. |
| Sanglier/genévrier via CGTrader, TurboSquid, Free3D | Écarté | Licences par défaut « royalty-free »/« free » de ces plateformes ≠ CC0 ; vérification par modèle non faite (nécessiterait un compte et une lecture cas par cas) → écarté par prudence. |
| Sanglier/buisson via Meshy.ai | Écarté | Plateforme de génération 3D par IA ; la mention « CC0 » n'a pas pu être vérifiée avec certitude sans création de compte, et la provenance IA fragilise la traçabilité de la licence → écarté par prudence. |
| Pack « 5 low poly trees » (OpenGameArt) | Écarté | Page affichant à la fois un tag CC0 et un tag CC-BY-SA 3.0 sans distinction claire de quel fichier relève de quelle licence → incertitude jugée trop grande. |
| Mouton riggé alternatif (« Sheep rigged, textured and animated », OpenGameArt) | Écarté | Licence CC-BY-SA 3.0 (attribution + partage à l'identique obligatoires) → non conforme. Le mouton Quaternius CC0 couvre déjà le besoin. |
| Kenney « Animal Pack » | Téléchargé puis écarté | Vérification a montré qu'il s'agit d'icônes 2D (éléphant, girafe, hippopotame, singe, panda, perroquet, pingouin, cochon, lapin, serpent) — aucun rapport avec la faune ardéchoise, et pas des modèles 3D. Supprimé. |
| OpenGameArt « Animated Wild Animals » (Boar.zip / Deer_0.zip / Fox.zip) | Téléchargé puis écarté | Vérification a montré qu'il s'agit de sprites 2D pixel art (idle/walk/run en PNG plats), pas de modèles 3D. Supprimé. |

## Formats à signaler

- **`.blend`** (sanglier, cerf x2, corbeau) : format natif Blender, pas glTF/FBX. Godot 4 peut l'importer nativement si Blender est installé et son chemin renseigné dans les préférences de l'éditeur — sinon export manuel à faire depuis Blender. C'est le seul écart aux formats demandés dans la mission.
- Tout le reste est livré en **glTF 2.0** (végétation Poly Haven) ou **FBX binaire** (animaux Quaternius/Esox, végétation stylisée), **JPG 2K** (textures) et **HDR 2K** (ciel) — conforme aux formats demandés.

## Taille totale

~231 Mo utilisés sur les 2 Go de budget (dont 111 Mo pour le seul `tree_small_02`, le plus gros poste).
