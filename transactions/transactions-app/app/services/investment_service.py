from datetime import datetime, timezone, timedelta

from bson import ObjectId


INVESTMENT_RATES = {
    3: 0.03,
    6: 0.07,
    12: 0.15,
    18: 0.22,
}

APP_FEE_RATIO = 1 / 3

VALID_TERMS = (3, 6, 12, 18)


class InvestmentService:
    def __init__(self, db):
        self.collection = db["investments"]

    def create(self, user_id, user_email, data):
        term_months = int(data["term_months"])
        amount = float(data["amount"])

        if term_months not in VALID_TERMS:
            return None, f"Plazo inválido. Opciones: {', '.join(str(t) for t in VALID_TERMS)} meses"

        if amount <= 0:
            return None, "El monto debe ser mayor a 0"

        rate = INVESTMENT_RATES[term_months]
        gross_return = amount * rate
        app_fee = gross_return * APP_FEE_RATIO
        net_return = gross_return - app_fee
        total_payout = amount + net_return

        now = datetime.now(timezone.utc)
        maturity_date = now + timedelta(days=term_months * 30)

        doc = {
            "user_id": user_id,
            "user_email": user_email,
            "amount": amount,
            "term_months": term_months,
            "return_rate": rate,
            "gross_return": round(gross_return, 2),
            "app_fee": round(app_fee, 2),
            "net_return": round(net_return, 2),
            "total_payout": round(total_payout, 2),
            "status": "active",
            "maturity_date": maturity_date,
            "created_at": now,
            "updated_at": now,
        }

        result = self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return self._serialize(doc), None

    def get_all(self, user_id, status=None, page=1, per_page=20):
        query = {"user_id": user_id}
        if status:
            query["status"] = status

        skip = (page - 1) * per_page
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(per_page)
        items = [self._serialize(doc) for doc in cursor]
        total = self.collection.count_documents(query)

        return {
            "investments": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }

    def get_by_id(self, user_id, investment_id):
        try:
            doc = self.collection.find_one({"_id": ObjectId(investment_id), "user_id": user_id})
        except Exception:
            return None
        return self._serialize(doc) if doc else None

    def update(self, user_id, investment_id, data):
        try:
            doc = self.collection.find_one({"_id": ObjectId(investment_id), "user_id": user_id})
        except Exception:
            return None

        if not doc:
            return None

        update_fields = {}
        if "status" in data and data["status"] in ("matured", "cancelled"):
            update_fields["status"] = data["status"]

        if not update_fields:
            return self._serialize(doc)

        update_fields["updated_at"] = datetime.now(timezone.utc)
        self.collection.update_one({"_id": ObjectId(investment_id)}, {"$set": update_fields})

        doc = self.collection.find_one({"_id": ObjectId(investment_id)})
        return self._serialize(doc)

    @staticmethod
    def _serialize(doc):
        return {
            "id": str(doc["_id"]),
            "user_id": doc["user_id"],
            "user_email": doc.get("user_email", ""),
            "amount": doc["amount"],
            "term_months": doc["term_months"],
            "return_rate": doc["return_rate"],
            "gross_return": doc["gross_return"],
            "app_fee": doc["app_fee"],
            "net_return": doc["net_return"],
            "total_payout": doc["total_payout"],
            "status": doc["status"],
            "maturity_date": doc["maturity_date"].isoformat() if doc.get("maturity_date") else None,
            "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
            "updated_at": doc["updated_at"].isoformat() if doc.get("updated_at") else None,
        }
