"""LLM'e gönderilen talimatlar (prompt'lar).

Prompt'ları koddan ayrı tutmak, davranışı değiştirmek istediğimizde
sadece bu dosyaya bakmamızı sağlar.
"""

from .models import PresentationPlan, PresentationRequest

TONE_GUIDES = {
    "Profesyonel": "Net, özlü ve iş dünyasına uygun bir dil kullan.",
    "Eğitici": "Sade bir dille anlat, kavramları günlük hayattan örneklerle açıkla.",
    "Akademik": "Kavramları doğru terimlerle, derinlemesine ve tarafsız bir dille ele al.",
    "İkna edici": "Faydaları ve nedenleri öne çıkar, dinleyiciyi harekete geçirecek bir dil kullan.",
}

SYSTEM_INSTRUCTION = """\
Sen ödüllü bir sunum tasarımcısı ve içerik yazarısın. Dinleyiciyi sıkmayan,
bilgi dolu ve akılda kalıcı sunumlar hazırlarsın.

Kurallar:
- Tüm metinleri Türkçe yaz (sadece image_query alanları İngilizce).
- Genel geçer, boş cümleler kurma; her madde somut bir bilgi, örnek, neden veya sonuç içersin.
- Bilgi uydurma; emin olmadığın sayı, tarih ve isimleri kullanma.
- image_query: stok fotoğraf sitesinde aranacak, 2-4 kelimelik, somut ve
  fotoğraflanabilir bir sorgu (örn. "wind turbines field", "students classroom").
  Fotoğrafta görülebilecek nesne veya sahneyi yaz; "concept", "benefits", "future"
  gibi soyut kelimeler kullanma.
"""


def _request_summary(request: PresentationRequest) -> str:
    return (
        f"Konu: {request.topic}\n"
        f"Hedef kitle: {request.audience}\n"
        f"Anlatım tonu: {request.tone}. {TONE_GUIDES[request.tone]}"
    )


def build_plan_prompt(request: PresentationRequest) -> str:
    """1. adım: konudan slayt planı çıkarma talimatı."""
    return f"""\
Aşağıdaki konu için bir sunum planı hazırla.

{_request_summary(request)}

İstenenler:
- Dikkat çekici, en fazla 7 kelimelik bir sunum başlığı ve tek cümlelik bir alt başlık.
- Kapak fotoğrafı için image_query.
- Tam olarak {request.slide_count} slayt. Her slaytın başlığı en fazla 7 kelime olsun ve
  konuyu ilerleten ayrı bir fikri anlatsın; aynı şeyi iki slaytta tekrar etme.
- Akış: konuya giriş ve neden önemli olduğu, ana konular, sonuç veya gelecek.
- Kapak, gündem, özet ve kapanış slaytlarını ekleme; onlar otomatik eklenecek.
"""


def build_content_prompt(request: PresentationRequest, plan: PresentationPlan) -> str:
    """2. adım: plandaki her slaytın düzenini seçme ve içeriğini yazma talimatı."""
    return f"""\
Aşağıdaki sunum planındaki her slayt için içerik yaz.

{_request_summary(request)}

Plan:
{plan.model_dump_json(indent=2)}

Her slayt için:
- title: plandaki başlığı kullan.
- layout: slaytın düzenini seç.
    "image"      -> maddeler ve konuyla ilgili bir fotoğraf. En sık kullanılacak düzen.
    "cards"      -> 3-4 eşit önemde kavram, tür, adım veya örnek varsa.
    "comparison" -> iki tarafı karşılaştırırken (avantaj/dezavantaj, önce/sonra, A/B).
    "highlight"  -> tek bir çarpıcı ana mesaj. Sunumda en fazla 1 kez.
  Çeşitlilik sağla: art arda iki slaytta aynı düzeni kullanma, ilk slayt "image" olsun.
- bullets: "image" düzeninde 3-5 madde, her biri 8-14 kelime; "cards" düzeninde 3-4 madde,
  her biri EN FAZLA 10 kelime (kartlar dar, uzun cümle sığmaz; kısa ve vurucu yaz);
  diğer düzenlerde boş liste. Her madde bir iddia ve onu destekleyen somut bir ayrıntı içersin.
  Kötü: "Tanı süreçlerini hızlandırır."
  İyi: "Görüntü analizi, radyologların tümörleri daha erken fark etmesine yardım eder."
- columns: sadece "comparison" düzeninde tam 2 sütun (başlık ve 3-4 madde, her biri
  5-10 kelime), diğer düzenlerde boş liste.
- highlight: sadece "highlight" düzeninde en fazla 15 kelimelik tek cümle, diğerlerinde boş.
- image_query: slayta uygun fotoğraf sorgusu.
- notes: sunucunun doğal bir konuşma diliyle söyleyeceği 3-5 cümle. Slayttaki maddeleri
  aynen tekrar etme; açıklama, örnek veya bağlam ekle ve sonraki slayta geçişi hazırla.

Ayrıca:
- takeaways: dinleyicinin aklında kalması gereken 3 ana çıkarım, her biri en fazla 12 kelime.

Slaytların sırasını ve sayısını değiştirme.
"""
