# Jupire — proto étape 0

> Le test de l'âme (doc 13) : **deux inconnus se comprennent-ils sans un mot — et est-ce joyeux ?**
> Code jetable assumé. Ce n'est pas le jeu, c'est l'épreuve de son cœur.

## Lancer

```bash
npm install
npm run dev
```

→ http://localhost:5180

Le serveur WebSocket de jeu est greffé sur le serveur de dev Vite (même port, `/ws`).
Une seule commande, rien d'autre à démarrer.

## Jouer (2 joueurs)

- **Onglet 1** = premier connecté = **DONNEUR** (capsule dorée). Il a 3 objets 🔴🟢🔵.
- **Onglet 2** = **CHERCHEUR** (capsule violette). Il voit *en privé* lequel des 3 il veut,
  mais ne peut **rien écrire** : seulement bouger et émettre 6 symboles abstraits.
- Le donneur doit **deviner** et cliquer le bon objet. Bon → `✓`, score +1, nouveau round.

Contrôles : déplacement `ZQSD`/flèches · symboles `1`–`6` (ou clic).

**Le point** : les 6 symboles ne correspondent à *rien* de prédéfini. Les deux joueurs
doivent **inventer leur convention**. L'étincelle = le moment « on s'est compris ! ».

## Tester avec un pote

- **Même réseau** : il ouvre l'URL `Network:` affichée au démarrage (http://TON_IP:5180).
- **À distance** : un tunnel, ex. `npx cloudflared tunnel --url http://localhost:5180`
  (le client passe en `wss://` tout seul derrière https).

## Critère de réussite (doc 13)

Si toi + un pote ressentez le **frisson de la compréhension partagée** → feu vert.
Sinon → itérer sur le canal (nombre de symboles, persistance des signes, gestes/pointage)
avant de conclure. Ne **rien** ajouter d'autre (terrain, fog, naissances) avant ce feu vert.

## Pile

SvelteKit + Svelte 5 (client, canvas 2D vue de dessus) · `ws` (serveur de jeu, greffé sur Vite).
Choix web assumé : zone de confort, partage par URL, jetable. Le débat « moteur du jeu
complet » (Godot vs web/Three.js) est reporté *après* le feu vert.
```
