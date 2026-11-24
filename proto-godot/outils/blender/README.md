# L'usine à sprites — Blender + Cycles

Elle fait en path tracing ce que `scripts/usine.gd` fait en miniature dans Godot :
photographier des volumes sous 8 angles, en projection **orthographique**, à une
inclinaison fixe, et écrire des PNG à fond transparent.

## Relancer

```bash
~/blender-4.5.9-linux-x64/blender --background --python outils/blender/usine.py
```

Options (après `--`, qui est déjà consommé par Blender) :

| option | défaut | à quoi ça sert |
|---|---|---|
| `--props a,b,c` | tous | ne refaire qu'une partie du catalogue |
| `--variantes N` | 3 | formes par objet (ou **poses** pour les animaux) |
| `--angles N` | 8 | pas de 360°/N |
| `--echantillons N` | 160 | échantillons Cycles avant débruitage |
| `--haut-px N` | 384 | hauteur de rendu ; la largeur en découle |
| `--sortie DIR` | `textures/sprites` | où écrire |
| `--ciel hdri\|nishita` | `hdri` | HDRI Poly Haven écrêté, ou ciel Nishita calculé |
| `--cpu` | — | forcer le CPU |

Exemple, pour ne refaire qu'un chêne et le regarder vite :

```bash
~/blender-4.5.9-linux-x64/blender --background --python outils/blender/usine.py -- \
  --props chene_vert --variantes 1 --angles 2 --echantillons 48 --sortie /tmp/essai
```

## Regarder ce qui est sorti

`verif.py` est l'outil de contrôle. Il compose les PNG sur un gris moyen, trace
les repères du contrat (ligne de sol, axe, cadre du panneau) et **mesure** la
boîte des pixels opaques en fraction de panneau — c'est ce qui dit si un objet
déborde ou s'il flotte, au lieu de le deviner à l'œil.

```bash
~/blender-4.5.9-linux-x64/blender --background --factory-startup \
  --python outils/blender/verif.py -- textures/sprites/chene_vert/*.png \
  --cols 4 --sortie /tmp/planche.png
```

Sortie type :

```
chene_vert/v0_a0.png   z[-0.117..+0.703] x[-0.283..+0.277] lum 0.158 couv 27.4%
```

`z` est mesuré depuis la ligne de sol, en fraction de `H`. Le panneau va de
`−0,12` à `+0,88` : si `z_bas < −0,12` ou `z_haut > +0,88`, c'est rogné.

## Combien de temps

Mesuré sur RTX 2000 Ada (8 Go) sous WSL, Cycles en **CUDA** (OptiX n'est pas
exposé sur cette machine), 475 × 384 px, film transparent, débruitage OIDN :

| échantillons | s/image |
|---|---|
| 48 | 1,6 – 3,1 |
| 160 | 2,5 – 3,5 |

Le catalogue complet — 10 props × 3 variantes × 8 angles = **240 images** —
prend de l'ordre de **12 à 15 minutes**. Le chêne vert est le plus lourd
(~220 000 faces, ~7 s de construction par variante) ; les animaux sont
quasi gratuits (quelques centaines de faces).

Le script imprime le périphérique réellement retenu au démarrage. S'il affiche
`CPU`, c'est qu'aucun périphérique CUDA/OptiX n'a été activé dans les
préférences : baisser `--echantillons` à 48 et compter ~8× plus long.

## Ce qui est procédural, ce qui vient d'un asset CC0

### Procédural (aucun fichier externe)

| objet | comment |
|---|---|
| `chene_vert`, `chene_pubescent` | récursion de branches : 6 générations de tubes effilés, biais vertical dégradé (phototropisme en bas, gravité en haut), feuillage en rosettes de polygones à 6 sommets sur les 3 dernières générations. ~220 000 faces. |
| `buisson` | même moteur, 5 générations, plusieurs tiges partant du sol, petites feuilles coriaces (chêne kermès / ciste). |
| `rocher` | icosphère subdivisée 5 fois, déplacement fractal à 4 octaves, puis 9 à 13 tranches planes — le calcaire casse en dièdres, pas en boules. Ombrage plat assumé. |
| `herbe_seche` | 520 à 660 lames, chacune une bande de 4 quads effilée et retombante. |
| `tas_feuilles` | butte de terre bruitée + ~1 000 feuilles polygonales posées dessus. |
| matériaux calcaire, paille, terre, feuille, tache de contact | nœuds de bruit / Voronoï, aucune texture sur disque. |

L'add-on **Sapling Tree Gen** n'est pas utilisé : Blender 4.5 ne le livre plus
(14 add-ons `addons_core` seulement, `add_curve_sapling` a été retiré). La
récursion maison le remplace, et elle a l'avantage d'être déterministe et
paramétrable par essence.

### Assets CC0 utilisés

Tous CC0 / domaine public. Détail complet et URLs dans
`assets/cc0/LICENCES.md`.

