"""Promueve un usuario a administrador para poder usar el chat de IA.

Uso:
    python scripts/promote_admin.py correo@ejemplo.com
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pymongo import MongoClient  # noqa: E402

from app.config import Config  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python scripts/promote_admin.py <email>")
        sys.exit(1)

    email = sys.argv[1].strip().lower()
    client = MongoClient(Config.MONGO_URI, tz_aware=True)
    users = client[Config.MONGO_DB_USERS].users

    result = users.update_one(
        {"email": email},
        {"$set": {"role": "admin", "updated_at": datetime.now(timezone.utc)}},
    )

    if result.matched_count == 0:
        print(f"No existe ningún usuario con el email '{email}'")
        sys.exit(1)

    print(f"Listo: '{email}' ahora es administrador y puede usar el chat de IA.")


if __name__ == "__main__":
    main()
