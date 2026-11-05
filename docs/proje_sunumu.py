"""Projenin kendi tanıtım sunumunu, projenin kendi koduyla üretir.

İçerik burada elle yazılıdır; çizim build_pptx ile yapılır. Değerlendirme
sayıları evaluation/results/ altındaki sonuçlardan okunur, yani rapor
güncellenince sunum da güncel kalır.

Kullanım (proje klasöründen):
    python -m docs.proje_sunumu
"""

from pathlib import Path

from evaluation.report import MAIN_RUN, load_runs, summarize
from presentation_generator.config import DEFAULT_MODEL, load_settings
from presentation_generator.images import PixabayClient
from presentation_generator.models import Column, Presentation, Slide
from presentation_generator.pptx_builder import build_pptx

OUTPUT_PATH = Path(__file__).with_name("Proje_Sunumu.pptx")


def slide(title: str, layout: str, bullets: list[str], notes: str, *, image_query: str = "",
          highlight: str = "", columns: list[Column] | None = None) -> Slide:
    return Slide(title=title, layout=layout, bullets=bullets, columns=columns or [],
                 highlight=highlight, image_query=image_query, notes=notes)


def _alternative_summary(model: str, stats: dict) -> str:
    """Karşılaştırmadaki bir alternatif modelin tek satırlık özeti."""
    if not stats["succeeded"]:
        return f"{model}: test sırasında yanıt vermedi"
    return (f"{model}: {stats['succeeded']}/{stats['count']} başarı, "
            f"{stats['avg_seconds']:.0f} sn")


