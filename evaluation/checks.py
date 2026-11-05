"""Üretilen sunumun otomatik kalite kontrolleri.

Her kontrol, prompt'ta LLM'den istenen bir kuralın gerçekten uygulanıp
uygulanmadığına bakar. Ölçütler prompt'taki sınırlardan biraz esnektir
(ör. 14 kelime istenir, 16'ya kadar kabul edilir); amaç LLM'i cezalandırmak
değil, kuralı belirgin şekilde çiğneyip çiğnemediğini görmektir.
"""

import re
from io import BytesIO

from pptx import Presentation as PptxDeck

from presentation_generator.models import Presentation, PresentationRequest, Slide
from presentation_generator.pages import resolve_layout

TURKISH_LETTERS = set("çğıöşüÇĞİÖŞÜ")


def _words(text: str) -> int:
    return len(text.split())


def _sentences(text: str) -> int:
    return len([s for s in re.split(r"[.!?]+", text) if s.strip()])


def _is_turkish(text: str) -> bool:
    return any(char in TURKISH_LETTERS for char in text)


def _has_right_item_count(slide: Slide) -> bool:
    """Düzenin gösterdiği madde sayısı prompt'taki sınırlar içinde mi?"""
    if slide.layout == "image":
        return 3 <= len(slide.bullets) <= 5
    if slide.layout == "cards":
        return 3 <= len(slide.bullets) <= 4
    if slide.layout == "comparison":
        return all(2 <= len(column.bullets) <= 4 for column in slide.columns)
    return True  # highlight: madde yok, tek cümle


def run_checks(request: PresentationRequest, presentation: Presentation) -> dict[str, bool]:
    """Kalite kontrollerini çalıştırır: {kontrol adı: geçti mi}."""
    slides = presentation.slides
    bullets = [b for s in slides for b in s.bullets]
    bullets += [b for s in slides for column in s.columns for b in column.bullets]
    layouts = [s.layout for s in slides]
    slide_texts = [" ".join([s.title, s.highlight, *s.bullets, s.notes]) for s in slides]

    return {
        "Slayt sayısı istenenle aynı": len(slides) == request.slide_count,
        "Madde sayıları düzene uygun": all(_has_right_item_count(s) for s in slides),
        "Maddelerin %90'ı en fazla 16 kelime":
            sum(_words(b) <= 16 for b in bullets) >= 0.9 * len(bullets),
        "Kart maddeleri en fazla 12 kelime":  # kartlar dar; uzun madde taşar
            all(_words(b) <= 12 for s in slides if s.layout == "cards" for b in s.bullets),
        "Slayt başlıkları en fazla 9 kelime": all(_words(s.title) <= 9 for s in slides),
        "Seçilen düzenler uygulanabilir":
            all(resolve_layout(s, has_image=True) == s.layout for s in slides),
        "En fazla 1 vurgu slaytı": layouts.count("highlight") <= 1,
        "Art arda aynı düzen yok": all(a != b for a, b in zip(layouts, layouts[1:])),
        "Notlar en az 2 cümle ve 25 kelime":
            all(_sentences(s.notes) >= 2 and _words(s.notes) >= 25 for s in slides),
        "Tam 3 önemli çıkarım": len(presentation.takeaways) == 3,
        "İçerik Türkçe": all(_is_turkish(text) for text in slide_texts),
    }


def pptx_page_count(pptx_bytes: bytes) -> int:
    """Oluşturulan .pptx dosyasını python-pptx ile tekrar açar ve slayt sayısını döndürür."""
    return len(PptxDeck(BytesIO(pptx_bytes)).slides)
