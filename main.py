"""Komut satırı arayüzü.

Örnek:
    python main.py "Yapay Zekanın Eğitimdeki Rolü" --slides 6 --tone Eğitici --theme Orman
"""

import argparse
import sys
from pathlib import Path
from typing import get_args

from pydantic import ValidationError

from presentation_generator.config import ConfigError, load_settings
from presentation_generator.generator import PresentationGenerator
from presentation_generator.images import PixabayClient
from presentation_generator.llm import GeminiClient, LLMError
from presentation_generator.models import PresentationRequest, Tone
from presentation_generator.pptx_builder import build_pptx, file_name_for
from presentation_generator.themes import DEFAULT_THEME_NAME, THEMES

OUTPUT_DIR = Path("outputs")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bir konudan PowerPoint sunumu oluşturur.")
    parser.add_argument("topic", help="Sunumun konusu")
    parser.add_argument("--slides", type=int, default=6, help="İçerik slaytı sayısı (3-10)")
    parser.add_argument("--audience", default="Genel izleyici", help="Hedef kitle")
    parser.add_argument("--tone", choices=get_args(Tone), default="Profesyonel",
                        help="Anlatım tonu")
    parser.add_argument("--theme", choices=THEMES, default=DEFAULT_THEME_NAME,
                        help="Renk teması")
    parser.add_argument("--output", type=Path, help="Kaydedilecek .pptx dosyasının yolu")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        request = PresentationRequest(
            topic=args.topic, audience=args.audience, tone=args.tone, slide_count=args.slides
        )
        settings = load_settings()
        generator = PresentationGenerator(GeminiClient(settings))

        print("1/4  Slayt planı çıkarılıyor...")
        plan = generator.create_plan(request)
        for number, slide in enumerate(plan.slides, start=1):
            print(f"     {number}. {slide.title}")

        print("2/4  Slayt içerikleri yazılıyor...")
        presentation = generator.write_content(request, plan)

        if settings.pixabay_api_key:
            print("3/4  Fotoğraflar aranıyor...")
            images = PixabayClient(settings.pixabay_api_key).find_all(presentation.photo_queries())
        else:
            print("3/4  Fotoğraflar atlandı (.env içinde PIXABAY_API_KEY yok).")
            images = {}

        print("4/4  PowerPoint dosyası oluşturuluyor...")
        output_path = args.output or OUTPUT_DIR / file_name_for(presentation.title)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(build_pptx(presentation, THEMES[args.theme], images))

    except ValidationError:
        print("Hata: konu en az 3 karakter, slayt sayısı 3 ile 10 arasında olmalı.", file=sys.stderr)
        return 1
    except (ConfigError, LLMError) as exc:
        print(f"Hata: {exc}", file=sys.stderr)
        return 1

    print(f"\nSunum hazır: {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
