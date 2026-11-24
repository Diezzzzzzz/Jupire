# Pipeline de données — ce qu'on prend au réel, ce qu'on efface, ce qu'on invente

> Suite directe du doc 29. Envie exprimée (2026-07-27) : **le plus précis possible** ;
> demander au réel « y a-t-il une forêt ici ? » puis **générer la forêt
> procéduralement** ; et **surtout pas de chemins calqués sur les routes existantes**.
> Ce doc décrit le pipeline concret, et signale que le troisième point est beaucoup
> plus subtil qu'il n'en a l'air : **à haute résolution, la route n'est pas un objet
> posé sur le sol — elle EST le sol.**

## 0. La conséquence immédiate de « le plus précis possible »

Vouloir la précision, c'est **avoir déjà tranché le triangle du doc 29**. Le relief fin
n'existe qu'à l'échelle du corps ; toute compression le détruit (angles multipliés, ou
joueur géant). Donc : **terres à 1:1, mer contractée, fragments réels**. La question
« quelle échelle ? » est close par la question « quelle précision ? ». Les deux étaient
la même.

## 1. Le pipeline en trois questions

Tout se ramène à trois questions posées à la donnée, dans cet ordre :

1. **Quelle forme a le sol ?** → MNT (modèle numérique de terrain, le sol nu).
2. **Qu'est-ce qui pousse dessus ?** → couverture du sol + hauteur de végétation.
3. **Qu'est-ce qu'on efface ?** → la cicatrice humaine (routes, remblais, bâti).

La 3 est celle qu'on oublie, et c'est celle qui décide si le monde a l'air vierge.

## 2. « Quelle forme a le sol ? » — la précision disponible

| Zone | Source | Résolution | Statut |
|---|---|---|---|
| **France (Balazuc)** | **IGN LiDAR HD — MNT** | **50 cm** | gratuit, ~80 % du territoire fin 2025, complet fin 2026 |
| France (repli) | IGN RGE ALTI | 1–5 m | gratuit, couverture totale |
| Espagne | PNOA LiDAR | 2–5 m | gratuit |
| Italie | TINITALY | 10 m | gratuit |
| Reste (Grèce, Turquie, Maghreb) | FABDEM / Copernicus GLO-30 | 30 m | gratuit, mondial |

Vérifier la disponibilité LiDAR HD sur l'Ardèche avant toute chose (carte de diffusion
IGN). Si Balazuc est couvert, on a **le sol au demi-mètre** — c'est-à-dire mieux que ce
dont le jeu a besoin.

### Le poids, concrètement
- MNT 50 cm : **8 Mo bruts par km²** (4 M px × 16 bits). Balazuc + environs (25 km²)
  ≈ 200 Mo bruts, ~40 Mo compressés. Rien.
- Mais 400 km² au même détail ≈ **3,2 Go**. La précision ne se généralise pas.
- Le **nuage de points brut** (~10 pts/m², ~100–200 Mo de LAZ par km²) est un
  **intrant de pipeline, jamais un asset de jeu**. On le mange une fois hors ligne,
  on en sort des heightmaps et des listes d'objets. Le moteur ne voit jamais du LAZ.

### Corollaire : la résolution doit être variable
50 cm dans la gorge (là où la verticalité *joue* : parois, vires, méandres), 2–5 m sur
les plateaux, 30 m sur les côtes lointaines. Un plateau au demi-mètre est du gâchis de
Go et de vertices. **La finesse va où le regard travaille.**

## 3. « Y a-t-il une forêt ici ? » — trois niveaux de réponse

C'est ici que l'envie exprimée peut être **dépassée** : à Balazuc, on n'a pas besoin de
générer la forêt, on peut la **lire**.

### Niveau A — LiDAR HD (France) : les vrais arbres, un par un
Le nuage LiDAR HD est **classifié en 11 classes**, dont *végétation basse (0–50 cm)*,
*moyenne (50 cm–1,5 m)*, **haute (> 1,5 m)**, *bâtiment*, *eau*, *tablier de pont*.
Deux produits en découlent :

- **MNH** (Modèle Numérique de Hauteur = surface − sol) : la hauteur de la végétation
  en tout point. L'IGN le publie directement.
- **Détection d'arbres individuels** : sur le MNH lissé, chaque **maximum local** dans
  une fenêtre glissante (de rayon proportionnel à la hauteur) est une cime. Outils
  standards : `lidR` (`locate_trees` + `lmf`) en R, **PyCrown** en Python.

Sortie : une table `(x, y, hauteur, rayon de couronne)` pour **chaque arbre réel de
Balazuc**. Le « procédural » se réduit alors à choisir le sprite et l'orienter.
Pas de bruit de Perlin, pas de densité à régler, pas de placement à truquer.

*Attention connue : la détection de cimes se dégrade en forte pente (la fenêtre de
recherche circulaire suppose un sol horizontal) — précisément le terrain de la gorge.
À corriger en travaillant sur le MNH normalisé, pas sur le MNS brut.*

