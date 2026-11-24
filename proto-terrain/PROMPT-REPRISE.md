# Prompt de reprise — proto-terrain

> À copier tel quel au démarrage de la prochaine session.

```
Projet Jupire. Lis d'abord ~/Jupire/AGENT-BRIEFING.md, puis
~/Jupire/proto-terrain/README.md (la section « À LIRE EN PREMIER » en tête).

On reprend le proto-terrain, un rendu AoE2 de Balazuc à partir du MNT LiDAR HD.
Il tourne sur http://localhost:5190/ (sinon : cd ~/Jupire/proto-terrain &&
python3 -m http.server 5190 --bind 0.0.0.0). Le monde par défaut est
world_2400.json — Balazuc 2,4 km au pas de 1,17 m.

RÈGLE DE MÉTHODE, à respecter avant de toucher au code :
la session précédente a déraillé parce que tu ne voyais pas mon écran et que tu
corrigeais à l'aveugle. Demande-moi une capture d'écran AVANT de proposer un fix,
et redemande-en une après chaque changement visuel. Le numéro de build est affiché
sous le titre du panneau : vérifie que je vois bien le même que toi.

TROIS BUGS EN COURS :

1. Je ne vois pas l'eau (elle apparaît sur tes captures, pas sur mon écran).
   Hypothèse notée : le ShaderMaterial GLSL échouait selon le pilote (ANGLE sous
   WSL/Windows) et disparaissait sans erreur console. Le shader a été retiré au
   build v12, l'eau est en MeshBasicMaterial. À vérifier EN PREMIER : est-ce que
   l'eau réapparaît ? Si oui, cause confirmée → tout effet visuel devra rester en
   matériau standard, ou être testé sur ma machine avant d'être gardé.

2. Des arbres poussent dans l'eau. Cause certaine et déjà identifiée :
   pipeline/semis.py classe le sol par accumulation d'écoulement, qui ne détecte
   rien sur une petite fenêtre (classe « eau » = 0 %), alors que le rendu utilise
   le masque BD TOPO (<monde>.hydro.png). Les deux ne se parlent pas. Correctif :
   passer le masque à semis.py et interdire tout semis sous l'eau + marge de berge.

3. Les rochers du lit ne s'affichent pas. Probablement lié au point 1 (ils sont
   rendus juste après l'eau).

MES RÉGLAGES VALIDÉS, à ne pas changer sans me demander :
lissage 5 m · aplatissement 0,85 · creusement des gorges ×1,1 · niveau d'eau +0,5 m
· inclinaison caméra 36° · filtre ruisseaux 0.

Commence par me demander une capture, puis attaque le point 1.
```

## Rappels utiles pour la session

- **Pipeline** : `fetch_dem.py largeur_m hauteur_m resolution_m [lidar|rge] [lat] [lon]`
  → `semis.py` → `calques.py` (orthophoto + hydrographie, nommées d'après le monde).
- **Touches** : `G` mode libre / incarné · `O` orthophoto · `F` fog · `A`/`E` pivoter ·
  `ZQSD` marcher · clic (mode libre) pour poser le personnage.
- **Console** : `vue(x, z, portée)` · `repere()` · `__eau` · `__scene`.
- **Cache** : le module ES est mis en cache agressivement — rechargement forcé
  (`Ctrl+Shift+R`) après chaque modification, et vérifier le numéro de build.
- **Décisions de design** : docs 29 à 35 dans `~/Jupire/`, index dans le README racine.
