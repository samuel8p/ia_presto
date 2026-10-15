from flask import Flask
from pymongo import MongoClient

from app.config import Config
from app.routes.transactions import transactions_bp
from app.routes.limits import limits_bp
from app.routes.cashin import cashin_bp
from app.routes.cashout import cashout_bp
from app.routes.cards import cards_bp
from app.routes.credits import credits_bp
from app.routes.investments import investments_bp
from app.middleware.auth import jwt_middleware
from app.services.limits_service import LimitsService


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    client = MongoClient(Config.MONGO_URI)

    app.db_transactions = client[Config.MONGO_DB_TRANSACTIONS]
    app.db_logs = client[Config.MONGO_DB_LOGS]

    app.db_transactions.transactions.create_index("user_id")
    app.db_transactions.cashin.create_index("user_id")
    app.db_transactions.cashout.create_index("user_id")
    app.db_transactions.tarjetas_usuarios.create_index("user_id", unique=True)
    app.db_transactions.credits.create_index("user_id")
    app.db_transactions.investments.create_index("user_id")

    LimitsService(app.db_transactions)

    jwt_middleware(app)
    app.register_blueprint(transactions_bp, url_prefix="/api")
    app.register_blueprint(limits_bp, url_prefix="/api")
    app.register_blueprint(cashin_bp, url_prefix="/api")
    app.register_blueprint(cashout_bp, url_prefix="/api")
    app.register_blueprint(cards_bp, url_prefix="/api")
    app.register_blueprint(credits_bp, url_prefix="/api")
    app.register_blueprint(investments_bp, url_prefix="/api")

    return app
