from datetime import datetime, timezone


class CashInService:
    def __init__(self, db):
        self.collection = db["cashin"]

    def create(self, user_id, user_email, data, amount):
        now = datetime.now(timezone.utc)
        doc = {
            "user_id": user_id,
            "user_email": user_email,
            "amount": amount,
            "currency": data.get("currency", "ARS"),
            "source": data.get("source", ""),
            "description": data.get("description", ""),
            "status": "completed",
            "created_at": now,
            "updated_at": now,
        }
        result = self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return self._serialize(doc)

    def get_all(self, user_id, status=None, page=1, per_page=20):
        query = {"user_id": user_id}
        if status:
            query["status"] = status

        skip = (page - 1) * per_page
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(per_page)
        items = [self._serialize(doc) for doc in cursor]
        total = self.collection.count_documents(query)

        return {
            "cashin": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }

    def get_by_id(self, user_id, item_id):
        from bson import ObjectId

        try:
            doc = self.collection.find_one({"_id": ObjectId(item_id), "user_id": user_id})
        except Exception:
            return None
        return self._serialize(doc) if doc else None

    def update(self, user_id, item_id, data):
        from bson import ObjectId

        try:
            doc = self.collection.find_one({"_id": ObjectId(item_id), "user_id": user_id})
        except Exception:
            return None

        if not doc:
            return None

        update_fields = {}
        for field in ("description", "source", "status", "currency"):
            if field in data:
                update_fields[field] = data[field]

        if not update_fields:
            return self._serialize(doc)

        update_fields["updated_at"] = datetime.now(timezone.utc)
        self.collection.update_one({"_id": ObjectId(item_id)}, {"$set": update_fields})

        doc = self.collection.find_one({"_id": ObjectId(item_id)})
        return self._serialize(doc)

    def delete(self, user_id, item_id):
        from bson import ObjectId

        try:
            result = self.collection.delete_one({"_id": ObjectId(item_id), "user_id": user_id})
        except Exception:
            return False
        return result.deleted_count > 0

    @staticmethod
    def _serialize(doc):
        return {
            "id": str(doc["_id"]),
            "user_id": doc["user_id"],
            "user_email": doc["user_email"],
            "amount": doc["amount"],
            "currency": doc["currency"],
            "source": doc.get("source", ""),
            "description": doc.get("description", ""),
            "status": doc["status"],
            "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
            "updated_at": doc["updated_at"].isoformat() if doc.get("updated_at") else None,
        }
