# Le canal de communication — recherche & design

> La mécanique la plus importante du jeu : le canal par lequel des inconnus sans
> langue commune inventent du sens. Exigence : **très travaillée et modulaire**,
> car réutilisée partout (rencontre, traces, commerce, rumeurs, Oracle).
> Ce doc = synthèse de la recherche scientifique + design proposé + spec du proto.

## Ce que dit la science (des gens ont DÉJÀ fait notre Étape 0 en labo)

Le champ s'appelle **sémiotique expérimentale** : des adultes qui ne peuvent pas
utiliser de langue existante développent des systèmes de communication de zéro,
en conditions contrôlées. Quatre résultats directement exploitables :

1. **Galantucci (2005)** — deux inconnus + une tâche de coordination + un canal
   contraint : des systèmes de communication **émergent réellement**, et sont
   **combinatoires très tôt** (on combine vite des signes simples en messages
   composés). Détail crucial : son canal était *volontairement étrange* (un stylet
   dont le tracé dérivait, empêchant de dessiner ou d'écrire des lettres) — si le
   canal permet l'écriture ou le dessin facile, les gens y retombent et rien
   n'émerge. **Leçon : le canal doit rendre l'iconicité coûteuse, pas impossible.**
2. **Garrod & Fay (Pictionary sans mots)** — les signes commencent iconiques
   (dessins) et deviennent **symboles abstraits** par l'usage répété… mais
   seulement s'il y a **interaction et feedback** (la répétition seule ne suffit
   pas — exp. 1 et 2). Le sens migre du signe vers la mémoire partagée de son
   usage. Et **exp. 3 : les tiers ne comprennent pas** les conventions d'une
   paire. → **Les dialectes régionaux de Jupire émergeront tout seuls** — la
   divergence culturelle rêvée (doc 02) est un résultat de labo reproduit.
3. **Kirby, Cornish & Smith (PNAS 2008, iterated learning)** — une langue
   transmise de « génération » en « génération » d'apprenants devient **plus
   structurée et plus apprenable**, PARCE QUE chaque apprenant n'en voit qu'un
   fragment. La transmission imparfaite est *requise* pour que la structure
   émerge. → **Validation scientifique du pilier mortalité/transmission (docs
   08, 17) : la permadeath n'est pas un obstacle à la langue émergente, c'en
   est le moteur de structuration.** L'oubli partiel est une feature.
4. **Les jeux qui s'en approchent** — *Chants of Sennaar* : glyphes appris par
   contexte (fresques, gestes) — mais sens fixé par les devs, l'inverse de nous ;
   sa leçon = **le contexte est le professeur**. *Dark Souls* : messages en
   templates + vocabulaire fermé, posés dans le monde, asynchrones — preuve
   qu'un canal très contraint est expressif, et que **l'ambiguïté fait le
   charme** ; mais son vocabulaire a un sens préétabli (mots anglais) — nous
   voulons des signes SANS sens préétabli. *Journey* : un seul « chirp » +
   le mouvement suffisent à créer du lien — le corps communique déjà.

## Réponse aux trois questions d'architecture

- **« On écrit quelque chose et un moteur l'interprète ? » → NON, jamais.**
  Principe d'architecture n° 1 : **le moteur ne comprend rien**. Il transporte
  et stocke des formes opaques (des IDs de symboles) ; le sens n'existe que dans
  les têtes des joueurs. Un moteur qui interprète = traduction automatique =
  trahison frontale (doc 00), et Garrod & Fay montrent que c'est inutile : la
  mémoire partagée des joueurs fait le travail.
- **« On choisit des signes à montrer ? » → Oui, c'est la base** (palette fermée).
- **« Signes + écrire quelque chose ? » → Pas de texte libre, jamais.** Si on
  peut écrire, on écrit en français et la langue émergente meurt (leçon
  Galantucci). Le « dessin libre » viendra, mais comme module coûteux réservé
  aux traces persistantes (peintures, doc 05) — la lenteur du geste est le
  garde-fou anti-alphabet.

## Le design : 3 primitives, N supports (la modularité demandée)

Séparer **l'énoncé** (la donnée) de son **support** (le médium). Un énoncé =
une séquence courte de symboles : `[signe, signe, signe]` — objet de données
opaque, unique dans tout le jeu.

**Les trois primitives :**

