# Une Méditerranée dont on a perdu la carte

> Question (2026-07-27) : *avec ce qu'on vient de décider — 1:1 et aplatissement hybride —
> peut-on théoriquement faire tout le pourtour méditerranéen ?* Et, dans la foulée,
> l'intuition qui compte plus que la question : *« un monde imaginaire mais très inspiré
> du réel de la Méditerranée m'irait bien. »*
>
> Réponse : **non au pourtour entier, et pour une raison qui n'a rien de technique.**
> Mais l'intuition, elle, est exactement la sortie — et elle ne coûte aucun pilier.

## 1. La réponse à la question posée : non, et aucune machine n'y est pour rien

À 1:1, tout tient techniquement (docs 29, 30). Ce qui ne tient pas, c'est **l'arithmétique
du temps humain** :

- **46 000 km de côtes** méditerranéennes. À 5 km/h, c'est ~9 200 h de marche — soit,
  avec une vie de 100 à 200 h jouées (doc 19), **entre 46 et 92 vies pour en faire le
  tour**.
- Barcelone → Troie : 2 700 km, bateau à 10 km/h = **270 h de mer**, quand la décision
  fondatrice du doc 19 (une traversée = 1/4 de vie) en vise **17 à 33**.

L'écart est d'un facteur 10. Ce n'est pas un problème d'optimisation, c'est un mur.
L'intuition exprimée — *« les gens vont mettre des années à traverser »* — est
littéralement exacte.

### Et la vitesse, alors ?
C'était le bon réflexe (doc 31 : *pour changer un temps de trajet, on change la vitesse,
jamais la géométrie*). Mais elle ne sauve pas celui-ci :

- Tenir le budget à 1:1 demanderait un bateau à **~108 km/h**. Un hors-bord.
- Le **cheval** ne rattrape rien : sur longue distance, un cavalier fait 40–60 km/jour
  contre 30–40 pour un marcheur. Le cheval ne fait pas gagner un ordre de grandeur, il
  fait gagner en **charge transportée**. Le vrai gain de vitesse antique, c'est le bateau
  — et il est déjà dans le calcul.
