from flask import Blueprint, request, jsonify, g, current_app

from app.middleware.auth import login_required
from app.services.investment_service import InvestmentService
from app.services.card_service import CardService
from app.services.logger_service import LoggerService

investments_bp = Blueprint("investments", __name__)


def _get_service():
    return InvestmentService(current_app.db_transactions)


def _get_card_service():
    return CardService(current_app.db_transactions, current_app.config["SECRET_KEY"])


def _get_logger():
    return LoggerService(current_app.db_logs)


@investments_bp.route("/investments", methods=["POST"])
@login_required
def create_investment():
    data = request.get_json(silent=True) or {}

    if "amount" not in data:
        return jsonify({"error": "El campo 'amount' es requerido"}), 400

    if "term_months" not in data:
        return jsonify({"error": "El campo 'term_months' es requerido"}), 400

    amount = data["amount"]
    if not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({"error": "El monto debe ser un número mayor a 0"}), 400

    term_months = data["term_months"]
    if not isinstance(term_months, int) or term_months not in (3, 6, 12, 18):
        return jsonify({"error": "Plazo inválido. Opciones: 3, 6, 12, 18 meses"}), 400

    card_service = _get_card_service()
    card = card_service.get_by_user(g.user_id)

    if not card:
        return jsonify({"error": "Debes registrar tu tarjeta primero"}), 400

    if card.get("suspicious"):
        return jsonify({"error": "Cuenta bloqueada por actividad sospechosa"}), 403

    service = _get_service()
    investment, error = service.create(g.user_id, g.user_email, data)

    if error:
        return jsonify({"error": error}), 400

    logger = _get_logger()
    logger.log(
        action="investment_create",
        user_id=g.user_id,
        transaction_id=investment["id"],
        details={
            "amount": amount,
            "term_months": term_months,
            "return_rate": investment["return_rate"],
            "net_return": investment["net_return"],
        },
        ip_address=request.remote_addr,
    )

    return jsonify({"message": "Inversión creada", "investment": investment}), 201


@investments_bp.route("/investments", methods=["GET"])
@login_required
def list_investments():
    status = request.args.get("status")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    service = _get_service()
    result = service.get_all(g.user_id, status=status, page=page, per_page=per_page)

    return jsonify(result), 200


@investments_bp.route("/investments/<investment_id>", methods=["GET"])
@login_required
def get_investment(investment_id):
    service = _get_service()
    investment = service.get_by_id(g.user_id, investment_id)

    if not investment:
        return jsonify({"error": "Inversión no encontrada"}), 404

    return jsonify({"investment": investment}), 200


@investments_bp.route("/investments/<investment_id>", methods=["PUT"])
@login_required
def update_investment(investment_id):
    data = request.get_json(silent=True) or {}

    service = _get_service()
    investment = service.update(g.user_id, investment_id, data)

    if not investment:
        return jsonify({"error": "Inversión no encontrada"}), 404

    logger = _get_logger()
    logger.log(
        action="investment_update",
        user_id=g.user_id,
        transaction_id=investment_id,
        details=data,
        ip_address=request.remote_addr,
    )

    return jsonify({"message": "Inversión actualizada", "investment": investment}), 200
