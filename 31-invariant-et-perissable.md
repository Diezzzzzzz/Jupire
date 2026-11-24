# L'invariant et le périssable — retravailler le réel sans le trahir

> Trois décisions prises le 2026-07-27, qui referment les questions ouvertes des docs
> 29 et 30 : **(1)** le 1:1 avec un aplatissement vertical léger (« 10° devient 7° ») ;
> **(2)** effacement total des tracés existants, pour observer les **chemins du désir**
> des joueurs ; **(3)** garder l'emplacement des forêts mais **refaire** le couvert —
> « si je reprends le même monde du XXI<sup>e</sup> siècle ça ne sert à rien », le but
> étant de **perdre les utilisateurs**.
>
> Les trois obéissent en fait à une seule règle, énoncée plus bas.

## La règle unique

> **On modifie ce que le temps modifie. On ne touche jamais à ce que le temps ne
> modifie pas.**

Le relief calcaire de l'Ardèche est le même qu'il y a deux mille ans : à cette échelle,
l'érosion est négligeable. C'est un **invariant**. La végétation, elle, n'a rien à voir
avec celle de l'Antiquité — ni même avec celle de 1850. C'est du **périssable**.

Donc : **relief fidèle, couvert recalculé.** Ce n'est pas un compromis d'ingénieur,
c'est ce qui est physiquement vrai. Et ça donne la ligne pour dire non : dérouter le
joueur en déplaçant une falaise, c'est tricher — ça tue le pilier « c'est un vrai lieu »
(et donc l'assurance anti-fadeur du doc 29). Le dérouter en changeant la forêt, c'est
diégétique : le temps a passé, voilà tout.

**Le pipeline n'a le droit de toucher qu'aux couches périssables.**

## 1. La pente — « lisser » cache deux opérations opposées

Attention au mot : il y a deux façons de « lisser », et l'une ruine exactement ce que
le LiDAR à 50 cm te fait payer.

- ❌ **Filtrage spatial** (flou gaussien sur la heightmap) : efface les petits détails —
  ressauts, vires, blocs, ravines — et garde les grandes formes. C'est la mort du grain.
  **Ne jamais faire ça.**
- ✅ **Aplatissement vertical** (`z' = k × z`, k < 1) : garde **tous** les détails,
  réduit tous les dénivelés proportionnellement. C'est ce qu'il faut.

### Pourquoi k = 0,7 (« 10° → 7° ») est un très bon choix

L'aplatissement vertical est **non linéaire en degrés**, et il l'est dans le bon sens :

| Pente réelle | avec k = 0,7 |
|---|---|
| 10° | **7°** |
| 15° | 10,6° |
| 20° | 14,3° |
| 25° (sentier raide) | **18,1°** |
| 35° (à quatre pattes) | **26,1°** |
| 45° | 35° |
| 60° | 50,5° |
| 80° (falaise) | **75,9°** |

Lecture : il **adoucit énormément les pentes qui bloquent la marche** (35° → 26°,
franchissable) et **presque pas les falaises** (80° → 76°, toujours infranchissable).
C'est exactement l'outil recherché : **rendre le monde marchable sans aplatir la
verticalité.** L'inverse exact de ce que fait la compression horizontale du doc 29.

Ce que ça coûte : toutes les hauteurs baissent de 30 %. Les parois de Balazuc (~80 m)
tombent à ~56 m — encore 33 fois ta taille. Le vertige survit.

Et surtout : **c'est une constante, pas un pipeline.** Un seul nombre, réglable en
jouant, sans rien recalculer. À tester entre 0,6 et 0,85 le jour où on marche dans la
gorge.

### AMENDÉ (2026-07-27) — l'hybride existe, et le bon critère n'est pas l'angle

Objection légitime : perdre 30 % sur une falaise est un vrai coût, et on aimerait
n'aplatir que ce qui gêne. Réponse : **oui, c'est faisable — mais le critère n'est pas
le degré, c'est la longueur.**

> Ce qui bloque la marche, ce n'est pas une pente raide, c'est une pente raide **longue**.
> Un ressaut de 3 m à 40° se franchit d'un pas. 800 m à 25° épuise. Une falaise, de
> toute façon, on ne la monte pas — elle n'a jamais été le problème.

Un seuil sur l'angle traiterait donc pareil un talus de 3 m et un versant d'un kilomètre.
Un seuil sur l'**échelle spatiale** vise juste.

#### La méthode : décomposition basse / haute fréquence (deux lignes de code)

```
z_bas  = flou_gaussien(z, σ ≈ 250 m)     # les grandes formes : massif, versant, vallée
z_haut = z − z_bas                        # le détail : falaises, ressauts, vires, blocs
z'     = k × z_bas + z_haut               # on n'aplatit QUE les grandes formes
```

Ce que ça donne concrètement avec k = 0,7 :

| Objet | Sans hybride | **Avec hybride** |
|---|---|---|
| Falaise de 60 m, large de 40 m | 42 m (−18 m) | **~57 m (−3 m)** |
| Versant de 300 m de dénivelé sur 1,5 km | 210 m | 210 m |
| Ressaut de 3 m dans un chemin | 2,1 m | ~3 m |

**La falaise est intégralement en haute fréquence : elle est conservée.** Elle se
retrouve simplement située plus bas dans le paysage (son socle a baissé), mais elle
garde ses 60 m de haut. C'est exactement le souhait : le grand dénivelé s'assagit,
le vertige local reste intact.

Aucun problème de raccord : `z_haut` étant *exactement* la différence, la somme est
continue par construction — pas de marche, pas d'artefact.

#### Astuce de mise en œuvre
`z_bas` est par définition basse fréquence : **inutile de le calculer au demi-mètre.**
On le calcule sur un DEM décimé à 5 m puis on le ré-interpole — 100× moins cher, et
mathématiquement propre. Ça règle aussi le problème des bords : un σ de 250 m
demanderait 1 500 px de marge par dalle à 50 cm, contre 150 px à 5 m.

Deux paramètres à régler en marchant, pas sur le papier : **k** (0,6–0,85) et **σ**
(100–400 m). σ décide de ce qui compte comme « grande forme ».

#### La version savante, si un jour ça ne suffit pas
Le vrai outil est de **remapper le gradient plutôt que l'altitude** — n'adoucir que la
bande 20°–45°, laisser < 20° et > 55° intacts. Problème : un champ de gradient modifié
arbitrairement n'est plus intégrable ; il faut reconstruire le terrain au sens des
moindres carrés, c'est-à-dire résoudre une **équation de Poisson** sur toute la grille.

C'est exactement le problème du **tone mapping HDR** (compresser la dynamique globale
en préservant le contraste local — Fattal et al., 2002), transposé au relief. Résolu et
outillé depuis vingt ans, mais c'est un solveur, pas une ligne de code. **La
décomposition fréquentielle d'abord** : elle capture 90 % du bénéfice pour 1 % de
l'effort.

