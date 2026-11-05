"""Uygulamanın veri modelleri.

Veri akışı:

    PresentationRequest  ->  PresentationPlan  ->  Presentation
    (kullanıcı girdisi)      (1. LLM adımı)        (2. LLM adımı)

PresentationPlan ve DeckContent, LLM'e "yanıtını tam olarak bu yapıda ver"
demek için şema olarak da kullanılır. Böylece LLM'den serbest metin değil,
doğrulanmış Python nesneleri alırız.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# image: maddeler + fotoğraf · cards: numaralı kartlar
# comparison: iki sütunlu karşılaştırma · highlight: tek büyük ana mesaj
SlideLayout = Literal["image", "cards", "comparison", "highlight"]

Tone = Literal["Profesyonel", "Eğitici", "Akademik", "İkna edici"]


class PresentationRequest(BaseModel):
    """Kullanıcının oluşturmak istediği sunum."""

    model_config = ConfigDict(str_strip_whitespace=True)

    topic: str = Field(min_length=3, max_length=200)
    audience: str = "Genel izleyici"
    tone: Tone = "Profesyonel"
    slide_count: int = Field(default=6, ge=3, le=10)


class SlidePlan(BaseModel):
    """Plandaki tek bir slayt: henüz içerik yok, sadece ne anlatılacağı var."""

    title: str = Field(description="Slayt başlığı")
    goal: str = Field(description="Bu slaytta anlatılacak ana fikir, tek cümle")


class PresentationPlan(BaseModel):
    """Sunumun iskeleti (1. LLM adımının çıktısı)."""

    title: str = Field(description="Sunumun başlığı")
    subtitle: str = Field(description="Tek cümlelik alt başlık")
    image_query: str = Field(description="Kapak fotoğrafı için İngilizce arama sorgusu")
    slides: list[SlidePlan]


class Column(BaseModel):
    """Karşılaştırma slaytındaki bir sütun."""

    title: str = Field(description="Sütun başlığı, en fazla 3 kelime")
    bullets: list[str] = Field(description="2-4 kısa madde")


class Slide(BaseModel):
    """İçeriği yazılmış tek bir slayt."""

    title: str = Field(description="Slayt başlığı")
    layout: SlideLayout = Field(description="Slaytın düzeni")
    bullets: list[str] = Field(description="'image' ve 'cards' düzeninde 3-5 kısa madde")
    columns: list[Column] = Field(description="Sadece 'comparison' düzeninde tam 2 sütun")
    highlight: str = Field(description="Sadece 'highlight' düzeninde: tek cümlelik ana mesaj")
    image_query: str = Field(description="Slayt fotoğrafı için İngilizce arama sorgusu")
    notes: str = Field(description="Konuşmacının söyleyeceği 3-5 cümlelik not")


class DeckContent(BaseModel):
    """2. LLM adımının çıktısı."""

    slides: list[Slide]
    takeaways: list[str] = Field(description="Dinleyicinin aklında kalması gereken 3 ana çıkarım")


class Presentation(BaseModel):
    """Tamamlanmış sunum: .pptx dosyasına dönüştürülmeye hazır."""

    title: str
    subtitle: str
    image_query: str
    slides: list[Slide]
    takeaways: list[str]

    def photo_queries(self) -> dict[str, str]:
        """Fotoğraf gereken yerler ve arama sorguları: {yer: sorgu}.

        Yerler: kapak ve resimli/vurgu düzenindeki slaytlar. Fotoğraflar sorguya göre
        değil yere göre eşlenir; böylece aynı sorgu iki yerde geçse de farklı fotoğraf gelir.
        """
        queries = {COVER_PHOTO: self.image_query}
        for index, slide in enumerate(self.slides):
            if slide.layout in ("image", "highlight"):
                queries[slide_photo_key(index)] = slide.image_query
        return queries


COVER_PHOTO = "cover"


def slide_photo_key(index: int) -> str:
    """index sıradaki içerik slaytının fotoğraf yeri: 'slide-0', 'slide-1', ..."""
    return f"slide-{index}"
