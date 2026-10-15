import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
import jwt
from flask import request

import config


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def generate_reset_code() -> str:
    return f"{secrets.randbelow(1000000):06d}"


def create_token(user_id: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + timedelta(hours=config.JWT_EXPIRES_HOURS),
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return {"error": "Token requerido"}, 401
        try:
            payload = jwt.decode(
                header[7:], config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            return {"error": "Token expirado"}, 401
        except jwt.InvalidTokenError:
            return {"error": "Token inválido"}, 401
        return fn(payload, *args, **kwargs)

    return wrapper
