# Faisabilité — la Méditerranée procédurale

> Question posée (2026-07-27) : *peut-on techniquement recréer tout le bassin
> méditerranéen en jeu type AoE2 MMO, généré procéduralement à partir de points GPS,
> de hauteurs et de cartes ?* Réponse courte : **oui, et c'est même la partie facile.**
> Ce doc chiffre les briques, nomme les trois vrais murs techniques, et surtout
> pointe le **triangle impossible** que la question cachait — un arbitrage de design,
> pas d'ingénierie.

## Réponse courte

Rien dans cette idée n'est bloqué techniquement. Les données mondiales sont libres,
la donnée pèse quelques centaines de Mo, et le profil réseau de Jupire (dispersé,
lent, sans PvP nerveux — doc 09) est le plus facile qui soit. Les murs sont ailleurs :
la précision flottante, le viewshed serveur, et surtout **la fadeur**.

## 1. Les données existent, sont libres, et sont mondiales

| Besoin | Source | Résolution | Couverture |
|---|---|---|---|
| Relief terrestre | **FABDEM** (Copernicus GLO-30 corrigé) | 30 m | mondiale |
| Relief fin | IGN RGE ALTI (FR) / PNOA LiDAR (ES) / TINITALY (IT) | 1–10 m | nationale |
| Bathymétrie | **EMODnet DTM 2024** | ~115 m | toute la Méditerranée |
| Couverture du sol | **ESA WorldCover** | 10 m | mondiale |
| Vecteurs (trait de côte, rivières, sources, **ruines**) | OpenStreetMap | variable | mondiale |

Trois remarques qui comptent plus que le tableau :

- **FABDEM retire les bâtiments et les arbres** du DEM (erreur moyenne divisée par ~2
  en zone forestière, de 12,95 m à 0,45 m d'erreur médiane sous canopée dense). C'est
  littéralement *le monde rendu à la nature* livré comme produit sur étagère. Le pilier
  fondateur du projet est un dataset.
- **Les vraies ruines antiques sont dans OSM** (`historic=archaeological_site`,
  `ruins=yes`) avec leur position et leur polygone. Delphes, Carthage, Sélinonte,
  Éphèse existent en base. Le doc 03 proposait de *choisir à la main quelques bâtiments
  à ruiner* : à l'échelle méditerranéenne, on hérite gratuitement de ruines qui sont
  vraiment là, vraiment tombées. Et sans toponyme en jeu (mantra doc 00), le joueur
  voit une ruine anonyme et doit deviner — la donnée réelle ne donne aucune certitude.
- **Vigilance licence** : OSM est en ODbL (attribution + partage à l'identique de la
  *base dérivée*). Non bloquant pour un jeu, mais à cadrer une fois, pas à découvrir
  trois ans plus tard.

## 2. Ce que ça pèse vraiment

Une heightmap 16 bits pèse 2 octets par pixel. Donc, par km² :

| Résolution | px / km² | Mo bruts / km² |
|---|---|---|
| 30 m | 1 111 | 0,002 |
| 5 m | 40 000 | 0,08 |
| 2 m | 250 000 | 0,5 |
| 1 m | 1 000 000 | 2 |

Conséquences :

- **Tout le bassin en 30 m** (≈ 1 M km² de terres côtières utiles) ≈ **2 Go bruts**,
  quelques centaines de Mo en tuiles compressées (le relief compresse très bien).
- **8 fragments de 400 km² en 2 m** ≈ 1 600 Mo bruts, ~400 Mo compressés.
- **Contre-intuitif et important : la résolution coûte plus cher que la surface.**
  Toute la Méditerranée en grossier est *moins lourde* que huit vallées en fin.
  Le débat « est-ce trop grand ? » vise à côté ; le vrai débat est « à quelle finesse ».

Et la mer est le biome le moins cher du jeu (doc 19) : plate, procédurale, sans
végétation. **Le stockage n'est jamais le mur.**

## 3. Les trois vrais murs techniques (tous connus, tous franchis par d'autres)

### a) La précision flottante — à trancher TÔT
Godot stocke les positions en float32. Au-delà de quelques km de l'origine, les objets
**jittent** ; à 10 M d'unités il reste ~1 m de précision. Deux solutions officielles :
**floating origin** (on recentre le monde autour du joueur) ou build
`scons precision=double` (Terrain3D documente ce mode). Franchi par tous les jeux
spatiaux.

> **PRÉCISION (2026-07-27).** Ce doc a d'abord présenté ce choix comme « non
> rétrofittable ». C'est vrai d'un seul des deux :
> - **`precision=double` est réversible** — c'est un flag de compilation, le code du jeu
>   ne change pas. On peut l'activer le jour où le monde dépasse ~10 km.
> - **Le floating origin ne l'est pas** — il s'infiltre dans tout le code qui manipule
>   une position, et se rajoute mal après coup.
>
> Donc la vraie règle : **ne pas écrire de floating origin**, et passer en double le jour
> où c'est nécessaire. Rien à décider avant la première zone (5 × 5 km : aucun problème
> en Godot standard).

