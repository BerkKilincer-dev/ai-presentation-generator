"""Değerlendirmeyi çalıştırır: her test örneği için sunum üretir, ölçer ve kontrol eder.

Kullanım (proje klasöründen):
    python -m evaluation.run                       # 24 örnek, gerçek kullanım ayarlarıyla
    python -m evaluation.run --model gemini-3.8-flash --limit 6 --no-fallback --no-images

Sonuçlar evaluation/results/<ad>.json dosyasına yazılır. Rapor için:
    python -m evaluation.report
"""

import argparse
import json
import time
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from presentation_generator.config import load_settings
from presentation_generator.generator import PresentationGenerator
from presentation_generator.images import PixabayClient
from presentation_generator.llm import GeminiClient, LLMError
from presentation_generator.models import PresentationRequest
from presentation_generator.pages import plan_pages
from presentation_generator.pptx_builder import build_pptx

from .checks import pptx_page_count, run_checks
from .pricing import call_cost
from .test_cases import TEST_CASES

RESULTS_DIR = Path(__file__).parent / "results"


def evaluate_case(request: PresentationRequest, llm: GeminiClient,
                  pixabay: PixabayClient | None) -> dict:
    """Tek bir test örneğini uçtan uca çalıştırır; ölçümleri ve kontrol sonuçlarını döndürür."""
    result = request.model_dump()
    timings: dict[str, float] = {}
    llm.calls.clear()
    generator = PresentationGenerator(llm)

    def timed(step: str, func, *args, **kwargs):
        started = time.perf_counter()
        value = func(*args, **kwargs)
        timings[step] = round(time.perf_counter() - started, 2)
        return value

    try:
        plan = timed("plan", generator.create_plan, request)
        presentation = timed("content", generator.write_content, request, plan)
    except LLMError as exc:
        result.update(success=False, error=str(exc)[:300])
    else:
        queries = presentation.photo_queries()
        images = timed("images", pixabay.find_all, queries) if pixabay else {}
        pptx_bytes = timed("pptx", build_pptx, presentation, images=images)
        pages = plan_pages(presentation, images)

        checks = run_checks(request, presentation)
        pptx_ok = pptx_page_count(pptx_bytes) == len(pages)
        result.update(
            # Başarı: sunum üretildi, .pptx sorunsuz açılıyor ve istenen sayıda slayt var.
            success=pptx_ok and checks["Slayt sayısı istenenle aynı"],
            checks=checks,
            quality=round(sum(checks.values()) / len(checks), 3),
            title=presentation.title,
            layouts=[s.layout for s in presentation.slides],
            presentation=presentation.model_dump(),  # örnek çıktı olarak saklanır
            photos_found=len(images),
            photo_places=len(queries) if pixabay else 0,
        )

    costs = [call_cost(call) for call in llm.calls]
    result.update(
        timings=timings,
        seconds=round(sum(timings.values()), 2),
        models_used=sorted({call.model for call in llm.calls}),
        input_tokens=sum(call.input_tokens for call in llm.calls),
        output_tokens=sum(call.output_tokens for call in llm.calls),
        cost_usd=None if None in costs else round(sum(costs), 6),
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sunum oluşturucuyu test seti üzerinde değerlendirir.")
    parser.add_argument("--model", help="Kullanılacak Gemini modeli (varsayılan: .env / config)")
    parser.add_argument("--limit", type=int, help="Sadece ilk N test örneğini çalıştır")
    parser.add_argument("--no-fallback", action="store_true",
                        help="Yedek modelleri kapat (modelleri kendi başına ölçmek için)")
    parser.add_argument("--no-images", action="store_true", help="Pixabay fotoğraflarını atla")
    parser.add_argument("--name", help="Sonuç dosyasının adı (varsayılan: model adı)")
    parser.add_argument("--pause", type=float, default=0,
                        help="Örnekler arasında beklenecek saniye (ücretsiz katmanın dakikalık "
                             "istek sınırına takılmamak için)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings()
    if args.model:
        settings = replace(settings, model=args.model)

    llm = GeminiClient(settings, use_fallbacks=not args.no_fallback)
    pixabay = None if args.no_images or not settings.pixabay_api_key \
        else PixabayClient(settings.pixabay_api_key)
    cases = TEST_CASES[:args.limit] if args.limit else TEST_CASES

    RESULTS_DIR.mkdir(exist_ok=True)
    output_path = RESULTS_DIR / f"{args.name or settings.model}.json"
    run = {
        "name": args.name or settings.model,
        "model": settings.model,
        "fallbacks": not args.no_fallback,
        "images": pixabay is not None,
        "date": datetime.now().isoformat(timespec="seconds"),
        "cases": [],
    }

    for number, request in enumerate(cases, start=1):
        if number > 1:
            time.sleep(args.pause)
        result = evaluate_case(request, llm, pixabay)
        run["cases"].append(result)
        # Her örnekten sonra kaydet: yarıda kesilse bile o ana kadarki sonuçlar kalır.
        output_path.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")

        status = f"kalite %{result['quality'] * 100:.0f}" if result["success"] \
            else f"BAŞARISIZ: {result.get('error', 'kontrol')}"
        print(f"[{number:02d}/{len(cases)}] {request.topic[:40]:<40} {result['seconds']:>6.1f} sn  {status}",
              flush=True)

    print(f"\nSonuçlar: {output_path}")


if __name__ == "__main__":
    main()
