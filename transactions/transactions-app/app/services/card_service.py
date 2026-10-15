from datetime import datetime, timezone

from bson import ObjectId

from app.utils.crypto import encrypt_value, verify_value, extract_bin, extract_sub_bin


class CardService:
    MAX_FAILED_ATTEMPTS = 3

    def __init__(self, db, secret_key):
        self.collection = db["tarjetas_usuarios"]
        self.secret = secret_key

    def register_or_validate(self, user_id, data):
        existing = self.collection.find_one({"user_id": user_id})

        card_number = data.get("card_number", "")
        cvv = data.get("cvv", "")

        if not existing:
            return self._register(user_id, data, card_number, cvv)

        return self._validate(user_id, existing, card_number, cvv)

    def _register(self, user_id, data, card_number, cvv):
        now = datetime.now(timezone.utc)
        doc = {
            "user_id": user_id,
            "first_name": data.get("first_name", ""),
            "last_name": data.get("last_name", ""),
            "email": data.get("email", ""),
            "phone": data.get("phone", ""),
            "card_number": encrypt_value(card_number, self.secret),
            "cvv": encrypt_value(cvv, self.secret),
            "bin": extract_bin(card_number),
            "sub_bin": extract_sub_bin(card_number),
            "salary_monthly": float(data.get("salary_monthly", 0)),
            "failed_attempts": 0,
            "suspicious": False,
            "created_at": now,
            "updated_at": now,
        }
        result = self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return self._serialize(doc), True, None

    def _validate(self, user_id, existing, card_number, cvv):
        card_ok = verify_value(card_number, existing["card_number"], self.secret)
        cvv_ok = verify_value(cvv, existing["cvv"], self.secret)

        if card_ok and cvv_ok:
            self.collection.update_one(
                {"_id": existing["_id"]},
                {"$set": {"failed_attempts": 0, "updated_at": datetime.now(timezone.utc)}},
            )
            existing["failed_attempts"] = 0
            return self._serialize(existing), True, None

        new_count = existing.get("failed_attempts", 0) + 1
        suspicious = new_count > self.MAX_FAILED_ATTEMPTS

        self.collection.update_one(
            {"_id": existing["_id"]},
            {"$set": {
                "failed_attempts": new_count,
                "suspicious": suspicious,
                "updated_at": datetime.now(timezone.utc),
            }},
        )

        existing["failed_attempts"] = new_count
        existing["suspicious"] = suspicious

        return self._serialize(existing), False, {
            "attempts": new_count,
            "suspicious": suspicious,
        }

    def get_by_user(self, user_id):
        doc = self.collection.find_one({"user_id": user_id})
        return self._serialize(doc) if doc else None

    @staticmethod
    def _serialize(doc):
        return {
            "id": str(doc["_id"]),
            "user_id": doc["user_id"],
            "first_name": doc.get("first_name", ""),
            "last_name": doc.get("last_name", ""),
            "email": doc.get("email", ""),
            "phone": doc.get("phone", ""),
            "bin": doc.get("bin", ""),
            "sub_bin": doc.get("sub_bin", ""),
            "salary_monthly": doc.get("salary_monthly", 0),
            "failed_attempts": doc.get("failed_attempts", 0),
            "suspicious": doc.get("suspicious", False),
            "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
            "updated_at": doc["updated_at"].isoformat() if doc.get("updated_at") else None,
        }
