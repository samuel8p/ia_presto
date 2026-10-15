from datetime import datetime, timezone


class LimitsService:
    DEFAULT_LIMITS = {
        "min_amount": 1_000,
        "max_amount": 10_000_000,
        "currency": "ARS",
    }

    def __init__(self, db):
        self.collection = db["transaction_limits"]
        self._ensure_defaults()

    def _ensure_defaults(self):
        if self.collection.count_documents({}) == 0:
            doc = {**self.DEFAULT_LIMITS, "updated_at": datetime.now(timezone.utc)}
            self.collection.insert_one(doc)

    def get(self):
        return self.collection.find_one(
            {},
            {"_id": 0, "min_amount": 1, "max_amount": 1, "currency": 1, "updated_at": 1},
        )

    def update(self, min_amount=None, max_amount=None):
        update_fields = {"updated_at": datetime.now(timezone.utc)}
        if min_amount is not None:
            update_fields["min_amount"] = min_amount
        if max_amount is not None:
            update_fields["max_amount"] = max_amount

        self.collection.update_one({}, {"$set": update_fields}, upsert=True)
        return self.get()
