import os
import uuid
from config import YOOMONEY_WALLET, PLANS

def generate_label(user_id: int, plan: str) -> str:
    """Уникальная метка платежа для идентификации"""
    return f"vpn_{user_id}_{plan}_{uuid.uuid4().hex[:8]}"

def build_payment_url(label: str, amount: float, comment: str) -> str:
    """Ссылка на форму оплаты ЮMoney (shop-форма, карта AC)"""
    from urllib.parse import quote
    base = "https://yoomoney.ru/quickpay/confirm"
    params = (
        f"?receiver={YOOMONEY_WALLET}"
        f"&quickpay-form=shop"
        f"&targets={quote(comment)}"
        f"&sum={amount}"
        f"&label={label}"
        f"&paymentType=AC"
    )
    return base + params
