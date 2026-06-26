from uuid import uuid4
from secrets import token_urlsafe
from hashlib import sha256


def generate_reset_token():
    return token_urlsafe(48)


def hash_reset_token(token: str) -> str:
    return sha256(token.encode()).hexdigest()