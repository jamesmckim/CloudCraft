// webui/src/controllers/dashboardController.js
export class DashboardController {
    constructor(model, view, navView) {
        this.model = model;
        this.view = view;
		this.navView = navView;
		this.pendingStates = new Map();
		this.currentServers = [];
    }

    async refresh() {
        try {
            const [serverList, user] = await Promise.all([
				this.model.getAllServers().catch(() => []),
				this.model.getProfile()
            ]);
			
			this.updateUserUI(user);
			
            if (serverList.length > 0) {
                const detailPromises = serverList.map(server => 
                    this.model.getServerDetails(server.id)
                );
                this.currentServers = await Promise.all(detailPromises);
                
				this.currentServers.forEach(server => {
                    const pending = this.pendingStates.get(server.id);
                    if (pending === 'starting' && server.status === 'online') {
                        this.pendingStates.delete(server.id);
                    } else if (pending === 'stopping' && server.status === 'offline') {
                        this.pendingStates.delete(server.id);
                    }
                });
				
                this.view.renderServers(this.currentServers, this.handleServerAction.bind(this), this.pendingStates);
            } else {
                this.view.renderServers([], this.handleServerAction.bind(this), this.pendingStates);
            }

        } catch (err) {
            console.error("Dashboard Sync Error:", err);
        }
    }

    updateUserUI(user) {
        if (this.navView) {
			this.navView.updateAccountInfo(user);
		}
    }

    async handleServerAction(serverId, currentStatus) {
        if (this.pendingStates.has(serverId)) return;

        try {
            const action = (currentStatus === 'online') ? 'stop' : 'start';
            
            // 2. Mark as pending and immediately lock the UI
            this.pendingStates.set(serverId, action === 'start' ? 'starting' : 'stopping');
            this.view.renderServers(this.currentServers, this.handleServerAction.bind(this), this.pendingStates);

            // 3. Send the command to the backend
            await this.model.sendPowerAction(serverId, action);
            await this.refresh(); 
        } catch (err) {
            // 4. If it fails (e.g., out of credits), unlock the button so they can try again
            this.pendingStates.delete(serverId);
            this.refresh();
            alert(`Action failed: ${err.message}`);
        }
    }

    startHeartbeat(ms = 3000) {
        this.refresh();
        return setInterval(() => this.refresh(), ms);
    }
}