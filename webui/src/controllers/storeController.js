// webui/src/controllers/storeController.js
export class StoreController {
    constructor(storeView, paymentService) {
        this.storeView = storeView;
		this.paymentService = paymentService;
		
		this.storeView.init();
        
        // Bind the global window function for the Store modal buttons
        window.StoreController = {
            buy: (pkg, provider) => this.handlePurchase(pkg, provider)
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

    openStore() {
        this.storeView.open();
    }
}