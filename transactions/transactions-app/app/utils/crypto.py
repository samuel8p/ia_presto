import hashlib
import hmac


def encrypt_value(value: str, secret: str) -> str:
    return hmac.new(secret.encode(), value.encode(), hashlib.sha256).hexdigest()


def verify_value(value: str, hashed: str, secret: str) -> bool:
    return hmac.compare_digest(encrypt_value(value, secret), hashed)


def extract_bin(card_number: str) -> str:
    return card_number[:8]


def extract_sub_bin(card_number: str) -> str:
    return card_number[:6]
