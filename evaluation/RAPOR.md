# Değerlendirme Raporu

> Bu dosya `python -m evaluation.report` ile `evaluation/results/` altındaki sonuçlardan otomatik üretilir.

## Yöntem

- Her test örneği uçtan uca çalıştırıldı: plan → içerik → fotoğraflar → .pptx.
- **Başarı:** sunum üretildi, .pptx dosyası python-pptx ile sorunsuz açıldı ve istenen sayıda içerik slaytı var.
- **Kalite puanı:** başarılı sunumda geçilen otomatik kontrollerin oranı.
- **Gecikme:** dört adımın toplam süresi (kullanıcının beklediği süre).
- **Maliyet:** API'nin döndürdüğü token sayıları × ücretli katman fiyatları (düşünme token'ları dahil). Ücretsiz katmanda maliyet 0'dır.

## Özet

Model: `gemini-3.1-flash-lite` (yedek modeller açık, fotoğraflar açık) · Tarih: 2026-11-05T21:34:14

| Metrik | Değer |
|---|---|
| Test örneği | 24 |
| **Başarı oranı** | **%100.0** (24/24) |
| Ortalama kalite puanı | %99.2 |
| Ortalama gecikme | 15.8 sn |
| Medyan / p95 / en uzun gecikme | 10.9 / 45.0 / 56.7 sn |
| Ortalama token (girdi / çıktı) | 1,547 / 1,838 |
| **Sunum başına maliyet** | **$0.0031** |
| 1.000 sunumun maliyeti | $3.14 |
| Yedek modele düşülen örnek | 0 |
| Fotoğraf bulunma oranı | %100.0 (97/97) |

### Adım bazında ortalama süre

| Adım | Ortalama |
|---|---|
| 1. Plan (LLM) | 3.06 sn |
| 2. İçerik (LLM) | 10.05 sn |
| 3. Fotoğraflar (Pixabay) | 2.58 sn |
| 4. PPTX oluşturma | 0.14 sn |

## Kalite kontrolleri

Başarılı her sunum için prompt'taki kuralların uygulanıp uygulanmadığı otomatik kontrol edildi.

| Kontrol | Geçen |
|---|---|
| Slayt sayısı istenenle aynı | %100 (24/24) |
| Madde sayıları düzene uygun | %100 (24/24) |
| Maddelerin %90'ı en fazla 16 kelime | %100 (24/24) |
| Kart maddeleri en fazla 12 kelime | %92 (22/24) |
| Slayt başlıkları en fazla 9 kelime | %100 (24/24) |
| Seçilen düzenler uygulanabilir | %100 (24/24) |
| En fazla 1 vurgu slaytı | %100 (24/24) |
| Art arda aynı düzen yok | %100 (24/24) |
| Notlar en az 2 cümle ve 25 kelime | %100 (24/24) |
| Tam 3 önemli çıkarım | %100 (24/24) |
| İçerik Türkçe | %100 (24/24) |

## Test örnekleri

