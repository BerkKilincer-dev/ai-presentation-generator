"""evaluation/results/ altındaki sonuçlardan Markdown değerlendirme raporu üretir.

Kullanım (proje klasöründen):
    python -m evaluation.report

"main" adlı sonuç ana rapordur (24 örnek, gerçek kullanım ayarları);
"main-v1" prompt iyileştirmesinden önceki ana sonuçtur;
"cmp-" ile başlayanlar model karşılaştırma tablosuna girer.
Elle yazılan yorumlar evaluation/gozlemler.md dosyasından rapora eklenir.

Kalite kontrolleri, sonuç dosyalarında saklanan sunumlar üzerinde her seferinde
yeniden hesaplanır; kontroller değiştiğinde API'ye tekrar gitmek gerekmez.
"""

import json
import math
import re
from collections import Counter
from pathlib import Path
from statistics import mean, median

from presentation_generator.models import Presentation, PresentationRequest

from .checks import run_checks
from .run import RESULTS_DIR

REPORT_PATH = Path(__file__).parent / "RAPOR.md"
NOTES_PATH = Path(__file__).parent / "gozlemler.md"
MAIN_RUN = "main"
PREVIOUS_MAIN_RUN = "main-v1"


def load_runs() -> dict[str, dict]:
    runs = {path.stem: json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(RESULTS_DIR.glob("*.json"))}
    for run in runs.values():
        for case in run["cases"]:
            _refresh_checks(case)
    return runs


def _refresh_checks(case: dict) -> None:
    """Saklanan sunum üzerinde kalite kontrollerini güncel haliyle yeniden çalıştırır."""
    if "presentation" not in case:
        return
    request = PresentationRequest(topic=case["topic"], audience=case["audience"],
                                  tone=case["tone"], slide_count=case["slide_count"])
    checks = run_checks(request, Presentation.model_validate(case["presentation"]))
    case["checks"] = checks
    case["quality"] = round(sum(checks.values()) / len(checks), 3)


def percentile(values: list[float], ratio: float) -> float:
    """En yakın sıra yöntemiyle yüzdelik (ör. 0.95 -> p95)."""
    ordered = sorted(values)
    return ordered[max(0, math.ceil(ratio * len(ordered)) - 1)]


def summarize(run: dict) -> dict:
    """Bir çalıştırmanın özet metrikleri."""
    cases = run["cases"]
    succeeded = [c for c in cases if c["success"]]
    seconds = [c["seconds"] for c in succeeded]
    costs = [c["cost_usd"] for c in succeeded if c["cost_usd"] is not None]
    return {
        "count": len(cases),
        "succeeded": len(succeeded),
        "success_rate": len(succeeded) / len(cases),
        "quality": mean(c["quality"] for c in succeeded) if succeeded else 0,
        "avg_seconds": mean(seconds) if seconds else 0,
        "median_seconds": median(seconds) if seconds else 0,
        "p95_seconds": percentile(seconds, 0.95) if seconds else 0,
        "max_seconds": max(seconds) if seconds else 0,
        "avg_input_tokens": mean(c["input_tokens"] for c in succeeded) if succeeded else 0,
        "avg_output_tokens": mean(c["output_tokens"] for c in succeeded) if succeeded else 0,
        "avg_cost": mean(costs) if costs else None,
        "fallback_cases": sum(any(m != run["model"] for m in c["models_used"]) for c in cases),
    }


def _money(value: float | None, digits: int = 4) -> str:
    return "—" if value is None else f"${value:.{digits}f}"


def _per_thousand(cost: float | None) -> str:
    return _money(None if cost is None else cost * 1000, digits=2)


