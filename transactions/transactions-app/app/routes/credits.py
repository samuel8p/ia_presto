from flask import Blueprint, request, jsonify, g, current_app

from app.middleware.auth import login_required
from app.services.credit_service import CreditService
from app.services.card_service import CardService
from app.services.logger_service import LoggerService

credits_bp = Blueprint("credits", __name__)


def _get_service():
    return CreditService(current_app.db_transactions)


def _get_card_service():
    return CardService(current_app.db_transactions, current_app.config["SECRET_KEY"])


def _get_logger():
    return LoggerService(current_app.db_logs)


@credits_bp.route("/credits", methods=["POST"])
@login_required
def create_credit():
    data = request.get_json(silent=True) or {}

    if "amount" not in data:
        return jsonify({"error": "El campo 'amount' es requerido"}), 400

    if "cuotas" not in data:
        return jsonify({"error": "El campo 'cuotas' es requerido"}), 400

    amount = data["amount"]
    if not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({"error": "El monto debe ser un número mayor a 0"}), 400

    cuotas = data["cuotas"]
    if not isinstance(cuotas, int) or cuotas not in (3, 6, 12, 18):
        return jsonify({"error": "Cuotas inválidas. Opciones: 3, 6, 12, 18"}), 400

    card_service = _get_card_service()
    card = card_service.get_by_user(g.user_id)

    if not card:
        return jsonify({"error": "Debes registrar tu tarjeta primero"}), 400

    if card.get("suspicious"):
        return jsonify({"error": "Cuenta bloqueada por actividad sospechosa"}), 403

    salary = card.get("salary_monthly", 0)
    if salary <= 0:
        return jsonify({"error": "No se encontró información de salario en tu tarjeta"}), 400

    service = _get_service()
    credit, error = service.create(g.user_id, g.user_email, data, salary)

    if error:
        return jsonify({"error": error}), 400

    logger = _get_logger()
    logger.log(
        action="credit_create",
        user_id=g.user_id,
        transaction_id=credit["id"],
        details={"amount": amount, "cuotas": cuotas, "interest_rate": credit["interest_rate"]},
        ip_address=request.remote_addr,
    )

    return jsonify({"message": "Crédito aprobado", "credit": credit}), 201


@credits_bp.route("/credits", methods=["GET"])
@login_required
def list_credits():
    status = request.args.get("status")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    service = _get_service()
    result = service.get_all(g.user_id, status=status, page=page, per_page=per_page)

    return jsonify(result), 200


@credits_bp.route("/credits/<credit_id>", methods=["GET"])
@login_required
def get_credit(credit_id):
    service = _get_service()
    credit = service.get_by_id(g.user_id, credit_id)

    if not credit:
        return jsonify({"error": "Crédito no encontrado"}), 404

    return jsonify({"credit": credit}), 200


@credits_bp.route("/credits/<credit_id>", methods=["PUT"])
@login_required
def update_credit(credit_id):
    data = request.get_json(silent=True) or {}

    service = _get_service()
    credit = service.update(g.user_id, credit_id, data)

    if not credit:
        return jsonify({"error": "Crédito no encontrado"}), 404

    logger = _get_logger()
    logger.log(
        action="credit_update",
        user_id=g.user_id,
        transaction_id=credit_id,
        details=data,
        ip_address=request.remote_addr,
    )

    return jsonify({"message": "Crédito actualizado", "credit": credit}), 200
