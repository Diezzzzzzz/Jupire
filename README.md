# Jupire

> Notes de conception — projet de jeu d'exploration / société émergente.
> Brainstorming initial, 2026-06-17.

## Pitch en une phrase

Un monde réel (Balazuc, Ardèche) **rendu à la nature** : on y apparaît sans mots,
sans carte, sans savoir qui l'on croise. Il faut **inventer une langue**, se
comprendre, former des communautés, rebâtir une société parmi les **ruines** de
ceux d'avant.

## La fiction qui unifie tout

- Le **monde réel** (terrain, gorge, rivière de Balazuc) = le décor.
- Les **ruines** (emplacements d'anciens bâtiments) = une civilisation tombée.
- Les **joueurs** = des arrivants **sans langage**, qui doivent tout réinventer.
- **Inventer une langue** = reconstruire du sens.
- **Bâtir des villages** = reconstruire une société.

Une seule histoire : les anciens ont laissé des pierres, les nouveaux doivent
réapprendre à se parler.

## Direction artistique

DA façon **SimCity 4 / Age of Empires 2** : sprites pré-rendus (modélisés en 3D,
rendus en 2D sous un angle fixe) posés sur un **terrain 3D réel**. Cohérent avec
un univers **médiéval / exploration**. Tout (arbres, ruines, personnages,
animaux) = sprites multi-angles. GPU peu sollicité → tourne sur du matériel
modeste.

## Index des notes

- [proto-terrain/](proto-terrain/README.md) — **preuve de chaîne (docs 29→35)** : MNT RGE ALTI → pente/exposition/écoulement → végétation re-dérivée → semis Poisson-disc → rendu AoE2 dans le navigateur. Zéro dépendance. L'Ardèche sort de la donnée sans être dessinée ; l'aplatissement hybride est vérifié (k=0,4 → Δ 91 m au lieu de 52)
- [AGENT-BRIEFING.md](AGENT-BRIEFING.md) — **à lire avant toute session** : ton, posture, mantra (pour garder l'émotion entre agents)
- [PITCH.md](PITCH.md) — **pitch à partager** (plusieurs longueurs, pour non-joueurs)
- [DA-prompts-images.md](DA-prompts-images.md) — prompts ChatGPT pour générer un moodboard d'inspiration DA
- [00-etoile-polaire.md](00-etoile-polaire.md) — **vision fondatrice** : le jeu de la distance, le test pour dire non
- [01-concept-et-vision.md](01-concept-et-vision.md) — l'idée, la fiction, les références
- [02-game-design.md](02-game-design.md) — langage émergent, rencontre, coopération, agression
- [03-technique.md](03-technique.md) — moteur, terrain réel, data, pipeline sprites
- [04-prochaines-etapes.md](04-prochaines-etapes.md) — séquençage, premier prototype, questions ouvertes
- [05-ambiance.md](05-ambiance.md) — perception, verticalité des gorges, grottes/Chauvet, caméra
- [06-fog-of-war-et-camera.md](06-fog-of-war-et-camera.md) — fog of war en ligne de vue, 3 états, décision caméra · **amendé 2026-07-27 au proto : deux axes, pas un** (connaissance discrète × distance continue) — le noir ne vaut que pour ce que le relief masque ; le lointain en vue directe est **visible et imprécis** (« voir beaucoup mais pas précisément »), et cette gradation *est* le LOD dont le streaming a besoin
- [07-savoirs-techniques-et-culture.md](07-savoirs-techniques-et-culture.md) — savoir transmis (pas débloqué), anti-grind, émergence de culture
- [08-temps-mortalite-et-ciel.md](08-temps-mortalite-et-ciel.md) — vue du ciel, cycles, mortalité, résumé de vie, échelle de temps
- [09-faisabilite-et-multijoueur.md](09-faisabilite-et-multijoueur.md) — peurs techniques recadrées, pourquoi le multi est plus facile, concurrence faible, IA/ligne
- [10-metagame-densite-et-conflit.md](10-metagame-densite-et-conflit.md) — cartographie Discord, densité des villages, drame & guerre émergents
- [11-naissances-et-combat.md](11-naissances-et-combat.md) — combat 20v20 (lent + mortel), naissances par le lien, test des mantra
- [12-cycle-persistance-et-but.md](12-cycle-persistance-et-but.md) — cycle fractal, déconnexion/village rasé, pourquoi jouer
- [13-etape-0-prototype.md](13-etape-0-prototype.md) — **le cahier du premier prototype : go build this**
- [14-commerce-et-voyage.md](14-commerce-et-voyage.md) — troc (pont avant la langue), grand voyage, marchand = tissu conjonctif
- [15-motivation-besoin-pas-recompense.md](15-motivation-besoin-pas-recompense.md) — **garde-fou clé** : motiver par le besoin, jamais par un bonus
- [16-roles-et-boucles.md](16-roles-et-boucles.md) — rôles émergents (marchand/producteur/bâtisseur/dessinateur/chercheur), interdépendance, session hebdo
- [17-transmission-savoir-et-langue.md](17-transmission-savoir-et-langue.md) — **cœur mécanique** : technique par démonstration, langue par contexte (jamais traduite), traces = proto-dictionnaire
- [18-odyssee-lenteur-et-monde-acteur.md](18-odyssee-lenteur-et-monde-acteur.md) — le monde comme force (crues, dérive, vent), durée incertaine, lenteur pleine, **barque à réinventer**, horizon Rhône (grande navigation, furtivité)
- [19-echelle-du-monde-et-mediterranee.md](19-echelle-du-monde-et-mediterranee.md) — Méditerranée : **décision « voyage d'une vie »** (traversée = 1/4 de vie → échelle ~1:8-1:15, fixée par la durée de vie), berceaux de densité, réel compressé vs monde inventé, escale = une aventure, dérive hors-ligne
- [20-vieillesse-et-ancien-du-village.md](20-vieillesse-et-ancien-du-village.md) — malus d'âge qui orientent (jamais forcent), pèlerinages guidés par la rumeur, deux morts/deux gloires, **endgame social assumé pour passionnés : le jeune joue dans l'espace, l'ancien joue dans le temps** (transmission sélective, mémoire, calendrier, langue, liens)
- [21-corps-herite-et-demographie.md](21-corps-herite-et-demographie.md) — **pas de character creator, zéro choix** : corps hérité du pool du berceau (respecte doc 11), phénotypes régionaux émergents, l'apparence = information, démographie jouée, **garde-fou : la génétique ne porte jamais de stats**
- [22-secret-confie-et-colere-des-dieux.md](22-secret-confie-et-colere-des-dieux.md) — **les Oracles** (lieux cachés, énigmes individualisées par définition — le chemin est le juge, l'anti-spoil est structurel), destinées = direction jamais pouvoir, une par vie au plus, **le savoir doit voyager dans le monde**, parjure public → némésis + expiation (jamais ban)
- [23-canal-de-communication.md](23-canal-de-communication.md) — **la mécanique cœur, adossée à la science** (sémiotique expérimentale : Galantucci, Garrod & Fay, Kirby) : 3 primitives (désigner / énoncer / inscrire) × N supports (bulle, paroi, jeton, chant), le moteur ne comprend jamais rien, spec du proto v2 « A sait, B va »
- [24-etages-du-canal-et-scenarios.md](24-etages-du-canal-et-scenarios.md) — **le symbole est l'arrivée, le corps est le départ** (PISL, Nicaragua) : 5 étages (affect / deixis / mimesis / nombre / symbole), dialogues imaginés (loup, cité au SO, ruine, louanges), distance = temps + arc de soleil, **prochaine étape : proto sur table, pas en 3D**
- [25-repertoire-perceptif-et-croquis.md](25-repertoire-perceptif-et-croquis.md) — **ton vocabulaire = ta vie** : ce qu'on a perçu se dit en croquis rupestres à niveaux, le receveur décode au niveau de SA propre expérience (« le monde te montre un souvenir » mécanisé), téléphone arabe natif, symboles réservés aux noms/abstractions
- [26-le-mode-regard.md](26-le-mode-regard.md) — **l'horizon manquant de la vue AoE2** : 3e bascule de perception (SOL / REGARD / CIEL), panorama-peinture généré du vrai relief (raycast heightmap), portée réglée par la brume, **la silhouette est le nom du lieu** (vues de côtes des marins), atterrissage odysséen
- [27-granularite-des-crafts.md](27-granularite-des-crafts.md) — **ni le clou ni le bouton : l'étape-geste** (regardable / ratable-signifiant / rare), savoir-faire = répertoire perceptif à niveaux (doc 25 unifié), le chantier est l'école, fresque = proto-manuel, l'épave enseigne, arbre techno dans le monde jamais en menu
- [28-la-voix.md](28-la-voix.md) — **le seul canal qui marche sans se voir** : 4-5 cris primaux sur touches rapides (sifflet, alarme, menace, ohé), combinatoire rythmique libre → codes sifflés par culture (Silbo Gomero de la gorge), **le son est public** (crier = s'exposer), point & click posé
- [29-faisabilite-mediterranee-procedurale.md](29-faisabilite-mediterranee-procedurale.md) — **oui, techniquement** (FABDEM/EMODnet/WorldCover/OSM, quelques centaines de Mo), murs réels = précision flottante + viewshed serveur + raccord terre-mer, **le triangle impossible** (tout le bassin / verticalité / traversée en 1/4 de vie : n'en garder que 2) → **fragments réels dans une mer contractée**, le vrai risque est la fadeur, test = 10 panoramas PNG
- [30-pipeline-donnees-foret-et-routes.md](30-pipeline-donnees-foret-et-routes.md) — **le réel ne s'importe pas, il se nettoie** : LiDAR HD 50 cm (les vrais arbres un par un, pas du procédural) + BD Forêt pour l'essence, procédural = **reconquête** (friche) pas remplissage, et **la route EST le sol** (le MNT la garde) → effacer les infrastructures est la condition pour que les chemins des joueurs soient les leurs
- [31-invariant-et-perissable.md](31-invariant-et-perissable.md) — **on modifie ce que le temps modifie, jamais ce que le temps ne modifie pas** : 3 décisions (2026-07-27) — 1:1 + **aplatissement vertical hybride** (k≈0,7 sur la basse fréquence seule, σ≈250 m → les falaises gardent leur hauteur ; le bon critère est la **longueur**, pas l'angle ; 1:1,25–1:1,5 rejeté = paie sans rien gagner, pour raccourcir un trajet on change la **vitesse**), **effacement total des tracés** → chemins du désir (et ils retomberont sur les vrais : mêmes contraintes, mêmes solutions — le contraste est dans le réseau, pas la géométrie), forêt **re-dérivée du relief** + BD FORÊTS ANCIENNES (garder / supprimer / remettre), la cible n'est pas une date mais **l'abandon**
- [32-une-mediterranee-sans-carte.md](32-une-mediterranee-sans-carte.md) — **le pourtour entier à 1:1 = 46 à 92 vies pour en faire le tour** (mur arithmétique, pas technique ; ni le cheval ni la vitesse ne rattrapent un facteur 10) → sortie du triangle par **2+3** : « monde imaginaire inspiré du réel » = **vrai relief, géographie recomposée**, jamais relief inventé (= fadeur). Nom juste : **une Méditerranée dont on a perdu la carte** — tous les lieux sont vrais, aucun n'est à sa place ; **auteur de la géographie, pas de la matière**. TRANCHÉ : terrain réel **non retouché**, procédural = habillage (**le réel donne l'ordre, le procédural donne le désordre**) ; on ne colle jamais par la terre, **on sépare par la mer** (chaque morceau auto-borné)
- [33-expansion-et-vitesses.md](33-expansion-et-vitesses.md) — **TRANCHÉ : positions réelles, 1:1 intégral assumé** — le monde ne se traverse pas, **il se colonise** : frontière démographique (on ne peut pas s'étendre seul → « la connexion engendre la vie » devient une loi de géographie), l'objection densité du doc 19 tombe **si et seulement si le spawn reste concentré**, 99 % jamais visité assumé (**la taille ne coûte que si on la remplit**) ; vitesses : +2 km/h terrestre = confort pas structure, 10 km/h en mer **supprime les temps morts** plutôt qu'accélérer, **le fleuve a un sens** (descendre gratuit / remonter dur), et **vitesse = confort, autonomie = design**
- [34-densite-reelle-et-zone-du-proto.md](34-densite-reelle-et-zone-du-proto.md) — **5 000 joueurs remplissent ~1 %, soit un département** (50-100 villages en tache d'huile contiguë = des dizaines de frontières culturelles → 1 % suffit ; « le monde grec archaïque : un liseré habité et l'immense inconnu autour ») ; zone proto Vogüé→Orgnac = **300 km², 8× Skyrim** mais la taille est **un paramètre, pas un engagement** (départ : Balazuc+Vogüé 5×5 km) ; **Chauvet vide — le monde offre la paroi, jamais le modèle** ; piège : une heightmap ne peut faire **ni arche ni grotte ni aven** (Pont d'Arc, Chauvet, Orgnac = 3 meshes à la main)
- [35-ouverture-par-lots.md](35-ouverture-par-lots.md) — **TRANCHÉ : le monde s'ouvre zone par zone**, chacune avec sa passe de correction manuelle. Le seul chiffre qui compte = **la cadence** (le monde doit s'ouvrir plus vite que les joueurs n'avancent) ; le bord = **zone brute en tampon, jamais de mur** (on y trouve du désert, pas une limite) ; catalogue des anomalies (grottes/arches/avens impossibles en heightmap, **le fond des rivières n'existe pas**, ponts, dépressions fermées). **Dossier terrain fermé** — reste une seule décision non rétrofittable : floating origin vs `precision=double`

## Décisions déjà prises

- **Moteur** : Godot (gratuit, 2.5D/sprites excellent, export natif **et** web, API multi intégrée).
- **Multijoueur** : oui, à terme. Monde partagé persistant → serveur **autoritaire** (chantier dur, plus tard).
- **Terrain** : réel, **Balazuc et ses environs** (Ardèche), via MNT IGN RGE ALTI.
- **Option « nature »** : on garde forêts + rivières réelles, on **enlève le bâti**.
- **Bâti** : on n'en garde que **quelques-uns choisis à la main**, transformés en **ruines**.
- **Pas de PvP** pour l'instant. Chasse aux animaux oui. Attaquer un humain = possible mais **très coûteux** pour l'agresseur.
