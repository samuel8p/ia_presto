from functools import lru_cache
import logging

from openai import APIConnectionError, APIError, APITimeoutError, OpenAI, RateLimitError

from app.config import Config

logger = logging.getLogger("chat.llm")


class LLMUnavailableError(Exception):
    """El proveedor de LLM no respondió (caído, sin modelo, timeout, etc.)."""


class LLMRateLimitError(Exception):
    """El proveedor de LLM alcanzó su límite de uso (tier gratuito)."""


@lru_cache(maxsize=1)
def _get_client() -> OpenAI:
    return OpenAI(
        base_url=Config.LLM_BASE_URL,
        api_key=Config.LLM_API_KEY or "ollama",
        timeout=Config.LLM_TIMEOUT,
    )


def chat_completion(system_prompt: str, messages: list[dict]) -> str:
    """Devuelve la respuesta del modelo dado el prompt de sistema y el historial.

    messages: [{"role": "user"|"assistant", "content": str}, ...]
    """
    try:
        response = _get_client().chat.completions.create(
            model=Config.LLM_MODEL,
            messages=[{"role": "system", "content": system_prompt}, *messages],
            max_tokens=Config.LLM_MAX_TOKENS,
            temperature=Config.LLM_TEMPERATURE,
        )
    except RateLimitError as exc:
        logger.warning("El proveedor de LLM alcanzó su límite de uso: %s", exc)
        raise LLMRateLimitError("El servicio de IA alcanzó su límite de uso temporal") from exc
    except (APIConnectionError, APITimeoutError) as exc:
        logger.exception("No se pudo conectar con el proveedor de LLM (%s)", Config.LLM_BASE_URL)
        raise LLMUnavailableError(
            f"No se pudo conectar con el proveedor de LLM ({Config.LLM_BASE_URL})"
        ) from exc
    except APIError as exc:
        logger.exception("El proveedor de LLM respondió con un error")
        raise LLMUnavailableError(f"El proveedor de LLM respondió con un error: {exc}") from exc

    content = response.choices[0].message.content if response.choices else None
    if not content:
        raise LLMUnavailableError("El modelo devolvió una respuesta vacía")
    return content.strip()
