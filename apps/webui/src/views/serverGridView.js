// webui/src/views/serverGridView.js
export class ServerGridView {
    constructor() {
        this.grid = document.getElementById('server-grid');
    }

    renderServers(servers, onAction, pendingStates = new Map()) {
        this.grid.innerHTML = '';

        servers.forEach(server => {
            const isActive = server.status === 'online';
			const pendingState = pendingStates.get(server.id);
			const isLocked = pendingState !== undefined;
			
			let btnText = isActive ? 'Stop' : 'Start';
			let btnClass = isActive ? 'btn-stop' : 'btn-start';
			
			if (pendingState === 'starting') {
				btnText = 'Booting...';
				btnClass = 'btn-start';
			} else if (pendingState === 'stopping') {
				btnText = 'Stopping...';
				btnClass = 'btn-stop';
			}
			
            const card = document.createElement('section');
			card.className = 'server-card';
			card.dataset.serverId = server.id; // Store ID for reference
            
			card.innerHTML = `
				<div class="card-header">
					<h2>${server.name}</h2>
					<span class="status-indicator ${server.status}"></span>
				</div>
				<div class="card-body">
					<div class="stat-group">
						<label>Players Online: <strong>${isActive ? server.players : 0}</strong></label>
					</div>
					<div class="stat-group">
						<label>CPU: ${isActive ? server.cpu.toFixed(1) + '%' : 'N/A'}</label>
						<div class="progress-bar"><div style="width: ${server.cpu}%"></div></div>
					</div>
					<div class="stat-group">
						<label>RAM: ${isActive ? server.ram.toFixed(1) + '%' : 'N/A'}</label>
						<div class="progress-bar"><div style="width: ${server.ram}%" class="ram-fill"></div></div>
					</div>
				</div>
				<div class="card-controls">
                    <button class="action-btn ${btnClass}" ${isLocked ? 'disabled style="opacity: 0.5; cursor: not-allowed;"' : ''}>
                        ${btnText}
                    </button>
                    <button class="btn-settings">Settings</button>
                </div>
			`;

           const actionBtn = card.querySelector('.action-btn');
			actionBtn.addEventListener('click', () => {
				onAction(server.id, server.status);
			});

            this.grid.appendChild(card);
        });
    }
}