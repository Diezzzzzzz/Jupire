# L'expansion plutôt que la traversée — et le réglage des vitesses

> **TRANCHÉ (2026-07-27) : les morceaux restent à leur place réelle. Le 1:1 intégral est
> assumé.** Raison donnée : *« que cela prenne 46 à 92 vies fait partie du jeu ; on n'est
> pas obligé de vivre à des endroits cools, on doit se débrouiller pour perdurer ; d'autres
> joueurs pop et vont, à force, s'étendre sur toute la carte. »*
>
> Ce doc acte la décision, dit franchement ce qu'elle coûte, et pose la question des
> vitesses (terre, haute mer, fleuve).

## 1. Le retournement : le monde ne se traverse pas, il se colonise

C'est un changement de modèle, pas un réglage. Jusqu'ici, la taille du monde était
mesurée à l'aune d'**un joueur qui traverse** (doc 19 : la traversée = 1/4 de vie).
Désormais elle se mesure à l'aune d'**une population qui avance**.

Conséquence : *personne* ne fait le tour de la Méditerranée. Ce n'est plus un objectif
raté, c'est le sujet. Le monde cesse d'être un espace à parcourir pour devenir **une
promesse qui ne s'épuise pas**. Personne ne verra Troie — et c'est exactement la
petitesse devant l'immense du briefing.

### Ce que ça renforce
- **Doc 15 (le besoin, pas la récompense)** : *« on n'est pas obligé de vivre à des
  endroits cools »* en est la formulation la plus nette qu'on ait écrite. On s'installe
  où l'on peut tenir, pas où c'est beau. La géographie cesse d'être un catalogue de
  destinations.
- **Docs 08 / 11 / 21 (mortalité, naissances, corps hérité)** : l'expansion donne enfin
  un *sens* à la chaîne des générations. Une vie ne suffit pas à avancer ; c'est la
  lignée qui progresse.
