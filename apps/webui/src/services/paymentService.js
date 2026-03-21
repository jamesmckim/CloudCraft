// /webui/src/services/paymentService.js
import Auth from './authService.js';

const PaymentService = {
    // 1. Buy Credits (Redirects to Stripe/PayPal)
    async checkout(packageId, provider) {
        try {
            const response = await Auth.call('/api/payments/checkout', {
                method: 'POST',
                body: JSON.stringify({
                    package_id: packageId,
                    provider: provider // 'stripe' or 'paypal'
                })
            });

            const data = await response.json();
            
            // If the backend returns a URL, we must redirect the browser there
            if (data.url) {
                window.location.href = data.url;
            }
        } catch (error) {
            console.error("Payment Error:", error);
            alert("Failed to initialize payment: " + error.message);
        }
    }
};

export default PaymentService;