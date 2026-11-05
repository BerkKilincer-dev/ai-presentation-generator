# Demo Videosu Senaryosu (yaklaşık 4,5 dakika)

## Çekimden önce

- [ ] `streamlit run app.py` ile uygulamayı aç, tarayıcıyı tam ekran yap (F11).
- [ ] Bir sunumu önceden üretip `.pptx` dosyasını hazır tut (internet ya da API sorun çıkarırsa bunu gösterirsin).
- [ ] `.env` dosyasını kapat; ekranda API anahtarı görünmesin.
- [ ] Kayıt aracı: Windows'ta **Win + Alt + R** (Xbox Game Bar) ya da OBS Studio.
- [ ] Bekleme süresini (genellikle 10-15 sn) montajda hızlandırabilirsin; canlı anlatımda bu sürede mimariyi anlat.

## Akış

| Süre | Ekranda | Söylenecekler |
|---|---|---|
| 0:00 – 0:25 | Karşılama sayfası | "Bir sunum hazırlamak çoğu zaman saatler alıyor: konuyu planlamak, içeriği yazmak, görsel bulmak, tasarlamak. Konudan Sunum Oluşturucu bunu bir konudan başlayarak yaklaşık 10-15 saniyede yapıyor." |
| 0:25 – 0:55 | Konu kutusu, "Sunum ayarları" açılır | Konu yaz (ör. *Yapay zekânın sağlık sektörüne etkileri*). Hedef kitle, anlatım tonu ve slayt sayısını göster: "Aynı konu, lise öğrencilerine eğitici tonla ya da yöneticilere profesyonel tonla farklı anlatılıyor." |
| 0:55 – 1:40 | "Sunumumu Oluştur" → ilerleme adımları | "Arka planda iki ayrı yapay zekâ çağrısı var: önce sunumun akışı planlanıyor, ekranda başlıklar çıkıyor. Sonra her slaytın içeriği, düzeni ve konuşmacı notu yazılıyor. Model serbest metin değil, tanımladığımız yapıda JSON döndürüyor; bu yüzden çıktı her zaman PowerPoint'e dönüştürülebilir. Son adımda her slayta Pixabay'den farklı bir fotoğraf seçiliyor." |
| 1:40 – 2:30 | Sonuç sayfası, slayt önizlemesi | Slaytlarda gezin: kapak, gündem, fotoğraflı slayt, kartlar, karşılaştırma, vurgu, önemli çıkarımlar. "Düzeni slayta göre yapay zekâ seçiyor; kapak, gündem, özet ve kapanış otomatik ekleniyor." |
| 2:30 – 2:55 | Sağ panelde tema değiştir | Temaları sırayla değiştir: "Tema değişince sunum anında yeniden çiziliyor; yapay zekâya tekrar gidilmiyor, ek maliyet yok." |
| 2:55 – 3:15 | "Konuşmacı notları" sekmesi | "Her slayt için sunucunun söyleyeceği notlar da hazırlanıyor; maddeleri tekrar etmiyor, açıklama ve geçiş cümlesi ekliyor." |
| 3:15 – 3:40 | İndir → PowerPoint'te aç | Dosyayı aç, bir slaytın not bölümünü göster: "İndirilen dosya düzenlenebilir bir PowerPoint sunumu; notlar da içinde." |
| 3:40 – 4:15 | `evaluation/RAPOR.md` | "Sistemi 24 farklı konuda test ettik." Başarı oranını, ortalama süreyi ve sunum başına maliyeti söyle; model karşılaştırma tablosunu göster: "Modeli bu ölçümlere göre seçtik." |
| 4:15 – 4:35 | Kapanış (karşılama sayfası) | "Kod GitHub'da açık; kurulum adımları README'de. Teşekkürler." |

## Olası sorulara hazırlık

- **Model neden bu?** → `docs/PROMPT_VE_MODEL.md`, "Model seçimi" bölümü.
- **Yapay zekâ yanlış bilgi verirse?** → Prompt'ta "emin olmadığın sayı, tarih ve isimleri kullanma" kuralı var; sunum düzenlenebilir bir dosya olarak teslim ediliyor, son kontrol kullanıcıda.
- **Google'ın servisi yoğunsa?** → İstek otomatik olarak yedek modele gidiyor; değerlendirme raporunda "yedek modele düşülen örnek" sayısı var.
- **Maliyet?** → Ücretsiz katmanda 0; ücretli katmanda sunum başına maliyet raporda.
