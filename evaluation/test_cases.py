"""Değerlendirmede kullanılan 24 test örneği.

Konular farklı alanlardan (teknoloji, bilim, tarih, sağlık, iş dünyası, toplum)
seçildi; hedef kitle, ton ve slayt sayısı da çeşitlendirildi. Son satırlardaki
örnekler sınır durumlarını sınar: çok kısa konu, en fazla slayt, İngilizce konu.
"""

from presentation_generator.models import PresentationRequest


def _case(topic: str, audience: str, tone: str, slide_count: int) -> PresentationRequest:
    return PresentationRequest(topic=topic, audience=audience, tone=tone, slide_count=slide_count)


TEST_CASES = [
    _case("Yapay zekânın eğitimdeki rolü", "Öğretmenler", "Eğitici", 6),
    _case("Yenilenebilir enerji kaynakları", "Genel izleyici", "Profesyonel", 6),
    _case("İklim değişikliğinin tarıma etkileri", "Ziraat fakültesi öğrencileri", "Akademik", 7),
    _case("Siber güvenliğe giriş", "Lise öğrencileri", "Eğitici", 5),
    _case("Uzaktan çalışmanın verimliliğe etkisi", "Şirket yöneticileri", "Profesyonel", 6),
    _case("Osmanlı Devleti'nin kuruluş dönemi", "Lise öğrencileri", "Eğitici", 6),
    _case("Kuantum bilgisayarlar", "Yazılımcılar", "Akademik", 6),
    _case("Sağlıklı beslenme alışkanlıkları", "Ortaokul öğrencileri", "Eğitici", 4),
    _case("Elektrikli toplu taşımaya geçiş", "Belediye meclisi", "İkna edici", 6),
    _case("Sosyal medyanın gençlerin ruh sağlığına etkisi", "Ebeveynler", "Profesyonel", 6),
    _case("Girişimler için yatırım turları", "Girişimciler", "Profesyonel", 7),
    _case("Geri dönüşümü alışkanlık haline getirmek", "Mahalle sakinleri", "İkna edici", 5),
    _case("Blokzincir teknolojisi", "Bankacılar", "Profesyonel", 6),
    _case("Mars'a insanlı yolculuk", "Genel izleyici", "Eğitici", 6),
    _case("Türk mutfağının bölgesel çeşitliliği", "Yabancı turistler", "İkna edici", 5),
    _case("Agile ve Scrum ile proje yönetimi", "Yazılım ekipleri", "Profesyonel", 6),
    _case("Depreme hazırlık", "Aileler", "Eğitici", 5),
    _case("Veri bilimi kariyer yolu", "Üniversite öğrencileri", "Eğitici", 6),
    _case("Gönüllülük ve sivil toplum", "Üniversite öğrencileri", "İkna edici", 5),
    _case("E-ticarette müşteri deneyimi", "KOBİ sahipleri", "Profesyonel", 6),
    _case("Fotosentez", "İlkokul öğrencileri", "Eğitici", 4),
    # Sınır durumları
    _case("Kahve", "Genel izleyici", "Profesyonel", 3),  # tek kelimelik konu, en az slayt
    _case("Yapay zekâ etiği: önyargı, şeffaflık ve hesap verebilirlik",
          "Akademisyenler", "Akademik", 10),  # uzun konu, en fazla slayt
    _case("Machine learning basics", "Genel izleyici", "Eğitici", 5),  # İngilizce konu
]
