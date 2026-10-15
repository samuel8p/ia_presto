from datetime import datetime, timedelta, timezone

import config
from db import users
from utils.security import hash_password, verify_password


def find_by_email(email: str):
    return users.find_one({"email": email})


def create_user(name: str, email: str, password: str):
    now = datetime.now(timezone.utc)
    result = users.insert_one(
        {
            "name": name,
            "email": email,
            "password_hash": hash_password(password),
            "created_at": now,
            "updated_at": now,
        }
    )
    return result.inserted_id


def update_password(email: str, new_password: str):
    users.update_one(
        {"email": email},
        {
            "$set": {
                "password_hash": hash_password(new_password),
                "updated_at": datetime.now(timezone.utc),
            },
            "$unset": {"reset_code_hash": "", "reset_code_expires_at": ""},
        },
    )


def save_reset_code(email: str, code: str):
    now = datetime.now(timezone.utc)
    users.update_one(
        {"email": email},
        {
            "$set": {
                "reset_code_hash": hash_password(code),
                "reset_code_expires_at": now
                + timedelta(minutes=config.RESET_CODE_TTL_MINUTES),
                "updated_at": now,
            }
        },
    )


def check_reset_code(user: dict, code: str) -> bool:
    code_hash = user.get("reset_code_hash")
    expires_at = user.get("reset_code_expires_at")
    if not code_hash or not expires_at:
        return False
    if expires_at < datetime.now(timezone.utc):
        return False
    return verify_password(code, code_hash)