| usage | asset | source | licence |
|---|---|---|---|
| Éclairage indirect (ciel) | `kloofendal_43d_clear_puresky_2k.hdr` | Poly Haven | CC0 |
| Écorce des deux chênes | `jolcham_oak_bark_01` (diff / nor_gl / arm, 2K) | Poly Haven | CC0 |
| `chevreuil` | `doe.blend` (riggé + animé) | OpenGameArt — *Deer Female* | CC0 |
| `sanglier` | `boar.blend` (riggé + animé) | OpenGameArt — *Boar* | CC0 |
| `oiseau` | `raven_0.blend` (riggé + animé) | OpenGameArt — *Raven* | CC0 |
| `poisson` | `esox.fbx` + textures PBR | OpenGameArt — *Esox Animated Fish* | CC0 |

**Écartés, et pourquoi.** Les buissons et touffes d'herbe Poly Haven
(`shrub_02`, `shrub_04`, `wild_rooibos_bush`, `grass_medium_01/02`) sont larges
et plaqués au sol. Or à 36° d'inclinaison une empreinte de rayon R descend de
`tan(36°)·R = 0,73·R` **sous** la ligne de sol, et la marge basse ne vaut que
`0,12·H`. Mis au panneau, la touffe `grass_medium_01` tombait à 2,4 cm de large
dans un panneau de 80 cm (mesuré). Le procédural, lui, est taillé pour le
contrat. Le dictionnaire `MODELES` en tête du script est le point de bascule :
y remettre un chemin suffit à réessayer. Le pack low-poly Quaternius est écarté
aussi, il jure avec la cible photoréaliste.

## Le contrat géométrique

Il est écrit en tête de `usine.py` et il n'est pas négociable : la caméra de jeu
partage les mêmes nombres. Seule la marge basse est devenue un réglage par prop
(voir plus bas), déclaré dans le manifeste.

* projection **orthographique** ;
* inclinaison **36°** au-dessus de l'horizon ;
* 8 angles, azimut `a × 45°` ;
* taille verticale de caméra `H·cos(36°)`, image de rapport `1/cos(36°)`
  → 384 px de haut, **475 de large** ;
* visée à `(0,5 − marge)·H` au-dessus de la base — soit `0,38·H` à la marge
  nominale de 0,12 : le panneau va de `−marge·H` à `(1−marge)·H` ;
* PNG RGBA, fond transparent ;
* **le soleil et le ciel sont fixes dans le monde** sur les 8 angles.
  Azimut 2,35 rad, élévation 0,42 rad. S'ils suivaient la caméra, le côté
  éclairé tournerait avec elle et tout l'éclairage mentirait.

Godot est Y-haut, Blender est Z-haut : `Blender(x, −z, y) = Godot(x, y, z)`.

### L'HDRI, et pourquoi il est écrêté

Le soleil de `kloofendal_43d_clear_puresky` a été **mesuré** sur son pixel le
plus lumineux (2048 × 1024) : `u = 0,6003` → azimut 0,630 rad dans son repère,
`v = 0,7388` → élévation 0,750 rad, soit 43° — ce que dit son nom. Notre contrat
impose 0,42 rad (24°). Deux conséquences, traitées dans `monter_scene` :

1. l'HDRI est **tourné** de `azimut_voulu − 0,630` pour aligner les azimuts ;
2. son disque solaire (1,1 × 10⁵ en luminance) est **écrêté à 6,0** — sinon il
   porterait une seconde ombre, à la mauvaise élévation. La lumière directe
   vient de notre lampe Sun, à 0,42 rad ; l'HDRI ne sert qu'à l'indirect et à
   la couleur du ciel.

`--ciel nishita` bascule sur un ciel Nishita calculé exactement à 0,42 rad, sans
écrêtage. Il est plus juste physiquement, moins photographique.

### La mise au panneau

On **ne peut pas** cadrer sur la boîte englobante 3D. En ortho inclinée, un
point proche de la caméra descend dans l'image de `tan(36°)` × sa distance : un
houppier large déborde par le haut d'un côté et par le bas de l'autre, selon
l'azimut. Et les coins bas-larges de la boîte n'existent pas (il n'y a pas de
feuilles au ras du sol sous le bord du houppier) : cadrer dessus rétrécissait
les arbres à 20 % de leur taille (constaté).

`fabriquer` projette donc les **vrais sommets** (via le graphe de dépendances,
pour que les maillages déformés par armature soient pris posés) sur les 8
azimuts, et applique l'homothétie qui fait tenir le pire cas.

### La marge basse est un réglage PAR PROP, calculé

`marge_bas = 0,12` suffit pour un objet élancé (un arbre), pas pour un objet
large et plat. En ortho inclinée de `t`, un déport horizontal de R vers la
caméra descend à l'écran de `R·sin(t)`, quand la marge n'offre que
`marge·H·cos(t)` : il faut donc `marge ≥ R·tan(t)/H`. À 36° avec 0,12, ça
plafonne le rayon à `0,165·H` — parfait pour un chêne, absurde pour un sanglier,
qui est plus long que haut.

La marge est donc **calculée par prop** et **écrite dans le manifeste**, à côté
de la valeur par défaut qui reste à la racine :

