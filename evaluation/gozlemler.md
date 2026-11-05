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