### b) Le viewshed serveur (doc 06)
Le fog en ligne de vue doit être calculé côté serveur, sinon maphack. Ordre de grandeur :
un viewshed 360° sur 2 km à 5 m de pas ≈ 400 rayons × 400 échantillons = 160 k lookups
par joueur et par recalcul. À 50 joueurs × 2 Hz ≈ 16 M lookups/s. **Trop pour du
GDScript, confortable en C++/GDExtension ou en compute shader**, et divisible par 10
avec un recalcul conditionnel (seulement si le joueur a bougé de plus de N mètres).
La RAM serveur est un non-problème : 50 joueurs dispersés = 50 fenêtres de quelques
km² chargées, quelques dizaines de Mo.

### c) Le raccord terre–mer
Piège classique et sous-estimé : les DEM terrestres et les DTM bathymétriques ne se
raccordent pas au trait de côte (référentiels verticaux différents → marches d'escalier
de plusieurs mètres le long de 46 000 km de littoral). Il faut un blending contraint
par le trait de côte OSM. Rien d'exotique, mais c'est des semaines, pas des heures —
et ça touche exactement l'endroit du monde que le joueur regarde le plus.

**Ce qui n'est PAS un mur** : le netcode (doc 09 — dispersion + fog = interest management
offert), la persistance (procédural déterministe par seed + deltas en Postgres : la
*taille* du monde ne coûte quasi rien en base, seule l'*activité* coûte), le GPU
(sprites, doc 03).

## 4. Le triangle impossible (le vrai contenu de la question)

C'est ici que la question technique devient une question de design. Trois exigences,
on n'en tient que **deux** :

1. **Tout le bassin** — la continuité géographique réelle, d'Espagne en Turquie.
2. **Le relief à l'échelle du corps** — falaises, gorges, dévers : la verticalité qui
   *pilote le fog* (doc 06) et produit le vertige (doc 05).
3. **La traversée en 1/4 de vie** — la décision fondatrice du doc 19.

- **1 + 2** → le 1:1 → 150 h de navigation → personne ne se croise. Déjà écarté (doc 19).
- **1 + 3** → la compression uniforme → **et c'est là qu'est le piège caché.**
  Deux façons de compresser, deux dégâts. Ce n'est pas une *perte de précision* (le
  relief reste net) : c'est une **déformation** — la pente n'est pas floue, elle est
  fausse.

  **(a) Compresser XY seulement** (Z intact) → `tan(θ') = k × tan(θ)`. Les angles
  explosent :

  | Pente réelle | 1:2 | 1:5 | 1:10 |
  |---|---|---|---|
  | 5° (chemin) | 10° | 24° | 41° |
  | 15° (montée franche) | 28° | 53° | **69°** |
  | 25° (sentier raide) | **43°** | 67° | 78° |
  | 35° (à quatre pattes) | 55° | 74° | 82° |

  Repères humains : marche confortable ≤ 20°, sentier raide 25–30°, quatre pattes
  35–40°, escalade > 45°. Lecture : **dès 1:2, un simple sentier ardéchois devient
  de l'escalade.** La compression anisotrope n'est pas un curseur qu'on dose, c'est
  un interrupteur qui casse la marche.

  **(b) Compresser XYZ** (isotrope) → `tan(θ') = tan(θ)`, les angles sont **exacts**.
  Mais le personnage, lui, ne rétrécit pas : à 1:10, ton corps de 1,70 m en vaut 17 à
  l'échelle du monde. **Les parois de Balazuc deviennent un talus que tu enjambes.**
  La verticalité meurt — donc le fog LoS n'a plus de relief à mordre, donc « monter
  pour comprendre » n'existe plus.

  → Aucune des deux ne préserve l'expérience. **L'option 2 du doc 19 (« réel compressé
  1:5–1:10 ») coûte silencieusement le pilier des docs 05/06.** Contradiction latente
  à trancher.