- **Doc 09 (le vide n'est pas un bug)** : ici le vide n'est même plus toléré, il est le
  moteur.

### Le corollaire qui fait toute la beauté du modèle
Dans Jupire, on ne *spawn* pas où l'on veut : on **naît d'un lien** (doc 11), d'un pool
de berceau (doc 21). Donc l'expansion n'est pas « des joueurs qui apparaissent partout » :
c'est une **frontière démographique** qui avance à la vitesse des générations.

> **On ne peut donc pas s'étendre seul.** Fonder un nouveau berceau exige d'être
> plusieurs, et d'y rester assez longtemps pour que des enfants y naissent.
> « La connexion engendre la vie ; l'isolement stérilise » devient une **loi de
> géographie**.

C'est peut-être la meilleure justification qu'on ait trouvée à l'immensité : elle
transforme le pilier social en contrainte spatiale.

## 2. Ce que ça coûte — franchement

### a) La rencontre (l'objection du doc 19, à regarder en face)
Le doc 19 écartait le 1:1 pour une raison qui n'était pas la traversée mais la
**densité** : *« personne ne se croisera jamais »*. Les chiffres :

- Bande côtière habitable ≈ 46 000 km × 20 km ≈ **920 000 km²**.
- À **50 joueurs** connectés : 18 400 km² chacun — un carré de **135 km de côté**.
- À **500 joueurs** : un carré de **43 km** de côté.
- Portée de vue : ~2 km.

Éparpillés, les joueurs ne se croiseraient **jamais**, et le cœur du jeu mourrait de faim.

**Mais la décision prise ne les éparpille pas.** Le spawn concentré (naître d'un lien,
dans un berceau) fait que la situation réelle n'est pas « 50 joueurs sur 920 000 km² »
mais **« 50 joueurs dans une vallée, avec 920 000 km² devant eux »**. La densité locale
est celle d'un village ; l'immensité est un horizon, pas un terrain de dispersion.

→ L'objection du doc 19 tombe **à condition que le spawn reste concentré**. C'est
désormais une contrainte dure du design, pas une préférence : **tout mécanisme qui
laisserait choisir son lieu d'apparition ferait s'effondrer la rencontre.**

### b) 99 % du monde ne sera jamais visité
À assumer sans détour. Avec quelques dizaines de joueurs, l'expansion n'atteindra jamais
l'Italie, encore moins la Turquie. La Méditerranée entière restera un décor lointain
pour toujours.

Ce n'est un problème que si l'on paie pour ce décor. D'où la règle budgétaire :

> **La taille du monde ne coûte que si on la remplit.**
> Terrain réel streamé + habillage procédural = coût quasi indépendant de la surface.
> Tout le budget d'assets va aux berceaux et à leur proche périphérie.

C'est ce qui rend la décision soutenable : elle est chère en *ambition*, pas en *travail*.

### c) Le risque qui reste
Que la frontière n'avance jamais, et que le jeu se réduise de fait à une vallée — avec
un monde immense qui ne sert à rien. Ce ne serait pas grave (une vallée bien vivante
suffit), mais autant le savoir : **l'immensité est un pari sur la durée de vie du jeu**,
pas une feature livrée le premier jour.

## 3. Les vitesses

### Ce qu'un boost peut et ne peut pas faire
Passer la marche de 5 à 7 km/h (la proposition « +2 km/h ») fait gagner **40 %**. Sur les
46 000 km de côtes : 9 200 h → 6 570 h. On passe de 46–92 vies à 33–66. **Un boost ne
change pas un ordre de grandeur, et rien ne le fera.**

Mais ce n'est pas son rôle, et c'est le point utile :

| Type de trajet | Part du temps de jeu | Effet d'un +40 % |
|---|---|---|
| **Local** (le ruisseau, la forêt, le village voisin) | ~90 % | **énorme** — se sent à chaque session |
| **Expansion** (partir vers l'inconnu) | rare, un projet de vie | négligeable |

→ **Le boost terrestre est un réglage de confort, pas de structure.** Légitime, et à
régler au ressenti : +2 km/h est un bon point de départ. Il ne faut simplement pas en
attendre qu'il rende le monde traversable.

### La haute mer : 10 km/h n'est pas un boost de vitesse
Un navire antique file 7–15 km/h par bon vent — donc 10 km/h en pointe est **réaliste**.
Le vrai écart avec l'Antiquité est ailleurs : les navires réels perdaient l'essentiel de
leur temps en **pétole, nuits au mouillage, attente du vent et louvoyage** (moyenne
réelle sur 24 h : ~5 km/h ; une liaison rapide type Rhodes–Alexandrie tenait ~160 km/jour).

> **10 km/h soutenu n'accélère pas le bateau : ça supprime les temps morts.**

C'est la bonne façon de le doser — et ça laisse un levier intact pour plus tard : si l'on
veut *rallonger* les voyages sans ralentir la barque, on réintroduit les temps morts
(pétole, vent contraire) plutôt que de baisser le chiffre. Le monde-acteur du doc 18 est
précisément fait de ça.

### Le fleuve : l'asymétrie est un cadeau
L'intuition d'un boost **moindre** en rivière est juste, et sa vraie raison est meilleure
que le réglage : **un fleuve a un sens.**

- **Descendre** (vers la mer) : rapide et gratuit — le courant fait le travail.
- **Remonter** : très lent et coûteux — rames, halage, attente du vent.

C'est physiquement vrai, et c'est un cadeau de gameplay : le Rhône **descend** vers la
Méditerranée. Partir est facile, revenir est dur. Le fleuve devient une **porte à sens
unique** — exactement l'odyssée, et exactement le doc 18 (le monde comme force qui te
déplace).

### La hiérarchie qui en résulte
Ce n'est pas une liste de nombres, c'est une géographie du déplacement :

| Mode | Vitesse | Ce que ça dit du monde |
|---|---|---|
| Haute mer, vent portant | ~10 km/h | la mer est la seule vraie route |
| Fleuve descendant | rapide, gratuit | partir est facile |
| Cabotage | plus lent (escales, mouillages) | la côte se tisse, elle ne se franchit pas |
| Marche | 5–7 km/h | la terre est lente et coûteuse |
| Fleuve remontant | très lent | revenir est un travail |

## 4. Le garde-fou : vitesse = confort, autonomie = design

Test des mantra : la vitesse ne donne aucune certitude — elle ne révèle rien, ne réduit
aucune distance perceptive, elle réduit la friction. Elle est donc **sans danger**, à une
condition :

> **Ce qui doit limiter le voyage n'est pas la vitesse, c'est le besoin.**

L'eau et les vivres (docs 15 et 19 : *« le ravitaillement est le métronome du voyage »*)
sont ce qui transforme une traversée en odyssée. Tant que l'autonomie force les escales,
on peut être **généreux sur la vitesse sans rien perdre** — la lenteur pleine du doc 18
vient de l'obligation de s'arrêter, pas du nombre de km/h.

→ Régler la vitesse est un travail de confort. Régler l'autonomie est un travail de
design. Ne pas confondre les deux boutons.

## Verdict mantra

La décision tient, et pour une raison qui n'est pas celle qu'on croit. L'immensité à 1:1
ne sert pas « le grand voyage » (il n'aura pas lieu) : elle sert la **petitesse**. Un
monde qu'aucune lignée n'épuisera est la mise en scène la plus littérale de l'étoile
polaire — la distance ne se réduit pas, on n'en grignote qu'un bord, et on meurt avant
la fin.

Deux conditions non négociables l'accompagnent :

1. **Le spawn reste concentré.** C'est ce qui sauve la rencontre. Le jour où l'on
   laisserait choisir son lieu d'apparition, le monde deviendrait un désert social.
2. **On ne paie jamais pour le lointain.** Habillage authoré seulement là où l'on vit ;
   ailleurs, terrain réel nu et procédural. Sinon l'ambition mange le projet.

## Questions ouvertes

- **Vitesse de marche : +2 km/h, à tester.** Attention à la cohérence avec la DA (un
  personnage à 7 km/h trotte — l'animation doit suivre).
- **La vitesse dépend-elle du terrain ?** Une pente coûte plus qu'un chemin plat ; ce
  serait le prolongement naturel de l'aplatissement hybride (doc 31), et ça donnerait
  aux vallées et aux crêtes leur rôle de couloirs naturels — donc aux chemins du désir
  leur vraie logique.
- **Autonomie du bateau** : combien de jours d'eau et de vivres ? C'est **le** vrai
  réglage du voyage, bien avant les km/h.
- **La frontière avance-t-elle vraiment ?** Si aucune lignée ne dépasse jamais la
  première vallée, faut-il un mécanisme qui *pousse* (pression démographique,
  épuisement des ressources locales — doc 15) ou laisse-t-on faire ?
- **Que voit-on du lointain jamais atteint ?** Le mode Regard (doc 26) montrera des
  côtes que personne n'atteindra de sa vie. C'est probablement le plus bel usage possible
  de l'immensité — à creuser.
- **Dérive hors-ligne** (doc 19) : avec un monde 1:1, une nuit de dérive déplace de
  quelques dizaines de km — assez pour perdre sa position, pas assez pour changer de
  monde. Le réglage semble tenir tout seul.
