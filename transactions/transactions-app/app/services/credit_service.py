from datetime import datetime, timezone

from bson import ObjectId


CREDIT_RATES = {
    3: 0.03,
    6: 0.07,
    12: 0.15,
    18: 0.22,
}

VALID_CUOTAS = (3, 6, 12, 18)
MAX_SALARY_PERCENT = 0.30
SECOND_CREDIT_EXTRA = 0.10


class CreditService:
    def __init__(self, db):
        self.collection = db["credits"]

    def create(self, user_id, user_email, data, salary_monthly):
        cuotas = int(data["cuotas"])
        amount = float(data["amount"])

        if cuotas not in VALID_CUOTAS:
            return None, f"Cuotas inválidas. Opciones: {', '.join(str(c) for c in VALID_CUOTAS)}"

        max_allowed = salary_monthly * MAX_SALARY_PERCENT

        active_credits = list(self.collection.find({
            "user_id": user_id,
            "status": "active",
        }))

        total_active = sum(c.get("amount", 0) for c in active_credits)

        remaining = max_allowed - total_active

        if remaining <= 0:
            return None, "Ya tienes un crédito activo que alcanza el límite permitido (30% del salario)"

        if total_active > 0 and remaining < salary_monthly * SECOND_CREDIT_EXTRA:
            remaining = salary_monthly * SECOND_CREDIT_EXTRA

        if amount > remaining:
            return None, f"El monto máximo disponible es ${remaining:,.2f}"

        rate = CREDIT_RATES[cuotas]
        total_to_pay = amount + (amount * rate)
        monthly_payment = total_to_pay / cuotas

        now = datetime.now(timezone.utc)
        doc = {
            "user_id": user_id,
            "user_email": user_email,
            "amount": amount,
            "salary_monthly": salary_monthly,
            "max_allowed": max_allowed,
            "cuotas": cuotas,
            "interest_rate": rate,
            "total_to_pay": round(total_to_pay, 2),
            "monthly_payment": round(monthly_payment, 2),
            "status": "active",
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
            "credits": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }

    def get_by_id(self, user_id, credit_id):
        try:
            doc = self.collection.find_one({"_id": ObjectId(credit_id), "user_id": user_id})
        except Exception:
            return None
        return self._serialize(doc) if doc else None

    def update(self, user_id, credit_id, data):
        try:
            doc = self.collection.find_one({"_id": ObjectId(credit_id), "user_id": user_id})
        except Exception:
            return None

        if not doc:
            return None

        update_fields = {}
        if "status" in data and data["status"] in ("completed", "cancelled"):
            update_fields["status"] = data["status"]

        if not update_fields:
            return self._serialize(doc)

        update_fields["updated_at"] = datetime.now(timezone.utc)
        self.collection.update_one({"_id": ObjectId(credit_id)}, {"$set": update_fields})

        doc = self.collection.find_one({"_id": ObjectId(credit_id)})
        return self._serialize(doc)

    @staticmethod
    def _serialize(doc):
        return {
            "id": str(doc["_id"]),
            "user_id": doc["user_id"],
            "user_email": doc.get("user_email", ""),
            "amount": doc["amount"],
            "salary_monthly": doc.get("salary_monthly", 0),
            "max_allowed": doc.get("max_allowed", 0),
            "cuotas": doc["cuotas"],
            "interest_rate": doc["interest_rate"],
            "total_to_pay": doc["total_to_pay"],
            "monthly_payment": doc["monthly_payment"],
            "status": doc["status"],
            "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
            "updated_at": doc["updated_at"].isoformat() if doc.get("updated_at") else None,
        }