### AJOUT (2026-07-27, vérifié au proto) — la caméra exagère déjà les pentes ×2

Découvert en comparant le proto à la réalité : **la vue isométrique multiplie les pentes
perçues.** En projection orthographique inclinée de θ, une pente réelle α se lit
`tan(α') = tan(α) / tan(θ)`. À θ = 26,57° (le 2:1 d'AoE2 retenu au doc 06),
`tan θ = 0,5` → **facteur 2**.

Vérifié sur Balazuc : le village est sur un replat à **4,7°** de pente médiane (mesure
LiDAR), et il se lit à l'écran comme 9,3°.

C'est le **même effet mathématique que la compression horizontale du doc 29** — mais
optique, pas géométrique : le monde n'est pas déformé, seule sa lecture l'est.

Deux conséquences :
- **Bonne nouvelle** : le relief se lit sans effort, la verticalité « rend » mieux que
  dans le monde réel. C'est une qualité d'AoE2, pas un défaut.
- **À surveiller** : le joueur verra un monde deux fois plus pentu que celui qu'il
  parcourt. Un versant qui a l'air d'une muraille se monte tranquillement. Cette
  dissonance entre ce qu'on voit et ce qu'on éprouve en marchant est à tester —
  elle pourrait servir l'étoile polaire (l'écart perception/réalité est le sujet du jeu)
  ou simplement agacer.

