# /backend/app/payments/driver.py
import abc

class PaymentProvider(abc.ABC):
    @abc.abstractmethod
    def create_checkout_session(self, package_id: str, user_id: str):
        """
        Returns: {"url": "https://..."}
        """
        pass

    @abc.abstractmethod
    def verify_webhook(self, request_data: dict):
        """
        Returns: {"user_id": "123", "credits": 500, "status": "paid"} or None
        """
        pass