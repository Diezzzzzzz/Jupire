# Ce que 5 000 joueurs remplissent vraiment — et la zone du premier monde

> Deux questions (2026-07-27) : **(1)** avec 5 000 joueurs à terme, le monde se
> remplit-il ? **(2)** la zone du prototype = Balazuc, Vinezac, Vogüé, et peut-être
> jusqu'à Vallon-Pont-d'Arc, la grotte Chauvet et l'aven d'Orgnac.
>
> Réponses courtes : **non, 5 000 joueurs remplissent ~1 % — et c'est suffisant.**
> Et la zone choisie est magnifique mais **8 fois Skyrim**, avec un piège technique
> précis : ses trois lieux emblématiques sont exactement ceux qu'une heightmap ne peut
> pas représenter.

## 1. Ce que 5 000 joueurs colonisent réellement

D'abord la distinction qui change tout : **5 000 inscrits ≠ 5 000 simultanés.** Le ratio
habituel en MMO est de 3 à 8 % en ligne aux heures de pointe → **150 à 400 connectés**.

Mais le calcul « surface ÷ joueurs » est trompeur : il suppose une répartition uniforme,
que le spawn par lien (doc 33) rend impossible. Le bon calcul est **en villages** :

- 5 000 inscrits → ~1 500 joueurs actifs réguliers.
- Un village viable = 15 à 30 joueurs (doc 10) → **50 à 100 villages**.
- Un village exploite son rayon d'aller-retour dans la journée (3–6 km) → **25 à 100 km²**.

→ **Territoire réellement colonisé : 2 500 à 10 000 km².**

Sur les ~920 000 km² de bande côtière habitable (doc 33), cela fait **0,3 % à 1 %**.

> **5 000 joueurs remplissent à peu près un département français.**
> L'Ardèche fait 5 529 km². C'est l'ordre de grandeur exact.

Pour remplir la Méditerranée, il faudrait ~100 fois plus : **plusieurs centaines de
milliers de joueurs**, soit l'un des plus gros MMO de l'histoire. Autant le dire net :
**le monde ne se remplira pas.**

### Et pourtant 1 % suffit — pour trois raisons
1. **La densité qui compte est locale.** Dans son village et sa région, un joueur croise
   du monde en permanence. Le taux de remplissage global n'a aucun effet sur son
   expérience quotidienne.
2. **50 à 100 villages, c'est des dizaines de frontières culturelles.** Or « le vrai drame
   est à la frontière entre cultures » (doc 02). Le contenu dramatique du jeu ne dépend
   pas de la surface, il dépend du **nombre de voisins**.
3. **L'au-delà reste inépuisable** — ce qui est le sujet même du doc 33.

### La forme que ça donne au monde
Le spawn par lien fait avancer la colonisation en **tache d'huile contiguë** depuis le
berceau, pas en semis éparpillé. Donc les villages seront **voisins**, les contacts
culturels fréquents et proches — et le vide sera **au-delà** de la tache, pas entre les
villages.

> À 5 000 joueurs, ta Méditerranée ressemblera exactement à ce qu'était le monde grec
> archaïque : **un liseré habité, et l'immense inconnu tout autour.**

C'est le doc 19 (berceaux de densité + vide entre) réalisé par la démographie plutôt que
par le placement.

## 2. La zone du proto : superbe, et bien trop grande

Emprise de Vogüé (nord) à l'aven d'Orgnac (sud), de Vinezac (ouest) aux gorges (est) :
**~25 × 12 km, soit ~300 km²**.

Repères :
- **8 fois Skyrim** (37 km², fait par une équipe).
- **2,4 Go** de heightmap brute à 50 cm.
- Vogüé → Orgnac à pied : ~26 km à vol d'oiseau, **8 à 10 h de marche** par le terrain
  réel. Une expédition de plusieurs sessions — dans un *prototype*.

### Mais ce n'est pas un problème, parce que c'est le seul paramètre gratuit
Le pipeline étant générique par décision (doc 32 : *une bounding box GPS → une tuile de
monde*), **agrandir la zone, c'est télécharger plus de dalles.** Rien à refaire.

> **La taille de la zone n'est pas un engagement, c'est un paramètre.**
> Donc on ne commence pas petit par prudence — on commence petit **parce que c'est
> gratuit de grandir.**

