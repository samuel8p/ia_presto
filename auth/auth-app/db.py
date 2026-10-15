from pymongo import MongoClient, ASCENDING

import config

_client = MongoClient(config.MONGO_URI, tz_aware=True)

users = _client[config.MONGO_DB_USERS]["users"]
sessions_log = _client[config.MONGO_DB_LOGS]["sessions"]
password_resets_log = _client[config.MONGO_DB_LOGS]["password_resets"]


def ensure_indexes():
    users.create_index([("email", ASCENDING)], unique=True)