### Et le 1:1,25 ou 1:1,5 ? — non, c'est le pire des deux mondes

Tentation naturelle : compresser *un peu* en horizontal. Ce que ça coûte :

| Pente réelle | 1:1,25 | 1:1,5 |
|---|---|---|
| 15° | 18,5° | 21,9° |
| 25° (sentier raide) | 30,2° | **35,0°** (quatre pattes) |
| 35° | 41,2° | **46,4°** (escalade) |

Ce que ça rapporte : **rien sur le problème qu'on cherche à résoudre.** La traversée
Barcelone → Troie (2 700 km) tombe à 2 160 km (1:1,25) ou 1 800 km (1:1,5) — soit 216 h
ou 180 h de navigation, quand la cible du doc 19 est de **17 à 33 h**. Il faudrait un
facteur 8 à 15. On est à un ordre de grandeur.

> **Il n'existe pas de zone intermédiaire utile.** Soit on compresse massivement (et le
> relief meurt), soit on ne compresse pas du tout. Le 1:1,25 paie sans rien gagner.

Et si l'objectif n'était pas la Méditerranée mais simplement « raccourcir un peu les
trajets à pied dans la région », alors la réponse est ailleurs et elle est gratuite :

> **Pour changer le temps de trajet, on change la vitesse, jamais la géométrie.**

Passer un marcheur de 5 à 6 km/h produit exactement l'effet d'un 1:1,2 — sans déformer
une seule pente, sans retoucher un seul octet de heightmap, et c'est **réversible en une
ligne**. L'échelle, elle, est destructive et définitive. La vitesse est un curseur, la
géométrie est un engagement.

## 2. Les chemins du désir — et le retournement qui rend l'idée meilleure

**Décision : effacement total** (voir doc 30, stratégie 1). Et l'effacement doit porter
plus loin que les routes : **tout ce qui crée une ligne de moindre effort artificielle.**
En Ardèche, ça veut dire les **terrasses agricoles** — elles quadrillent les versants et
guident le déplacement horizontal aussi sûrement qu'un sentier. Sans elles effacées, les
joueurs suivront des courbes de niveau bâties par des paysans du XVIII<sup>e</sup>.

### Le retournement
Il faut s'attendre à ce que les chemins du désir des joueurs **retombent largement sur
les tracés réels**. Non par fuite de données — parce que les routes réelles ne sont pas
arbitraires : elles suivent les cols, les gués, les lignes de moindre pente. **Mêmes
contraintes physiques, mêmes solutions.**

Ce n'est pas l'échec de l'expérience, c'est son plus beau résultat possible :
*des joueurs qui n'ont jamais vu de carte retrouvent le chemin que des gens avaient usé
avant eux.* Mesurable directement : superposer la carte de chaleur des passages et le
réseau OSM effacé, et regarder le taux de recouvrement.

### Où sera le vrai contraste
Pas dans la géométrie locale — dans le **réseau**. Les routes d'aujourd'hui desservent
des lieux qui n'existeront pas dans le jeu (villages, écoles, exploitations, l'A7 au
loin). Les chemins des joueurs desserviront les lieux **qu'ils auront créés**. Même
tracé de versant, topologie entièrement différente. C'est ça, le contraste à observer.

### Ce que ça exige, et le test des mantra
Il faut la mécanique d'**usure du sol** (le passage tasse, la végétation recule) — une
vraie feature, pas un effet gratuit. Elle passe le test haut la main :

- un chemin usé est une **trace de vrais joueurs**, la seule catégorie d'« autre »
  autorisée avec le joueur en direct (doc 09) ;
- il ne donne aucune certitude : il dit *« des gens sont passés »*, jamais *qui*, *quand*,
  ni *vers quoi* — et il **s'efface** si on cesse d'y passer (l'information se périme,
  doc 06) ;
