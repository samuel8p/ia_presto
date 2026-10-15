"""Prueba end-to-end con usuario admin real y LLM real (borrar cuando ya no se necesite)."""

import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

import jwt
from pymongo import MongoClient

from app.config import Config

BASE = "http://127.0.0.1:5002"
EMAIL = "samuelsalgado363@gmail.com"


def make_token(sub: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": sub, "email": EMAIL, "iat": now, "exp": now + timedelta(hours=1)},
        Config.SECRET_KEY,
        algorithm="HS256",
    )


def call(method: str, path: str, token: str, body: dict | None = None):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


client = MongoClient(Config.MONGO_URI, tz_aware=True)
user = client[Config.MONGO_DB_USERS].users.find_one({"email": EMAIL})
assert user, f"No existe el usuario {EMAIL}"
token = make_token(str(user["_id"]))
print(f"Usuario admin: {user.get('name')} ({user['_id']})")

status, body = call("POST", "/api/chat/message", token, {"message": "Hola, ¿cuántos usuarios y créditos activos hay en la plataforma?"})
print(f"\n[1] POST /api/chat/message -> {status}")
print(json.dumps(body, ensure_ascii=False, indent=2)[:800])
conversation_id = body.get("conversation_id")

if status == 200 and conversation_id:
    status, body = call("GET", f"/api/chat/history?conversation_id={conversation_id}", token)
    print(f"\n[2] GET /api/chat/history -> {status} ({len(body.get('messages', []))} mensajes)")

    status, body = call("GET", "/api/chat/conversations", token)
    print(f"[3] GET /api/chat/conversations -> {status} ({body.get('total', '?')} conversaciones)")

    status, body = call("POST", "/api/chat/message", token, {"message": "¿Y en transacciones de hoy?", "conversation_id": conversation_id})
    print(f"[4] Segundo mensaje (con contexto) -> {status}")
    print(body.get("reply", body)[:400])
