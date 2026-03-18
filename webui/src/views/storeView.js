// /webui/src/views/storeView.js
const StoreView = {
    // The Modal HTML Template
    renderModal() {
        return `
        <div id="store-modal" class="modal-overlay" style="display:none;">
            <div class="modal-content">
                <span class="close-btn" onclick="document.getElementById('store-modal').style.display='none'">&times;</span>
                <h2>Top Up Credits</h2>
                <p>Select a package to keep your server running.</p>
                
                <div class="pricing-grid">
                    <div class="price-card">
                        <h3>Starter Pack</h3>
                        <p class="credits">500 Credits</p>
                        <p class="price">$5.00</p>
                        <div class="provider-buttons">
                            <button onclick="window.StoreController.buy('pack_starter', 'stripe')" class="btn-stripe">Pay Card</button>
                            <button onclick="window.StoreController.buy('pack_starter', 'paypal')" class="btn-paypal">PayPal</button>
                        </div>
                    </div>

                    <div class="price-card">
                        <h3>Pro Pack</h3>
                        <p class="credits">2500 Credits</p>
                        <p class="price">$20.00</p>
                        <div class="provider-buttons">
                            <button onclick="window.StoreController.buy('pack_pro', 'stripe')" class="btn-stripe">Pay Card</button>
                            <button onclick="window.StoreController.buy('pack_pro', 'paypal')" class="btn-paypal">PayPal</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        `;
    },

    // Helper to inject it into the page
    init() {
        if (!document.getElementById('store-modal')) {
            const modalHTML = this.renderModal();
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }
    },

    open() {
        const modal = document.getElementById('store-modal');
        if (modal) modal.style.display = 'flex';
    }
};

export default StoreView;