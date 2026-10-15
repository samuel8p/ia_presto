# Presto AI Chat (`chat-app`)

Microservicio de chat con IA para **administradores** de la plataforma Presto.
Está escrito en **Python + FastAPI** (el backend del proyecto es Python/Flask, así que
se integra naturalmente) y sigue las mismas convenciones que `auth` y `transactions`:

- Puerto **5002**, rutas bajo `/api`
- JWT **HS256** con el mismo `SECRET_KEY` que auth y transactions
- MongoDB Atlas (bases `chat`, `users`, `transactions`, `logs`)
- Respuestas: `{"message": ..., ...}` / errores `{"error": "<mensaje en español>"}`
- Auditoría en la base `logs` (colección `chat_logs`)

## ¿Qué hace?

1. Valida el JWT y exige que el usuario tenga `role == "admin"` en la colección `users`.
2. Toma un snapshot **solo lectura** de los datos reales de la plataforma
   (usuarios, transacciones, créditos, inversiones, cashin/cashout, tarjetas).
3. Se lo pasa al LLM como contexto junto con el historial de la conversación.
4. Guarda la conversación en Mongo (`chat.conversations` / `chat.messages`).

## LLM: gratis (Groq por defecto, Ollama como alternativa)

Por defecto usa la **API gratuita de [Groq](https://console.groq.com)** (sin tarjeta,
muy rápida, cuota generosa). El modelo configurado es `qwen/qwen3.8-27b`, que responde
muy bien en español. Alternativamente, puedes correr un modelo **local con
[Ollama](https://ollama.com)**: gratis para siempre, ilimitado y **los datos financieros
nunca salen del servidor**. El código usa el cliente compatible con OpenAI, así que
cambiar de proveedor = cambiar solo 3 variables del `.env`:

| Variable | Groq (default) | Ollama local |
|---|---|---|
| `LLM_BASE_URL` | `https://api.groq.com/openai/v1` | `http://127.0.0.1:11434/v1` |
| `LLM_API_KEY` | tu key de Groq | `ollama` (lo ignora) |
| `LLM_MODEL` | `qwen/qwen3.8-27b` | `qwen2.5:3b-instruct` |

> ⚠️ Con Groq, los mensajes del chat (incluidos los datos de la plataforma que viajan
> como contexto) salen hacia los servidores de Groq. Si algún día necesitás privacidad
> total, pasá a Ollama sin tocar código.

### Instalar Ollama (Windows, alternativa local)

```powershell
winget install Ollama.Ollama
# cerrar y abrir la terminal, y luego:
ollama pull qwen2.5:3b-instruct     # recomendado para PC con GPU de 4 GB (GTX 1650 SUPER)
ollama serve                        # si no queda corriendo como servicio
```

### Modelos sugeridos

| Modelo | Tamaño aprox. | Recomendado para |
|---|---|---|
| `qwen2.5:3b-instruct` (por defecto) | ~2 GB | GPUs de 4 GB, rápido y buen español |
| `qwen2.5:7b-instruct` | ~4.7 GB | Más calidad; con 16 GB de RAM funciona por CPU (más lento) |
| `llama3.2:3b-instruct` | ~2 GB | Alternativa liviana |

## Instalación y ejecución

```powershell
cd chat\chat-app
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env   # completar MONGO_URI y SECRET_KEY (¡el mismo de auth y transactions!)
python run.py
```

Servicio en `http://127.0.0.1:5002`. Docs interactivas en `/docs` (Swagger).

## Convertir un usuario en administrador

El chat es solo para admins. Como el JWT todavía no trae el claim `role`,
el servicio lo consulta en la base `users`:

```powershell
python scripts\promote_admin.py correo@ejemplo.com
```

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/health` | Health check (`{"status": "ok"}`) |
| POST | `/api/chat/message` | Envía un mensaje. Body: `{"message": "...", "conversation_id": "..."?}`. Respuesta: `{"message", "conversation_id", "reply"}` |
| GET | `/api/chat/history?conversation_id=` | Historial de una conversación |
| GET | `/api/chat/conversations?page=&per_page=` | Lista de conversaciones del usuario (paginada) |

Todos requieren `Authorization: Bearer <token JWT>` y rol admin (salvo `/api/health`).

## Integración con el API Gateway

Ya está hecha en `api/api-gateway-app`: las rutas `/api/chat/*` se enrutan al
servicio `chat` (`CHAT_SERVICE_URL`, por defecto `http://127.0.0.1:5002`) y usan un
timeout mayor (`CHAT_REQUEST_TIMEOUT=120`), porque el LLM tarda más que el resto.

El front (`Front/frontend-app-builders`) ya consumía `/api/chat/message` y
`/api/chat/history` desde `src/lib/api/chat.ts`, así que el widget de chat que ya
existe funciona contra este servicio sin cambios en el front.

## Variables de entorno

| Variable | Descripción | Default |
|---|---|---|
| `MONGO_URI` | URI de Atlas (misma que el resto) | — (obligatoria) |
| `MONGO_DB_CHAT` | Base para conversaciones | `chat` |
| `SECRET_KEY` | Misma que auth y transactions | — (obligatoria) |
| `LLM_BASE_URL` | Endpoint OpenAI-compatible del LLM | `http://127.0.0.1:11434/v1` (Ollama) |
| `LLM_API_KEY` | Key del proveedor (Ollama la ignora) | `ollama` |
| `LLM_MODEL` | Modelo a usar | `qwen2.5:3b-instruct` |
| `LLM_TIMEOUT` | Timeout de la llamada al LLM (s) | `120` |
| `LLM_MAX_TOKENS` | Máximo de tokens de respuesta (el tier gratis de Groq limita a 1000/min) | `700` |
| `LLM_TEMPERATURE` | Creatividad (0 = muy literal) | `0.3` |
| `HISTORY_CONTEXT_MESSAGES` | Mensajes de contexto enviados al modelo | `12` |
| `PORT` | Puerto del servicio | `5002` |
