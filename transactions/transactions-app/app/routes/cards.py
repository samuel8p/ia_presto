from flask import Blueprint, request, jsonify, g, current_app

from app.middleware.auth import login_required
from app.services.card_service import CardService
from app.services.logger_service import LoggerService

cards_bp = Blueprint("cards", __name__)


def _get_service():
    return CardService(current_app.db_transactions, current_app.config["SECRET_KEY"])


def _get_logger():
    return LoggerService(current_app.db_logs)


@cards_bp.route("/cards", methods=["POST"])
@login_required
def validate_card():
    data = request.get_json(silent=True) or {}

    required = ("card_number", "cvv", "first_name", "last_name", "email", "phone", "salary_monthly")
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Campos requeridos: {', '.join(missing)}"}), 400

    card_number = data["card_number"]
    if not card_number.isdigit() or len(card_number) < 13 or len(card_number) > 19:
        return jsonify({"error": "Número de tarjeta inválido"}), 400

    cvv = data["cvv"]
    if not cvv.isdigit() or len(cvv) not in (3, 4):
        return jsonify({"error": "CVV inválido"}), 400

    salary = data.get("salary_monthly", 0)
    if not isinstance(salary, (int, float)) or salary <= 0:
        return jsonify({"error": "El salario mensual debe ser un número mayor a 0"}), 400

    service = _get_service()
    card, valid, extra = service.register_or_validate(g.user_id, data)

    logger = _get_logger()

    if valid:
        logger.log(
            action="card_validation_success",
            user_id=g.user_id,
            details={"bin": card.get("bin", ""), "sub_bin": card.get("sub_bin", "")},
            ip_address=request.remote_addr,
        )
        return jsonify({"message": "Datos de tarjeta válidos", "card": card}), 200

    logger.log(
        action="card_validation_failed",
        user_id=g.user_id,
        details={
            "attempts": extra["attempts"],
            "suspicious": extra["suspicious"],
        },
        ip_address=request.remote_addr,
    )

    if extra["suspicious"]:
        return jsonify({
            "error": "Datos de tarjeta incorrectos",
            "warning": "Transacción sospechosa detectada",
            "card": card,
        }), 401

    return jsonify({
        "error": "Datos de tarjeta incorrectos",
        "attempts": extra["attempts"],
        "remaining": 3 - extra["attempts"],
    }), 401


@cards_bp.route("/cards", methods=["GET"])
@login_required
def get_card():
    service = _get_service()
    card = service.get_by_user(g.user_id)

    if not card:
        return jsonify({"error": "No hay tarjeta registrada"}), 404

    return jsonify({"card": card}), 200
