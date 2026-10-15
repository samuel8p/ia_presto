import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB_TRANSACTIONS = os.getenv("MONGO_DB_TRANSACTIONS", "transactions")
    MONGO_DB_LOGS = os.getenv("MONGO_DB_LOGS", "logs")
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "24"))
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    TRANSACTION_MIN = 1_000
    TRANSACTION_MAX = 10_000_000

    CREDIT_RATES = {3: 0.03, 6: 0.07, 12: 0.15, 18: 0.22}
    VALID_CUOTAS = (3, 6, 12, 18)
    MAX_SALARY_PERCENT = 0.30
    SECOND_CREDIT_EXTRA = 0.10

    INVESTMENT_RATES = {3: 0.03, 6: 0.07, 12: 0.15, 18: 0.22}
    VALID_TERMS = (3, 6, 12, 18)
    APP_FEE_RATIO = 1 / 3