Départ proposé : **Balazuc + Vogüé, ~5 × 5 km**. La gorge, le méandre, la falaise, la
rivière — tout ce qui teste la verticalité et le fog en ligne de vue est déjà là. Orgnac
et Chauvet viendront en ajoutant des dalles, le jour où il y a un jeu à mettre dedans.

## 3. Chauvet — le lieu le plus important du dossier, et la règle qui va avec

Mettre la grotte Chauvet dans le monde n'est pas un choix touristique. C'est mettre
**le lieu fondateur du geste que le jeu réinvente** à l'intérieur du jeu :

- doc 23 : « inscrire » est l'une des trois primitives du canal de communication ;
- doc 25 : le vocabulaire se dit en **croquis rupestres** ;
- doc 05 : les grottes / Chauvet étaient déjà dans l'ambiance dès le premier jour.

Des joueurs vont peindre sur des parois pour se faire comprendre. Et il y aurait, dans
leur monde, la caverne où quelqu'un l'a fait il y a 36 000 ans.

### La règle : **la grotte, sans les peintures**
Y placer des fresques donnerait un **modèle** — les joueurs copieraient au lieu
d'inventer, et la langue émergente mourrait sur place (doc 17 : la langue ne se traduit
pas, elle s'invente). Laisser la grotte **vide** est plus fort à tous égards :

> **Le monde offre la paroi, jamais le modèle.**
> La plus belle caverne du monde, parfaite pour peindre — et personne n'y a encore rien
> peint. Les joueurs seront les premiers.

C'est peut-être le plus bel objet du jeu, et il ne coûte rien à fabriquer : c'est un vide.

## 4. Le piège technique : une heightmap ne peut pas faire de grotte

Une heightmap est une fonction `z(x, y)` — **une seule altitude par point**. Donc elle ne
peut représenter **ni grotte, ni surplomb, ni arche**.

Ironie exacte : les trois lieux emblématiques de la zone choisie sont précisément les
trois cas impossibles.

| Lieu | Pourquoi impossible en heightmap |
|---|---|
| **Le Pont d'Arc** | une arche = deux altitudes au même point |
| **La grotte Chauvet** | un vide sous la roche |
| **L'aven d'Orgnac** | un puits qui s'élargit sous la surface |

**Solution, standard et bornée** : ces objets ne sont pas du terrain, ce sont des
**meshes posés sur le terrain** — modélisés à la main, avec leur propre collision. C'est
ce que font tous les jeux pour leurs grottes.

Donc : ce n'est pas un problème de pipeline, c'est **trois assets à modéliser**. Travail
fini, connu, différable. Mais à savoir avant de promettre le Pont d'Arc.

*(Note : l'aven d'Orgnac sert magnifiquement le doc 06 — dans un gouffre, la ligne de vue
est nulle par construction. La verticalité extrême y devient obscurité, sans une ligne de
code spéciale.)*

## Verdict mantra

Rien ici ne menace l'étoile polaire, et une décision la sert particulièrement bien :
**Chauvet vide**. C'est l'exemple parfait de ce que le jeu doit faire — offrir le support
d'un geste sans jamais en donner le sens. Le contraire d'un tutoriel.

Le seul point de vigilance est le vieux risque (briefing, risque n°1) : la zone choisie
est déjà un monde entier, et l'Étape 0 n'est toujours pas faite. La bonne nouvelle est
que ça ne coûte rien de l'admettre — la zone est un paramètre, pas un engagement.

## Questions ouvertes

- **Combien de berceaux au lancement ?** Un seul (tout le monde naît au même endroit,
  densité maximale, une seule culture) ou deux-trois (des cultures distinctes dès le
  départ, donc du contact culturel tout de suite, mais densité divisée) ? C'est la
  décision qui suit directement de la contrainte « spawn concentré » du doc 33.
- **Que se passe-t-il quand un village meurt ?** Si la tache d'huile peut reculer, la
  frontière respire ; sinon elle ne fait qu'avancer. Rejoint doc 12 (village rasé).
- **Chauvet est-elle atteignable dès le premier jour, ou faut-il la mériter ?** Une
  caverne qu'on trouve au bout de dix heures de marche n'est pas la même que celle qu'on
  visite en arrivant.
- **Les trois meshes (Pont d'Arc, Chauvet, Orgnac) : à quel niveau de fidélité ?**
  Relevés réels indisponibles publiquement ; modélisation « à la ressemblance » suffisante ?
