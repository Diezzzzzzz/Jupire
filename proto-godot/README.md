# proto-godot — les deux caméras, côte à côte

> **À LIRE EN PREMIER.** Ce proto ne sert qu'à trancher UNE question :
> faut-il verrouiller l'orientation de la caméra (AoE2 pur, un seul rendu par
> objet) ou la faire pivoter par paliers de 45° (huit rendus) ?
> Tout le reste — terrain, eau, semis, sprites — est là pour rendre la question
> jugeable à l'œil, pas pour être beau.

```bash
./lancer.sh            # la fenêtre s'ouvre sur le fond de gorge de Balazuc
```

| touche | effet |
|---|---|
| **1** / **2** | yaw verrouillé / paliers de 45° |
| **A** / **E** | pivoter (mode 2) · **T** inclinaison (refabrique les sprites) |
| **G** | caméra libre ↔ collée au perso |
| **ZQSD** | déplacer (Maj = vite) · **clic droit glissé** déplacer la vue |
| **clic gauche** | poser le perso là où on clique |
| **B** / **H** | fond de gorge / belvédère · **molette** zoom |
| **F** | brume atmosphérique · **X** matières tuilées ↔ aplat de secours |
| **L** | soleil cuit dans le monde ↔ dans la caméra |
| **R** | remettre les compteurs · **F12** capture · **Échap** quitter |

## Les matières du terrain

Quatre textures CC0 d'ambientCG, tuilées et mélangées par une carte de poids :
`Rock019` (calcaire clair de falaise), `Ground109` (garrigue sèche caillouteuse),
`Ground106` (litière de sous-bois), `Gravel023` (galets de berge). La répartition
vient de la pente, des classes du semis et de la distance à l'eau ; la falaise
est projetée en triplanaire pour ne pas s'étirer sur le vertical.

**Pourquoi tuilé plutôt qu'une grande texture cuite** : 8192² sur 2,4 km ne
donne que 30 cm par pixel — à la portée de jeu c'est encore un aplat. Tuilé, le
détail vaut ~2 cm/px, et la carte de mélange (2,3 m) ne porte que la répartition.
Détail fin et macro-structure sont deux problèmes à deux résolutions.

L'étalonnage se fait dans le shader (`scripts/terrain.gdshader`), pas dans les
fichiers sources : les textures CC0 sont photographiées à plat, chacune avec son
exposition. Réglage actuel vérifié à la mesure de pixels, pas à l'œil — falaise
ensoleillée à sRGB 182, ombre portée à 52-79, 0,2 % de pixels saturés.

## Ce qu'il faut regarder

1. **Appuie sur 1.** Yaw verrouillé. Le HUD dit « PERSO MASQUÉ » : tu es
   derrière la paroi et tu ne peux rien y faire.
2. **Appuie sur 2, puis A deux fois.** Le perso réapparaît. C'est tout le débat.
3. **Regarde la ligne « angles de sprite utilisés ».** Elle passe de 1/8 à 8/8
   — mais le perso, lui, n'a jamais eu besoin de plus de 8 images. Le pas de la
   caméra (45°) est un multiple du pas des sprites (45°), donc l'angle relatif
   reste sur la grille. **La rotation ne coûte pas un sprite de plus.**
4. **Les huit ruines en couronne** portent les huit orientations du monde. En
   mode 2, les huit cases de la planche servent en même temps : c'est l'objet
   ORIENTÉ qui exige les angles, pas l'arbre.
5. **Appuie sur L.** Le soleil passe du monde à la caméra. Pivote : le côté
   éclairé des arbres suit la caméra. C'est le piège du pré-rendu, et il se
   règle à l'usine, pas au jeu.

## Ce que la mesure dit (et elle corrige une affirmation trop rapide)

`outils/occlusion.py` tire, pour 15 106 points du terrain, un rayon vers la
caméra sous chacun des 8 paliers, et compte. Sur le terrain transformé (k=0,85,
creusement ×1,1) :

