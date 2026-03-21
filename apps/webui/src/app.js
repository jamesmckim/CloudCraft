import { DashboardModel } from './models/dashboardModel.js';
import { GameModel } from './models/gameModel.js';
import { NavigationView } from './views/navigationView.js';
import { ServerGridView } from './views/serverGridView.js';
import { GameView } from './views/gameView.js';

import { AuthController } from './controllers/authController.js';
import { DashboardController } from './controllers/dashboardController.js';
import { GameController } from './controllers/gameController.js';
import { StoreController } from './controllers/storeController.js';

import StoreView from './views/storeView.js';
import PaymentService from './services/paymentService.js';

// Initialize Models and Views
const dashModel = new DashboardModel();
const gameModel = new GameModel();
const navView = new NavigationView();
const gridView = new ServerGridView();
const gameView = new GameView();

// Initialize Controllers
const dashCtrl = new DashboardController(dashModel, gridView, navView);
const gameCtrl = new GameController(gameModel, gameView, dashModel);
const authCtrl = new AuthController(startApp);
const storeCtrl = new StoreController(StoreView, PaymentService);

async function startApp() {
    document.getElementById('login-overlay').style.display = 'none';

    // 1. Tab Switching Logic
    navView.bindTabSwitch((tabId) => {
        navView.showTab(tabId);
		// Quick data refresh
        if (tabId === 'dashboard') dashCtrl.refresh();
        if (tabId === 'selection') gameCtrl.loadGames();
    });
	
	navView.bindOpenStore(() => {
        storeCtrl.openStore();
    });
	
    // 2. Global Event Delegation (Deployment)
    document.querySelector('.game-grid')?.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-login');
        if (btn) gameCtrl.handleDeploy(btn.getAttribute('data-id'), btn);
    });

    // 3. Start Heartbeat
    dashCtrl.startHeartbeat(3000);
}

// Initial Entry Point
authCtrl.init();