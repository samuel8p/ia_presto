"""Snapshot de solo lectura de la plataforma para dar contexto al LLM.

Lee directo de las bases que ya existen en la misma instancia de MongoDB Atlas
(users y transactions), igual que las demás carpetas del proyecto. Nunca escribe.
"""

from datetime import datetime, timezone

from pymongo.database import Database


def _start_of_day(now: datetime) -> datetime:
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _start_of_month(now: datetime) -> datetime:
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _aggregate(db: Database, collection: str, filters: dict, amount_fields: tuple[str, ...] = ("amount",)) -> dict:
    group = {"count": {"$sum": 1}}
    for field in amount_fields:
        group[f"{field}_total"] = {"$sum": f"${field}"}

    pipeline = [{"$match": filters}, {"$group": {"_id": None, **group}}]
    result = list(db[collection].aggregate(pipeline))
    if not result:
        empty = {"count": 0}
        for field in amount_fields:
            empty[f"{field}_total"] = 0.0
        return empty

    row = result[0]
    row.pop("_id", None)
    return {key: (round(float(value), 2) if isinstance(value, float) else value) for key, value in row.items()}


def get_admin_snapshot(db_transactions: Database, db_users: Database) -> dict:
    now = datetime.now(timezone.utc)
    today = _start_of_day(now)
    month = _start_of_month(now)

    credits_fields = ("amount", "total_to_pay")
    investments_fields = ("amount", "net_return")

    return {
        "generated_at": now.isoformat(),
        "currency": "MXN",
        "users": {"total": db_users.users.count_documents({})},
        "transactions": {
            "today": _aggregate(db_transactions, "transactions", {"created_at": {"$gte": today}}),
            "month": _aggregate(db_transactions, "transactions", {"created_at": {"$gte": month}}),
            "all_time": _aggregate(db_transactions, "transactions", {}),
        },
        "credits": {
            "active": _aggregate(db_transactions, "credits", {"status": "active"}, credits_fields),
            "all_time": _aggregate(db_transactions, "credits", {}, credits_fields),
        },
        "investments": {
            "active": _aggregate(db_transactions, "investments", {"status": "active"}, investments_fields),
            "all_time": _aggregate(db_transactions, "investments", {}, investments_fields),
        },
        "cashin": {"all_time": _aggregate(db_transactions, "cashin", {})},
        "cashout": {"all_time": _aggregate(db_transactions, "cashout", {})},
        "cards": {"total": db_transactions.tarjetas_usuarios.count_documents({})},
    }
