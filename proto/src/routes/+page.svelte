<script lang="ts">
	import { onMount } from 'svelte';

	// — Constantes partagées (doivent matcher gameServer.js) —
	const SYMBOLS = ['○', '△', '□', '◇', '☆', '⬡']; // 6 glyphes abstraits, AUCUN texte
	const OBJ_COLORS = ['#e0533d', '#46b06a', '#4a90d9']; // 🔴 🟢 🔵
	const OBJ_NAMES = ['', '', '']; // volontairement vide : pas de mots

	type PeerState = { id: number; role: string; x: number; y: number; sym: number };
	type Snapshot = {
		roomW: number;
		roomH: number;
		numObjects: number;
		round: number;
		score: number;
		you: number;
		role: 'giver' | 'seeker';
		target: number | null;
		peers: number;
		flash: { ok: boolean; given: number; target: number; at: number } | null;
		players: PeerState[];
	};

	let snap = $state<Snapshot | null>(null);
	let status = $state<'connecting' | 'connected' | 'full' | 'closed'>('connecting');
	let canvas: HTMLCanvasElement;

	let ws: WebSocket;
	const local = { x: 0, y: 0, init: false };
	const keys = new Set<string>();
	let lastSent = 0;

	const role = $derived(snap?.role ?? null);
	const target = $derived(snap?.target ?? null);

	function send(obj: unknown) {
		if (ws && ws.readyState === 1) ws.send(JSON.stringify(obj));
	}

	function emitSymbol(i: number) {
		send({ t: 'symbol', s: i });
	}
	function give(i: number) {
		if (role === 'giver') send({ t: 'give', obj: i });
	}

	onMount(() => {
		const proto = location.protocol === 'https:' ? 'wss' : 'ws';
		ws = new WebSocket(`${proto}://${location.host}/ws`);
		ws.onopen = () => (status = 'connected');
		ws.onclose = () => (status = status === 'full' ? 'full' : 'closed');
		ws.onmessage = (e) => {
			const m = JSON.parse(e.data);
			if (m.t === 'full') {
				status = 'full';
				return;
			}
			if (m.t === 'state') {
				snap = m;
				const me = m.players.find((p: PeerState) => p.id === m.you);
				if (me && !local.init) {
					local.x = me.x;
					local.y = me.y;
					local.init = true;
				}
			}
		};

		const onKey = (down: boolean) => (ev: KeyboardEvent) => {
			const k = ev.key.toLowerCase();
			if (['arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(k)) ev.preventDefault();
			if (down && k >= '1' && k <= '6') emitSymbol(+k - 1);
			else keys[down ? 'add' : 'delete'](k);
		};
		const kd = onKey(true);
		const ku = onKey(false);
		window.addEventListener('keydown', kd);
		window.addEventListener('keyup', ku);

		let raf = 0;
		const loop = () => {
			step();
			draw();
			raf = requestAnimationFrame(loop);
		};
		raf = requestAnimationFrame(loop);

		return () => {
			cancelAnimationFrame(raf);
			window.removeEventListener('keydown', kd);
			window.removeEventListener('keyup', ku);
			ws.close();
		};
	});

	const SPEED = 4;
	function step() {
		if (!snap || !local.init) return;
		let dx = 0;
		let dy = 0;
		if (keys.has('w') || keys.has('arrowup')) dy -= 1;
		if (keys.has('s') || keys.has('arrowdown')) dy += 1;
		if (keys.has('a') || keys.has('arrowleft')) dx -= 1;
		if (keys.has('d') || keys.has('arrowright')) dx += 1;
		if (dx || dy) {
			const n = Math.hypot(dx, dy) || 1;
			local.x = Math.max(0, Math.min(snap.roomW, local.x + (dx / n) * SPEED));
			local.y = Math.max(0, Math.min(snap.roomH, local.y + (dy / n) * SPEED));
		}
		const now = performance.now();
		if (now - lastSent > 45) {
			send({ t: 'move', x: local.x, y: local.y });
			lastSent = now;
		}
	}

	function draw() {
		const ctx = canvas?.getContext('2d');
		if (!ctx || !snap) return;
		const W = snap.roomW;
		const H = snap.roomH;
		canvas.width = W;
		canvas.height = H;

		// sol
		ctx.fillStyle = '#1c1f26';
		ctx.fillRect(0, 0, W, H);
		ctx.strokeStyle = '#2c313c';
		ctx.lineWidth = 1;
		for (let x = 0; x <= W; x += 50) {
			ctx.beginPath();
			ctx.moveTo(x, 0);
			ctx.lineTo(x, H);
			ctx.stroke();
		}
		for (let y = 0; y <= H; y += 50) {
			ctx.beginPath();
			ctx.moveTo(0, y);
			ctx.lineTo(W, y);
			ctx.stroke();
		}

		for (const p of snap.players) {
			const isMe = p.id === snap.you;
			const x = isMe ? local.x : p.x;
			const y = isMe ? local.y : p.y;
			// corps (capsule = cercle ici)
			ctx.beginPath();
			ctx.arc(x, y, 18, 0, Math.PI * 2);
			ctx.fillStyle = p.role === 'giver' ? '#d9a441' : '#7e6bd9';
			ctx.fill();
			ctx.lineWidth = isMe ? 3 : 1.5;
			ctx.strokeStyle = isMe ? '#fff' : '#0008';
			ctx.stroke();
			// symbole flottant
			if (p.sym >= 0) {
				ctx.font = '40px serif';
				ctx.textAlign = 'center';
				ctx.fillStyle = '#fff';
				ctx.fillText(SYMBOLS[p.sym], x, y - 34);
			}
		}
	}

	const flashOk = $derived(snap?.flash && snap.flash.ok);
	const flashShow = $derived(!!snap?.flash);
</script>

<div class="wrap">
	<div class="hud">
		<div class="brand">Jupire <span>· proto étape 0</span></div>
		{#if snap}
			<div class="meta">
				<span>round <b>{snap.round}</b></span>
				<span>compris <b>{snap.score}</b></span>
				<span class="role" class:giver={role === 'giver'} class:seeker={role === 'seeker'}>
					{role === 'giver' ? 'tu DONNES' : 'tu CHERCHES'}
				</span>
				<span class="peers">{snap.peers}/2</span>
			</div>
		{/if}
	</div>

	{#if status === 'full'}
		<div class="overlay">La pièce est pleine (2 joueurs max). Ferme un onglet et réessaie.</div>
	{:else if status === 'closed'}
		<div class="overlay">Connexion perdue. Recharge la page.</div>
	{:else if !snap}
		<div class="overlay">Connexion…</div>
	{/if}

	<div class="stage">
		<canvas bind:this={canvas}></canvas>
		{#if flashShow}
			<div class="flash" class:ok={flashOk}>{flashOk ? '✓' : '✗'}</div>
		{/if}
	</div>

	{#if snap}
		<div class="panel">
			{#if role === 'seeker'}
				<div class="want">
					<span class="lbl">tu veux&nbsp;:</span>
					{#if target !== null}
						<span class="chip big" style="--c:{OBJ_COLORS[target]}"></span>
					{/if}
					<span class="hint">fais-le comprendre — bouge, montre les symboles. Aucun mot.</span>
				</div>
			{:else}
				<div class="want"><span class="hint">devine ce qu'il veut, puis donne-le ↓</span></div>
			{/if}

			<div class="objects">
				{#each OBJ_COLORS as c, i}
					<button
						class="obj"
						style="--c:{c}"
						disabled={role !== 'giver'}
						onclick={() => give(i)}
						title={OBJ_NAMES[i]}
					></button>
				{/each}
			</div>

			<div class="symbols">
				{#each SYMBOLS as s, i}
					<button class="sym" onclick={() => emitSymbol(i)}>
						<span>{s}</span><kbd>{i + 1}</kbd>
					</button>
				{/each}
			</div>

			<div class="help">déplacement <kbd>ZQSD</kbd>/<kbd>flèches</kbd> · symboles <kbd>1–6</kbd></div>
		</div>
	{/if}
</div>

<style>
	:global(body) {
		background: #14161b;
		color: #e7e9ee;
		font-family: ui-sans-serif, system-ui, sans-serif;
	}
	.wrap {
		max-width: 1040px;
		margin: 0 auto;
		padding: 14px 16px 28px;
	}
	.hud {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		margin-bottom: 10px;
	}
	.brand {
		font-weight: 700;
		letter-spacing: 0.5px;
	}
	.brand span {
		font-weight: 400;
		color: #8a90a0;
		font-size: 0.85em;
	}
	.meta {
		display: flex;
		gap: 14px;
		align-items: center;
		font-size: 0.9em;
		color: #aeb4c2;
	}
	.meta b {
		color: #fff;
	}
	.role {
		padding: 2px 9px;
		border-radius: 99px;
		font-weight: 700;
		font-size: 0.8em;
	}
	.role.giver {
		background: #d9a44122;
		color: #d9a441;
	}
	.role.seeker {
		background: #7e6bd922;
		color: #9d8df0;
	}
	.peers {
		color: #6b7180;
	}
	.stage {
		position: relative;
		border-radius: 10px;
		overflow: hidden;
		box-shadow: 0 6px 30px #0006;
	}
	canvas {
		display: block;
		width: 100%;
		height: auto;
		background: #1c1f26;
	}
	.overlay {
		text-align: center;
		padding: 14px;
		background: #2a2f3a;
		border-radius: 8px;
		margin-bottom: 10px;
		color: #c9cedb;
	}
	.flash {
		position: absolute;
		inset: 0;
		display: grid;
		place-items: center;
		font-size: 160px;
		font-weight: 800;
		color: #e0533d;
		background: #e0533d18;
		animation: pop 0.25s ease;
	}
	.flash.ok {
		color: #46b06a;
		background: #46b06a18;
	}
	@keyframes pop {
		from {
			transform: scale(0.6);
			opacity: 0;
		}
	}
	.panel {
		margin-top: 14px;
		display: flex;
		flex-direction: column;
		gap: 12px;
		align-items: center;
	}
	.want {
		display: flex;
		gap: 10px;
		align-items: center;
		min-height: 30px;
	}
	.want .lbl {
		color: #aeb4c2;
	}
	.hint {
		color: #7c8290;
		font-size: 0.9em;
	}
	.chip {
		display: inline-block;
		border-radius: 99px;
		background: var(--c);
	}
	.chip.big {
		width: 26px;
		height: 26px;
		box-shadow: 0 0 0 3px #fff2;
	}
	.objects {
		display: flex;
		gap: 14px;
	}
	.obj {
		width: 58px;
		height: 58px;
		border-radius: 99px;
		border: 3px solid #fff3;
		background: var(--c);
		cursor: pointer;
		transition: transform 0.08s;
	}
	.obj:not(:disabled):hover {
		transform: scale(1.08);
		border-color: #fff;
	}
	.obj:disabled {
		opacity: 0.5;
		cursor: default;
	}
	.symbols {
		display: flex;
		gap: 8px;
	}
	.sym {
		width: 52px;
		height: 52px;
		border-radius: 10px;
		border: 1px solid #3a4150;
		background: #232833;
		color: #e7e9ee;
		font-size: 22px;
		cursor: pointer;
		position: relative;
		display: grid;
		place-items: center;
	}
	.sym:hover {
		background: #2d3340;
		border-color: #5a6275;
	}
	.sym kbd {
		position: absolute;
		bottom: 2px;
		right: 4px;
		font-size: 9px;
		color: #6b7180;
	}
	kbd {
		background: #2a2f3a;
		border-radius: 4px;
		padding: 1px 5px;
		font-size: 0.85em;
		border: 1px solid #3a4150;
	}
	.help {
		color: #6b7180;
		font-size: 0.85em;
	}
</style>
