import re

from bson import ObjectId
from flask import Blueprint, jsonify, request
from pymongo.errors import DuplicateKeyError

from db import users
from services import logger
from services import users as users_service
from utils.security import create_token, generate_reset_code, require_auth, verify_password

auth_bp = Blueprint("auth", __name__, url_prefix="/api")

EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")


def _client_info():
    return request.remote_addr, request.headers.get("User-Agent", "")


def _public_user(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user.get("name"),
        "email": user["email"],
        "role": user.get("role"),
    }


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name:
        return jsonify({"error": "El nombre es obligatorio"}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Email inválido"}), 400
    if len(password) < 8:
        return jsonify({"error": "La contraseña debe tener al menos 8 caracteres"}), 400

    try:
        user_id = users_service.create_user(name, email, password)
    except DuplicateKeyError:
        return jsonify({"error": "El email ya está registrado"}), 409

    ip, ua = _client_info()
    logger.log_session("register", email, ip=ip, user_agent=ua)

    return (
        jsonify(
            {
                "message": "Usuario registrado correctamente",
                "user": {"id": str(user_id), "name": name, "email": email},
            }
        ),
        201,
    )


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    ip, ua = _client_info()

    user = users_service.find_by_email(email)
    if not user or not verify_password(password, user.get("password_hash", "")):
        logger.log_session("login_failed", email, ip=ip, user_agent=ua)
        return jsonify({"error": "Credenciales inválidas"}), 401

    token = create_token(str(user["_id"]), user["email"])
    logger.log_session("login_success", email, ip=ip, user_agent=ua)

    return jsonify(
        {
            "message": "Login exitoso",
            "token": token,
            "user": _public_user(user),
        }
    )


@auth_bp.post("/forgot-password")
def forgot_password():
    generic = {"message": "Si el email existe, se generó un código de recuperación"}
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    user = users_service.find_by_email(email) if EMAIL_RE.match(email) else None
    if not user:
        return jsonify(generic), 200

    code = generate_reset_code()
    users_service.save_reset_code(email, code)
    logger.log_password_reset("forgot_password_requested", email)

    return jsonify({**generic, "reset_code": code}), 200


@auth_bp.post("/reset-password")
def reset_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    code = (data.get("code") or "").strip()
    new_password = data.get("new_password") or ""

    if not EMAIL_RE.match(email) or not code:
        return jsonify({"error": "Datos inválidos"}), 400
    if len(new_password) < 8:
        return jsonify({"error": "La nueva contraseña debe tener al menos 8 caracteres"}), 400

    user = users_service.find_by_email(email)
    if not user or not users_service.check_reset_code(user, code):
        logger.log_password_reset("reset_failed", email)
        return jsonify({"error": "Código inválido o expirado"}), 400

    users_service.update_password(email, new_password)
    logger.log_password_reset("password_changed", email)

    return jsonify({"message": "Contraseña actualizada correctamente"}), 200


@auth_bp.get("/me")
@require_auth
def me(payload):
    try:
        user = users.find_one({"_id": ObjectId(payload["sub"])})
    except Exception:
        return jsonify({"error": "Token inválido"}), 401
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify({"user": _public_user(user)})
