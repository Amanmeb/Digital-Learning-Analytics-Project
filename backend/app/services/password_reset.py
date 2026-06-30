from hashlib import sha256
from secrets import token_urlsafe


def generate_reset_token():
    return token_urlsafe(48)


def hash_reset_token(token: str) -> str:
    return sha256(token.encode()).hexdigest()