# Proto terrain — Balazuc jouable

## ⚠ À LIRE EN PREMIER — reprise de session (2026-07-27, fin)

La session s'est terminée sur un désaccord de perception : **mes captures montraient
l'eau, l'écran de Rémi non.** Trois symptômes signalés et non résolus :

1. **L'eau invisible** chez lui, visible chez moi.
2. **Des arbres poussent dans l'eau.**
3. **Les rochers du lit ne s'affichent pas.**

### Hypothèse n°1 pour (1) et (3) : le shader
J'avais écrit un `ShaderMaterial` GLSL pour l'eau. **Un shader custom peut échouer à
compiler selon le pilote** (Windows/WSL passe par ANGLE, pas le même que mon Chrome de
contrôle headless) — et il disparaît alors *sans aucune erreur console*.
→ **Déjà fait : le shader est retiré** (`build v12`), l'eau est revenue à un
`MeshBasicMaterial` standard. À vérifier en premier au redémarrage.
Si l'eau réapparaît, la cause est confirmée : tout effet visuel devra être fait en
matériau standard, ou testé sur la machine cible avant d'être gardé.

### Cause certaine pour (2) : le semis ignore le masque hydro
`semis.py` classe le sol par **accumulation d'écoulement**, qui ne détecte quasi rien
sur une petite fenêtre (classe `eau` = 0 % sur toutes les zones générées). Il sème donc
des arbres dans le lit. Le rendu, lui, utilise le **masque BD TOPO** — les deux ne se
parlent pas.
→ **Correctif à faire** : passer `<monde>.hydro.png` à `semis.py` et interdire tout
semis sous le masque (et sur une marge de berge). C'est quelques lignes, et ça supprime
définitivement les arbres dans l'eau.

### Méthode à changer
Je n'ai **pas pu voir ce que voyait Rémi** pendant la majeure partie de la session (mon
navigateur de contrôle était en conflit), et j'ai compensé par des diagnostics Python
hors ligne. Ils étaient justes sur le calcul, mais aveugles sur le rendu — d'où trois
tours à corriger l'eau alors que le défaut venait du terrain, puis du pilote.
→ **Au prochain démarrage : demander une capture d'écran avant de toucher au code.**

### État livré
`build v12` · monde par défaut `world_2400.json` (Balazuc 2,4 km à 1,17 m, la
configuration jugée bonne) · réglages retenus : lissage 5 m · aplatissement 0,85 ·
creusement ×1,1 · eau +0,5 m · inclinaison 36° · filtre ruisseaux 0.



> **État : proto de jeu, avec deux modes — <kbd>G</kbd> bascule.**
>
> | | **Mode libre** (démarrage) | **Incarné** |
> |---|---|---|
> | à quoi ça sert | façonner, régler, inspecter | jouer |
> | caméra | libre, on tire le sol à la souris | suit le personnage |
> | fog | désactivé, on voit tout | **ligne de vue temps réel** |
> | déplacement | clic pour poser le personnage | <kbd>Z</kbd><kbd>Q</kbd><kbd>S</kbd><kbd>D</kbd>, 7 km/h, bloqué au-delà de 40° |
>
> En incarné, le **fog du doc 06 tourne en temps réel** : on ne voit que ce que le
> personnage voit depuis sa position, relief compris. Le versant d'en face se révèle,
> le fond de vallon reste noir, ce qu'on a vu passe en brume désaturée et froide —
> les trois états du doc 06.
>
> Le viewshed réutilise **exactement** le raycast d'horizon écrit pour l'occlusion du
> ciel. Comme prévu, ce code sert deux fois.



> Preuve de chaîne pour les docs 29 → 35 : **des vraies données jusqu'à une image**.
> Séparé du `proto/` (Étape 0), qui ne doit rien recevoir avant le feu vert (doc 13).

## Lancer

```bash
# largeur_m hauteur_m resolution_m [source] [lat] [lon]
python3 pipeline/fetch_dem.py 6400 3000 3.0 lidar 44.5060 4.34195   # Balazuc → Vinezac
python3 pipeline/semis.py
python3 -m http.server 5190                     # puis http://127.0.0.1:5190/
```

La zone n'a pas à être carrée : on cadre la vallée. `fetch_dem.py` récupère les **trois
calques** d'un coup (MNT, orthophoto, hydrographie) depuis le même service sur la même
bbox — alignement garanti, aucun recalage.

