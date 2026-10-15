from datetime import datetime, timezone
from bson import ObjectId


def serialize_transaction(tx):
    return {
        "id": str(tx["_id"]),
        "user_id": tx["user_id"],
        "user_email": tx["user_email"],
        "amount": tx["amount"],
        "currency": tx["currency"],
        "type": tx["type"],
        "description": tx.get("description", ""),
        "category": tx.get("category", ""),
        "status": tx["status"],
        "created_at": tx["created_at"].isoformat() if tx.get("created_at") else None,
        "updated_at": tx["updated_at"].isoformat() if tx.get("updated_at") else None,
    }


def create_transaction_document(user_id, user_email, data, amount, tx_type):
    now = datetime.now(timezone.utc)
    return {
        "user_id": user_id,
        "user_email": user_email,
        "amount": amount,
        "currency": data.get("currency", "MXN"),
        "type": tx_type,
        "description": data.get("description", ""),
        "category": data.get("category", ""),
        "status": "completed",
        "created_at": now,
        "updated_at": now,
    }
