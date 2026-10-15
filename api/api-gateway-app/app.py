import logging
import time

import requests
from flask import Flask, jsonify, request
from requests.exceptions import RequestException, Timeout as RequestsTimeout
from werkzeug.exceptions import NotFound

from config import (
    AUTH_SERVICE_URL,
    CHAT_REQUEST_TIMEOUT,
    CHAT_SERVICE_URL,
    DEBUG,
    GATEWAY_HOST,
    GATEWAY_PORT,
    REQUEST_TIMEOUT,
    TRANSACTIONS_SERVICE_URL,
)

logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger("api-gateway")

AUTH_SERVICE = "auth"
TRANSACTIONS_SERVICE = "transactions"
CHAT_SERVICE = "chat"

AUTH_PATHS = {
    "/api/register",
    "/api/login",
    "/api/forgot-password",
    "/api/reset-password",
    "/api/me",
}

HEADERS_TO_REMOVE = {
    "host",
    "content-length",
    "accept-encoding",
    "connection",
    "transfer-encoding",
    "te",
    "keep-alive",
}


def resolve_service(path: str) -> str:
    if path.startswith("/api/chat"):
        return CHAT_SERVICE
    return AUTH_SERVICE if path in AUTH_PATHS else TRANSACTIONS_SERVICE


def forward_payload(method: str, url: str, body: bytes, timeout: float = REQUEST_TIMEOUT):
    headers = {k: v for k, v in request.headers.items() if k.lower() not in HEADERS_TO_REMOVE}
    response = requests.request(
        method,
        url,
        data=body,
        headers=headers,
        params=request.args,
        timeout=timeout,
    )
    return response


def build_response(response: requests.Response):
    response_headers = {k: v for k, v in response.headers.items() if k.lower() not in HEADERS_TO_REMOVE}
    content_type = response_headers.get("Content-Type", response.headers.get("content-type", "application/json"))
    return response.content, response.status_code, {**response_headers, **{"Content-Type": content_type}}


def create_app():
    app = Flask(__name__)

    @app.before_request
    def log_start():
        request.environ["GW_START"] = time.time()

    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            return "", 204

    @app.after_request
    def add_cors_headers(resp):
        origin = request.headers.get("Origin")
        resp.headers["Access-Control-Allow-Origin"] = origin or "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        resp.headers["Access-Control-Max-Age"] = "86400"
        resp.headers["Vary"] = "Origin"
        return resp

    @app.after_request
    def log_request(resp):
        start = request.environ.get("GW_START", time.time())
        elapsed_ms = round((time.time() - start) * 1000, 2)
        logger.info(
            "%s %s -> %s (%s) %.2fms",
            request.method,
            request.full_path,
            getattr(request, "gw_target_service", "-"),
            resp.status_code,
            elapsed_ms,
        )
        return resp

    @app.route("/", methods=["GET"])
    def root():
        return jsonify({"message": "API Gateway ien", "status": "ok"}), 200

    @app.route("/api/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    def proxy(path):
        full_path = "/api/" + path
        service = resolve_service(full_path)
        if service == AUTH_SERVICE:
            base_url = AUTH_SERVICE_URL
        elif service == CHAT_SERVICE:
            base_url = CHAT_SERVICE_URL
        else:
            base_url = TRANSACTIONS_SERVICE_URL
        target_url = base_url + full_path
        request.gw_target_service = service
        timeout = CHAT_REQUEST_TIMEOUT if service == CHAT_SERVICE else REQUEST_TIMEOUT

        try:
            response = forward_payload(request.method, target_url, request.get_data(cache=True), timeout)
        except RequestsTimeout:
            return jsonify({"error": "El servicio tardó demasiado en responder"}), 504
        except RequestException:
            logger.exception("servicio %s no disponible en %s", service, base_url)
            return jsonify({"error": f"El servicio {service} no está disponible"}), 502

        return build_response(response)

    @app.errorhandler(NotFound)
    def not_found(_):
        return jsonify({"error": "Ruta no encontrada"}), 404

    @app.errorhandler(405)
    def method_not_allowed(_):
        return jsonify({"error": "Método no permitido"}), 405

    @app.errorhandler(500)
    def server_error(_):
        return jsonify({"error": "Error interno del servidor"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host=GATEWAY_HOST, port=GATEWAY_PORT, debug=DEBUG)