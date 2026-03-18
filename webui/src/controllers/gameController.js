// webui/src/controllers/gameController.js
export class GameController {
    constructor(model, view, dashModel) {
        this.model = model;
        this.view = view;
        this.dashModel = dashModel; // Needed to trigger deployment
    }

    async loadGames() {
        try {
            const games = await this.model.fetchAvailableGames();
            this.view.renderGrid(games);
        } catch (err) {
            this.view.showError("Error loading games from CraftCloud.");
        }
    }

    async handleDeploy(gameId, button) {
        button.disabled = true;
        button.textContent = 'Deploying...';

		let configData = {};
		if(gameId === 'valheim') {
			configData = {
				VALHEIM_SERVER_NAME: document.getElementById(`${gameId}-name`).value,
				VALHEIM_WORLD_NAME: document.getElementById(`${gameId}-world`).value,
				VALHEIM_SERVER_PASS: document.getElementById(`${gameId}-pass`).value,
				VALHEIM_UPDATE_CRON: document.getElementById(`${gameId}-cron`).value,
				VALHEIM_BACKUPS_MAX_COUNT: document.getElementById(`${gameId}-backups`).value
			};
		}
		
        try {
            await this.dashModel.deployServer(gameId, configData);
			
            alert(`Success! ${gameId} is spinning up.`);
            button.textContent = 'Active';
            button.style.background = '#2ecc71';
        } catch (err) {
            button.disabled = false;
            button.textContent = 'Deploy Server';
            alert("Deployment failed.");
        }
    }
}