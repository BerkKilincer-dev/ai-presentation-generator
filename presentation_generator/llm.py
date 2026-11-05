"""Gemini API ile konuşan katman.

Uygulamanın geri kalanı Gemini'nin detaylarını bilmez; sadece
`generate(prompt, schema)` çağırır ve doğrulanmış bir nesne alır.
Her çağrının token sayısı ve süresi `calls` listesine kaydedilir
(değerlendirme raporundaki maliyet ve gecikme buradan hesaplanır).
"""

import time
from dataclasses import dataclass
from typing import TypeVar

import httpx
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError

from .config import Settings
from .prompts import SYSTEM_INSTRUCTION

T = TypeVar("T", bound=BaseModel)

# Asıl model yoğunsa sırayla bu modeller denenir.
FALLBACK_MODELS = ("gemini-3.5-flash-lite", "gemini-2.5-flash")

# Bu hata kodları "model şu an yoğun / yetişemedi" demektir; başka model denenebilir.
BUSY_ERROR_CODES = {429, 500, 503, 504}

# Her model için: isteği 2 kez dene, tek istek en fazla 60 saniye beklesin.
RETRY_OPTIONS = types.HttpRetryOptions(attempts=2, initial_delay=2, max_delay=5)
REQUEST_TIMEOUT_MS = 60_000


class LLMError(Exception):
    """LLM isteği başarısız olduğunda veya yanıt beklenen yapıda olmadığında."""


@dataclass(frozen=True)
class CallStats:
    """Tek bir LLM çağrısının ölçümleri."""

    model: str  # isteği yanıtlayan model (yedeğe düşülmüş olabilir)
    input_tokens: int
    output_tokens: int  # yanıt + düşünme (thinking) token'ları; ikisi de çıktı fiyatından ödenir
    seconds: float


class GeminiClient:
    def __init__(self, settings: Settings, use_fallbacks: bool = True):
        self._client = genai.Client(
            api_key=settings.api_key,
            http_options=types.HttpOptions(
                timeout=REQUEST_TIMEOUT_MS, retry_options=RETRY_OPTIONS
            ),
        )
        # Önce .env'deki model, sonra yedekler (aynı model iki kez denenmesin).
        fallbacks = [m for m in FALLBACK_MODELS if m != settings.model] if use_fallbacks else []
        self._models = [settings.model] + fallbacks
        self.calls: list[CallStats] = []

    def generate(self, prompt: str, schema: type[T]) -> T:
        """Prompt'u gönderir, yanıtı verilen Pydantic şemasına göre döndürür."""
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",  # sadece JSON yanıt ver
            response_schema=schema,  # JSON tam olarak bu yapıda olsun
            temperature=0.7,
        )
        started = time.perf_counter()
        response, model = self._send(prompt, config)
        self.calls.append(_call_stats(response, model, time.perf_counter() - started))

        if not response.text:
            raise LLMError("Gemini boş yanıt döndürdü, lütfen tekrar deneyin.")

        try:
            return schema.model_validate_json(response.text)
        except ValidationError as exc:
            raise LLMError("Gemini beklenmeyen formatta yanıt verdi.") from exc

    def _send(self, prompt: str, config: types.GenerateContentConfig):
        """İsteği sırayla modellere gönderir; yoğun olan modeli atlayıp sıradakine geçer.

        Yanıtla birlikte onu veren modelin adını da döndürür.
        """
        failures = []  # hangi model neden yanıt vermedi (hata mesajında gösterilir)
        for model in self._models:
            try:
                response = self._client.models.generate_content(
                    model=model, contents=prompt, config=config
                )
                return response, model
            except errors.APIError as exc:
                if exc.code not in BUSY_ERROR_CODES:
                    raise LLMError(f"Gemini isteği başarısız oldu: {exc}") from exc
                failures.append(f"{model}: {exc.code} {exc.status}")
            except httpx.TimeoutException:
                failures.append(f"{model}: zaman aşımı")  # sıradaki modele geç

        raise LLMError("Tüm modeller şu an çok yoğun, lütfen biraz sonra tekrar deneyin. "
                       f"({'; '.join(failures)})")


def _call_stats(response: types.GenerateContentResponse, model: str, seconds: float) -> CallStats:
    usage = response.usage_metadata
    if usage is None:
        return CallStats(model, 0, 0, seconds)
    output = (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)
    return CallStats(model, usage.prompt_token_count or 0, output, seconds)