- c'est **la primitive « inscrire » du doc 23, faite sans le vouloir**. Un chemin est un
  message écrit par les pieds — le premier acte de langage collectif du monde, et le
  seul qu'on ne peut pas mentir.

## 3. La forêt — ne pas retoucher, re-dériver

L'envie : connaître l'emplacement, mais ne pas reprendre le couvert de 2020. La bonne
méthode n'est pas de *retoucher* la carte forestière — c'est de la **recalculer depuis
le relief**, qu'on possède au demi-mètre.

### La végétation potentielle se déduit du terrain
Chaque combinaison (altitude, exposition, pente, distance à l'eau, humidité
topographique) correspond à une communauté végétale d'équilibre connue. Tous ces
paramètres se calculent depuis le MNT :

- **exposition** (adret / ubac) ← direction du gradient ;
- **pente** ← norme du gradient ;
- **humidité topographique** (TWI) ← surface drainée / pente ;
- **distance à l'eau** ← réseau hydrographique.

En Ardèche méridionale, la série est documentée : **chêne vert** omniprésent sur les
adrets secs jusqu'à ~500 m, **chêne pubescent** puis chênes caducs en transition vers
~700 m, **hêtre** en ubac frais et en altitude, **ripisylve** (aulne, frêne, saule) le
long de l'Ardèche. Sur les adrets les plus maigres : végétation basse, genêts, buis.

**Résultat visé : quelqu'un qui connaît Balazuc reconnaît la gorge, le méandre, la
falaise — et pas un seul bosquet.** Perdu et chez lui en même temps. C'est exactement
l'effet cherché, et il est obtenu sans mentir sur rien.

### La donnée de 2020 change de rôle : de source à contrôle
Elle ne dicte plus la forêt, elle la **vérifie** — là où le couvert est ancien et non
planté, le modèle doit retomber dessus. S'il n'y retombe pas, c'est le modèle qui est
faux.

### Le cadeau : la BD FORÊTS ANCIENNES (IGN, gratuite)
L'IGN croise la **carte d'état-major (1820–1866)** avec la BD Forêt V2 et publie une
carte à **trois classes** — et les trois sont exactement les instructions du pipeline :

| Classe | Ce que ça veut dire | Ce qu'on en fait |
|---|---|---|
| **Forêt ancienne** | boisée depuis au moins 1850, jamais défrichée | **garder telle quelle** — c'est le plus proche du naturel qu'on ait |
| **Forêt récente** | recolonisation post-1850 (déprise agricole, plantations de résineux, robinier) | **supprimer**, remplacer par le modèle potentiel |
| **Forêt disparue** | boisée en 1850, défrichée depuis | **remettre** — la donnée te dit où étaient les forêts perdues |

Le choix de l'état-major n'est pas un hasard : 1820–1866 est le **minimum forestier de
l'histoire de France** (~15 % du territoire, contre ~31 % aujourd'hui). Une forêt qui
tenait *à ce moment-là* est une forêt qui n'a jamais été prise. C'est le meilleur proxy
disponible de « ce qui pousse ici quand on laisse faire ».

### Sur l'Antiquité : ne pas y courir
L'idéal exprimé (« dans l'utopie, celui de l'Antiquité ») est un piège, pour deux raisons.

1. **Ce n'est pas le monde de Jupire.** Jupire se passe **après une chute** : ni 2026, ni
   −500, mais *un lieu abandonné depuis longtemps*. C'est plus facile à définir — c'est
   la végétation d'équilibre — et ça se **calcule**, au lieu de se reconstituer.
2. **L'Antiquité méditerranéenne était déjà largement déboisée** par l'homme (navires,
   métallurgie, pâturage) ; la déforestation est antérieure de plusieurs millénaires à
   notre ère, et « la Gaule chevelue » est un mythe. Viser l'Antiquité ramènerait à des
   paysages **pastoraux et cultivés** — l'inverse d'un monde rendu à la nature.

