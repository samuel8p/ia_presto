import jwt
from bson import ObjectId
from fastapi import Depends, Request

from app.config import Config
from app.exceptions import ChatError


def decode_token(request: Request) -> dict:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise ChatError("Token requerido", 401)

    try:
        payload = jwt.decode(
            header[7:], Config.SECRET_KEY, algorithms=[Config.JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        raise ChatError("Token expirado", 401)
    except jwt.InvalidTokenError:
        raise ChatError("Token inválido", 401)

    if not payload.get("sub"):
        raise ChatError("Token sin identificador de usuario", 401)
    return payload


async def get_current_user(request: Request) -> dict:
    return decode_token(request)


async def require_admin(request: Request, user: dict = Depends(get_current_user)) -> dict:
    """Solo permite usuarios con role == "admin" en la colección users.

    El JWT aún no trae el claim "role" (auth no lo emite), así que se valida
    contra la base de datos users. Cuando auth agregue el claim, acá se puede
    leer directo del token.
    """
    user_id = user["sub"]
    query = {"_id": ObjectId(user_id)} if ObjectId.is_valid(user_id) else {"_id": user_id}

    doc = request.app.state.db_users.users.find_one(query, {"role": 1, "email": 1, "name": 1})
    if not doc or doc.get("role") != "admin":
        raise ChatError("Se requiere permiso de administrador", 403)

    return {**user, "role": "admin", "name": doc.get("name"), "email": doc.get("email")}