### Niveau B — BD Forêt V2 (France) : quelle essence
Polygones ≥ 5 000 m², **32 catégories** de formations végétales (chêne pubescent, pin
sylvestre, châtaignier, taillis, garrigue…), Licence Ouverte. Le LiDAR dit *où* et
*combien haut* ; la BD Forêt dit **quoi** — donc quel sprite. Le combo est complet.

### Niveau C — hors de France : là, vraie génération procédurale
**ESA WorldCover 10 m** (tree cover / shrubland / grassland / cropland / bare) donne le
masque. Plus aucune position d'arbre : on génère. Recette : masque WorldCover → semis
Poisson-disc (espacement minimal, pas de grille visible) → densité modulée par la pente,
l'exposition et l'altitude → essence tirée d'une table par biome.

> **Le procédural n'est donc pas la même chose partout.** À Balazuc il est presque
> inutile (le réel est plus riche) ; au Maghreb il fait 100 % du travail. Le pipeline
> doit accepter les deux régimes derrière la même interface : *« donne-moi les arbres
> de cette tuile »* — que la réponse vienne d'un fichier ou d'un seed.

### Le point de design : le procédural ne remplit pas, il fait VIEILLIR
La végétation des données, c'est celle de 2020. Or Jupire se passe **après la chute** :
les champs seraient en friche, les vergers ensauvagés, les villages en broussailles.
Donc la règle :

- **Le réel donne l'ossature** : ce qui est forêt depuis toujours reste forêt mature.
- **Le procédural gère la reconquête** : tout ce que la donnée classe *cropland* ou
  *built-up* devient friche, ronces, taillis pionniers, arbres isolés — jamais un champ.

C'est là que le procédural sert vraiment le concept, au lieu de simplement meubler.

> **AMENDÉ (2026-07-27) — doc 31.** La règle ci-dessus reste juste mais s'est durcie :
> on ne *retouche* pas la carte forestière actuelle, **on la re-dérive du relief**
> (végétation potentielle) et on la recale sur la BD FORÊTS ANCIENNES de l'IGN.
> Le couvert de 2020 devient un **contrôle**, plus une source.

## 4. Les routes — le vrai piège, et pourquoi l'intuition est juste

### Le facile
Ne pas importer `highway` d'OSM : une ligne de filtre. Fait.

### Le piège
**À 50 cm, la route est dans le relief.** Une route de coteau, c'est un déblai, un
remblai, une saignée horizontale de 6 m de large et des lacets — tout ça est du *sol*.
Le MNT LiDAR retire les arbres et les bâtiments par construction… mais **la route, il
la garde, parce qu'elle EST le terrain.** C'est le seul artefact humain que la donnée
« sol nu » conserve nécessairement.

Ironie : plus tu montes en précision, plus la cicatrice humaine est nette. Même sans
une seule texture de bitume, le joueur marchera sur une terrasse parfaitement plane et
régulière qui serpente à flanc de coteau — **plus lisible qu'une texture de route.**

