// webui/src/models/dashboardModel.js
import Auth from '../services/authService.js';

export class DashboardModel {
    // 1. Unified Request Wrapper
    async #request(endpoint, options = {}) {
        try {
            const response = await Auth.call(endpoint, options);
			
            // Fetch does NOT throw on 404/500, so we do it manually
            if (!response.ok) {
                const errorBody = await response.json().catch(() => ({}));
                throw new Error(errorBody.detail || `HTTP Error ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`[Model Error] ${endpoint}:`, error.message);
            throw error; 
        }
    }

    /**
     * Fetches the list of all managed containers
     */
    async getAllServers() {
        return this.#request('/api/servers');
    }
	
	async getProfile() {
        // This endpoint returns user data based on the Bearer Token
        const response = await Auth.call('/api/users/me');
		if (!response.ok) throw new Error("Failed to fetch profile");
		return await response.json();
    }

    /**
     * Fetches status and telemetry for a specific server
     * @param {string} serverId - The Docker container ID or name
     */
    async getServerDetails(serverId) {
        // Combined status/stats call for efficiency in a grid view
        return this.#request(`/api/servers/${serverId}`);
    }

    /**
     * Sends start/stop/restart commands for a specific server
     * @param {string} serverId 
     * @param {string} action - 'start', 'stop', or 'restart'
     */
    async sendPowerAction(serverId, action) {
        return this.#request(`/api/servers/${serverId}/power`, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action }) 
        });
    }
	
	/**
     * Deploys a new server instance
     * @param {string} gameId - The template ID (e.g., 'valheim', 'minecraft')
     * @param {object} configData - The dynamic environment variables gathered from the form
     */
    async deployServer(gameId, configData = {}) {
        return this.#request('/api/servers/deploy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
				game_id: gameId,
				config: configData
			})
        });
    }
}