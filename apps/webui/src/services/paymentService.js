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
    },

    // 2. DEV MODE: Grant Free Credits for Testing
    async grantcredits(amount) {
        try {

            const numericAmount = parseFloat(amount);

            const response = await Auth.call('/api/users/me/add-funds', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ amount: numericAmount })
            });

            if (!response.ok) {
                const errorData = await response.json();
                console.error("FastAPI Error:", errorData);
                throw new Error('Failed to add credits');
            }

            // This should return { status: "success", new_balance: X }
            return await response.json();
        } catch (error) {
            console.error("Grant Credits Error:", error);
            throw error; // Let the controller catch and show the alert
        }
    }
};

export default PaymentService;