# Faisabilité, multijoueur & peurs

> Recadrage des peurs techniques. Conclusion : la peur du « 100 joueurs en multi »
> vise mal — le design de Jupire rend le multijoueur PLUS facile, et le vrai risque
> est humain, pas technique.

## Hommage rendu par la communauté (ajout au pilier mémoire)

Les autres peuvent bâtir un monument / peindre les actes d'un défunt. Effets :
- La mort devient un **événement social**, acte de mémoire collective.
- **La communauté écrit ses propres légendes** : elle choisit ses héros, ses fondateurs
  → naissance d'une tradition.
- L'hommage se **mérite** : reliés → pierre ; destructeur/ermite → personne, ou marque
  d'avertissement. L'hommage (ou son absence) raconte la vie sans un mot.
- Chaque culture honore *à sa manière* → divergence.

## Pourquoi le design rend le multijoueur PLUS facile

Termes d'ingénieur :
- **Joueurs dispersés** (pilier distance, rencontres rares) → faible densité → peu
  d'entités à synchroniser/joueur. L'enfer du netcode = 100 joueurs *au même endroit*
  (bataille/siège). Jupire = l'inverse, par conception.
- **Jeu lent** (pas de combat nerveux/PvP twitch) → **tick rate bas OK**, **aucune lag
  compensation** sub-100ms. Élimine la partie la plus dure du temps réel.
- **Le fog of war EST l'optimisation réseau.** On ne synchronise à un client que ce que
  son perso voit (viewshed) = **interest management / area-of-interest**, technique reine
  du scaling MMO, déjà EXIGÉE par le gameplay. On n'envoie jamais 100 joueurs à chaque
  client, juste la poignée visible.

**Anvil of Empires** = profil DIFFICILE (centaines de joueurs en combat/siège temps réel
au même endroit). Jupire = profil FACILE (clairsemé, lent, sans combat nerveux). Ne pas
se comparer à un problème plus dur que le sien.

## Le vrai recadrage : pas besoin de 100 joueurs simultanés

Ne pas confondre « monde qui contient une civilisation » et « 100 connectés en même temps ».
- Monde **persistant + plein de traces** (peintures, ruines, monuments, savoirs chez les
  survivants) → même avec **peu de joueurs en ligne**, le monde se *sent* peuplé par les
  absents. Modèle **Dark Souls / Death Stranding** : présence **asynchrone**.
- Rencontres live **rares et précieuses** (= le design) → **petite concurrence (8/20/50)**
  suffit. La rareté n'est pas un défaut technique, c'est le design.

→ Monde persistant qui se souvient de tous + peu de concurrents = expérience complète.
Plus atteignable ET plus fidèle que 100-simultanés.

## Où est le vrai travail (zone de confort de Rémi)

Le morceau dur n'est pas le netcode, c'est la **persistance** : monde qui évolue,
constructions, peintures, état des savoirs, monuments, culture accumulée = beaucoup
d'**état persistant**. = **le métier de Rémi** (Postgres, modélisation, event-sourcing,
serveur autoritaire).

Archi probable : **serveur Godot headless autoritaire** (tick bas) + **Postgres** (état
du monde). Compétences déjà acquises.

## Solo + IA : tracer la ligne

- Remplacer les joueurs par de l'IA **tue l'âme** (la magie = un vrai esprit en face,
  qu'on ne comprend pas au début). Pas de solo-IA comme vision centrale.
- **Ligne nette** : IA légitime pour **animaux / faune / ambiance** (boids, comportements),
  **jamais** pour le cœur social/langage. Humains pour les humains, IA pour le vivant
  non-humain.

## DÉCISION ACTÉE : pas de PNJ / faux joueurs (même pour peupler ou faire masse)

Tentation récurrente : ajouter des sprites de fausses personnes pour animer un marché /
une place, ou créer de la masse pendant les guerres. **Refusé.** Ce n'est pas que les PNJ
sont mauvais en général — c'est que *Jupire est bâti sur la réalité de l'autre*.

- **Fausse masse de guerre = puissance/certitude gratuite.** L'armée paraît grande sans
  que personne de réel ne risque rien ; tuer un PNJ n'efface aucun savoir → les enjeux
  s'évaporent → retour au deathmatch banni. Brise « tu importes parce que tu es perdable ».
- **Faux indistinguables des vrais = poison.** Ça dévalue *toutes* les rencontres :
  pourquoi faire l'effort de comprendre quelqu'un qui pourrait n'être qu'un décor creux ?
  Le doute « est-il réel ? » attaque l'anonymat-qui-protège-la-langue.
- **Le vide n'est pas un bug, c'est le jeu** (solitude, petitesse, silhouette rare = l'étoile
  polaire). Remplir de figurants tue ce qui fait qu'une *vraie* rencontre compte.

**Règle propre** : les seuls « autres » = **vrais joueurs (en direct)** OU **traces de
vrais joueurs (asynchrones, figées : étals bâtis, peintures, objets déposés, état gelé
dans la brume)**. Jamais de personnes simulées. Un lieu se peuple de ce que de vrais gens
ont *fait*, pas de mannequins. La masse de guerre vient de vrais ralliements dans le temps ;
sinon on assume l'échelle qu'on a (le couteau dans le dos > le 50v50 à moitié faux).

## Chemin pragmatique

Ne PAS architecturer pour 100 dès le départ. Prototyper **petit** : **une région
(Balazuc), 8–20 joueurs**, prouver la boucle. Scaler ensuite si besoin — dispersion +
fog rendent le scaling progressif et naturel.

## La peur à avoir À LA PLACE

Le risque de Jupire est **humain**, pas technique : de vrais joueurs vont-ils *vraiment*
inventer une langue et tisser une culture — ou s'ignorer, griefer, partir ? Aucune archi
ne le garantit. C'est ce que teste l'**Étape 0** (2 joueurs, 6 symboles, échanger un objet).
Déplacer la peur du serveur (domptable) vers la boucle sociale (le vrai pari). Si c'est
magique à deux, le reste est de l'ingénierie maîtrisée.
