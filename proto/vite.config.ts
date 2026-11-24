import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig, type PluginOption } from 'vite';
import { attachGameServer } from './gameServer.js';

// Greffe le serveur WebSocket de jeu sur le serveur HTTP de Vite (dev + preview).
function gameServerPlugin(): PluginOption {
	return {
		name: 'jupire-game-server',
		configureServer(server) {
			if (server.httpServer) attachGameServer(server.httpServer);
		},
		configurePreviewServer(server) {
			if (server.httpServer) attachGameServer(server.httpServer);
		}
	};
}

export default defineConfig({
	plugins: [sveltekit(), gameServerPlugin()]
});