Même problème pour : les **terrasses agricoles** (l'Ardèche en est tapissée), les
murets, les carrières, les digues, les remblais ferroviaires, les **tabliers de pont**
(classe dédiée dans le LiDAR HD).

### Pourquoi ça compte vraiment (et pas seulement pour l'esthétique)
Le jour où les chemins s'usent sous les pas des joueurs (érosion émergente), un terrain
qui propose déjà les meilleurs tracés fait que **les joueurs emprunteront les lacets de
la départementale** — et « leurs » chemins seront en fait ceux de la DDE. Le monde leur
aura donné l'itinéraire optimal gratuitement.

> **Effacer les routes est la condition pour que les chemins des joueurs soient les
> leurs.** L'intuition est exacte, et sa vraie raison est là.

### Trois stratégies
1. **Effacement (inpainting)** — masquer les emprises `highway` OSM bufferisées, puis
   reboucher le trou par interpolation depuis le terrain alentour (`gdal_fillnodata`,
   splines). Bon en pente douce, moche sur un remblai de 10 m (on obtient une bosse
   molle). Standard, éprouvé en hydrologie.
2. **Assumer et retourner** — les routes deviennent des **cicatrices** : ruines
   linéaires envahies, cohérent avec la civilisation tombée (doc 03 fait déjà ça pour
   le bâti). Mais ça offre un réseau de circulation gratuit. Frontière mantra :
   « le monde te montre une trace » (bon) vs « le monde te donne l'itinéraire » (mauvais).
3. **Mixte** : effacer les **infrastructures modernes** (routes départementales,
   remblais, ponts, carrières, parkings) et **garder** les **terrasses agricoles et les
   vieux chemins de pierre**, qui sont exactement ce qu'une civilisation tombée aurait
   laissé. On efface le XX<sup>e</sup> siècle, on garde le XVIII<sup>e</sup>.

L'arbitrage tient à une question simple, à poser objet par objet :
**est-ce que ça donne une direction, ou est-ce que ça donne un trajet ?**
Une terrasse en ruine intrigue. Un lacet goudronné conduit.

> **TRANCHÉ (2026-07-27) : stratégie 1, effacement total.** Aucun tracé existant ne doit
> être visible ni praticable. L'objectif explicite : voir les joueurs créer leurs propres
> **chemins du désir**, et les comparer aux vrais. L'effacement porte donc aussi sur ce
> qui n'est pas une route mais crée une ligne de moindre effort artificielle — au premier
> chef les **terrasses agricoles**, qui tapissent l'Ardèche et guident le déplacement
> horizontal aussi sûrement qu'un sentier. Voir doc 31.

## 5. Ordre de fabrication du pipeline

1. Vérifier la couverture LiDAR HD sur Balazuc (carte de diffusion IGN).
2. MNT 50 cm → heightmap 16 bits tuilée. Fixer **maintenant** la convention d'échelle
   et le choix floating origin / `precision=double` (doc 29, non rétrofittable).
3. Effacer les infrastructures (masque OSM → inpainting) — **avant** de générer quoi
   que ce soit dessus.
4. MNH → détection de cimes → table d'arbres. Croiser BD Forêt V2 pour l'essence.
5. Passe de reconquête : reclasser les zones cultivées/bâties en friches.
6. Export : heightmap + tables d'objets, versionnées. Le moteur ne consomme que ça.

Les étapes 1 à 4 sont du **Python/GDAL/lidR hors ligne** — pas du Godot. C'est un
travail d'outillage, testable et rejouable, et c'est là que se joue la tête du monde.

## Verdict mantra

Le pipeline ne pose aucun problème d'étoile polaire — sauf sur un point, et c'est celui
qu'on vient de nommer : **le réel importé peut donner de la certitude gratuitement.**
Pas par une minimap, par le sol lui-même. Une route effacée à moitié, et le monde
souffle au joueur où aller.

À l'inverse, la précision **sert** le mantra plus qu'aucune autre feature : c'est le
relief fin qui produit le fog en ligne de vue (doc 06), donc la distance spatiale, donc
« monter pour comprendre ». Le demi-mètre n'est pas du luxe technique — **c'est le
support physique du cœur du jeu.**

Et la vraie leçon de ce doc : **le réel ne s'importe pas, il se nettoie.** Le travail
n'est pas d'aller chercher la donnée (elle est là, gratuite, en une après-midi), il est
de décider **quoi effacer**. Un monde rendu à la nature est un monde dont on a retiré
quelque chose — pas un monde qu'on a rempli.

## Questions ouvertes

- **Balazuc est-il couvert par le LiDAR HD** aujourd'hui, ou faut-il partir sur le
  RGE ALTI 1–5 m en attendant fin 2026 ?
- **Où passe la ligne d'effacement ?** Les terrasses agricoles restent-elles (traces
  d'anciens) ou partent-elles (elles quadrillent tout le paysage ardéchois) ?
- **La détection d'arbres individuels vaut-elle son coût**, ou un semis procédural
  contraint par le MNH (densité + hauteur moyenne par cellule) suffit-il visuellement ?
  À trancher par comparaison visuelle, pas par principe.
- **Résolution variable : comment on la découpe ?** Par zone dessinée à la main, ou
  dérivée automatiquement de la rugosité du terrain (les zones accidentées héritent du
  50 cm) ?
- **Les ponts** : effacés (la rivière redevient un obstacle — très bon pour la distance)
  ou gardés en ruine (un pont écroulé est un lieu) ?
- **Que fait-on des bâtiments retirés ?** Le doc 03 propose d'en garder quelques-uns en
  ruines ; à l'échelle méditerranéenne, OSM `historic=archaeological_site` fournit les
  vraies ruines antiques (doc 29). Les deux sources se combinent-elles, ou choisit-on ?

## Sources

- [IGN — Programme LiDAR HD (couverture nationale visée fin 2026)](https://www.ign.fr/institut/programme-lidar-hd-vers-une-nouvelle-cartographie-3d-du-territoire)
- [MNT LiDAR HD — 50 cm, dalles 1 km, GeoTIFF](https://cartes.gouv.fr/aide/fr/partenaires/ign/observations-regulieres-territoire/relief/mnt-lidar-hd/)
- [MNH LiDAR HD (hauteur de végétation)](https://cartes.gouv.fr/aide/fr/partenaires/ign/observations-regulieres-territoire/relief/mnh-lidar-hd/)
- [Nuages de points LiDAR HD — 11 classes](https://cartes.gouv.fr/aide/fr/partenaires/ign/observations-regulieres-territoire/relief/nuages-points-lidar-hd/)
- [BD Forêt V2 — 32 catégories d'essences, Licence Ouverte](https://cartes.gouv.fr/aide/fr/partenaires/ign/referentiels-description-territoire/foret/bd-foret-v2/)
- [lidR — Individual Tree Detection & Segmentation](https://tgoodbody.github.io/lidRtutorial/06_its.html)
- [PyCrown — segmentation d'arbres individuels](https://github.com/manaakiwhenua/pycrown)
- [Effect of slope on treetop detection using a LiDAR CHM](https://www.sciencedirect.com/science/article/abs/pii/S0924271615000581)
- [ESA WorldCover 10 m](https://esa-worldcover.org/en)
