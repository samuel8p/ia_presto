import os

from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI no está definida en el archivo .env")

MONGO_DB_USERS = os.getenv("MONGO_DB_USERS", "users")
MONGO_DB_LOGS = os.getenv("MONGO_DB_LOGS", "logs")

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "24"))

RESET_CODE_TTL_MINUTES = int(os.getenv("RESET_CODE_TTL_MINUTES", "10"))

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
