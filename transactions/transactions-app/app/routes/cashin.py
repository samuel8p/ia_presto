from flask import Blueprint, request, jsonify, g, current_app

from app.middleware.auth import login_required
from app.services.cashin_service import CashInService
from app.services.logger_service import LoggerService

cashin_bp = Blueprint("cashin", __name__)


def _get_service():
    return CashInService(current_app.db_transactions)


def _get_logger():
    return LoggerService(current_app.db_logs)


@cashin_bp.route("/cashin", methods=["POST"])
@login_required
def create_cashin():
    data = request.get_json(silent=True) or {}

    if "amount" not in data:
        return jsonify({"error": "El campo 'amount' es requerido"}), 400

    amount = data["amount"]
    if not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({"error": "El monto debe ser numérico y mayor a 0"}), 400

    service = _get_service()
    item = service.create(g.user_id, g.user_email, data, amount)

    logger = _get_logger()
    logger.log(
        action="cashin_create",
        user_id=g.user_id,
        transaction_id=item["id"],
        details={"amount": amount, "source": data.get("source", "")},
        ip_address=request.remote_addr,
    )

    return jsonify({"message": "Cash-in registrado", "cashin": item}), 201


@cashin_bp.route("/cashin", methods=["GET"])
@login_required
def list_cashin():
    status = request.args.get("status")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    service = _get_service()
    result = service.get_all(g.user_id, status=status, page=page, per_page=per_page)

    return jsonify(result), 200


@cashin_bp.route("/cashin/<item_id>", methods=["GET"])
@login_required
def get_cashin(item_id):
    service = _get_service()
    item = service.get_by_id(g.user_id, item_id)

    if not item:
        return jsonify({"error": "Cash-in no encontrado"}), 404

    return jsonify({"cashin": item}), 200


@cashin_bp.route("/cashin/<item_id>", methods=["PUT"])
@login_required
def update_cashin(item_id):
    data = request.get_json(silent=True) or {}

    service = _get_service()
    item = service.update(g.user_id, item_id, data)

    if not item:
        return jsonify({"error": "Cash-in no encontrado"}), 404

    logger = _get_logger()
    logger.log(
        action="cashin_update",
        user_id=g.user_id,
        transaction_id=item_id,
        details=data,
        ip_address=request.remote_addr,
    )

    return jsonify({"message": "Cash-in actualizado", "cashin": item}), 200


@cashin_bp.route("/cashin/<item_id>", methods=["DELETE"])
@login_required
def delete_cashin(item_id):
    service = _get_service()
    deleted = service.delete(g.user_id, item_id)

    if not deleted:
        return jsonify({"error": "Cash-in no encontrado"}), 404

    logger = _get_logger()
    logger.log(
        action="cashin_delete",
        user_id=g.user_id,
        transaction_id=item_id,
        ip_address=request.remote_addr,
    )

    return jsonify({"message": "Cash-in eliminado"}), 200
