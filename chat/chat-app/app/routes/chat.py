from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.config import Config
from app.exceptions import ChatError
from app.middleware.auth import require_admin
from app.prompts import build_system_prompt
from app.services import admin_stats, conversation_service, llm_service, logger_service

router = APIRouter()


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = None


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/chat/message")
def send_message(
    payload: ChatMessageRequest,
    request: Request,
    user: dict = Depends(require_admin),
):
    db = request.app.state.mongo
    user_id = user["sub"]

    if payload.conversation_id:
        conversation = conversation_service.get_conversation(db, payload.conversation_id, user_id)
        if conversation is None:
            raise ChatError("Conversación no encontrada", 404)
    else:
        conversation = conversation_service.create_conversation(db, user_id, payload.message)

    history = conversation_service.get_messages(
        db, conversation["_id"], limit=Config.HISTORY_CONTEXT_MESSAGES
    )
    llm_history = [{"role": m["role"], "content": m["content"]} for m in history]
    llm_history.append({"role": "user", "content": payload.message})

    snapshot = admin_stats.get_admin_snapshot(
        request.app.state.db_transactions, request.app.state.db_users
    )
    system_prompt = build_system_prompt(snapshot)

    try:
        reply = llm_service.chat_completion(system_prompt, llm_history)
    except llm_service.LLMRateLimitError:
        raise ChatError(
            "El servicio de IA alcanzó su límite de uso temporal, intentá de nuevo en unos minutos", 429
        )
    except llm_service.LLMUnavailableError:
        raise ChatError("El servicio de IA no está disponible en este momento", 502)

    conversation_service.add_message(db, conversation["_id"], user_id, "user", payload.message)
    conversation_service.add_message(db, conversation["_id"], user_id, "assistant", reply)

    logger_service.log_chat_message(
        request.app.state.db_logs,
        user_id=user_id,
        conversation_id=str(conversation["_id"]),
        details={
            "message_length": len(payload.message),
            "reply_length": len(reply),
            "model": Config.LLM_MODEL,
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent", ""),
    )

    return {
        "message": "Respuesta generada",
        "conversation_id": str(conversation["_id"]),
        "reply": reply,
    }


@router.get("/chat/history")
def get_history(
    conversation_id: str,
    request: Request,
    user: dict = Depends(require_admin),
):
    db = request.app.state.mongo
    conversation = conversation_service.get_conversation(db, conversation_id, user["sub"])
    if conversation is None:
        raise ChatError("Conversación no encontrada", 404)

    messages = conversation_service.get_messages(db, conversation["_id"], limit=200)
    return {
        "conversation_id": conversation_id,
        "messages": [
            {
                "role": m["role"],
                "content": m["content"],
                "created_at": m["created_at"].isoformat() if m.get("created_at") else None,
            }
            for m in messages
        ],
    }


@router.get("/chat/conversations")
def get_conversations(
    request: Request,
    user: dict = Depends(require_admin),
    page: int = 1,
    per_page: int = 20,
):
    page = max(1, page)
    per_page = max(1, min(per_page, 50))

    items, total, pages = conversation_service.list_conversations(
        request.app.state.mongo, user["sub"], page, per_page
    )
    return {
        "conversations": [
            {
                "id": str(item["_id"]),
                "title": item.get("title", ""),
                "message_count": item.get("message_count", 0),
                "created_at": item["created_at"].isoformat() if item.get("created_at") else None,
                "updated_at": item["updated_at"].isoformat() if item.get("updated_at") else None,
            }
            for item in items
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
    }
