// webui/src/controllers/storeController.js
export class StoreController {
    constructor(storeView, paymentService) {
        this.storeView = storeView;
        this.paymentService = paymentService;

        this.storeView.init();

        // Bind the global window function for the Store modal buttons
        window.StoreController = {
            buy: (pkg, provider) => this.handlePurchase(pkg, provider),
            grant: (amount) => this.handleGrant(amount)
        };
    }

    async handlePurchase(packageId, provider) {
        console.log(`Processing purchase: ${packageId} via ${provider}`);
        try {
            await this.paymentService.checkout(packageId, provider);
        } catch (error) {
            console.error("Purchase failed:", error);
            alert("Failed to initialize payment.");
        }
    }

    // Remove this thing
    async handleGrant(amount) {
        try {
            // 1. Call the backend
            const result = await this.paymentService.grantcredits(amount);

            alert(`Success! 100 free credits added. You now have ${result.new_balance}.`);

            // Optional: Close the store modal automatically
            document.getElementById('store-modal').style.display = 'none';

        } catch (error) {
            alert("Failed to redeem promo code.");
        }
    }

    openStore() {
        this.storeView.open();
    }
}