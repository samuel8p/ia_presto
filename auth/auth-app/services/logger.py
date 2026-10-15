from datetime import datetime, timezone

from db import sessions_log, password_resets_log


def _base(action: str, email: str, **extra):
    doc = {
        "action": action,
        "email": email,
        "created_at": datetime.now(timezone.utc),
    }
    doc.update(extra)
    return doc


def log_session(action: str, email: str, ip=None, user_agent=None, detail=None):
    doc = _base(action, email, detail=detail)
    if ip:
        doc["ip"] = ip
    if user_agent:
        doc["user_agent"] = user_agent
    return sessions_log.insert_one(doc)


def log_password_reset(action: str, email: str, detail=None):
    return password_resets_log.insert_one(_base(action, email, detail=detail))
