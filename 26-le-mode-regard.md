# Le mode Regard — voir et dire le lointain

> Le problème (technique et réel) : la vue AoE2/SC4 choisie au doc 06 n'a **pas
> d'horizon**. Comment montrer une montagne au loin, une île ? Le dézoom ne
> résout pas (dézoomer jusqu'à voir l'île = une carte satellite : trahison de
> « la carte = le paysage », et l'échelle du doc 19 rendrait tout minuscule).

## La solution : une troisième bascule de perception

Le jeu est **déjà** fait de bascules (doc 08 : « sol ↔ ciel = une de plus »).
On en assume une troisième :

- **SOL** — la vue dimétrique du doc 06 : l'action, le proche, le village.
- **REGARD** — *nouveau* : on s'arrête et on **regarde au loin** dans une
  direction → vue subjective panoramique, à hauteur d'yeux du personnage.
- **CIEL** — le mode astro du doc 08 : le temps, les étoiles, le vent.

Le Regard est un **acte volontaire** (doc 05 : « on ne perçoit que ce qu'on
regarde ») : immobile, une direction choisie, le panorama s'ouvre. Regarder
loin coûte un moment d'arrêt — la contemplation devient un geste de gameplay.

## Ce qu'on y voit : un panorama-peinture généré du vrai relief

Techniquement classique (cf. PeakFinder) : **lancer de rayons sur la heightmap**
depuis la position et la hauteur d'yeux du perso → silhouettes d'horizon en
plans successifs → rendu stylisé « peinture » : couches de silhouettes
délavées par la brume atmosphérique (le depth haze du doc 05, déjà prévu).

- **Fond de gorge** : le Regard bute sur les falaises — on voit un mur et un
  ruban de ciel. **Belvédère** : on voit à des jours de marche. La même
  asymétrie que le fog du doc 06, produite par les mêmes données, gratuite.
- **La portée se règle par la brume, pas par la physique** : pas de courbure
  terrestre à simuler — l'épaisseur atmosphérique décide jusqu'où porte un
  regard (et depuis les hauteurs, on perce plus loin). Un paramètre de design.
- **Ce qui vit au loin** : silhouettes seulement — un panache de fumée, une
  voile, un vol d'oiseaux. Jamais de détail : « voir beaucoup mais pas
  précisément » à l'état pur. (Serveur : n'insère dans le panorama que ce que
  la ligne de vue autorise — même règle anti-maphack que le doc 06.)
- **Le Regard ne révèle rien sur la carte** (pas de zone explorée gagnée) :
  il nourrit les *yeux* du joueur et son **répertoire perceptif** (doc 25) —
  voir une montagne au loin = acquérir son croquis-silhouette, niveau bas.

## Dire le lointain — la silhouette est le nom du lieu

C'est là que tout se noue avec les docs 24-25 :

- **En co-présence** : A pointe une direction (deixis, doc 24) → B se tourne
  et Regarde dans cette direction → **attention conjointe** sur le même
  panorama ; A désigne la silhouette de l'île dedans. « Montrer une montagne
  au loin » = pointer + regarder ensemble.
- **En absence (displacement)** : le **croquis de silhouette** (doc 25 étendu
  aux lieux). Le profil d'une montagne ou d'une côte EST son identité — c'est
  une pratique maritime réelle : les « vues de côtes » des livres de pilotage,
  profils dessinés que les marins comparaient à l'horizon pour reconnaître
  leur atterrissage. Dire « l'île aux deux pics, au sud-ouest, deux jours de
  mer » = [pointe SO] + [croquis silhouette] + [soleil, deux arcs].
- **Le gameplay d'atterrissage** : naviguer vers une île qu'on ne connaît que
  par un croquis dégradé, scruter l'horizon en mode Regard jusqu'à ce qu'une
  forme *corresponde* — le déclic de reconnaissance du doc 25, en pleine mer.
  C'est l'arrivée d'Ulysse en vue d'une terre : le moment odysséen par
  excellence, produit par trois systèmes existants qui s'emboîtent.
- **Peint sur une paroi**, le croquis de silhouette devient la **proto-carte**
  (doc 10 : la cartographie comme savoir in-game) — non pas une carte vue du
  ciel, mais des profils d'horizon annotés : la carte des marins d'avant les
  cartes.

## Verdict mantra

**Passe.** Regarder loin coûte (s'arrêter, monter), ne donne que du flou, et
nourrit la mémoire plutôt que la carte. La trahison serait : un dézoom
satellite, un panorama qui révèle du détail ou des zones de carte, un
marqueur posable sur l'horizon.

## Impact technique (borné) — et SANS 3D : la recette

Idée reçue à casser : « horizon = 3D = compliqué ». Non — le panorama n'est
**pas une scène 3D rendue par une caméra**, c'est un **dessin calculé à partir
de nombres** :

1. La heightmap est une grille d'altitudes (une image en niveaux de gris).
2. Depuis la position du perso, pour chaque **colonne** du panorama (~300
   colonnes pour un écran), on « marche » le long de cette direction dans la
   grille en échantillonnant l'altitude à distance croissante. Pour chaque
   échantillon : hauteur angulaire apparente = (altitude − yeux) / distance.
   On garde le max par tranche de distance (proche / moyen / lointain).
3. Résultat par colonne : 3-4 nombres = la hauteur de silhouette de chaque
   plan. Mis bout à bout : des **courbes de crête** (polylignes).
4. On les dessine en 2D, du fond vers l'avant : formes pleines, couleur de
   plus en plus délavée + haze par plan (Polygon2D + un dégradé dans Godot,
   ou même une simple image générée). C'est du papier découpé, pas de la 3D.

Le perso est **immobile** en mode Regard → on peut générer le panorama **une
fois** à l'entrée du mode (pas de coût par frame). Les éléments vivants
(fumée, voile) = des sprites posés à la colonne et hauteur voulues, par-dessus.

Référence d'humilité : PeakFinder fait ça dans un navigateur de téléphone avec
le MNT de la planète entière ; Comanche le faisait en temps réel sur un 386 en
1992. Notre version (statique, stylisée) est la variante *facile* du problème.

**Preuve en une soirée, sans moteur de jeu** : un script (Python + une dalle
IGN de Balazuc) qui sort un PNG — le panorama stylisé depuis un point choisi
de la gorge. Indépendant de l'Étape 0 (qui reste la table, doc 24) : c'est la
preuve technique jetable du Regard, comme la table est la preuve du canal.

- Même donnée que le viewshed du doc 06 — budget commun.
- Insertion des éléments vivants : serveur, filtrée par LoS.
- S'ajoute au chantier caméra du doc 06 sans le rouvrir : le SOL ne change pas.

## Questions ouvertes

- Le Regard est-il panoramique (360° en tournant) ou directionnel strict
  (un cône, il faut se tourner) ? Instinct : directionnel — on scrute.
- Transition SOL ↔ REGARD : fondu, travelling, instantané ? (Le ressenti de
  « lever les yeux » compte énormément — doc 05.)
- Depuis un bateau : le Regard au ras de l'eau porte peu (l'île surgit tard) —
  le monter au mât (la vigie !) porte plus. Rôle de vigie à bord ?
- Que voit-on la nuit en Regard (feux lointains ! — le phare, le camp) ?
