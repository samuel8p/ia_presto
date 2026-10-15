from flask import Blueprint, request, jsonify, current_app

from app.middleware.auth import login_required
from app.services.limits_service import LimitsService

limits_bp = Blueprint("limits", __name__)


def _get_service():
    return LimitsService(current_app.db_transactions)


@limits_bp.route("/limits", methods=["GET"])
@login_required
def get_limits():
    service = _get_service()
    limits = service.get()
    return jsonify({"limits": limits}), 200


@limits_bp.route("/limits", methods=["PUT"])
@login_required
def update_limits():
    data = request.get_json(silent=True) or {}

    min_amount = data.get("min_amount")
    max_amount = data.get("max_amount")

    if min_amount is not None and not isinstance(min_amount, (int, float)):
        return jsonify({"error": "min_amount debe ser numérico"}), 400
    if max_amount is not None and not isinstance(max_amount, (int, float)):
        return jsonify({"error": "max_amount debe ser numérico"}), 400

    if min_amount is not None and min_amount < 0:
        return jsonify({"error": "min_amount no puede ser negativo"}), 400
    if max_amount is not None and max_amount < 0:
        return jsonify({"error": "max_amount no puede ser negativo"}), 400

    if min_amount is not None and max_amount is not None:
        if min_amount > max_amount:
            return jsonify({"error": "min_amount no puede ser mayor que max_amount"}), 400

    service = _get_service()
    limits = service.update(min_amount=min_amount, max_amount=max_amount)

    return jsonify({"message": "Límites actualizados", "limits": limits}), 200