| # | Konu | Hedef kitle | Ton | Slayt | Sonuç | Kalite | Süre | Maliyet |
|---|---|---|---|---|---|---|---|---|
| 1 | Yapay zekânın eğitimdeki rolü | Öğretmenler | Eğitici | 6 | ✅ | %100 | 10.8 sn | $0.0032 |
| 2 | Yenilenebilir enerji kaynakları | Genel izleyici | Profesyonel | 6 | ✅ | %100 | 10.2 sn | $0.0034 |
| 3 | İklim değişikliğinin tarıma etkileri | Ziraat fakültesi öğrencileri | Akademik | 7 | ✅ | %100 | 11.9 sn | $0.0040 |
| 4 | Siber güvenliğe giriş | Lise öğrencileri | Eğitici | 5 | ✅ | %100 | 45.0 sn | $0.0028 |
| 5 | Uzaktan çalışmanın verimliliğe etkisi | Şirket yöneticileri | Profesyonel | 6 | ✅ | %100 | 13.8 sn | $0.0032 |
| 6 | Osmanlı Devleti'nin kuruluş dönemi | Lise öğrencileri | Eğitici | 6 | ✅ | %100 | 13.4 sn | $0.0032 |
| 7 | Kuantum bilgisayarlar | Yazılımcılar | Akademik | 6 | ✅ | %100 | 35.6 sn | $0.0036 |
| 8 | Sağlıklı beslenme alışkanlıkları | Ortaokul öğrencileri | Eğitici | 4 | ✅ | %100 | 14.1 sn | $0.0023 |
| 9 | Elektrikli toplu taşımaya geçiş | Belediye meclisi | İkna edici | 6 | ✅ | %100 | 9.6 sn | $0.0034 |
| 10 | Sosyal medyanın gençlerin ruh sağlığına etkisi | Ebeveynler | Profesyonel | 6 | ✅ | %100 | 9.2 sn | $0.0033 |
| 11 | Girişimler için yatırım turları | Girişimciler | Profesyonel | 7 | ✅ | %100 | 56.7 sn | $0.0035 |
| 12 | Geri dönüşümü alışkanlık haline getirmek | Mahalle sakinleri | İkna edici | 5 | ✅ | %100 | 10.2 sn | $0.0028 |
| 13 | Blokzincir teknolojisi | Bankacılar | Profesyonel | 6 | ✅ | %100 | 15.2 sn | $0.0034 |
| 14 | Mars'a insanlı yolculuk | Genel izleyici | Eğitici | 6 | ✅ | %91 | 9.2 sn | $0.0033 |
| 15 | Türk mutfağının bölgesel çeşitliliği | Yabancı turistler | İkna edici | 5 | ✅ | %100 | 10.2 sn | $0.0030 |
| 16 | Agile ve Scrum ile proje yönetimi | Yazılım ekipleri | Profesyonel | 6 | ✅ | %100 | 9.1 sn | $0.0031 |
| 17 | Depreme hazırlık | Aileler | Eğitici | 5 | ✅ | %100 | 17.6 sn | $0.0028 |
| 18 | Veri bilimi kariyer yolu | Üniversite öğrencileri | Eğitici | 6 | ✅ | %100 | 11.0 sn | $0.0031 |
| 19 | Gönüllülük ve sivil toplum | Üniversite öğrencileri | İkna edici | 5 | ✅ | %100 | 9.1 sn | $0.0028 |
| 20 | E-ticarette müşteri deneyimi | KOBİ sahipleri | Profesyonel | 6 | ✅ | %100 | 17.2 sn | $0.0034 |
| 21 | Fotosentez | İlkokul öğrencileri | Eğitici | 4 | ✅ | %100 | 8.1 sn | $0.0021 |
| 22 | Kahve | Genel izleyici | Profesyonel | 3 | ✅ | %91 | 6.6 sn | $0.0021 |
| 23 | Yapay zekâ etiği: önyargı, şeffaflık ve hesap verebilirlik | Akademisyenler | Akademik | 10 | ✅ | %100 | 18.6 sn | $0.0051 |
| 24 | Machine learning basics | Genel izleyici | Eğitici | 5 | ✅ | %100 | 7.6 sn | $0.0026 |

## Prompt iyileştirmesi: önce ve sonra

İlk ana değerlendirmede kart maddelerinin sık sık 10 kelime sınırını aştığı ve kartlardan taştığı görüldü. Prompt'taki kart kuralı netleştirildi ve aynı 24 örnek yeniden çalıştırıldı.

| Metrik | Önce (v1) | Sonra (v2) |
|---|---|---|
| Başarı oranı | %100 | %100 |
| Ortalama kalite puanı | %97.0 | %99.2 |
| Ortalama gecikme | 11.1 sn | 15.8 sn |
| Medyan gecikme | 9.9 sn | 10.9 sn |
| Sunum başına maliyet | $0.0032 | $0.0031 |
| Kart maddeleri en fazla 12 kelime | %67 | %92 |

## Model karşılaştırması

Aynı test örnekleri her model için yedek modeller ve fotoğraflar kapalı olarak çalıştırıldı.
Başarısız istekler API hata koduyla gösterilir (429: kota/hız sınırı, 503: model aşırı yoğun).

| Model | Başarı | Kalite | Ort. gecikme | p95 | Sunum başına | 1.000 sunum | API hataları |
|---|---|---|---|---|---|---|---|
| `gemini-2.5-flash` | %0 (0/6) | — | — | — | — | — | 429 ×6 |
| `gemini-3.1-flash-lite` | %100 (6/6) | %95.5 | 10.4 sn | 22.9 sn | $0.0033 | $3.29 | — |
| `gemini-3.5-flash-lite` | %17 (1/6) | %100.0 | 14.8 sn | 14.8 sn | $0.0056 | $5.59 | 503 ×5 |
| `gemini-3.8-flash` | %0 (0/6) | — | — | — | — | — | 429 ×6 |

## Gözlemler

### Sonuçların yorumu

- **Başarı oranı %100:** 24 test örneğinin hepsinde sunum üretildi, `.pptx` dosyası sorunsuz
  açıldı ve istenen slayt sayısı tuttu. Yapılandırılmış çıktı (Pydantic şeması) sayesinde
  ayrıştırma hatası hiç görülmedi; sınır durumları (tek kelimelik konu, 10 slayt, İngilizce
  konu) da sorunsuz geçti. İngilizce konu verildiğinde içerik yine Türkçe üretildi.
