// webui/scr/views/gameView.js
export class GameView {
    renderGrid(games) {
        const grid = document.querySelector('.game-grid');
		if (!grid) return;
		
	grid.innerHTML = games.map(game => {
			// Conditionally render an input form for Valheim
			let configForm = '';
			if (game.id === 'valheim') {
				configForm = `
					<div class="server-config" style="text-align: left; padding: 10px; font-size: 0.9em;">
						<label>Server Name: <input type="text" id="${game.id}-name" value="YourServerName"></label><br>
						<label>World Name: <input type="text" id="${game.id}-world" value="ThisIsTest"></label><br>
						<label>Password: <input type="password" id="${game.id}-pass" value="YourSecretPassword"></label><br>
						<label>Update Cron: <input type="text" id="${game.id}-cron" value="0 6 * * *"></label><br>
						<label>Max Backups: <input type="number" id="${game.id}-backups" value="5"></label>
					</div>
				`;
			}

			return `
				<div class="server-card game-card">
					<div class="card-header">
						<h2>${game.name}</h2>
						<span class="status-indicator online" style="background: #ebf5ff; color: #3498db;">Stable</span>
					</div>
					<div class="card-body" style="text-align: center; padding: 20px 0;">
						<div style="font-size: 3rem; margin-bottom: 10px;">${game.icon}</div>
						<p><strong>Version:</strong> ${game.version}</p>
					</div>
					${configForm}
					<div class="card-controls">
						<button class="btn-login deploy-btn" data-id="${game.id}">Deploy Server</button>
					</div>
				</div>
			`;
		}).join('');
	}
};