```json
{"marge_bas": 0.12,
 "props": {"sanglier": {"hauteur_m": 1.6, "marge_bas": 0.31, ...}}}
```

Elle se déduit de la descente RÉELLE de la géométrie (`s_bas`, la projection la
plus basse sur les 8 azimuts), pas de la borne théorique `1,1·R·tan(t)/H` : cette
borne suppose que tout le rayon horizontal touche le sol, ce qui est vrai d'un
quadrupède et faux d'un arbre, dont le houppier est large mais haut. Mesuré sur
le chêne vert, la borne réservait `0,328·H` pour un besoin réel de `0,107·H` —
un tiers de panneau perdu.

Échelle et marge se déterminent l'une l'autre ; `fabriquer` les résout par six
tours de point fixe. La visée en découle : le centre du panneau est à
`(0,5 − marge)·H`, ce qui redonne bien `0,38·H` quand la marge vaut 0,12.

Les hauteurs de panneau des quadrupèdes ont été relevées en conséquence
(`chevreuil` 1,7 → **2,0 m**, `sanglier` 1,2 → **1,6 m**) : mieux vaut un panneau
un peu plus haut qu'une marge qui mange tout.

**Plus aucun débordement.** Le script imprime `! <prop> vN : X px de
débordement sous le panneau` s'il en reste ; le lot livré n'en produit aucun.

### Les animaux : la variante est une pose

Pour `chevreuil`, `sanglier`, `oiseau` et `poisson`, `v0/v1/v2` ne sont pas trois
individus mais **trois instants du cycle d'animation** (`Run`, `walk`, `fly`,
`Swiming-Slow`), pris à intervalles réguliers. Le manifeste le dit :
`"variante_est": "pose"`. Ils partagent tous la même homothétie — sinon la bête
changerait de taille en marchant. Augmenter `--variantes` donne plus de poses.

Deux pièges de ces `.blend`, tous deux constatés au rendu et traités :

* ils embarquent leurs propres lampes, une caméra et un sol. Importés tels quels
  ils écrasaient notre éclairage (bêtes blanches, 0,8 de luminance mesurée) ;
* leurs matériaux sont du Blender Internal, que Blender 4 ne convertit plus : ils
  sont reconstruits en Principled sur la diffuse du fichier.

Le `.fbx` du brochet embarque en plus un plan d'eau de 2,5 m et des cercles de
projection — inclus dans la boîte, ils réduisaient le poisson à 3 cm. Seuls
l'armature et le maillage le plus dense sont conservés.

### L'ancrage : le pied de l'objet est l'origine

`(0, 0, 0)` est le **pied** de l'objet, pas le centre de sa boîte : c'est ce
point que Godot posera sur le terrain. Deux erreurs ont été mesurées avant
d'arriver là, et elles valent d'être connues :

* caler le zéro sur le sommet le plus **bas** remontait l'arbre de la hauteur de
  son rameau le plus retombant — le pied du tronc arrivait à 14,1 % du bas au
  lieu de 12 % ;
* centrer x/y sur la boîte décalait le tronc hors de l'axe, et comme un déport
  horizontal de `d` fait monter l'image de `tan(36°)·d`, la ligne de sol se
  mettait à **bouger d'un angle à l'autre** (`+0,010·H` à l'azimut 0,
  `−0,037·H` à 45°).

Les constructeurs procéduraux plantent donc le tronc en `(0,0,0)` et on n'y
touche plus ; seuls les modèles importés sont recalés. Un houppier asymétrique
sort décentré dans le panneau : c'est juste, un vrai chêne l'est aussi.

Contrôle numérique (`min_z` du maillage construit, après mise au panneau) :

| prop | min_z | en pixels |
|---|---|---|
| `chene_vert` | −0,059 m | −2,5 px |
| `chene_pubescent` | −0,026 m | −0,8 px |
| `buisson` | −0,038 m | −5,6 px |
| `rocher`, `herbe_seche`, `tas_feuilles` | 0,000 m | 0 px |

Rien ne pousse sous terre : `_rameaux` bute les points à `z ≥ 0`. Sans cette
butée, une branche retombante du chêne pubescent descendait à **1,19 m sous la
base**, ce qui faisait grimper la marge du panneau de 0,12 à 0,264 pour rien.

## La tache de contact

Ce n'est pas l'ombre portée : à 24° de hauteur de soleil, celle d'un chêne de 9 m
ferait 20 m et sortirait vingt fois du panneau. C'est un **disque attrape-ombre**
(`is_shadow_catcher`) au shader dégradé — diffus au centre, transparent au bord,
via une rampe sur la distance à l'axe. L'ombre captée s'éteint donc *avant* la
lisière du disque : pas d'arc de coupe visible, et la vraie pénombre calculée par
Cycles sur les deux premiers mètres est conservée. Un sol de rebond invisible à
la caméra (200 m, brun garrigue) fournit en plus le renvoi de lumière qui empêche
le dessous des houppiers d'être noir.
