# /backend/config/packages.py

CREDIT_PACKAGES = {
    "pack_starter": {
        "name": "Starter Pack",
        "credits": 500,
        "price_usd": 5.00,
        "stripe_price_id": "price_1Qx...",  # From Stripe Dashboard
        "paypal_sku": "sku_starter"         # Arbitrary string for PayPal
    },
    "pack_pro": {
        "name": "Pro Pack",
        "credits": 2500,
        "price_usd": 20.00,
        "stripe_price_id": "price_1Qy...",
        "paypal_sku": "sku_pro"
    }
}