- Multiplier la vitesse par 10 tuerait le doc 18 (la lenteur pleine, l'Odyssée). On
  remplacerait un problème par une trahison.

**La vitesse est un curseur fin, pas un facteur 10.** Elle règle un ressenti, elle ne
change pas un ordre de grandeur.

## 2. La convergence : l'intuition est la sortie du triangle

Le triangle du doc 29 disait : *tout le bassin / le relief à l'échelle du corps / la
traversée en 1/4 de vie — on n'en garde que deux.*

- La compression a été refusée (on veut les vraies pentes) → **« 1+3 » éliminé**.
- Le pourtour entier vient d'être mesuré → **« 1+2 » intraversable**.

Il ne reste que **2+3 : des vrais lieux, dans une géographie recomposée.** Et c'est
précisément ce que décrit *« un monde imaginaire mais très inspiré du réel »*.

Ce n'est donc pas un renoncement de confort : c'est le point où le calcul et le ressenti
arrivent ensemble. Le doc 19 posait la condition — *« à ne considérer que si le réel
compressé s'avère injouable, pas par confort »* — et les docs 29/31 l'ont remplie : le
réel compressé **est** injouable.

## 3. Attention : « monde imaginaire » a deux sens opposés

Tout se joue ici.

| | **(a) Relief inventé** | **(b) Vrai relief, géographie recomposée** |
|---|---|---|
| D'où vient le terrain | bruit + érosion simulée | LiDAR / DEM de lieux réels |
| Chaque lieu est… | une invention | **un vrai endroit** |
| Ce qui est faux | tout | **seulement la carte** |
| Risque de fadeur | **élevé** — un relief généré s'épuise en trois heures | **nul** — c'est l'assurance du doc 29 |
| Pilier « c'est un vrai lieu » | perdu | **intact** |

L'option (a) rompt le pilier fondateur et, pire, retire la seule protection connue
contre la fadeur d'un monde vaste. L'option (b) ne coûte rien du tout.

## 4. Le nom juste

Ce n'est pas « un monde imaginaire inspiré de la Méditerranée ».
C'est :

> **Une Méditerranée dont on a perdu la carte.**
> Tous les lieux sont vrais. Aucun n'est à sa place.

Et c'est **plus fidèle à l'étoile polaire que la reproduction exacte** : celui qui
reconnaît une côte crétoise ne peut jamais en déduire où il se trouve. Le savoir du
monde réel cesse d'être un raccourci — même le géographe est perdu. Exactement ce que
la version calquée n'aurait pas su faire.

Rappel du garde-fou qui rend ça possible : **il n'y a pas de carte dans le jeu** (doc 00).
Le joueur ne peut jamais superposer sa perception à une projection ; le collage est donc
littéralement invisible. Seule contrainte technique, déjà posée au doc 29 : **le monde
reste un plan euclidien unique** — on déplace des masses, on ne plie jamais la métrique,
sinon l'estime au cap se trahit.

## 5. Le contrôle, retrouvé

L'autre inquiétude exprimée — *« ce serait plus contrôlable si je faisais moi-même le
monde »* — est réglée par (b), et sans rien payer :

> **Tu es l'auteur de la géographie. Tu n'es pas l'auteur de la matière.**

Tu choisis quels morceaux existent, dans quel ordre, à quelle distance, quels berceaux
sont voisins et lesquels sont un mois de mer. Tu doses la densité, la difficulté, le
rythme des escales. C'est un travail de **composition** — et c'est exactement le contrôle
recherché.

Ce que tu ne fais pas toi-même, c'est le grain : les falaises, les vires, les ravines,
les criques. Celles-là, tu les prends au réel — et c'est une chance, parce que c'est
précisément la partie qu'aucun humain ne peut inventer à cette échelle sans devenir fade.

## 6. Ce que ça change pour le sud-Ardèche : rien, sauf une chose

Commencer par le sud-Ardèche reste juste, et cette décision ne le modifie pas. Une seule
conséquence d'architecture, déjà signalée au doc 29 et maintenant confirmée :

- **Le pipeline doit être générique dès la première ligne** — une fonction
  « *une bounding box GPS → une tuile de monde* », jamais du code câblé pour Balazuc.
- **Floating origin ou `precision=double` : à décider avant d'écrire ce pipeline**, même
  si le premier monde ne fait que 20 km. C'est le seul point non rétrofittable de tout
  le dossier terrain.

Le reste (k, σ, ce qu'on efface, les essences) reste des curseurs, réglables plus tard.

## Verdict mantra

Aucun pilier n'est entamé, et un s'en trouve renforcé :

- « **Le monde réel rendu à la nature** » : intact — chaque motte de terre est réelle.
- « **Voir beaucoup mais pas précisément** » : renforcé — reconnaître un lieu ne dit plus
  où il est.
- « **Le savoir se transmet, il ne se débloque pas** » : renforcé aussi — la géographie
  du monde devient un savoir qui ne peut venir que d'un autre joueur ou de ses propres
  pieds. Aucun atlas terrestre ne peut le donner.

Le seul risque à surveiller reste celui du doc 29 : **la fadeur**. Le collage la tient à
distance tant que les morceaux sont réels. Le jour où l'on serait tenté de « boucher un
trou » avec du terrain généré, c'est là que le pilier tombe — pas aujourd'hui.

## 7. TRANCHÉ (2026-07-27) — terrain réel non retouché, procédural = habillage

Deux décisions distinctes, à ne pas confondre :

| Décision | Statut |
|---|---|
| **Sculpte-t-on le terrain ?** | **Non.** On prend les terrains réels tels quels. |
| **Les laisse-t-on à leur place réelle ?** | **Ouvert** — le mur des 46 à 92 vies (§1) reste entier. |

La seconde est *reportée*, pas résolue : elle ne se pose que le jour où il y a plus d'une
région. Le sud-Ardèche seul n'en dépend pas.

### Le raccord : on ne colle pas, on sépare
Crainte exprimée — *« ça risque d'être très compliqué d'accrocher des bouts ensemble »*.
Elle est fondée, et elle disparaît :

- **Coller deux terrains par la terre** = raccorder des courbes de niveau, éviter les
  marches, faire coïncider les réseaux hydrographiques. Compliqué, laid, à éviter. C'est
  la vraie faiblesse de l'option « 2 bis », et l'instinct avait raison.
- **Coller par la mer** = gratuit. Deux morceaux ne se touchent jamais : l'eau à z = 0
  fait le raccord toute seule. Une translation, rien de plus.

Le principe qui en découle : **chaque morceau doit être auto-borné.**
- Une **île** est le cas idéal — son bord est donné.
- Une **côte continentale** découpée a des bords « terre » à traiter : les faire plonger
  sous l'eau sur quelques centaines de mètres (le morceau devient une île), ou les borner
  par du relief infranchissable.
- Dans les deux cas c'est un travail **local, par morceau, sans coordination** avec les
  autres. Rien à voir avec un raccord.

Et **retravailler l'intérieur d'un morceau reste permis et facile** (creuser une baie,
relever une crête) : ce qui est difficile, ce n'est pas d'éditer un terrain, c'est d'en
**joindre deux**.

### La division du travail
> **Le réel donne l'ordre. Le procédural donne le désordre.**

Le réel dit *où est la forêt, où est la falaise, où coule l'eau*. Le procédural sème ce
qu'aucune donnée ne contient et qui fait qu'un lieu est vivant : chablis, éboulis, bois
mort, ronces, blocs détachés au pied des parois. C'est la bonne répartition — le désordre
est précisément ce que le procédural fait le mieux, et l'ordre ce qu'il fait le plus mal.

Deux réserves :
- **« On met juste des textures et de la vie » est 90 % du travail du jeu.** Le terrain
  est la partie facile et bornée ; le pipeline d'assets (sprites multi-angles, doc 03) est
  le vrai chantier, et il croît avec le nombre de biomes.
- **Les animaux ne sont pas de l'habillage.** C'est de l'IA et du gameplay, un chantier à
  part (doc 03), borné par la ligne du doc 09 : IA pour le vivant non-humain, jamais pour
  l'humain.

## Statut

**Orientation forte, pas encore actée** pour l'agencement (§2–5) ; **tranché** pour le
terrain et le procédural (§7). Ce doc amende l'option 2 du doc 19 (« réel
compressé »), désormais écartée, et promeut son option 3 sous une forme que le doc 19
n'avait pas envisagée : ni le calque, ni l'invention — **le collage de vrais lieux**.
À confirmer par le test du doc 29 (les dix panoramas), qui reste la seule preuve
disponible que le relief réel porte une identité à lui seul.

## Questions ouvertes

- **Combien de morceaux, et de quelle taille ?** Rejoint « où sont les berceaux de
  spawn » (doc 19) et la densité (doc 10).
- **Le sud-Ardèche est-il un morceau du monde, ou seulement le terrain d'essai ?**
  Le doc 19 aimait que Balazuc soit *réellement* relié à la mer par le Rhône ; le collage
  rend ce lien décoratif. À assumer ou à préserver.
- **Qui compose ?** Un éditeur de monde maison (poser/orienter les masses) — quelques
  semaines d'outil, à budgéter comme outil, pas comme jeu.
- **La mer entre les morceaux est-elle vide, ou parsemée d'îlots** ? Le vide sert
  l'immensité ; quelques cailloux servent la navigation à vue (doc 26).
