from app.services.limits_service import LimitsService

VALID_TX_TYPES = ("income", "expense", "transfer")
VALID_STATUSES = ("pending", "completed", "cancelled")


def validate_amount(amount, db):
    if not isinstance(amount, (int, float)):
        return False, "El monto debe ser numérico"

    limits = LimitsService(db).get()
    min_amt = limits.get("min_amount", 1_000)
    max_amt = limits.get("max_amount", 10_000_000)

    if amount < min_amt:
        return False, f"El monto mínimo es ${min_amt:,.2f}"
    if amount > max_amt:
        return False, f"El monto máximo es ${max_amt:,.2f}"
    return True, None


def validate_transaction_type(tx_type):
    if tx_type not in VALID_TX_TYPES:
        return False, f"Tipo inválido. Opciones: {', '.join(VALID_TX_TYPES)}"
    return True, None


def validate_status(status):
    if status not in VALID_STATUSES:
        return False, f"Estado inválido. Opciones: {', '.join(VALID_STATUSES)}"
    return True, None


def validate_create_data(data, db):
    errors = []

    if "amount" not in data:
        errors.append("El campo 'amount' es requerido")
    else:
        ok, msg = validate_amount(data["amount"], db)
        if not ok:
            errors.append(msg)

    if "type" not in data:
        errors.append("El campo 'type' es requerido")
    else:
        ok, msg = validate_transaction_type(data["type"])
        if not ok:
            errors.append(msg)

    return errors
