// webui/src/views/navigationView.js
export class NavigationView {
    constructor() {
        this.navButtons = document.querySelectorAll('.nav-btn');
        this.tabs = document.querySelectorAll('.tab-content');
        this.nameEl = document.getElementById('display-username');
        this.creditEl = document.getElementById('display-credits');
		this.buyBtn = document.getElementById('btn-buy-credits');
    }

    bindTabSwitch(handler) {
        this.navButtons.forEach(btn => {
            btn.addEventListener('click', () => handler(btn.dataset.tab));
        });
    }

    showTab(tabId) {
        this.navButtons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabId);
        });
        this.tabs.forEach(tab => {
            tab.classList.toggle('active', tab.id === `tab-${tabId}`);
        });
    }
	
	bindOpenStore(handler) {
		if (this.buyBtn) {
			this.buyBtn.addEventListener('click', handler);
		} else {
			console.warn("Buy Credits button (id='btn-buy-credits') not found in HTML");
		}
	}

    updateAccountInfo(user) {
        if (this.nameEl) this.nameEl.textContent = user.username;
        if (this.creditEl) this.creditEl.textContent = parseFloat(user.credits).toFixed(2);
    }
}