def build_presentation() -> Presentation:
    runs = load_runs()
    main = summarize(runs[MAIN_RUN])
    comparison = {run["model"]: summarize(run) for name, run in runs.items() if name.startswith("cmp-")}
    chosen = comparison.get(DEFAULT_MODEL, main)
    alternatives = {model: s for model, s in comparison.items() if model != DEFAULT_MODEL}

    return Presentation(
        title="Konudan Sunum Oluşturucu",
        subtitle="Bir konudan, yapay zekâ ile saniyeler içinde düzenlenebilir PowerPoint sunumu",
        image_query="presentation business meeting",
        slides=[
            slide("Sunum Hazırlamak Neden Zor?", "image", [
                "Konuyu araştırmak, akışı planlamak ve içeriği yazmak saatler sürüyor.",
                "Her slayta uygun görsel bulmak ayrı bir iş yükü oluşturuyor.",
                "Tutarlı bir tasarım için tasarım bilgisi ve zaman gerekiyor.",
                "Konuşmacı notları çoğu zaman hiç hazırlanmıyor.",
            ], "Projenin çıkış noktası: sunum hazırlamanın en çok zaman alan kısımları planlama, "
               "içerik yazma ve görsel bulma. Bu adımları otomatikleştirmek istedik. "
               "Şimdi çözümümüzün nasıl çalıştığına bakalım.",
                  image_query="person laptop working late"),
            slide("Dört Adımlı Üretim Hattı", "cards", [
                "Plan: Gemini konunun akışını çıkarır",
                "İçerik: maddeler, notlar ve düzen yazılır",
                "Fotoğraflar: Pixabay'den paralel aranır",
                "PowerPoint: python-pptx ile çizilir",
            ], "Kullanıcı sadece konuyu, hedef kitleyi, tonu ve slayt sayısını giriyor. "
               "İlk iki adım yapay zekâ çağrısı, üçüncüsü fotoğraf servisi, dördüncüsü tamamen "
               "bizim kodumuz. Sunum başına sadece iki LLM çağrısı yapılıyor."),
            slide("Prompt Tasarımı", "image", [
                "İki aşama: önce akışın tamamı, sonra her slaytın içeriği planlanır.",
                "Model serbest metin değil, Pydantic şemasına uyan JSON döndürür.",
                "Kurallar somut: madde uzunluğu, düzen seçimi, çeşitlilik, not yapısı.",
                "Kötü ve iyi madde örneği, genel geçer cümleleri belirgin şekilde azalttı.",
            ], "Yapılandırılmış çıktı sayesinde yanıtı ayrıştırırken hiç hata almıyoruz; şemaya "
               "uymayan yanıt doğrudan reddediliyor. Prompt'u test ettikçe geliştirdik: örneğin "
               "maddeler çok genel çıkınca kötü-iyi örnek ekledik, alakasız fotoğraflar gelince "
               "soyut arama kelimelerini yasakladık.",
                  image_query="writing notebook desk"),
            slide("Model Seçimi", "comparison", [
                f"Seçilen model: {DEFAULT_MODEL}",
                "Alternatifler aynı test setinde karşılaştırıldı",
                "Yedek modeller yoğunlukta devreye giriyor",
            ], "Dört aday modeli aynı test örnekleriyle, yedek modeller kapalıyken ölçtük. "
               "Seçimde başarı oranı, kalite puanı, gecikme ve maliyeti birlikte değerlendirdik. "
               "Ayrıntılar değerlendirme raporunda ve prompt-model belgesinde.",
                  columns=[
                      Column(title=f"Seçilen: {DEFAULT_MODEL}", bullets=[
                          f"Başarı: %{chosen['success_rate'] * 100:.0f}",
                          f"Kalite: %{chosen['quality'] * 100:.0f}",
                          f"Ortalama süre: {chosen['avg_seconds']:.0f} sn",
                          f"Sunum başına: ${chosen['avg_cost']:.4f}",
                      ]),
                      Column(title="Alternatifler", bullets=[
                          _alternative_summary(model, s) for model, s in alternatives.items()
                      ]),
                  ]),
            slide("Değerlendirme: 24 Test Örneği", "cards", [
                f"%{main['success_rate'] * 100:.0f} başarı oranı",
                f"%{main['quality'] * 100:.0f} ortalama kalite puanı",
                f"{main['median_seconds']:.0f} sn medyan süre",
                f"${main['avg_cost']:.3f} sunum başına maliyet",
            ], "Farklı alanlardan, farklı hedef kitle ve tonlarla 24 konu denedik; çok kısa konu, "
               "en fazla slayt ve İngilizce konu gibi sınır durumlarını da ekledik. Kalite puanı, "
               "prompt'taki kuralların uygulanıp uygulanmadığını otomatik kontrol eden 11 testten "
               "geliyor. Maliyet ücretli katman fiyatlarıyla hesaplandı; ücretsiz katmanda sıfır."),
            slide("Mimari ve Dayanıklılık", "image", [
                "Çekirdek paket arayüzden bağımsız; web ve komut satırı aynı kodu kullanır.",
                "Sayfa düzeni kararı tek yerde verilir; önizleme ve dosya hep aynıdır.",
                "Model yoğunsa istek otomatik olarak yedek modele yönlendirilir.",
                "Fotoğraf bulunamazsa slayt resimsiz çizilir, sunum asla yarım kalmaz.",
            ], "Kodu her dosya tek bir iş yapacak şekilde ayırdık. Arayüzdeki önizleme ile indirilen "
               "dosya aynı sayfa planını kullandığı için birbirinden farklı görünemiyor. Hata "
               "durumlarında kullanıcıya teknik mesaj yerine anlaşılır bir uyarı gösteriliyor.",
                  image_query="server room cables"),
            slide("Bu Sunum Nasıl Hazırlandı?", "highlight", [
                "Sunum projenin kendi koduyla çizildi.",
                "Sayılar değerlendirme sonuçlarından okundu.",
                "Fotoğraflar Pixabay'den seçildi.",
            ], "Son olarak: izlediğiniz sunumun kendisi de projenin kendi kodu ile, aynı tema ve "
               "düzenlerle üretildi. İçeriği biz yazdık, çizimi ve fotoğrafları sistem yaptı.",
                  highlight="İzlediğiniz bu sunum da projenin kendi koduyla üretildi.",
                  image_query="colorful abstract light"),
        ],
        takeaways=[
            "Bir konudan yaklaşık 10-15 saniyede düzenlenebilir bir PowerPoint sunumu.",
            "Yapılandırılmış çıktı ve somut prompt kuralları güvenilir sonuç veriyor.",
            "Model seçimi 24 testlik ölçümle başarı, kalite, süre ve maliyete göre yapıldı.",
        ],
    )


def main() -> None:
    presentation = build_presentation()
    settings = load_settings()
    images = {}
    if settings.pixabay_api_key:
        images = PixabayClient(settings.pixabay_api_key).find_all(presentation.photo_queries())
    OUTPUT_PATH.write_bytes(build_pptx(presentation, images=images))
    print(f"Sunum yazıldı: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
