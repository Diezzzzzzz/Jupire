# Étape 0 — le cahier du prototype

> La fondation conceptuelle est complète (docs 00→12). Le risque n°1 désormais = rêver
> sans fin. Prochaine action = PROUVER LE NOYAU. Ce doc est le « go build this ».

## Le test

**Deux inconnus se comprennent-ils sans un mot — et est-ce *joyeux* ?**

C'est l'épreuve de l'âme de Jupire. Si ça marche, tout le reste mérite d'être bâti. Si
c'est laborieux, on l'apprend en une semaine (pas en un an) et on itère sur le canal.

## Le setup minimal

- **Scène** : une pièce plate et vide. PAS de terrain, PAS de Balazuc, PAS de fog. Deux
  capsules. (Godot, API multijoueur haut niveau — ou deux fenêtres en local.)
- **Le canal de communication** : une **palette de 6 symboles abstraits** affichables
  au-dessus de la tête. **AUCUN texte.** Bonus si le temps : pointer une direction,
  prendre/poser un objet.
- **La tâche (asymétrique, force à communiquer)** :
  - Ex. A : A possède 3 objets ; B veut un objet précis mais ne peut que *montrer* lequel.
  - Ex. B : B sait où un objet est caché et doit *guider* A jusqu'à lui.
  - L'asymétrie d'information **oblige** à inventer du sens.

## Ce qu'on observe

- Des conventions **émergent**-elles entre les deux joueurs ?
- Le moment « on s'est compris ! » provoque-t-il une **étincelle** — ou est-ce pénible ?

## Critère de réussite

Si toi + un pote ressentez le **frisson de la compréhension partagée** → **feu vert** pour
le reste du projet. Sinon → itérer sur le canal (nombre de symboles, persistance des
signes, ajout de gestes/pointage) jusqu'à trouver l'étincelle, ou conclure et ajuster.

## Rappels

- **Code jetable, assumé.** Ce n'est pas le jeu, c'est l'épreuve de son âme.
- Ne PAS ajouter de features (terrain, fog, naissances…) avant ce feu vert.
- Garder le **test des mantra** sous les yeux (doc 00 / 11) : tout ajout doit faire
  *travailler* le joueur pour réduire une distance, jamais donner la certitude gratis.

## Après le feu vert (ordre indicatif, ne pas anticiper)

1. Terrain réel Balazuc + perso qui marche (heightmap IGN → Terrain3D).
2. Fog of war en ligne de vue.
3. Premières techniques transmissibles (feu, abri).
4. Persistance (l'état du monde — zone de confort backend).
5. Quelques joueurs sur une région, traces persistantes.
6. … (cf. docs 04, 07, 08).
