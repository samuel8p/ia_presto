from functools import wraps
from datetime import datetime, timezone, timedelta

import jwt
from flask import request, jsonify, g, current_app


def jwt_middleware(app):
    @app.before_request
    def verify_token():
        if request.endpoint in ("transactions.health",):
            return

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token requerido"}), 401

        token = auth_header.split(" ", 1)[1]

        try:
            payload = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"],
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido"}), 401

        g.user_id = payload.get("sub") or payload.get("user_id")
        g.user_email = payload.get("email")

        if not g.user_id:
            return jsonify({"error": "Token sin identificador de usuario"}), 401


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not getattr(g, "user_id", None):
            return jsonify({"error": "Autenticación requerida"}), 401
        return f(*args, **kwargs)
    return decorated
