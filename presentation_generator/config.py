"""Uygulama ayarları. Değerler .env dosyasından okunur."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

# Seçim gerekçesi ve ölçümler: docs/PROMPT_VE_MODEL.md, evaluation/RAPOR.md
DEFAULT_MODEL = "gemini-3.1-flash-lite"


class ConfigError(Exception):
    """Ayarlar eksik veya hatalı olduğunda fırlatılır."""


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str
    pixabay_api_key: str | None  # yoksa sunum resimsiz üretilir


def load_settings() -> Settings:
    """Ortam değişkenlerinden ayarları okur."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ConfigError(
            "GEMINI_API_KEY bulunamadı. '.env.example' dosyasını '.env' olarak "
            "kopyalayıp API anahtarınızı yazın."
        )

    model = os.getenv("GEMINI_MODEL", "").strip() or DEFAULT_MODEL
    pixabay_api_key = os.getenv("PIXABAY_API_KEY", "").strip() or None
    return Settings(api_key=api_key, model=model, pixabay_api_key=pixabay_api_key)
