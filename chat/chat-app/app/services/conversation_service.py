import math
from datetime import datetime, timezone

from bson import ObjectId
from pymongo.database import Database


def create_conversation(db: Database, user_id: str, first_message: str) -> dict:
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "title": first_message.strip()[:60] or "Nueva conversación",
        "created_at": now,
        "updated_at": now,
        "message_count": 0,
    }
    result = db.conversations.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def get_conversation(db: Database, conversation_id: str, user_id: str) -> dict | None:
    if not ObjectId.is_valid(conversation_id):
        return None
    return db.conversations.find_one({"_id": ObjectId(conversation_id), "user_id": user_id})


def add_message(db: Database, conversation_id: ObjectId, user_id: str, role: str, content: str) -> None:
    now = datetime.now(timezone.utc)
    db.messages.insert_one(
        {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "created_at": now,
        }
    )
    db.conversations.update_one(
        {"_id": conversation_id},
        {"$inc": {"message_count": 1}, "$set": {"updated_at": now}},
    )


def get_messages(db: Database, conversation_id: ObjectId, limit: int = 50) -> list[dict]:
    messages = list(db.messages.find({"conversation_id": conversation_id}).sort("created_at", 1))
    return messages[-limit:]


def list_conversations(db: Database, user_id: str, page: int, per_page: int) -> tuple[list[dict], int, int]:
    query = {"user_id": user_id}
    total = db.conversations.count_documents(query)
    pages = max(1, math.ceil(total / per_page))
    items = list(
        db.conversations.find(query)
        .sort("updated_at", -1)
        .skip((page - 1) * per_page)
        .limit(per_page)
    )
    return items, total, pages