def _main_section(run: dict) -> list[str]:
    s = summarize(run)
    cases = run["cases"]
    succeeded = [c for c in cases if c["success"]]

    lines = [
        "## Özet",
        "",
        f"Model: `{run['model']}` (yedek modeller {'açık' if run['fallbacks'] else 'kapalı'}, "
        f"fotoğraflar {'açık' if run['images'] else 'kapalı'}) · Tarih: {run['date']}",
        "",
        "| Metrik | Değer |",
        "|---|---|",
        f"| Test örneği | {s['count']} |",
        f"| **Başarı oranı** | **%{s['success_rate'] * 100:.1f}** ({s['succeeded']}/{s['count']}) |",
        f"| Ortalama kalite puanı | %{s['quality'] * 100:.1f} |",
        f"| Ortalama gecikme | {s['avg_seconds']:.1f} sn |",
        f"| Medyan / p95 / en uzun gecikme | {s['median_seconds']:.1f} / "
        f"{s['p95_seconds']:.1f} / {s['max_seconds']:.1f} sn |",
        f"| Ortalama token (girdi / çıktı) | {s['avg_input_tokens']:,.0f} / {s['avg_output_tokens']:,.0f} |",
        f"| **Sunum başına maliyet** | **{_money(s['avg_cost'])}** |",
        f"| 1.000 sunumun maliyeti | {_per_thousand(s['avg_cost'])} |",
        f"| Yedek modele düşülen örnek | {s['fallback_cases']} |",
    ]

    if run["images"] and succeeded:
        found = sum(c["photos_found"] for c in succeeded)
        places = sum(c["photo_places"] for c in succeeded)
        lines.append(f"| Fotoğraf bulunma oranı | %{found / places * 100:.1f} ({found}/{places}) |")

    step_names = {"plan": "1. Plan (LLM)", "content": "2. İçerik (LLM)",
                  "images": "3. Fotoğraflar (Pixabay)", "pptx": "4. PPTX oluşturma"}
    lines += ["", "### Adım bazında ortalama süre", "", "| Adım | Ortalama |", "|---|---|"]
    for step, label in step_names.items():
        values = [c["timings"][step] for c in succeeded if step in c["timings"]]
        if values:
            lines.append(f"| {label} | {mean(values):.2f} sn |")

    check_names = list(succeeded[0]["checks"]) if succeeded else []
    lines += ["", "## Kalite kontrolleri", "",
              "Başarılı her sunum için prompt'taki kuralların uygulanıp uygulanmadığı otomatik kontrol edildi.",
              "", "| Kontrol | Geçen |", "|---|---|"]
    for name in check_names:
        passed = sum(c["checks"][name] for c in succeeded)
        lines.append(f"| {name} | %{passed / len(succeeded) * 100:.0f} ({passed}/{len(succeeded)}) |")

    lines += ["", "## Test örnekleri", "",
              "| # | Konu | Hedef kitle | Ton | Slayt | Sonuç | Kalite | Süre | Maliyet |",
              "|---|---|---|---|---|---|---|---|---|"]
    for number, c in enumerate(cases, start=1):
        outcome = "✅" if c["success"] else "❌"
        quality = f"%{c['quality'] * 100:.0f}" if c["success"] else "—"
        lines.append(f"| {number} | {c['topic']} | {c['audience']} | {c['tone']} | {c['slide_count']} "
                     f"| {outcome} | {quality} | {c['seconds']:.1f} sn | {_money(c['cost_usd'])} |")

    failures = [c for c in cases if not c["success"]]
    if failures:
        lines += ["", "### Başarısız örnekler", ""]
        lines += [f"- **{c['topic']}**: {c.get('error', 'kontrol başarısız')}" for c in failures]
    return lines


def _comparison_section(runs: dict[str, dict]) -> list[str]:
    lines = ["## Model karşılaştırması", "",
             "Aynı test örnekleri her model için yedek modeller ve fotoğraflar kapalı olarak çalıştırıldı.",
             "Başarısız istekler API hata koduyla gösterilir (429: kota/hız sınırı, 503: model aşırı yoğun).",
             "", "| Model | Başarı | Kalite | Ort. gecikme | p95 | Sunum başına | 1.000 sunum | API hataları |",
             "|---|---|---|---|---|---|---|---|"]
    for run in runs.values():
        s = summarize(run)
        if s["succeeded"]:
            quality = f"%{s['quality'] * 100:.1f}"
            avg, p95 = f"{s['avg_seconds']:.1f} sn", f"{s['p95_seconds']:.1f} sn"
        else:  # hiç yanıt alınamadı: ölçüm yok
            quality = avg = p95 = "—"
        lines.append(
            f"| `{run['model']}` | %{s['success_rate'] * 100:.0f} ({s['succeeded']}/{s['count']}) "
            f"| {quality} | {avg} | {p95} | {_money(s['avg_cost'])} "
            f"| {_per_thousand(s['avg_cost'])} | {_error_codes(run)} |"
        )
    return lines