- **2 + 3** → ⭐ **des fragments réels dans une mer contractée.** On renonce à la
  *continuité*, pas au *réel*. Chaque masse (une côte crétoise, un cap turc, une baie
  tunisienne, le berceau ardéchois) garde son échelle vraie ; ce qu'on compresse, c'est
  **le vide entre elles**.

### La règle en une phrase
**On ne peut compresser que ce qui est plat.** La compression ne détruit que le relief ;
là où il n'y a pas de relief, elle est gratuite. La mer est à z = 0 : la contracter d'un
facteur 10 ne crée pas une seule pente. C'est toute la justification physique de
l'option 3 — **les terres à 1:1, le large contracté.**

### Pourquoi le collage est légitime ici (et pas ailleurs)
Deux garde-fous rendent l'option 3 propre :

- **Le monde reste un plan euclidien unique.** On a le droit de *déplacer* des masses ;
  on n'a pas le droit de faire varier la métrique localement. Un espace non-euclidien
  se trahit à l'estime : partir au cap X, revenir au cap opposé, et ne pas retrouver
  son port. Un réarrangement, lui, est indétectable — la boussole interne du joueur
  reste vraie.
- **Il n'y a pas de carte dans Jupire.** Le mantra « pas de minimap » (doc 00) a un
  effet de bord technique inattendu : **le joueur ne peut jamais superposer sa
  perception à une projection.** L'absence de carte *autorise* le collage. Le refus
  d'un raccourci de confort paie en liberté d'architecture.

Ce que ça coûte : « la Méditerranée » cesse d'être une carte fidèle pour devenir un
**archipel de vrais lieux**. Ce qu'on garde intact : la silhouette de chaque côte
(doc 26), la marchabilité du relief, et le « ça, c'est un vrai endroit ».

## 5. Ce que le procédural doit faire — et surtout ne pas faire

Même en fragments, on parle de centaines de km de littoral. **Aucun humain n'habille
ça à la main : le procédural n'est pas une optimisation, c'est une nécessité
structurelle.** D'où la ligne à tenir :

- **Le réel donne la forme, le procédural donne la matière.** Le DEM et les vecteurs
  fixent *où* est la crique, la crête, le lit du torrent, la ruine. Le bruit déterministe
  place les arbres, les rochers, les sentiers d'érosion — jamais la macro-forme.
- **Le procédural doit être déterministe et partagé** (même seed → même monde chez tous
  les clients et sur le serveur). C'est ce qui rend un monde immense gratuit en réseau :
  on ne transmet jamais le décor, seulement les *deltas* joueurs.
- **Ce qu'il ne doit jamais faire : inventer une côte.** Une côte générée par bruit est
  fade au bout de trois minutes ; une côte réelle ne l'est jamais. C'est précisément le
  réel qui sauve le procédural de la fadeur — pas l'inverse.

## Verdict mantra

La bonne question n'est pas « peut-on générer 25 000 km² ? » (oui, et pour quelques
centaines de Mo). C'est : **chaque km² mérite-t-il qu'on marche jusqu'à lui ?**