1. **DÉSIGNER (deixis)** — pointer : une direction, un objet, un lieu visible.
   Pré-linguistique, universel, toujours disponible (Tomasello : le pointage +
   l'attention conjointe sont le socle de toute communication humaine). C'est
   le bootstrap : on peut « parler de » quelque chose avant d'avoir un mot.
2. **ÉNONCER** — composer une séquence de symboles abstraits depuis une palette
   fermée (6 au départ). Les séquences dès le début (pas un symbole isolé) :
   c'est de la combinatoire que naît la structure (Galantucci).
3. **INSCRIRE** — attacher un énoncé à un support :
   - **la bulle** au-dessus de la tête : éphémère, temps réel (la parole) ;
   - **la surface** : peint sur paroi/pierre : persistant, asynchrone
     (l'écriture — doc 05, les grottes-livres) ;
   - **l'objet** : gravé sur un jeton portable : la **lettre**, troquable,
     transportable (le commerce d'info du doc 14 devient physique) ;
   - plus tard : **le chant** (motif audio porté à distance, vent — doc 08).

Même donnée partout → tout ce qui est dit peut être écrit, tout ce qui est
écrit peut être porté, troqué, retrouvé des générations plus tard. La rumeur,
la carte peinte, la lettre de marchand, l'énigme de l'Oracle : **un seul
système**. C'est la modularité demandée — et le moteur ne voit que des listes
d'IDs.

**Réglages dictés par la recherche :**
- **Symboles de départ abstraits** (pas de flèche, pas de pictogramme d'objet) :
  le sens doit se négocier. L'iconicité passe par le pointage et le dessin
  coûteux, pas par la palette.
- **Le feedback est obligatoire** (Garrod & Fay) : la tâche doit montrer si on
  s'est compris (l'objet rapporté est le bon ou non). Dans le jeu final, le
  monde fournit ce feedback naturellement (l'échange aboutit, le gué existait).
- **La palette peut grandir** (6 → plus) : à tester ; trop de signes trop tôt
  dilue la négociation de sens.

## Spec du prototype v2 (la tâche redéfinie)

**A sait, B va.** A connaît la cache (3 objets) et l'objet voulu ; B ne sait
rien mais peut se déplacer. A ne peut pas franchir sa zone (immobile — déjà
la scène ancien/jeune du doc 20, sans le vouloir). B doit **trouver la cache
puis rapporter le bon objet**. Deux étages de difficulté dans une seule tâche :

1. **Guider vers un lieu hors de vue** = *displacement* (parler de ce qui n'est
   pas là — le trait le plus dur et le plus « langage » de tous) ;
2. **Désigner un référent parmi trois** = référence pure (le jeu de Lewis,
   l'atome de la sémiotique expérimentale).

Setup : un petit espace avec **3-4 repères géométriques distincts** (un rocher,
un arbre, une butte — il faut des points de repère pour que « guider » ait un
sens), sinon fidèle au doc 13 : jetable, pas de Balazuc, pas de fog. Canal :
palette de 6 symboles en séquences de 1 à 4, pointage. Rien d'autre.
On observe : des conventions pour les directions/distances émergent-elles ?
Le « on s'est compris ! » au retour du bon objet — étincelle ou corvée ?

## Sources

- [Experimental Semiotics — Galantucci, Language & Linguistics Compass (2012)](https://compass.onlinelibrary.wiley.com/doi/10.1002/lnc3.351) ;
  [le recueil Galantucci & Garrod](https://benjamins.com/catalog/bct.45)
- [Garrod, Fay et al. — Foundations of Representation: Where Might Graphical
  Symbol Systems Come From? (Cognitive Science, 2007)](https://onlinelibrary.wiley.com/doi/10.1080/03640210701703659)
- [Kirby, Cornish & Smith — Cumulative cultural evolution in the laboratory
  (PNAS, 2008)](https://www.pnas.org/doi/10.1073/pnas.0707835105)
- [Chants of Sennaar — Deep Dive (Game Developer)](https://www.gamedeveloper.com/design/deep-dive-the-visual-tapestry-of-i-chants-of-sennaar-i-) ;
  [design de l'immersion linguistique](https://www.gamedeveloper.com/design/immersing-players-in-the-culture-of-a-people-with-language-puzzler-chants-of-sennaar)
- [Dark Souls Messaging (mécanique)](https://darksouls.fandom.com/wiki/Messaging) ;
  [analyse](https://www.thegamer.com/dark-souls-messages/)

## Questions ouvertes

- Forme visuelle des 6 symboles de départ (abstraits mais mémorisables et
  distinguables en petite taille — à dessiner).
- Longueur max d'un énoncé (4 ? 6 ?) et persistance de la bulle (combien de
  secondes — assez pour lire, pas assez pour « afficher en continu »).
- Le pointage : direction seule, ou aussi « pointer un symbole de la palette » ?
- Faut-il un signe de feedback minimal universel (hochement oui/non) ou même
  ça doit-il émerger ? (Instinct : même ça, ça s'invente — Galantucci l'a vu.)
