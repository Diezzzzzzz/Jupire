// Serveur de jeu autoritaire-léger pour le proto étape 0.
// Une seule "pièce" de 2 joueurs. Code jetable assumé (cf. doc 13).
import { WebSocketServer } from 'ws';

const ROOM_W = 1000;
const ROOM_H = 700;
const NUM_OBJECTS = 3; // 🔴 🟢 🔵
const TICK_MS = 50; // 20 Hz

/** @typedef {{ id:number, role:'giver'|'seeker', x:number, y:number, sym:number, symAt:number, ws:any }} Player */

function makeRoom() {
	return {
		/** @type {Player[]} */
		players: [],
		target: Math.floor(Math.random() * NUM_OBJECTS),
		round: 1,
		score: 0,
		// feedback éphémère après un "give" : { ok, given, target, at }
		flash: null
	};
}

export function attachGameServer(httpServer) {
	const wss = new WebSocketServer({ server: httpServer, path: '/ws' });
	const room = makeRoom();
	let nextId = 1;

	function newRound(keepScore = true) {
		room.target = Math.floor(Math.random() * NUM_OBJECTS);
		room.round += 1;
		if (!keepScore) room.score = 0;
	}

	function snapshotFor(p) {
		const now = Date.now();
		return {
			t: 'state',
			roomW: ROOM_W,
			roomH: ROOM_H,
			numObjects: NUM_OBJECTS,
			round: room.round,
			score: room.score,
			you: p.id,
			role: p.role,
			// le seeker voit sa cible ; le giver ne la voit JAMAIS (asymétrie = cœur du test)
			target: p.role === 'seeker' ? room.target : null,
			peers: room.players.length,
			flash: room.flash,
			players: room.players.map((q) => ({
				id: q.id,
				role: q.role,
				x: q.x,
				y: q.y,
				// symbole encore "vivant" (< 3s) ?
				sym: now - q.symAt < 3000 ? q.sym : -1
			}))
		};
	}

	function broadcast() {
		for (const p of room.players) {
			if (p.ws.readyState === 1) p.ws.send(JSON.stringify(snapshotFor(p)));
		}
	}

	wss.on('connection', (ws) => {
		if (room.players.length >= 2) {
			ws.send(JSON.stringify({ t: 'full' }));
			ws.close();
			return;
		}
		const role = room.players.some((p) => p.role === 'giver') ? 'seeker' : 'giver';
		/** @type {Player} */
		const player = {
			id: nextId++,
			role,
			x: role === 'giver' ? ROOM_W * 0.3 : ROOM_W * 0.7,
			y: ROOM_H * 0.5,
			sym: -1,
			symAt: 0,
			ws
		};
		room.players.push(player);

		ws.on('message', (buf) => {
			let msg;
			try {
				msg = JSON.parse(buf.toString());
			} catch {
				return;
			}
			if (msg.t === 'move') {
				player.x = Math.max(0, Math.min(ROOM_W, +msg.x || 0));
				player.y = Math.max(0, Math.min(ROOM_H, +msg.y || 0));
			} else if (msg.t === 'symbol') {
				const s = +msg.s;
				if (s >= 0 && s < 6) {
					player.sym = s;
					player.symAt = Date.now();
				}
			} else if (msg.t === 'give' && player.role === 'giver') {
				const given = +msg.obj;
				const ok = given === room.target;
				if (ok) room.score += 1;
				room.flash = { ok, given, target: room.target, at: Date.now() };
				// nouveau round après un court délai (le feedback reste visible)
				const prevTarget = room.target;
				setTimeout(() => {
					if (room.flash && room.flash.at) newRound(true);
					room.flash = null;
				}, 1800);
				void prevTarget;
			}
		});

		ws.on('close', () => {
			const i = room.players.indexOf(player);
			if (i >= 0) room.players.splice(i, 1);
		});
	});

	const interval = setInterval(broadcast, TICK_MS);
	wss.on('close', () => clearInterval(interval));

	return wss;
}
