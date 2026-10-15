"""Prueba de humo rápida del servicio de chat (borrar cuando ya no se necesite)."""

import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

import jwt

BASE = "http://127.0.0.1:5002"
SECRET = "a8bf24a1ff02c02aab4abee2a266fc7a29ac774ccdf012daa638d47346080e4c"


def make_token(sub: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": sub, "email": "test@example.com", "iat": now, "exp": now + timedelta(hours=1)}, SECRET, algorithm="HS256")


def call(method: str, path: str, token: str | None = None, body: dict | None = None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


tests = []

status, body = call("GET", "/api/health")
tests.append(("health", status == 200 and body == {"status": "ok"}, f"{status} {body}"))

status, body = call("POST", "/api/chat/message", body={"message": "hola"})
tests.append(("sin token -> 401", status == 401 and body.get("error") == "Token requerido", f"{status} {body}"))

status, body = call("POST", "/api/chat/message", token="tokenfalso", body={"message": "hola"})
tests.append(("token inválido -> 401", status == 401 and body.get("error") == "Token inválido", f"{status} {body}"))

status, body = call("POST", "/api/chat/message", token=make_token("656f8b9d1234567890abcde1"), body={"message": "hola"})
tests.append(("usuario no admin -> 403", status == 403, f"{status} {body}"))

# Nota: la validación del body (mensaje vacío) corre después de la dependencia
# require_admin, así que un usuario no admin recibe 403 antes que el 400.
status, body = call("POST", "/api/chat/message", token=make_token("656f8b9d1234567890abcde1"), body={"message": ""})
tests.append(("mensaje vacío (no admin) -> 403", status == 403, f"{status} {body}"))

status, body = call("POST", "/api/chat/message", token=make_token("noesunobjectid"), body={"message": "hola"})
tests.append(("sub inválido -> 403", status == 403, f"{status} {body}"))

ok = True
for name, passed, detail in tests:
    print(f"[{'OK' if passed else 'FALLA'}] {name}: {detail}")
    ok = ok and passed

print("TODO OK" if ok else "HAY FALLOS")