| inclinaison | pentes perçues | fond de gorge : ≥1 palier bouché | moyenne | aucun palier libre |
|---|---|---|---|---|
| 20° | ×2,75 | 40,5 % des points | 0,95/8 | **0 %** |
| 26,565° (le 2:1 d'AoE2) | ×2,00 | 26,5 % | 0,54/8 | **0 %** |
| 36° (ton réglage) | ×1,38 | 13,2 % | 0,24/8 | **0 %** |
| 45° | ×1,00 | 6,0 % | 0,11/8 | **0 %** |

Trois enseignements, dont un désagréable :

- **L'occultation est rare.** À 36°, un yaw verrouillé laisse le perso caché
  dans ~3 % des situations de fond de gorge (0,24 palier sur 8), pas « une
  bonne partie du temps » comme je l'avais annoncé. Je me suis trompé d'un
  ordre de grandeur, et c'est le proto qui l'a montré.
- **Aucun point du monde n'est bouché sous les 8 paliers.** Donc pas besoin de
  fondre le relief occultant façon Diablo — l'argument « il faudrait un shader,
  et les shaders t'ont déjà coûté une session » tombe aussi.
- **L'inclinaison pèse plus que le mode.** Descendre de 36° à 26,565° pour
  retrouver le 2:1 d'AoE2 multiplie l'occultation par 2,3. Le choix du tilt et
  le choix du yaw ne sont pas indépendants.

L'argument qui, lui, tient toujours — et qui n'est pas une question
d'occultation mais de lecture du paysage (doc 05) :

```
75 057 mailles de pente > 25°  (7,2 % du terrain)
  une seule orientation  : 53,5 % des faces vues de face, au mieux
  les 8 paliers réunis   : 100 %
```

**Une caméra verrouillée ne montrera jamais plus de la moitié des faces de
falaise de Balazuc.** L'autre moitié est vue de dos pour toujours. Comme la
doc 05 fait de la verticalité l'émotion centrale et la doc 06 de l'angle le
moyen de la lire, c'est là que se joue la décision — pas sur le perso caché.

## D'où viennent les données

`outils/convertir.py` lit `../proto-terrain/data/world_2400.json` (MNT LiDAR HD,
2048² au pas de 1,17 m) et `world_2400.hydro.png` (hydrographie BD TOPO), et
sort des binaires que Godot se contente de lire. Tout le calcul de monde est
là : rééchantillonnage en 1024² au pas de 2,34 m, débruitage, aplatissement
0,85, creusement ×1,1 sur les creux raides, couture des berges, surface d'eau
par maille, couleurs et ombrage cuits.

**Au passage, le bug 2 de juillet est réglé** : le semis venait de `semis.py`,
qui classe par accumulation d'écoulement et ne voyait que 0,28 % d'eau, alors
que le rendu utilisait le masque BD TOPO. Ici c'est le masque BD TOPO qui
filtre le semis — 5 270 arbres sur 58 412 (9 %) tombaient dans l'eau ou sur la
berge et ont été jetés.

Pour regénérer : `python3 outils/convertir.py` (~45 s, Python pur, pas de
dépendance, comme le reste du pipeline Jupire).

## Ce qui est du placeholder assumé

- **Les volumes 3D** (`scripts/volumes.gd`) sont des primitives empilées. C'est
  l'argument même du sprite pré-rendu : à 40 px de haut, la géométrie ne se
  voit pas. Chacun se remplace par un modèle CC0 ou un arbre de geometry nodes
  sans toucher au reste.
- **L'usine à sprites** (`scripts/usine.gd`) tourne dans Godot pour que le proto
  soit autonome. En vrai ce sera Blender en batch — le principe est identique :
  caméra ORTHO, à l'inclinaison exacte du jeu, soleil fixe dans le monde.
- **L'eau** est un matériau standard sans shader, volontairement : la session de
  juillet a perdu l'eau à cause d'un ShaderMaterial GLSL qui tombait en silence
  sous ANGLE. Rien ne revient en shader tant que ce n'est pas vérifié sur ta
  machine.

## Angles vifs connus

- La surface d'eau déborde un peu sur la berge là où le masque BD TOPO est
  large (elle prend le minimum local sur 24 m). Cosmétique, pas gênant pour la
  question posée.
- Le débruitage est une gaussienne là où le proto browser applique un filtre
  bilatéral : les crêtes sont un cheveu plus rondes ici.
- Les classes du semis ne contiennent ni ripisylve ni rocher sur cette emprise,
  donc les volumes `peuplier` et `rocher` sont fabriqués mais jamais semés.
