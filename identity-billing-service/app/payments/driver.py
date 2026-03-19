# /identity-billing-service/app/payments/driver.py
import abc

class PaymentProvider(abc.ABC):
    @abc.abstractmethod
    def create_checkout_session(self, package_id: str, user_id: str) -> dict:
        pass

    @abc.abstractmethod
    def verify_webhook(self, raw_payload: bytes, headers: dict) -> dict | None:
        pass