def _error_codes(run: dict) -> str:
    """Başarısız örneklerin API hata kodları, ör. '503 ×5'."""
    codes = Counter(code for c in run["cases"] if not c["success"]
                    for code in re.findall(r": (\d{3}) ", c.get("error", "")))
    return ", ".join(f"{code} ×{count}" for code, count in codes.most_common()) or "—"


def _iteration_section(before: dict, after: dict) -> list[str]:
    """Prompt iyileştirmesinden önceki ve sonraki ana çalıştırmanın karşılaştırması."""
    lines = ["## Prompt iyileştirmesi: önce ve sonra", "",
             "İlk ana değerlendirmede kart maddelerinin sık sık 10 kelime sınırını aştığı ve "
             "kartlardan taştığı görüldü. Prompt'taki kart kuralı netleştirildi ve aynı 24 örnek "
             "yeniden çalıştırıldı.", "",
             "| Metrik | Önce (v1) | Sonra (v2) |", "|---|---|---|"]
    b, a = summarize(before), summarize(after)
    rows = [
        ("Başarı oranı", f"%{b['success_rate'] * 100:.0f}", f"%{a['success_rate'] * 100:.0f}"),
        ("Ortalama kalite puanı", f"%{b['quality'] * 100:.1f}", f"%{a['quality'] * 100:.1f}"),
        ("Ortalama gecikme", f"{b['avg_seconds']:.1f} sn", f"{a['avg_seconds']:.1f} sn"),
        ("Medyan gecikme", f"{b['median_seconds']:.1f} sn", f"{a['median_seconds']:.1f} sn"),
        ("Sunum başına maliyet", _money(b["avg_cost"]), _money(a["avg_cost"])),
    ]
    for name in after["cases"][0].get("checks", {}):
        rows.append((name, _check_rate(before, name), _check_rate(after, name)))
    lines += [f"| {metric} | {old} | {new} |" for metric, old, new in rows
              if old != new or metric in ("Başarı oranı", "Ortalama kalite puanı")]
    return lines


def _check_rate(run: dict, name: str) -> str:
    succeeded = [c for c in run["cases"] if c["success"]]
    passed = sum(c["checks"][name] for c in succeeded)
    return f"%{passed / len(succeeded) * 100:.0f}"


def build_report() -> str:
    runs = load_runs()
    lines = ["# Değerlendirme Raporu", "",
             "> Bu dosya `python -m evaluation.report` ile `evaluation/results/` altındaki "
             "sonuçlardan otomatik üretilir.", ""]

    lines += ["## Yöntem", "",
              "- Her test örneği uçtan uca çalıştırıldı: plan → içerik → fotoğraflar → .pptx.",
              "- **Başarı:** sunum üretildi, .pptx dosyası python-pptx ile sorunsuz açıldı ve "
              "istenen sayıda içerik slaytı var.",
              "- **Kalite puanı:** başarılı sunumda geçilen otomatik kontrollerin oranı.",
              "- **Gecikme:** dört adımın toplam süresi (kullanıcının beklediği süre).",
              "- **Maliyet:** API'nin döndürdüğü token sayıları × ücretli katman fiyatları "
              "(düşünme token'ları dahil). Ücretsiz katmanda maliyet 0'dır.", ""]

    if MAIN_RUN in runs:
        lines += _main_section(runs[MAIN_RUN]) + [""]

    if PREVIOUS_MAIN_RUN in runs and MAIN_RUN in runs:
        lines += _iteration_section(runs[PREVIOUS_MAIN_RUN], runs[MAIN_RUN]) + [""]

    comparison = {name: run for name, run in runs.items() if name.startswith("cmp-")}
    if comparison:
        lines += _comparison_section(comparison) + [""]

    if NOTES_PATH.exists():
        lines += [NOTES_PATH.read_text(encoding="utf-8").strip(), ""]

    return "\n".join(lines)


def main() -> None:
    REPORT_PATH.write_text(build_report(), encoding="utf-8")
    print(f"Rapor yazıldı: {REPORT_PATH}")


if __name__ == "__main__":
    main()
