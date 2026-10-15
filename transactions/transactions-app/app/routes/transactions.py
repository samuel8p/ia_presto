from flask import Blueprint, request, jsonify, g, current_app

from app.middleware.auth import login_required
from app.services.transaction_service import TransactionService
from app.services.logger_service import LoggerService
from app.utils.validators import (
    validate_create_data,
    validate_amount,
    validate_transaction_type,
    validate_status,
)

transactions_bp = Blueprint("transactions", __name__)


def _get_service():
    return TransactionService(current_app.db_transactions)


def _get_logger():
    return LoggerService(current_app.db_logs)


@transactions_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@transactions_bp.route("/transactions", methods=["POST"])
@login_required
def create_transaction():
    data = request.get_json(silent=True) or {}

    errors = validate_create_data(data, current_app.db_transactions)
    if errors:
        return jsonify({"errors": errors}), 400

    amount = float(data["amount"])
    tx_type = data["type"]

    service = _get_service()
    tx = service.create(g.user_id, g.user_email, data, amount, tx_type)

    logger = _get_logger()
    logger.log(
        action="create",
        user_id=g.user_id,
        transaction_id=tx["id"],
        details={"amount": amount, "type": tx_type},
        ip_address=request.remote_addr,
    )

    return jsonify({"message": "Transacción creada", "transaction": tx}), 201


@transactions_bp.route("/transactions", methods=["GET"])
@login_required
def list_transactions():
    tx_type = request.args.get("type")
    status = request.args.get("status")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    if tx_type:
        ok, msg = validate_transaction_type(tx_type)
        if not ok:
            return jsonify({"error": msg}), 400

    if status:
        ok, msg = validate_status(status)
        if not ok:
            return jsonify({"error": msg}), 400

    service = _get_service()
    result = service.get_all(g.user_id, tx_type=tx_type, status=status, page=page, per_page=per_page)

    return jsonify(result), 200


@transactions_bp.route("/transactions/<tx_id>", methods=["GET"])
@login_required
def get_transaction(tx_id):
    service = _get_service()
    tx = service.get_by_id(g.user_id, tx_id)

    if not tx:
        return jsonify({"error": "Transacción no encontrada"}), 404

    logger = _get_logger()
    logger.log(
        action="read",
        user_id=g.user_id,
        transaction_id=tx_id,
        ip_address=request.remote_addr,
    )

    return jsonify({"transaction": tx}), 200


@transactions_bp.route("/transactions/<tx_id>", methods=["PUT"])
@login_required
def update_transaction(tx_id):
    data = request.get_json(silent=True) or {}

    if "amount" in data:
        ok, msg = validate_amount(data["amount"], current_app.db_transactions)
        if not ok:
            return jsonify({"error": msg}), 400

    if "type" in data:
        ok, msg = validate_transaction_type(data["type"])
        if not ok:
            return jsonify({"error": msg}), 400

    if "status" in data:
        ok, msg = validate_status(data["status"])
        if not ok:
            return jsonify({"error": msg}), 400

    service = _get_service()
    tx = service.update(g.user_id, tx_id, data)

    if not tx:
        return jsonify({"error": "Transacción no encontrada"}), 404

    logger = _get_logger()
    logger.log(
        action="update",
        user_id=g.user_id,
        transaction_id=tx_id,
        details=data,
        ip_address=request.remote_addr,
    )

    return jsonify({"message": "Transacción actualizada", "transaction": tx}), 200


@transactions_bp.route("/transactions/<tx_id>", methods=["DELETE"])
@login_required
def delete_transaction(tx_id):
    service = _get_service()
    deleted = service.delete(g.user_id, tx_id)

    if not deleted:
        return jsonify({"error": "Transacción no encontrada"}), 404

    logger = _get_logger()
    logger.log(
        action="delete",
        user_id=g.user_id,
        transaction_id=tx_id,
        ip_address=request.remote_addr,
    )

    return jsonify({"message": "Transacción eliminada"}), 200
