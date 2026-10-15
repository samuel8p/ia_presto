import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pymongo import MongoClient

from app.config import Config
from app.exceptions import ChatError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chat")


def _validation_message(err: dict) -> str:
    if err.get("type") == "json_invalid":
        return "El cuerpo de la solicitud no es JSON válido"
    campo = ".".join(str(loc) for loc in err["loc"] if loc != "body") or "cuerpo"
    tipo = err.get("type", "")
    if tipo == "missing":
        detalle = "es requerido"
    elif tipo == "string_too_short":
        detalle = "no puede estar vacío"
    elif tipo == "string_too_long":
        detalle = "supera el largo máximo permitido"
    elif tipo == "int_parsing":
        detalle = "debe ser un número entero"
    else:
        detalle = f"es inválido ({err['msg']})"
    return f"El campo '{campo}' {detalle}"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Presto AI Chat",
        description="Chat de IA con acceso a datos de la plataforma, para administradores",
        version="1.0.0",
    )

    client = MongoClient(Config.MONGO_URI, tz_aware=True)
    app.state.mongo_client = client
    app.state.mongo = client[Config.MONGO_DB_CHAT]
    app.state.db_users = client[Config.MONGO_DB_USERS]
    app.state.db_transactions = client[Config.MONGO_DB_TRANSACTIONS]
    app.state.db_logs = client[Config.MONGO_DB_LOGS]

    app.state.mongo.conversations.create_index("user_id")
    app.state.mongo.conversations.create_index("updated_at")
    app.state.mongo.messages.create_index([("conversation_id", 1), ("created_at", 1)])
    app.state.db_logs.chat_logs.create_index("timestamp")

    @app.exception_handler(ChatError)
    async def chat_error_handler(request: Request, exc: ChatError):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.message})

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        messages = [_validation_message(err) for err in exc.errors()]
        return JSONResponse(status_code=400, content={"error": "; ".join(messages)})

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        logger.exception("Error interno no controlado en %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"error": "Error interno del servidor"})

    from app.routes.chat import router as chat_router

    app.include_router(chat_router, prefix="/api")

    return app