La cible juste n'est pas une date, c'est un **état** : l'abandon.

## Verdict mantra

Les trois décisions vont dans le même sens et renforcent l'étoile polaire :

- **L'aplatissement à 0,7** rend le monde marchable *sans* rendre la verticalité gratuite :
  les falaises restent des falaises, donc le fog en ligne de vue garde son relief, donc
  « monter pour comprendre » survit intact.
- **L'effacement des tracés** retire au monde le seul raccourci qu'il pouvait offrir
  sans qu'on s'en aperçoive : l'itinéraire optimal, servi par le sol lui-même.
- **La forêt recalculée** fait travailler le joueur au lieu de le renseigner, y compris
  celui qui connaît vraiment Balazuc — et c'est peut-être le plus élégant :
  **même la connaissance du monde réel ne donne plus de certitude gratuite.**

Le seul garde-fou à tenir : « perdre les utilisateurs » est un bon objectif **tant qu'il
vient du temps écoulé, jamais de la falsification**. Le jour où l'on serait tenté de
déplacer une crête pour désorienter, c'est le pilier du réel qui tombe — et avec lui la
seule assurance contre la fadeur d'un monde immense (doc 29).

## Questions ouvertes

- **Valeurs de k et σ** : k ≈ 0,7 (0,6–0,85) et σ ≈ 250 m (100–400 m), en mode hybride
  basse/haute fréquence. À régler en marchant dans la gorge — un seul essai réel vaut
  mieux que dix tableaux.
- **σ mérite-t-il d'être variable ?** Un σ unique traite pareil une falaise de gorge et
  un ressaut de plateau. Probablement inutile ; à vérifier seulement si le résultat
  déçoit quelque part.
- **L'aplatissement s'applique-t-il aussi sous l'eau ?** Les fonds contractés changent
  les hauts-fonds et donc les échouages (doc 19). Probablement sans importance, à noter.
- **Les terrasses agricoles : effacées ou gardées en ruine ?** Le doc 30 penchait pour
  les garder, la décision du jour dit de les effacer (elles guident). Mais elles sont
  aussi le plus beau témoignage d'une civilisation tombée. **Piste : les effacer du
  relief (donc de la marche) et n'en garder que la trace de pierre** — on voit le muret,
  on ne bénéficie pas de la terrasse.
- **Le modèle de végétation potentielle : à quelle finesse ?** Trois classes suffisent
  probablement pour le proto (adret sec / versant frais / bord d'eau) ; la série complète
  peut attendre.
- **Vérifier la couverture LiDAR HD sur l'Ardèche** (doc 30) — toujours l'action bloquante
  n°1 du pipeline.
- **L'usure du sol : quelle vitesse d'apparition et d'effacement ?** C'est le réglage qui
  décide si un chemin est une trace vivante ou un monument. Reporté, mais c'est une vraie
  variable de design, pas un détail de shader.

## Sources

- [BD FORÊTS ANCIENNES — IGN Géoservices](https://geoservices.ign.fr/bdforets-anciennes)
- [La carte des forêts anciennes de la France métropolitaine — Observatoire des forêts françaises](https://observatoire.foret.gouv.fr/actualites/la-carte-des-forets-anciennes-de-la-france-metropolitaine)
- [Carte de l'État-Major 1820–1866 — Géoportail](https://www.geoportail.gouv.fr/donnees/carte-de-letat-major-1820-1866)
- [Taux de boisement — Observatoire des forêts françaises](https://observatoire.foret.gouv.fr/themes/taux-de-boisement) (minimum historique ~15 % vers 1830)
- [Les peuplements forestiers en Ardèche — Services de l'État en Ardèche](https://www.ardeche.gouv.fr/Actions-de-l-Etat/Foret-et-filiere-bois/Les-forets-d-Ardeche/Les-peuplements-forestiers-en-Ardeche)
- [Botanique en Ardèche méridionale](https://www.monardeche.com/Botanique-en-Ardeche-meridionale.html) (série chêne vert / chênes caducs / hêtre)
