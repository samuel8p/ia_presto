import os

from dotenv import load_dotenv

load_dotenv()

GATEWAY_HOST = os.getenv("GATEWAY_HOST", "127.0.0.1")
GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", "8080"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:5000")
TRANSACTIONS_SERVICE_URL = os.getenv("TRANSACTIONS_SERVICE_URL", "http://127.0.0.1:5001")
CHAT_SERVICE_URL = os.getenv("CHAT_SERVICE_URL", "http://127.0.0.1:5002")

REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "30"))
# El chat de IA puede tardar más (el LLM tarda en responder)
CHAT_REQUEST_TIMEOUT = float(os.getenv("CHAT_REQUEST_TIMEOUT", "120"))