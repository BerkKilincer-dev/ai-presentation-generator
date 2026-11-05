"""Sunumun sayfa sırası: hangi sayfa, hangi düzenle, kaçıncı sırada.

.pptx oluşturucu ve arayüzdeki önizleme bu listeyi birlikte kullanır;
böylece ikisi her zaman aynı sayfaları aynı sırayla gösterir.

Sayfa türleri:
    cover       kapak (fotoğraf varsa sağda)
    agenda      gündem: içerik slaytlarının başlıkları
    image       maddeler solda, fotoğraf sağda
    cards       her madde numaralı bir kartta
    comparison  iki sütunlu karşılaştırma
    highlight   tek büyük ana mesaj (fotoğraf varsa arka planda)
    bullets     düz madde listesi (LLM'in seçtiği düzen uygulanamazsa)
    takeaways   önemli çıkarımlar
    closing     teşekkürler
"""

from dataclasses import dataclass

from .models import COVER_PHOTO, Presentation, Slide, slide_photo_key

Images = dict[str, bytes]  # fotoğraf yeri ('cover', 'slide-0', ...) -> fotoğraf

MAX_CARDS = 4  # daha fazla madde yan yana kartlara sığmaz
MIN_SLIDES_FOR_AGENDA = 4  # kısa sunumlarda gündem sayfası gereksiz


@dataclass(frozen=True)
class Page:
    number: int
    kind: str
    slide: Slide | None = None  # sadece içerik sayfalarında dolu
    image: bytes | None = None


def plan_pages(presentation: Presentation, images: Images) -> list[Page]:
    """Sunumun tüm sayfalarını sırasıyla döndürür."""
    pages: list[tuple[str, Slide | None, bytes | None]] = [
        ("cover", None, images.get(COVER_PHOTO))
    ]
    if len(presentation.slides) >= MIN_SLIDES_FOR_AGENDA:
        pages.append(("agenda", None, None))

    for index, slide in enumerate(presentation.slides):
        image = images.get(slide_photo_key(index))
        pages.append((resolve_layout(slide, has_image=image is not None), slide, image))

    if presentation.takeaways:
        pages.append(("takeaways", None, None))
    pages.append(("closing", None, None))

    return [Page(number, kind, slide, image)
            for number, (kind, slide, image) in enumerate(pages, start=1)]


def resolve_layout(slide: Slide, has_image: bool) -> str:
    """LLM'in seçtiği düzen uygulanabiliyorsa onu, uygulanamıyorsa 'bullets' döndürür."""
    if slide.layout == "highlight" and slide.highlight:
        return "highlight"
    if slide.layout == "comparison" and len(slide.columns) == 2:
        return "comparison"
    if slide.layout == "cards" and 2 <= len(slide.bullets) <= MAX_CARDS:
        return "cards"
    if slide.layout == "image" and has_image:
        return "image"
    return "bullets"
