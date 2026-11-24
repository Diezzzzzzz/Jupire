# Fog of war & caméra

> Décision clé : le **fog of war découple la caméra de la perception**. C'est le
> brouillard qui gère la limite de ce que le perso *connaît*, pas le zoom. Donc on
> peut garder une god-view sans devenir omniscient.

## Le brouillard calculé sur le VRAI relief (idée maîtresse)

Ne PAS calculer le fog comme un rayon plat (StarCraft). Le calculer en
**ligne de vue (viewshed) sur le terrain 3D réel** :

- **Fond de gorge** : les falaises **bloquent** la vue → vision minuscule, on ne
  voit ni par-dessus la paroi ni après le méandre. Le relief enferme.
- **Belvédère** : la ligne de vue porte loin → vaste zone révélée d'un coup.

→ **La verticalité PILOTE le brouillard.** L'asymétrie « monter = comprendre où l'on
est / descendre = rencontrer » devient la mécanique elle-même, et elle **émerge
gratuitement du MNT**. On ne la designe pas, le terrain réel la produit.

## Les trois états (fog of war détourné pour l'exploration sociale)

1. **Inexploré** — noir, inconnu.
2. **Exploré mais hors-vue → brume** — on se souvient du terrain + du *dernier état
   vu*, mais le live est caché. On sait que « c'est là », pas ce qui s'y passe *maintenant*.
3. **Visible** — live, animé, à jour.

**L'information se périme** : « si dans la brume il se passe quelque chose, il faut
re-aller voir ». Le monde ne ment pas — il montre un **souvenir**, et les souvenirs
vieillissent. Donne de la valeur à l'éclaireur, aux points hauts, à la patrouille.

## Ce que ça renforce

- **La carte = le paysage** : le brouillard *est* la mémoire du joueur. Explorer = dessiner sa carte mentale.
- **Incertitude sociale** : état réel du hors-vue inconnu → rumeur, prudence, repérage.
- **Belvédères** : révèlent de vastes zones → lieux stratégiques/sociaux. Mais le
  lointain reste *flou* (pilier imprécision : on révèle la zone, pas le détail).
- **Anonymat** : brume + distance brouillent qui est qui.

## Décision caméra : god-view dimétrique angulée + dézoom libre + fog LoS

- **Angle** (SC4/AoE, pas top-down pur) → montre les **faces de falaise** → on *lit*
  la verticalité (un top-down l'aplatirait).
- **Dézoom libre** → sentir qu'on est minuscule au fond de la gorge.
- **Fog en ligne de vue** → non-omniscient malgré la god-view.

Renforcer le vertige sans baisser la caméra : ombres longues, échelle (perso
minuscule vs paroi), brume atmosphérique épaississant avec la distance, **caméra
contextuelle** qui s'abaisse/se resserre dans les passages étroits.

Résout l'hésitation god-view vs caméra basse : on garde les deux bénéfices, et on
reste fidèle à la DA sprite.

## Rendu de la brume

Zones brume = désaturées / brumeuses, sprites du *dernier état vu* « gelés » ;
zones live = couleur pleine + animées. Très cohérent avec la DA peinture/SC4.

## Gardes-fous

- **Multijoueur** : fog **calculé côté serveur** (le client ne reçoit que ce que le
  perso voit) → sinon maphack / voir à travers les falaises. Rejoint le serveur autoritaire.
- **LoS sur terrain 3D = vraie feature** (calcul de viewshed, plus coûteux qu'un fog
  plat). Faisable mais à budgéter, pas un détail.

## AMENDEMENT (2026-07-27, constaté au proto) — deux axes, pas un

En implémentant le fog, une erreur est apparue : les **trois états** ci-dessus mélangent
deux dimensions indépendantes, et les traiter comme une seule échelle produit un rendu
faux (du noir là où, dans la vraie vie, on *voit* quelque chose).

| Axe | Nature | Ce qu'il dit |
|---|---|---|
| **Connaissance** (mémoire) | discret | jamais vu · souvenir · actuel |
| **Distance** (perception) | **continu** | net tout près, imprécis au loin |

- Le **noir** ne vaut que pour ce que le **relief masque** — derrière une crête, on ne
  voit réellement rien. Là, il est juste.
- Ce qui est **en vue directe mais lointain** doit être **visible et imprécis** :
  couleurs délavées, air épaissi, formes sans détail. Pas noir.

> C'est la phrase-ancre du doc 00 rendue littérale : **« voir beaucoup mais pas
> précisément. »** On distingue la montagne dès le premier jour ; on ne sait pas ce
> qu'il y a dessus tant qu'on n'y est pas allé.

Deux portées distinctes en découlent, et ce sont deux réglages de design différents :
- **la netteté** (~150–250 m) : au-delà, on voit sans savoir ;
- **la visibilité** (~2–5 km) : au-delà, la brume ferme l'horizon.

Bénéfice inattendu : cette gradation **est** le niveau de détail dont le moteur a besoin
pour streamer un monde immense (doc 33/35) — proche = fin et marchable, lointain = une
silhouette. La hiérarchie perceptive et la hiérarchie technique demandent la même chose,
ce qui est le meilleur signe qu'on est sur la bonne architecture. Rejoint doc 26 :
« la silhouette est le nom du lieu ».

## Question ouverte

**Qu'est-ce qui persiste dans la brume ?**
- Option A : juste le **terrain** (on se souvient du relief, mais ni gens ni changements).
- Option B : aussi le **dernier état vu des entités** (campement « gelé » là où on l'a laissé).
→ Change à quel point le monde « ment » et la force de la boucle « re-aller voir ».
