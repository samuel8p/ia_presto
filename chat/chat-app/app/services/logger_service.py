from datetime import datetime, timezone


def log_chat_message(
    db_logs,
    *,
    user_id: str,
    conversation_id: str,
    details: dict,
    ip_address: str | None = None,
    user_agent: str = "",
    action: str = "chat_message",
) -> None:
    db_logs.chat_logs.insert_one(
        {
            "action": action,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "details": details,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.now(timezone.utc),
        }
    )
