# Prochaines étapes

## Principe de séquençage

Le projet grossit vite → **discipline de scope**. Chaque étape doit rester
jouable/testable. Et surtout : **dé-risquer l'âme avant de bâtir le corps**.

## Étape 0 (CONSEILLÉE EN PREMIER) — prototyper l'âme

Pas Balazuc, pas le terrain. Le cœur du jeu = la **rencontre** et le **langage**.
Testable avec deux cubes dans une pièce vide :

> Deux joueurs, aucun texte, juste une palette de ~6 symboles.
> Objectif : réussir à échanger un objet.
> Le sens émerge-t-il ? Est-ce *amusant* ou *frustrant* ?

Si magique → on a un jeu. Si pénible → appris en une semaine, on ajuste le canal.

## Pipeline technique (une fois l'âme validée)

1. **Terrain réel + perso qui marche** : dalle IGN Balazuc → heightmap → Terrain3D
   + collision → un capsule/cube qui marche dans la gorge vierge.
2. **Textures de sol par biome** (herbe/roche/forêt) → les plaines apparaissent.
3. **Forêts** : scatter de sprites-arbres en MultiMesh dans les zones forêt (OSM).
4. **Rivières** : mesh + shader d'eau le long des `waterway`.
5. **Ruines** : 3-4 bâtiments choisis → props de ruines sur leur emprise.
6. **Un seul animal** qui erre et fuit (valider la boucle IA).
7. *Ensuite* : multijoueur (2 joueurs qui se voient bouger), puis serveur
   autoritaire, persistance, zones → villages/villes joueurs.

## Multijoueur — à acter tôt

Architecture réseau = contamine tout le code. Monde partagé persistant
(villes qui vivent hors connexion) → **serveur autoritaire** + pensée
**zones/sharding** dès le début. Ne PAS commencer par là, mais ne pas coder
« comme si » c'était solo.

## Questions ouvertes

- **Le canal de communication** : quel medium exact (symboles / gestes / sons /
  dessin / objets) ? Comment le sens se fige et se transmet ? Dictionnaire de tribu ?
- **Le verbe premier** : comprendre / échanger / bâtir / survie douce ? (oriente le proto)
- **Densité / cold-start** : combien de joueurs concurrents pour que la magie opère ?
  Mécanismes de rencontre (spawn groupés, ruines = Schelling points, signaux sonores).
- **Onboarding** : rendre l'incompréhension *conçue* (émerveillement) et non frustrante.
- **Coût de l'agression** : marque visible, perte de sens, rareté des armes — à équilibrer.

## Les trois murs identifiés

1. **Densité** (sans monde, pas de société émergente).
2. **Persistance** (serveur autoritaire = le gros morceau technique).
3. **Onboarding** (un jeu qui n'explique rien est brutal s'il n'est pas conçu pour).
