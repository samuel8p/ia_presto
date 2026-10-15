from bson import ObjectId

from app.models.transaction import serialize_transaction, create_transaction_document


class TransactionService:
    def __init__(self, db_transactions):
        self.collection = db_transactions["transactions"]

    def create(self, user_id, user_email, data, amount, tx_type):
        doc = create_transaction_document(user_id, user_email, data, amount, tx_type)
        result = self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return serialize_transaction(doc)

    def get_all(self, user_id, tx_type=None, status=None, page=1, per_page=20):
        query = {"user_id": user_id}
        if tx_type:
            query["type"] = tx_type
        if status:
            query["status"] = status

        skip = (page - 1) * per_page
        cursor = (
            self.collection.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(per_page)
        )

        transactions = [serialize_transaction(tx) for tx in cursor]
        total = self.collection.count_documents(query)

        return {
            "transactions": transactions,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }

    def get_by_id(self, user_id, tx_id):
        try:
            tx = self.collection.find_one({"_id": ObjectId(tx_id), "user_id": user_id})
        except Exception:
            return None
        if not tx:
            return None
        return serialize_transaction(tx)

    def update(self, user_id, tx_id, data):
        try:
            tx = self.collection.find_one({"_id": ObjectId(tx_id), "user_id": user_id})
        except Exception:
            return None

        if not tx:
            return None

        update_fields = {}
        allowed = ("description", "category", "status", "currency")
        for field in allowed:
            if field in data:
                update_fields[field] = data[field]

        if not update_fields:
            return serialize_transaction(tx)

        from datetime import datetime, timezone
        update_fields["updated_at"] = datetime.now(timezone.utc)

        self.collection.update_one({"_id": ObjectId(tx_id)}, {"$set": update_fields})

        tx = self.collection.find_one({"_id": ObjectId(tx_id)})
        return serialize_transaction(tx)

    def delete(self, user_id, tx_id):
        try:
            result = self.collection.delete_one({"_id": ObjectId(tx_id), "user_id": user_id})
        except Exception:
            return False
        return result.deleted_count > 0