Le MNT vient du **WMS de la Géoplateforme en BIL 32 bits** : une grille entière en
**une** requête (4 s), au lieu des 1 800 appels de l'API alti (11 min). Sources :
`lidar` (MNT LiDAR HD) ou `rge` (RGE ALTI). Le WMS plafonne vers 2048 points/côté.

Aucune dépendance : stdlib Python + three.js par CDN. Ni GDAL, ni QGIS, ni Blender.

## Ce que ça fait

**`fetch_dem.py`** — 2,5 × 2,5 km centrés sur Balazuc, pas de 10 m, via l'API
altimétrie de la Géoplateforme (**RGE ALTI**). 313 requêtes de 200 points, throttlées
(l'API renvoie 429 si on la brusque). → `data/dem.json`

**`semis.py`** — applique le doc 31 (*la végétation se re-dérive du relief*) :

1. remplissage des cuvettes (priority-flood) — sinon l'écoulement se bloque sur les
   artefacts d'interpolation (doc 35) ;
2. **pente** et **exposition** (adret/ubac) depuis le gradient ;
3. **accumulation d'écoulement** D8 → le lit de l'Ardèche sort tout seul de la donnée ;
4. **classification** : eau · rocher (pente > 52°) · ripisylve · chêne vert (adret) ·
   chêne pubescent (ubac) · garrigue (adret raide) · pelouse ;
5. **semis Poisson-disc** à rayon variable, graine fixe (`random.seed(1789)`) →
   même graine, même forêt, chez tous les clients et sur le serveur (doc 30).

**`index.html`** — rendu AoE2 : caméra **orthographique dimétrique** (inclinaison
`atan(0.5)`, le 2:1 d'AoE2), rotation **par paliers de 90°**, sprites d'arbres
**générés en canvas** avec leur ombrage cuit (même principe que le pré-rendu Blender du
doc 03), instanciés par `InstancedMesh`.

L'éclairage du terrain est cuit dans les couleurs de sommets, en trois couches :
- **hillshade** — le produit scalaire normale × soleil ;
- **occlusion du ciel** (sky-view factor, 8 directions) — quelle fraction de la voûte
  est visible ? C'est elle qui fait exister les cuvettes : un fond de gorge est sombre
  parce que la paroi lui mange le ciel. Le fond des creux prend en plus la **teinte
  froide** du ciel ;
- **ombre portée** — le rayon vers le soleil (rasant, 24°) est-il coupé par le relief ?

Les deux derniers sont le **même calcul de visibilité que le viewshed du doc 06** : ce
code servira deux fois.

Les curseurs **k** et **σ** appliquent l'aplatissement hybride du doc 31, en direct.

## Résultats mesurés

- Relief réel : **126 → 252 m, Δ 126 m** sur 1,8 km. Pente médiane 8°.
- **La résolution décide de l'existence des falaises** :

  | Pas du MNT | Pente max | Ce qu'on voit |
  |---|---|---|
  | 10 m | 75° | la paroi est étalée sur 1,5 cellule → un talus |
  | **3 m** | **84°** | cannelures, ressauts, vraie paroi |

  À 10 m, une falaise de 60 m sur 15 m de large ne *peut pas* exister dans la donnée.
  Ce n'est pas un défaut de rendu, c'est de l'échantillonnage.
- Classes : chêne vert 60 %, chêne pubescent 31 %, garrigue 4 %, ripisylve 4 %,
  rocher 1 %, eau 1 %.
- **62 493 sprites** semés (100/ha), 3,6 Mo de JSON.
- **L'aplatissement hybride est vérifié** :

  | k | Δ avec hybride | Δ si uniforme |
  |---|---|---|
  | 1,0 | 131 m | 131 m |
  | 0,7 | **110 m** | 92 m |
  | 0,4 | **91 m** | 52 m |

  À k = 0,4 on garde 91 m de dénivelé au lieu de 52 : les falaises survivent à
  l'aplatissement, les grandes ondulations non. **Exactement ce que prévoyait le doc 31.**

## Le gain de raideur (curseur « raideur des falaises »)

Constat au proto : même à 1,17 m avec le vrai LiDAR HD, les falaises paraissent molles.
Diagnostic en trois temps :

1. **Ce n'est pas la source.** À 1 m, LiDAR HD et RGE ALTI donnent la même pente max
   (87,2° vs 86,3°). Les parois *sont* dans la donnée.
2. **C'est que Balazuc est majoritairement doux** — pente médiane 8°. Les vraies parois
   sont des accidents rares et étroits, noyés dans le lissage du maillage.
3. **Et une heightmap ne peut pas faire d'à-pic** : elle relie ses points par des rampes.
   *AoE2 lui-même ne fait pas ses falaises avec sa heightmap* — son terrain monte par
   paliers et les falaises sont des **objets** avec une face verticale dessinée.

D'où le curseur : `z' = k·(grandes formes) + g·(détail)`. C'est le mécanisme du doc 31,
**utilisé dans l'autre sens** — `k < 1` assagit la marche, `g > 1` redresse les ruptures.

Piège rencontré, et sa leçon : à `g = 2,6` avec la pente mesurée sur **une cellule**
(1,17 m), tout le terrain se hérisse d'aiguilles — le gain amplifie le bruit de mesure
autant que les falaises. Corrigé en mesurant la pente sur **8 m** :

> Une vraie falaise est raide **sur une distance** ; le bruit est raide sur un pixel.
> C'est exactement la leçon du doc 31 : le bon critère est la longueur, pas l'angle.

Réglage qui marche : **g ≈ 2,0, pente évaluée sur 8 m, seuil 28°→50°.**

### Et le garde-fou
Le gain **exagère le relief réel** : le terrain n'est plus exactement celui de Balazuc.
La ligne à tenir (précision au doc 31/32) :

> Une transformation **uniforme et paramétrique** (k, σ, g) préserve « c'est un vrai
> lieu » — tous les points subissent la même règle. Une **édition locale à la main** ne
> le préserve pas. C'est ça, la vraie frontière — pas « toucher ou ne pas toucher ».

## L'eau — elle ne s'ajoute pas, elle se **détecte**

Trois tentatives, et c'est la troisième qui était juste :

1. **Plan horizontal à `min(terrain) + h`** → l'eau n'apparaissait qu'aux bords : le point
   le plus bas de la zone n'est pas dans le lit (le creusement des gorges en avait créé
   un plus bas ailleurs).
2. **Nappe suivant le fond de vallée** (minimum local + hauteur) → des flaques dans tous
   les talwegs secondaires, toujours rien dans l'Ardèche.
3. **La bonne** : le doc 35 avait déjà la réponse et je ne l'avais pas appliquée —
   **le laser ne traverse pas l'eau.** L'IGN reconstruit la *surface* de la rivière
   comme un plan à partir de points virtuels. Le lit n'est donc pas creusé :
   **la nappe est déjà dans le MNT**, sous la forme d'une large zone anormalement plate
   et basse.

Mesure sur Balazuc qui confirme sans ambiguïté :

| Tranche d'altitude | Cellules à moins de 0,7° |
|---|---|
| **126–130 m** | **4 552** |
| 186–198 m (le plateau) | ~1 950 au total, réparties sur 6 tranches |

Dix fois plus de plat dans une seule tranche de 4 m : c'est l'Ardèche, et rien d'autre.

D'où `detecterEau()` : chercher le mode des altitudes plates dans le tiers inférieur du
relief. Le curseur ne règle plus un niveau absolu mais un **écart au niveau détecté** —
il reste utile parce que l'aplatissement (`k`) et le creusement (`gain`) déplacent les
altitudes.

> **Leçon générale : ce qui est déjà dans la donnée ne doit pas être reconstruit.**
> Deux des trois tentatives ont échoué pour avoir voulu *fabriquer* ce qui était mesuré.

**Et une rivière descend, et serpente.** Deux tentatives de plus ont échoué :
un **plan incliné** (moindres carrés) marche sur un tronçon droit mais déborde dès qu'il
y a un méandre ; une **nappe propagée** depuis les points bas noie les plaines.

### La vraie cause : je devinais la rivière au lieu de la connaître
Le test « plat et bas » n'attrape pas *la rivière* — il attrape **toutes** les zones
plates et basses : terrasses alluviales, gravières, plages de galets, champs de fond de
vallée, routes. D'où les débordements et les fausses crues.

**Correctif : le vrai tracé.** La BD TOPO hydrographie de l'IGN
(`IGNF_HYDROGRAPHY.HYDROGRAPHY`) est servie par le **même WMS sur la même bbox** — donc
alignée au pixel près sur la grille. Chargée en PNG transparent, elle donne un masque
`eau / pas eau` exact. Le niveau est pris comme le **minimum du terrain sous le tracé**
dans chaque maille (le trait déborde un peu sur les berges, qui sont plus hautes), et
lissé une seule fois le long du cours — **aucune propagation aveugle**.

`fetch_dem.py` récupère maintenant les trois calques d'un coup : MNT, orthophoto,
hydrographie. Même service, même emprise, alignement garanti.

> Troisième fois que le même réflexe se paie : **ce qui existe en donnée ne doit pas être
> deviné.** Le relief pour le relief, la BD TOPO pour l'eau, l'orthophoto pour vérifier.

## La vue isométrique exagère les pentes d'un facteur 2

Observation au proto : *« on dirait que le village est en pente »*. Mesure sur la donnée
brute au cœur du village : **pente médiane 4,7°**, profil est-ouest 178 → 194 → 197 → 195.
**Le village est bien sur un replat.** Ce n'était donc ni la donnée ni les réglages.

C'est la **projection** :

> En orthographique inclinée d'un angle θ, une pente réelle α apparaît à l'écran comme
> `tan(α') = tan(α) / tan(θ)`.
> À θ = 26,57° (le 2:1 d'AoE2), `tan θ = 0,5` : **toutes les pentes sont perçues deux
> fois plus fortes.** Le replat du village à 4,7° se lit comme 9,3°.

Ce n'est pas un bug : AoE2 fait exactement pareil, et c'est même une de ses qualités —
le relief se lit d'un coup d'œil. Mais il faut le savoir, parce que c'est **le même
effet mathématique que la compression horizontale du doc 29** (`tan` multiplié par un
facteur) — sauf qu'ici il est *optique*, pas géométrique : le monde n'est pas déformé,
seule sa lecture l'est.

Le curseur **Inclinaison caméra** permet de le vérifier : il affiche le facteur
d'exagération, et à 45° il indique « fidèle » (`tan 45° = 1`).

### L'arbitrage, et il n'a pas de bonne réponse
On ne peut pas avoir en même temps la perception fidèle des pentes et l'angle d'AoE2 :

| Inclinaison | Pentes perçues | Ce qu'on gagne / perd |
|---|---|---|
| 26,6° (AoE2) | **×2,0** | le look, les faces de falaise bien lisibles (l'argument du doc 06) |
| 35° | ×1,4 | compromis |
| **40°** | **×1,2** | quasi fidèle, encore un peu de face |
| 45° | ×1,0 | fidèle, mais vue plongeante — la verticalité se lit mal |

À noter : l'angle du doc 06 avait été choisi *pour* voir les faces de falaise.
L'exagération ×2 n'est donc pas un accident, c'est le prix de ce choix.
**Jugé au proto : la dissonance voir-raide / marcher-facile agace.** Retenu pour l'instant :
**40°** (×1,2).

## Des falaises vraiment abruptes — le lissage était le coupable

Retour au proto : *« on glisse tout doucement sur une courbe, le bord des falaises
devrait être plus droit »*. Cause : **le lissage à 3 m que j'avais ajouté était un flou
gaussien**, et un flou moyenne tous les voisins — il enlève le grain de mesure, mais il
arrondit aussi le sommet et le pied des falaises, c'est-à-dire précisément ce qui fait
qu'une falaise est une falaise.

Trois corrections, dans l'ordre d'importance :

1. **Filtre bilatéral au lieu de gaussien.** Il pondère aussi par l'écart d'altitude :
   un voisin 20 m plus bas, de l'autre côté de l'arête, ne compte pas. Le bruit part,
   les ruptures restent franches. *C'est le fix principal.*
2. **Demi-gain sur les bosses, là où c'est déjà raide.** Le gain ne s'appliquait qu'aux
   creux (pour éviter les pics) : la falaise s'approfondissait, mais son bord restait
   arrondi. Il agit maintenant à 50 % sur les bosses, modulé par `RAIDE` — qui vaut 0
   sur le plateau, donc **aucun pic ne pousse**, mais l'arête du sommet se redresse.
3. **Seuil de raideur resserré** : 30°→42° au lieu de 28°→50°. Un seuil large donne un
   dégradé mou ; on veut une rupture, pas une courbe.

Réglage obtenu : relief Δ 161 m (contre 97 m réels), pentes max 87°, bord de falaise
franc. **C'est une exagération assumée de +65 %** — dans la règle du doc 31
(transformation uniforme et paramétrique), mais à surveiller.

## Comparer avec la réalité — <kbd>O</kbd>

L'**orthophoto IGN** de la même emprise (couche `ORTHOIMAGERY.ORTHOPHOTOS`, même WMS,
même bbox) se plaque sur le terrain 3D. C'est le seul moyen honnête de vérifier que le
relief, l'échelle et les réglages correspondent au vrai lieu — et de contrôler que la
rivière détectée est bien là où elle coule.

Elle rend aussi visible, d'un coup d'œil, tout ce que le doc 30 prévoit d'effacer :
le village, les routes, les vignes, le pont.

## Jusqu'où on peut agrandir — mesuré, pas estimé

| Zone | Résolution | Cellules | `world.json` | Recalcul | Mémoire |
|---|---|---|---|---|---|
| 1,2 × 1,2 km | 1,17 m | 1,0 M | 12 Mo | **2,0 s** | ~300 Mo |
| 2,4 × 2,4 km | 1,17 m | 4,2 M | 48 Mo | **7,8 s** | **733 Mo** |
| **6,4 × 3,0 km** (Balazuc→Vinezac) | **3,13 m** | 2,0 M | 31 Mo | **3,3 s** | **295 Mo** |
| 5 × 5 km à 1,17 m (extrapolé) | 1,17 m | 18 M | ~210 Mo | ~33 s | ~3 Go → **impossible** |

> **19,2 km² tournent plus vite que 5,8 km².** Au seul prix de passer de 1,17 m à 3,13 m.
> C'est la démonstration en vrai de ce que le doc 29 annonçait : **la résolution coûte
> plus cher que la surface.**

### Le triangle, et le sélecteur de monde
Agrandir ne se paie pas en fluidité mais **en finesse** — et ça se voit tout de suite
(falaises molles, lit de rivière mal résolu). Surface × finesse × fluidité : on n'en a
que deux. D'où trois mondes livrés, un par usage, choisis dans l'UI :

| Monde | Surface | Pas | Cellules | Recalcul | Mémoire |
|---|---|---|---|---|---|
| **Balazuc seul** | 1,4 km² | **1,17 m** | 1,0 M | 2,0 s | 300 Mo |
| **Balazuc→Vinezac fluide** | 38 km² | 4,0 m | 2,4 M | **1,6 s** | 412 Mo |
| **Balazuc→Vinezac fin** | 38 km² | **2,2 m** | 7,9 M | 8,3 s | **1,4 Go** |

C'est le **streaming par tuiles du doc 35 en tout petit** : on ne peut pas avoir la
finesse et l'étendue, donc on charge celle dont on a besoin.

### Deux optimisations qui ont repoussé le mur
1. **Occlusion et ombres calculées sur grille décimée (÷3) puis interpolées.** Elles sont
   basse fréquence par nature — les calculer à pleine résolution était du gâchis.
   **2 641 ms → 630 ms**, différence invisible à l'œil.
2. **Mosaïque WMS.** Le service plafonne vers 2048 px par côté ; on découpe l'emprise en
   tuiles et on recolle. C'est ce qui débloque la haute résolution sur grande surface
   (2 545 × 3 091 en 2×2 tuiles).

Le goulot est maintenant le **filtre bilatéral** (5 860 ms sur 7,9 M) — et lui doit
rester à pleine résolution, puisque son rôle est justement de préserver les arêtes fines.
Le décimer reviendrait à réintroduire le flou qu'on a passé du temps à supprimer.

Détail du recalcul sur 2,4 km :

| Étape | Temps |
|---|---|
| ombrage (occlusion + ombres portées) | 4 555 ms |
| filtres (bilatéral + basse fréquence + raideur) | 3 170 ms |
| eau | 55 ms |
| **maillage (GPU)** | **46 ms** |
| **arbres (GPU)** | **19 ms** |

> **Le rendu est gratuit. Tout le coût est en calcul JavaScript mono-thread, une seule
> fois.** Une fois le terrain calculé, marcher et regarder reste fluide quelle que soit
> la taille. Ce qui rame, ce sont **les curseurs** — pas le jeu.

C'est exactement ce que le doc 29 annonçait : le mur n'est ni le GPU ni le stockage.

**Limite pratique de cette architecture : ~3 km à 1,17 m.** Au-delà, dans l'ordre :

1. **Baisser la résolution loin du joueur.** 1,17 m est du luxe sur un plateau ; à 2,5 m
   le coût est divisé par 4,5 pour une perte invisible hors des falaises.
2. **Précalculer l'ombrage en Python** et le livrer dans `world.json`. Les curseurs
   servent à *trouver* les réglages ; une fois trouvés, le client n'a plus qu'à afficher.
   C'est le gros du coût qui disparaît.
3. **Format binaire** au lieu de JSON : 48 Mo → 17 Mo.
4. **Streaming par tuiles** (doc 35) — la vraie réponse, et le seul chemin vers des
   dizaines de km.

## Ce que ça prouve (et ce que ça ne prouve pas)

✅ La chaîne complète tourne, sans outillage lourd, en quelques minutes.
✅ L'Ardèche apparaît **sans être dessinée** : elle sort de l'accumulation d'écoulement.
✅ L'adret/ubac produit une répartition de végétation crédible depuis le seul relief.
✅ L'aplatissement hybride fonctionne comme la théorie le disait.

❌ Ce n'est **pas** une réponse au test des dix panoramas (doc 29) : la question
« le relief réel porte-t-il une identité à lui seul ? » reste ouverte.
❌ Ce n'est pas le jeu, et ça ne remplace pas l'Étape 0.

### ❌ Et surtout : la vue AoE2 ne donnera JAMAIS l'encaissement

Constat fait en regardant le proto (2026-07-27). On peut beaucoup améliorer la
**lisibilité** du relief — résolution, occlusion, ombres portées, éboulis — et on l'a
fait. Mais vu de 26° au-dessus, on **domine** la cuvette : impossible d'être écrasé par
une paroi qu'on regarde d'en haut. Le vertige exige de lever les yeux.

C'est exactement ce que le **doc 26** avait nommé : *« l'horizon manquant de la vue
AoE2 »*, d'où la 3ᵉ bascule SOL / REGARD / CIEL. Le ressenti au proto confirme le design
écrit avant lui.

→ **Le prochain proto qui compte pour cette question n'est pas celui-ci, c'est le
panorama du doc 26.** Et il réutilisera le raycast d'horizon déjà écrit ici
(`skyView` / `ombres`).

## Limites connues, à corriger dans cet ordre

0. ~~**Le réseau hydrographique ne se déduit pas d'une petite fenêtre.**~~ → **RÉSOLU
   autrement, et la vraie explication est meilleure. Voir « L'eau » ci-dessous.**
   (Reste vrai pour l'accumulation d'écoulement : L'accumulation
   d'écoulement ne voit que le bassin versant *dans la zone chargée* : sur 1,2 km on ne
   draine que 144 ha, alors que l'Ardèche en draine 200 000 à Balazuc. Résultat, la
   rivière est marginale à 1,2 km et nette à 2,5 km. **Correctif : prendre le réseau
   dans OSM (`waterway`) comme le prévoyait le doc 03**, et ne garder l'accumulation
   que pour les talwegs locaux.
1. **Densité** : 100 sprites/ha sature de près (couronnes recouvertes). Le curseur ouvre
   à 55 %, ce qui est plus juste. À reporter dans `DENSITE` si ça se confirme.
2. **Répartition déséquilibrée** : 60 % de chêne vert. Les seuils de `classer()`
   (chaleur, TWI) demandent un calage — c'est du réglage, pas de la structure.
3. **Rocher encore pauvre** : les éboulis existent (82 % de blocs sur la classe rocher)
   mais le rocher ne fait que 1 % de la zone — donc peu visible. Le seuil de pente
   (52°) qui déclenche la classe ROCHER est sans doute trop haut à 3 m.
4. **Pas d'effacement des routes** (doc 30) : le RGE ALTI les contient encore.
   Peu visible à 3 m, criant à 50 cm.
5. **Sprites générés au trait** : suffisant pour juger la silhouette et l'échelle, très
   loin du pré-rendu Blender du doc 03.
6. **Tri de profondeur** : `alphaTest` seulement, pas de tri par distance. Tient à cette
   densité, cassera avec des sprites plus grands.

## Repères

Un humain de 1,70 m est posé au centre de la vue (capsule claire) — c'est l'étalon
d'échelle. Les arbres font 9 à 16 m, soit 5 à 9 fois sa taille.

Console : `vue(x, z, portée)` pour se déplacer, `repere()` pour trouver le point le plus
bas et la pente la plus forte.
