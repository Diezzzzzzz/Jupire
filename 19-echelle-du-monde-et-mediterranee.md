# Échelle du monde — la Méditerranée de Jupire

> L'envie : un monde **gigantesque, ultra immense, limite trop**, où le voyage est
> une vraie aventure très longue, avec plusieurs régions vivantes — côtes espagnoles,
> Italie, îles grecques, côtes turques, Afrique du Nord. Question posée : à quelle
> échelle reproduire la Méditerranée ? 1:1 ? 1:24 ? Ou inventer son propre monde ?
> **Statut : une décision fondatrice prise (le voyage d'une vie, ci-dessous) ;
> le reste = questions ouvertes.**

## Reformulation : l'échelle n'est pas un choix esthétique

L'échelle est la **conséquence** de deux variables de design, pas un ratio qu'on
choisit dans l'absolu :

1. **La durée réelle (en heures de jeu) de la plus longue traversée voulue.**
2. **La densité de rencontre** : à quelle fréquence croise-t-on un humain ?

Loi d'échelle : `taille du monde = vitesse du bateau × durée max de voyage voulue`.
On choisit le *ressenti*, l'échelle en découle.

## Les ordres de grandeur (voilier ~10 km/h, vitesse antique réaliste)

Méditerranée utile (Espagne → Turquie) ≈ 3 000 km. Repères :

| Échelle | Marseille → Athènes (~1 500 km) | Île à île, Cyclades (15–40 km) | Monde E-O |
|---|---|---|---|
| **1:1** | ~150 h de navigation réelle | 1,5 à 4 h | 3 000 km |
| **1:5** | ~30 h (une expédition multi-sessions) | 20–50 min | 600 km |
| **1:10** | ~15 h | 10–25 min | 300 km |
| **1:24** | ~6 h | 4–10 min | 125 km |

Lecture : au **1:1**, une traversée = 150 h réelles — même « limite trop » a une
limite : quasi personne ne la fera, et surtout **personne ne se croisera jamais**
(le cœur du jeu meurt de faim). Au **1:24**, la Grèce est à une soirée de Marseille —
grand, mais plus « limite trop ». La zone du ressenti Ulysse est probablement
**1:5 à 1:10** : la grande traversée = une expédition de plusieurs sessions
(10–30 h réelles), le cabotage entre îles = le rythme d'une session.

À croiser avec la **permadeath** (doc 08) : une vie = N saisons. Le grand voyage
doit-il tenir dans une vie ? Un voyage qui *coûte* une vie est très Ulysse — mais
c'est une décision, pas un accident d'échelle.

## DÉCISION : le voyage d'une vie (l'étalon du monde)

**Une grande traversée (type Barcelone → Troie) = 1/4 d'une vie, escales comprises.**
L'aller-retour = la moitié d'une vie. Un personnage qui ne fait quasi que du bateau
peut accomplir **3-4 grandes traversées dans sa vie** — c'est l'archétype du grand
marin, celui qui lie les civilisations. « Le voyage d'une vie » devient littéral.

Conséquences en chaîne :

- **La vie se mesure en temps joué** (cohérent docs 08 « saisons jouées » et 12
  « le perso se repose hors-ligne ») → le ratio 1/4 vaut pour tous les joueurs,
  quel que soit leur rythme réel de sessions.
- **L'arithmétique** : soit `L` = durée d'une vie en heures jouées (l'étalon encore
  ouvert du doc 08). Traversée = `L/4`, dont ~2/3 de navigation pure (le reste :
  escales, ravitaillement, aventures — ratio à régler). Barcelone → Troie ≈ 2 700 km
  réels par les côtes, bateau ~10 km/h :
  - `L = 100 h` → traversée 25 h, ~17 h de mer → ~170 km monde → échelle ≈ **1:15**
  - `L = 200 h` → traversée 50 h, ~33 h de mer → ~330 km monde → échelle ≈ **1:8**

  → L'échelle atterrit d'elle-même dans la bande **1:8 – 1:15**. La dernière
  variable libre est `L` : **fixer la durée d'une vie fixe la taille du monde.**
- **Le ravitaillement = le métronome du voyage.** On ne traverse pas d'une traite :
  l'autonomie du bateau (eau, vivres) **force les escales**, et les escales sont les
  aventures — chaque île d'Ulysse est une histoire parce qu'il *doit* s'y arrêter.
  Pile le doc 15 : la motivation par le besoin, jamais par la récompense. C'est
  l'autonomie limitée qui transforme une traversée en odyssée.
- **Deux archétypes marins** (prolonge doc 16) : le **caboteur** — marchande d'île
  en île, rythme d'une session, tisse une région ; le **grand voyageur** — traverse
  le monde 3-4 fois dans sa vie, pollinise les civilisations entre elles.
- **Mourir au loin** : celui qui meurt à Troie laisse sa trace (doc 08) à un monde
  de chez lui — sa tombe est une énigme pour ceux qui la trouvent, une légende pour
  ceux qui l'attendaient. La permadeath et le voyage se renforcent.

## Le vrai arbitrage : immensité vs rencontre

L'immensité sert l'étoile polaire (distance ✓). Mais le cœur est « tendre la main
par-dessus » — un monde si grand qu'on n'y rencontre personne le trahit. Résolution :

**Des berceaux de densité, et l'immense vide entre.** Les régions rêvées (Espagne,
Italie, Grèce, Turquie, Afrique du Nord) = **zones de spawn distinctes** → chacune
développe sa culture et sa langue en quasi-isolement. Entre elles : la mer, vraiment
vide, vraiment longue. Le voyageur qui traverse est celui qui met les cultures en
contact — le premier contact du doc 02, à l'échelle des civilisations. L'immensité
n'est pas là pour être *remplie* : elle est la distance entre les mondes.