Le vrai risque de ce projet de monde immense n'est pas le CPU, c'est la **fadeur** —
et la fadeur trahit l'étoile polaire *plus sûrement qu'une minimap*. Une minimap donne
la certitude gratuitement ; un monde générique fait pire : il rend l'effort de réduire
la distance **inutile**, parce qu'il n'y a rien à découvrir en s'approchant. Le cœur
(« s'approcher pour voir net ») tourne alors à vide.

La sortie est déjà écrite dans les notes : **le vide n'est pas un bug, c'est le jeu**
(doc 09), et **la silhouette est le nom du lieu** (doc 26). Donc la règle :
**existence procédurale partout, densité authorée seulement dans les berceaux et les
escales.** Un littoral nu mais *vrai* n'est pas fade — il est désert, ce qui est
exactement la fiction.

Reste que ce verdict repose sur un pari non vérifié : *le relief réel, seul, sans
habillage, suffit-il à donner une identité à un lieu ?* Tant qu'il n'est pas testé,
tout le reste est du rêve — et le rêve sans fin est le risque n°1 du projet.

## Le test le moins cher (une soirée, et il tranche)

Il existe déjà, il attend dans le doc 26 : **le script PNG d'horizon**. L'étendre
suffit à répondre :

1. Choisir 10 points GPS réels en Méditerranée (une côte crétoise, un cap turc, une
   baie tunisienne, une calanque catalane, une île cycladique…).
2. Raycaster le DEM depuis chacun → 10 panoramas PNG, **relief nu, sans habillage**.
3. Les regarder côte à côte. **Les distingue-t-on ? Peut-on leur donner un nom ?**

- Si oui → le réel porte l'identité, le procédural n'a qu'à habiller : le monde immense
  est viable, la piste des fragments réels est la bonne.
- Si non → aucun budget d'assets ne sauvera 46 000 km de côte : il faudra un monde
  beaucoup plus petit et authoré.

Coût : GDAL + Python, quelques heures. C'est un test de **faisabilité du ressenti**,
pas de la machine — le seul genre de test qui puisse encore surprendre.

## Garde-fou anti-rêve (rappel doc 19)

Rien de tout ceci n'entre dans l'Étape 0 (doc 13), qui reste la porte du feu vert.
Les deux seules choses que ce doc change *aujourd'hui* :
1. **Décider tôt** floating origin vs double precision (non rétrofittable).
2. **Trancher le triangle** avant d'écrire la moindre ligne de pipeline générique.

## Questions ouvertes

- **Le triangle : 2+3 est-il accepté ?** C'est-à-dire : renonce-t-on officiellement à
  la continuité géographique (une Méditerranée-collage) pour sauver la verticalité ?
  Ça amende l'option 2 du doc 19.
- **Quelle échelle pour les fragments** — 1:1 strict (Balazuc reste Balazuc, doc 19)
  ou 1:2 uniforme sur toutes les masses ? 1:2 double la surface utile pour un coût de
  verticalité encore lisible ; 1:1 protège la gorge.
- **Combien de fragments, et de quelle taille ?** Croise directement « où sont les
  berceaux de spawn » (doc 19) et la densité (doc 10).
- **Un fragment est-il une île, ou une côte ouverte ?** Une île borne naturellement le
  monde jouable sans mur invisible — mais un monde d'îles seules affadit les cultures
  continentales.
- **Le trait de côte est-il jouable partout, ou seulement aux escales ?** Détermine si
  le caboteur (doc 19) a vraiment un métier ou s'il n'existe qu'entre deux fragments.
- **Faut-il un éditeur de monde maison** (poser/orienter les masses sur le plan global) ?
  Probablement oui, quelques semaines — à budgéter comme un outil, pas comme du jeu.

## Sources

- [FABDEM — A 30 m global map of elevation with forests and buildings removed](https://iopscience.iop.org/article/10.1088/1748-9326/ac4d4f) (Hawker et al., 2022)
- [FABDEM — University of Bristol / Fathom](https://www.fathom.global/insight/egu22-fabdem/)
- [EMODnet Bathymetry DTM 2024 (~115 m, toute la Méditerranée)](https://emodnet.ec.europa.eu/en/emodnet-bathymetry-dtm-2024-release)
- [ESA WorldCover 10 m (mondial, gratuit, sans restriction d'usage)](https://esa-worldcover.org/en)
- [Godot — Large world coordinates (float32, floating origin, `precision=double`)](https://docs.godotengine.org/en/stable/tutorials/physics/large_world_coordinates.html)
- [Terrain3D — double precision](https://github.com/TokisanGames/Terrain3D/blob/0.9/doc/docs/double_precision.md)
- [Godot — Emulating double precision on the GPU to render large worlds](https://godotengine.org/article/emulating-double-precision-gpu-render-large-worlds/)
