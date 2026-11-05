"""Değerlendirmede üretilen sunumları .pptx dosyası olarak dışa aktarır.

Sunum içerikleri sonuç dosyasında saklandığı için Gemini'ye tekrar istek atılmaz;
sadece fotoğraflar Pixabay'den yeniden indirilir.

Kullanım (proje klasöründen):
    python -m evaluation.export_decks              # "main" sonucundaki 24 sunum
    python -m evaluation.export_decks --run main-v1
"""

import argparse
import json
import time
from pathlib import Path

from presentation_generator.config import load_settings
from presentation_generator.images import PixabayClient
from presentation_generator.models import Presentation
from presentation_generator.pptx_builder import build_pptx, file_name_for

from .run import RESULTS_DIR

OUTPUT_DIR = Path("outputs") / "degerlendirme"
PAUSE_SECONDS = 3  # Pixabay dakikada 100 istek kabul eder; peş peşe sunumlarda sınırı aşmamak için


def main() -> None:
    parser = argparse.ArgumentParser(description="Değerlendirme sunumlarını .pptx olarak kaydeder.")
    parser.add_argument("--run", default="main", help="Sonuç dosyasının adı (varsayılan: main)")
    args = parser.parse_args()

    run = json.loads((RESULTS_DIR / f"{args.run}.json").read_text(encoding="utf-8"))
    settings = load_settings()
    pixabay = PixabayClient(settings.pixabay_api_key) if settings.pixabay_api_key else None
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for number, case in enumerate(run["cases"], start=1):
        if "presentation" not in case:
            continue  # başarısız örnek: kaydedilecek sunum yok
        presentation = Presentation.model_validate(case["presentation"])
        queries = presentation.photo_queries()
        images = pixabay.find_all(queries) if pixabay else {}
        path = OUTPUT_DIR / f"{number:02d}-{file_name_for(case['topic'])}"
        path.write_bytes(build_pptx(presentation, images=images))
        print(f"[{number:02d}] {path}  ({len(images)}/{len(queries)} fotoğraf)", flush=True)
        time.sleep(PAUSE_SECONDS)


if __name__ == "__main__":
    main()