- **Gecikme:** Medyan süre ~11 sn. İkinci turda 3 örnekte içerik adımı 30-50 sn sürdü; bu
  örneklerde token sayıları diğerleriyle aynı olduğu için sebep prompt değil, Gemini API
  tarafındaki anlık yavaşlık ve otomatik yeniden denemeler. Bu yüzden ortalama yerine
  medyan, kullanıcı deneyimini daha iyi temsil ediyor; p95 ise en kötü durumu gösteriyor.
- **Maliyet:** Sunum başına ~$0,003 (yaklaşık 1.500 girdi + 1.850 çıktı token). 1.000 sunum
  ~3 dolar tutuyor. Uygulama ücretsiz katmanda çalıştığı için gerçek maliyet 0.
- **Fotoğraflar:** İkinci turda 97 fotoğraf yerinin hepsine farklı bir fotoğraf bulundu.

### Değerlendirmenin bulduğu sorun ve düzeltmesi

İlk turda (v1) otomatik kontroller %100 geçiyordu; ancak çıktılar elle incelendiğinde kart
maddelerinin sık sık 10 kelime sınırını aştığı ve bazı kartlarda metnin taştığı görüldü.
Kontroller bunu yakalayamıyordu çünkü kelime sınırını tüm maddeler için tek bir eşikle ölçüyordu.

1. Kartlara özel yeni bir kontrol eklendi ("Kart maddeleri en fazla 12 kelime"); v1'de 24
   sunumun 8'i bu kontrolden kaldı.
2. Prompt'taki kart kuralı netleştirildi ("EN FAZLA 10 kelime; kartlar dar, uzun cümle sığmaz").
3. Kod tarafına güvenlik ağı eklendi: kart maddeleri uzunsa punto otomatik küçülüyor.
4. Aynı 24 örnek yeniden çalıştırıldı (v2): kontrolden kalan sunum sayısı 8'den 2'ye düştü.

### Otomatik kontrollerin sınırları: elle inceleme

Otomatik kontroller **biçimi** (kurallara uyum) ölçer; **bilginin doğruluğunu** ölçmez. Bu
yüzden farklı alanlardan sunumlar (tarih, kuantum fiziği, kahve, makine öğrenmesi) elle okundu:

- **Genel olarak doğru ve dolu içerik.** Örneğin Osmanlı sunumundaki Söğüt, istimalet
  politikası, Ahilik, Yaya-Müsellem birlikleri ve Çimpe Kalesi bilgileri doğru.
- **Teknik konularda basitleştirme hataları.** Kuantum sunumunda "hata düzeltme kodları
  dekoheransı durdurur" (doğrusu: hataları düzeltir) ve dolanıklığın "hesaplama hızını katlanarak
  artırdığı" gibi popüler ama yanıltıcı ifadeler görüldü. Uzmanlık gerektiren konularda
  sunumun kullanıcı tarafından gözden geçirilmesi gerekiyor.
- **Sayılar az ama var.** "Emin olmadığın sayıları kullanma" kuralına rağmen 137 içerik
  slaytının 6'sında sayı ya da yüzde geçiyor (ör. kahve pazarının büyüklüğü). İncelenen
  sayılar yaygın kaynaklarla uyumluydu, ama doğrulanmadan kullanılmamalı.
- **Ton konuyu yönlendirebiliyor.** Tek kelimelik "Kahve" konusu "Profesyonel" tonla
  istendiğinde sunum, kahvenin iş dünyasındaki rolüne kaydı.

Bu nedenle sunum düzenlenebilir bir PowerPoint dosyası olarak teslim ediliyor; son kontrol
kullanıcıda.

### Sınırlamalar

- Her test örneği bir kez çalıştırıldı; `temperature=0.7` olduğu için aynı konuda farklı
  sonuçlar çıkabilir.
- Model karşılaştırması, ücretsiz katmanın kota ve yoğunluk sınırları içinde yapıldı; bazı
  modeller test sırasında yanıt vermediği için ölçülemedi (bkz. `docs/PROMPT_VE_MODEL.md`).
- Maliyet, API'nin bildirdiği token sayıları ve Kasım 2026 fiyatlarıyla hesaplandı.
- İçerik doğruluğu otomatik ölçülmedi; elle inceleme örneklem üzerinde yapıldı.

### Geliştirme fikirleri

- Doğruluk için ikinci bir LLM çağrısıyla içerikteki iddiaları denetleyen bir "editör" adımı.
- Kullanıcının tek bir slaytı yeniden ürettirebilmesi.
- Değerlendirmeye insan puanlaması (ör. 1-5 arası içerik kalitesi) eklenmesi.