## Les trois options

1. **Méditerranée réelle 1:1** — les données existent (voir technique) mais tue la
   rencontre. Non, sauf à viser une simulation plus qu'un jeu.
2. **Méditerranée réelle compressée (1:5–1:10)** ⭐ — on échantillonne le vrai relief
   et on le compresse : les îles gardent leurs *formes*, les lieux restent
   reconnaissables (« ça, c'est la Crète »), le pilier **monde réel** survit au
   changement d'échelle. Bonus de cohérence : Balazuc est *réellement* relié à la
   Méditerranée (Ardèche → Rhône → delta → mer, ~150 km réels). L'horizon du doc 18
   se prolonge sans retcon : le berceau ardéchois débouche sur la grande mer.
3. **Monde inventé « remanié »** — liberté totale de dosage, mais **rompt un pilier
   fondateur** (le monde réel rendu à la nature, la poésie du « c'est un vrai lieu »).
   À ne considérer que si le réel compressé s'avère injouable — pas par confort.

Variante à étudier pour l'option 2 : **échelle à deux étages** — lieux de vie presque
riches/denses (échelle locale fine), liaisons (mer, plaines vides) plus compressées.
C'est ce que font implicitement beaucoup de mondes de jeu ; à tester contre le malaise
de l'incohérence physique.

## Technique — recadrage (réflexe doc 09 : la peur est plus grosse que le mur)

- **Les données mondiales sont libres** : Copernicus GLO-30 (relief 30 m, toute la
  planète), EMODnet/GEBCO (bathymétrie méditerranéenne). Le pipeline MNT existant
  (IGN → terrain) se généralise.
- **La mer est le biome le moins cher du jeu** : plate, procédurale, sans sprites de
  végétation. Un monde à 70 % de mer est *plus léger* qu'un monde à 70 % de forêt.
- **Le streaming résout la taille** : on ne charge que les tuiles autour du joueur.
  Flight Simulator streame la planète 1:1 ; Sailwind (un seul dev) fait vivre des
  traversées d'heures entre archipels. Godot n'a rien d'incompatible.
- **Le serveur d'un monde vaste mais creux est facile** : l'interest management est
  trivial quand 95 % du monde est vide. La densité coûte, pas la surface.
- **Le vrai chantier** : pipeline de tuiles + navigation/météo en mer + bateaux
  (nouvel axe art/physique). Gros, mais borné et différable.

## Garde-fou anti-rêve (risque n°1 du projet)

Rien de tout ceci n'entre dans l'Étape 0. Le prototype reste le cahier du doc 13 ;
la Méditerranée est l'étoile lointaine qui oriente les choix d'architecture (pipeline
de terrain *générique*, pas codé en dur pour Balazuc) — pas un chantier à ouvrir.

## Questions ouvertes

- **`L`, la durée d'une vie en heures jouées** — désormais LA variable maîtresse :
  elle fixe la traversée (L/4) donc la taille du monde. (Rejoint la « décision-clé »
  du doc 08 ; le voyage vient d'en resserrer l'enjeu.) Précision doc 20 : `L` est
  un **horizon** (vie complète jusqu'à la vieillesse), pas une durée garantie —
  le monde tue avant, et le voyage est un pari sur sa propre durée.
- **Ratio navigation / escales — principe posé** : pas un ratio d'heures, une règle
  de contenu : **chaque escale doit être assez longue pour vivre une aventure sur
  l'île.** L'autonomie du bateau (eau, vivres) se règle pour produire ça. Reste à
  doser en prototype.
- **Déconnexion en mer — orientation posée** (sujet plus vaste à creuser) : plutôt
  la **dérive** que le « rejoint le port le plus proche » — l'auto-navigation serait
  un raccourci gratuit (le monde résout ta position pour toi), la dérive prolonge le
  monde-acteur (doc 18) : vent et courant te déplacent pendant l'absence, tu te
  réveilles au large d'une côte que tu ne reconnais pas — la dérive d'Ulysse endormi.
  Borne doc 12 : la dérive **déplace mais ne tue jamais** (pas de naufrage hors-ligne ;
  au pire échoué quelque part). Perte de position = perte de lieu, autorisée ;
  perte de vie hors-ligne, jamais.
- **Échelle uniforme ou à deux étages** (lieux fins / liaisons compressées) ?
- **Vitesse des bateaux** : réaliste (~10 km/h) ou levier de réglage de l'échelle ?
- **Balazuc garde-t-il son 1:1** au milieu d'un monde compressé, ou tout le monde
  passe-t-il à l'échelle commune ?
- **Où sont les berceaux de spawn** et combien, pour que chaque culture soit viable
  (densité doc 10) sans que la mer cesse d'être vide ?
- **L'aval s'ouvre-t-il progressivement** (le monde grandit avec ses cultures) ou
  tout est-il là dès le début, simplement hors de portée ?
