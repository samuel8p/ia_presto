import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5002"))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    # MongoDB (misma instancia Atlas que usan auth y transactions)
    MONGO_URI = os.getenv("MONGO_URI", "")
    MONGO_DB_CHAT = os.getenv("MONGO_DB_CHAT", "chat")
    MONGO_DB_USERS = os.getenv("MONGO_DB_USERS", "users")
    MONGO_DB_TRANSACTIONS = os.getenv("MONGO_DB_TRANSACTIONS", "transactions")
    MONGO_DB_LOGS = os.getenv("MONGO_DB_LOGS", "logs")

    # JWT (mismo SECRET_KEY y algoritmo que auth y transactions)
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

    # LLM (por defecto Ollama local, gratis. Compatible con cualquier API OpenAI:
    # solo cambiando LLM_BASE_URL / LLM_API_KEY / LLM_MODEL puedes apuntar a Groq,
    # OpenAI, etc., sin tocar código.)
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://127.0.0.1:11434/v1")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "ollama")
    LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:3b-instruct")
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "120"))
    # El límite gratis de Groq para qwen3.8-27b es 1000 tokens de salida por minuto
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "700"))
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

    # Cuántos mensajes previos se envían al modelo como contexto
    HISTORY_CONTEXT_MESSAGES = int(os.getenv("HISTORY_CONTEXT_MESSAGES", "12"))

    if not MONGO_URI:
        raise RuntimeError("MONGO_URI no está definida en el archivo .env")
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY no está definida en el archivo .env")
