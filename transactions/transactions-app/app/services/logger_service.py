from datetime import datetime, timezone


class LoggerService:
    def __init__(self, db_logs):
        self.collection = db_logs["transaction_logs"]

    def log(self, action, user_id, transaction_id=None, details=None, ip_address=None):
        doc = {
            "action": action,
            "user_id": user_id,
            "transaction_id": transaction_id,
            "details": details or {},
            "ip_address": ip_address,
            "timestamp": datetime.now(timezone.utc),
        }
        self.collection.insert_one(doc)
