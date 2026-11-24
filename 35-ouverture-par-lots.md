# L'ouverture par lots — la stratégie de production du monde

> **TRANCHÉ (2026-07-27)** : le monde s'ouvre **zone par zone**, chacune passant par une
> **correction manuelle** (entrées de grottes, formations géologiques atypiques que le
> pipeline ne sait pas rendre) avant d'être livrée.
>
> Ce doc fixe la stratégie, nomme le chiffre à mesurer, règle la question du bord, et
> donne le catalogue des anomalies à corriger — dont deux qui ne sont pas évidentes.

## 1. Pourquoi c'est la bonne stratégie

Elle fait coïncider trois choses qui n'allaient pas ensemble jusqu'ici :

- **Le coût suit le jeu réel, pas l'ambition.** On ne paie que pour ce qui est habité
  (règle du doc 33 : *la taille du monde ne coûte que si on la remplit*).
- **Chaque zone est un lot fini** : télécharger → nettoyer → corriger → habiller → tester.
  Un travail borné, répétable, mesurable — l'inverse d'un chantier infini.
- **Rien n'est décidé d'avance.** L'immensité du doc 33 reste vraie sans qu'un seul km²
  de trop soit produit.

## 2. Le seul chiffre qui compte : la cadence

> **Le monde doit s'ouvrir plus vite que les joueurs n'avancent.**
> Sinon la frontière de production devient un mur invisible — et un mur invisible est la
> seule chose qui puisse trahir l'immensité qu'on vient de décider.

Donc **la première zone n'est pas qu'un test de rendu, c'est une mesure de production** :
combien d'heures pour ouvrir 25 km² ? Cette valeur décide de tout le reste :

| Si une zone de 25 km² coûte… | Alors… |
|---|---|
| quelques jours | l'ouverture manuelle tient largement, on peut soigner |
| 2–3 semaines | ça tient encore (50-100 villages mettent des mois à s'étendre) |
| plus d'un mois | il faut automatiser la passe de correction, ou réduire son ambition |

C'est le premier chiffre à noter le jour où la première zone est faite. Il vaut plus que
n'importe quelle estimation faite aujourd'hui.

## 3. Le bord : trois niveaux, jamais de mur

Les zones étant contiguës (elles s'ajoutent les unes aux autres), le bord est **temporaire
et mobile**. Il ne doit ni bloquer, ni mentir, ni obliger à un retcon quand il reculera.

| Niveau | Contenu | Rôle |
|---|---|---|
| **Zone ouverte** | pipeline + correction manuelle + habillage | le jeu |
| **Zone brute** | pipeline seul (relief nettoyé, routes effacées, forêt recalculée) — sans grottes, sans anomalies traitées, sans faune, sans ressources | **le tampon** |
| **Non généré** | rien | jamais atteignable |

La règle : **le joueur ne doit jamais atteindre le « non généré »**, mais il a parfaitement
le droit d'atteindre la zone brute — il y trouvera du **désert**, pas un mur.

C'est honnête (rien ne ment), ça ne bloque personne, ça se remplit plus tard sans
contradiction, et c'est **exactement la fiction** : le monde est vide, on marche loin,
il n'y a rien. Le vide n'est pas un bug (doc 09).

Bonne nouvelle de coût : la zone brute est **entièrement automatique** — l'effacement des
routes, la végétation recalculée, l'aplatissement hybride sont tous du pipeline (docs 30,
31). Seule la passe manuelle distingue une zone ouverte d'une zone brute.

## 4. Catalogue des anomalies à corriger

Ce que le pipeline ne saura jamais produire, et qu'il faut traiter à la main :

### Impossibles par nature (une heightmap est `z(x,y)`)
- **Entrées de grottes et porches** — le MNT passe *par-dessus* le vide : la grotte
  n'existe simplement pas.
- **Arches et surplombs** — deux altitudes au même point (le Pont d'Arc, doc 34).
- **Avens et gouffres** — un puits qui s'élargit sous la surface.

→ Tous sont des **meshes posés sur le terrain**, avec leur propre collision. Travail
d'asset, borné, différable.

### Artefacts du relevé (moins évidents, et ils vont surprendre)
- **Le fond des rivières n'existe pas.** Le laser topographique ne traverse pas l'eau : le
  LiDAR HD reconstruit une **surface d'eau plane** à partir de points virtuels. Donc
  **l'Ardèche a un fond plat artificiel**. Sans importance si on longe la rivière — mais
  dès qu'on nage, qu'on gué, qu'on pêche ou qu'on navigue (docs 18, 33), il faut creuser
  un lit à la main ou par règle.
- **Ponts et tunnels** — le LiDAR HD a une classe *tablier de pont* dédiée : selon le
  traitement, un pont devient un barrage plein en travers de la rivière, ou un tunnel
  devient une colline bouchée. À vérifier zone par zone.
- **Falaises verticales** — une paroi verticale s'écrase sur 1–2 pixels : normales et
  collisions y deviennent instables. À 50 cm c'est acceptable, mais c'est précisément là
  que le joueur regardera (doc 06).
- **Dépressions fermées** — artefacts d'interpolation qui piègent l'eau et cassent tout
  écoulement. Correction standard en hydrologie (*sink filling*), automatisable.

### Déjà traités par le pipeline (rappel)
Routes, remblais, carrières, terrasses, bâtiments : effacement automatique (doc 30).
Ne pas les refaire à la main.

## Verdict mantra

La stratégie ne touche à aucun pilier, et elle protège le risque n°1 du projet : elle
rend l'immensité **payable en tranches**. On ne peut plus se ruiner en rêvant, puisqu'on
ne produit que ce qui est habité.

Un seul garde-fou : **la zone brute ne doit jamais être « améliorée » avec du terrain
généré** pour faire joli en attendant. Le jour où l'on bouche un trou avec du procédural
de relief, le pilier du réel tombe (doc 32) — et avec lui la seule assurance contre la
fadeur.

## 5. Où en est le dossier terrain

**Fermé.** Docs 29 → 35 : les données, l'échelle, les pentes, l'effacement, la végétation,
l'agencement, les vitesses, la densité, la zone, la production. Aucune question ouverte
n'est bloquante.

Et il ne reste **aucune décision bloquante**. Le point « floating origin ou
`precision=double` » (doc 29), présenté plus tôt comme non rétrofittable, l'est en fait
à moitié seulement :

> **`precision=double` est un flag de compilation, réversible à tout moment.**
> **Le floating origin est du code partout, et ne se rajoute pas après coup.**
>
> Règle : **on n'écrit jamais de floating origin.** On démarre en Godot standard (5 × 5 km
> ne pose aucun problème) et on recompile en double le jour où le monde dépasse ~10 km.

Et il reste l'**Étape 0** (doc 13), qui n'a toujours pas eu lieu, et dont rien de ce
dossier ne dépend — mais dont tout ce dossier dépend.

## Questions ouvertes

- **Qui décide qu'une zone s'ouvre ?** À la main (on livre quand on veut) ou déclenché
  par la pression des joueurs (la frontière s'ouvre quand on s'en approche) ? Le second
  est plus vivant mais impose la cadence.
- **Une zone peut-elle se re-fermer** si plus personne n'y vit ? Probablement inutile,
  mais ça rejoint doc 12 (village rasé).
- **Combien de temps pour ouvrir 25 km² ?** — à mesurer, pas à estimer. C'est le premier
  chiffre du projet.
