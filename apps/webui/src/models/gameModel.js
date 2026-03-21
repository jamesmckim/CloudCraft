// webui/scr/models/gameModel.js
export class GameModel {
    async fetchAvailableGames() {
        // Current: Local Data
        const localData = [
            { id: 'valheim', name: 'Valheim', icon: '🌲', version: '0.217.38' },
            { id: 'minecraft', name: 'Minecraft', icon: '⛏️', version: '1.20.4' },
            { id: 'rust', name: 'Rust', icon: '☢️', version: 'Latest' },
            { id: 'palworld', name: 'Palworld', icon: '🥚', version: 'v0.1.4.1' }
        ];
        
        // Future: return await fetch('api/games').then(r => r.json());
        return localData;
    }
};