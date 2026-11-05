# 📊 Konudan Sunum Oluşturucu

Bir konu yazarsınız; yapay zekâ (Google Gemini) slayt planını ve içeriğini hazırlar,
uygulama da bunu fotoğraflı, temalı ve indirilebilir bir PowerPoint (`.pptx`) dosyasına dönüştürür.

**Kullanılan teknolojiler:** Python · Google Gemini (`gemini-3.1-flash-lite`) · python-pptx · Pydantic · Pixabay API · Streamlit

## Teslim edilenler

| İstenen | Nerede |
|---|---|
| Kurulum adımları | Bu dosya: [Kurulum](#kurulum) ve [Kullanım](#kullanım) |
| Çalışan demo | Web arayüzü (`streamlit run app.py`) ve komut satırı (`python main.py ...`) |
| Prompt tasarımı ve model seçimi gerekçeleri | [docs/PROMPT_VE_MODEL.md](docs/PROMPT_VE_MODEL.md) |
| Değerlendirme raporu (24 test, başarı oranı, maliyet, gecikme) | [evaluation/RAPOR.md](evaluation/RAPOR.md) |
| Demo videosu senaryosu | [docs/DEMO_SENARYOSU.md](docs/DEMO_SENARYOSU.md) |
| Kısa sunum | [docs/Proje_Sunumu.pptx](docs/Proje_Sunumu.pptx) (projenin kendi koduyla üretildi) |

### Değerlendirme özeti

24 farklı konuda (farklı alan, hedef kitle, ton ve slayt sayısı; sınır durumları dahil) uçtan uca test:

| Başarı oranı | Kalite puanı | Medyan gecikme | Sunum başına maliyet |
|---|---|---|---|
| **%100** (24/24) | **%99,6** | **12,2 sn** | **$0,0031** |

Ayrıntılar, model karşılaştırması ve elle inceleme bulguları [raporda](evaluation/RAPOR.md).

## Nasıl Çalışır?

```
 Konu ──► 1. Plan (LLM) ──► 2. İçerik (LLM) ──► 3. Fotoğraflar (Pixabay) ──► 4. PPTX (python-pptx)
          başlıklar, akış    maddeler, notlar,    her fotoğraf yeri için     seçilen temayla
                             düzen, foto sorgusu  farklı bir fotoğraf        slaytlar çizilir
```

1. **Plan:** LLM; konu, hedef kitle ve anlatım tonuna göre sunumun başlığını ve slaytların sırasını çıkarır.
2. **İçerik:** LLM her slayt için maddeleri ve konuşmacı notunu yazar, bir **düzen** seçer,
   fotoğraf için İngilizce bir **arama sorgusu** ve sunumun **önemli çıkarımlarını** üretir.
3. **Fotoğraflar:** Sorgular Pixabay'de aynı anda (paralel) aranır. Her sorgu için 30 aday içinden
   etiketleri sorguyla en çok örtüşen fotoğraf seçilir; uygun aday yoksa sunumun genel konusuna
   uyan bir fotoğraf kullanılır. Aynı fotoğraf iki slayta konmaz.
4. **PPTX:** Slaytlar seçilen temayla çizilir; konuşmacı notları PowerPoint'in not bölümüne eklenir.

Bir sunum için sadece **2 LLM çağrısı** yapılır. Tema LLM'i etkilemediği için
sunum üretildikten sonra tema, API'ye tekrar gitmeden anında değiştirilebilir.

LLM'den serbest metin değil, **yapılandırılmış JSON** istenir. Yanıtın yapısı
Pydantic modelleriyle tanımlanır ve doğrulanır.

### Sunumun sayfaları

Kapak → Gündem → içerik slaytları → Önemli Çıkarımlar → Teşekkürler

Kapak, gündem, özet ve kapanış otomatik eklenir. İçerik slaytlarının düzenini LLM seçer:

| Düzen | Görünüm | Ne zaman? |
|---|---|---|
| `image` | Maddeler solda, fotoğraf sağda | Çoğu slayt |
| `cards` | Her madde numaralı bir kartta, yan yana | 3-4 eşit önemde kavram |
| `comparison` | İki renkli sütun | Avantaj/dezavantaj, önce/sonra |
| `highlight` | Karartılmış fotoğraf üzerinde tek büyük mesaj | Çarpıcı sonuç, en fazla 1 kez |

Seçilen düzen uygulanamazsa (ör. fotoğraf bulunamadı) slayt düz madde listesi olarak çizilir.
Sayfa sırası ve düzen kararı tek bir yerde (`pages.py`) verilir; hem `.pptx` hem
arayüzdeki önizleme bu kararı kullanır, bu yüzden ikisi her zaman aynı görünür.

### Temalar ve anlatım tonları

- **Temalar:** Lacivert · Orman · Mercan · Gece. Yeni tema eklemek için `themes.py` içine bir giriş eklemek yeterli.
- **Tonlar:** Profesyonel · Eğitici · Akademik · İkna edici.

### Dayanıklılık

- Gemini modeli yoğunsa ya da kotası dolmuşsa istek otomatik olarak yedek modellere gider
  (`gemini-3.1-flash-lite` → `gemini-3.5-flash-lite` → `gemini-2.5-flash`).
- Fotoğraf bulunamazsa o slayt resimsiz çizilir; sunumun tamamı asla başarısız olmaz.
- Kullanıcıya teknik hata yerine anlaşılır bir mesaj gösterilir.

## Proje Yapısı

```
├── app.py                      # Streamlit web arayüzü (karşılama + sonuç sayfası)
├── main.py                     # Komut satırı arayüzü
├── presentation_generator/     # Uygulamanın çekirdeği (arayüzden bağımsız)
│   ├── config.py               # .env'den API anahtarları ve model ayarları
│   ├── models.py               # Veri modelleri (istek, plan, slayt, sunum)
│   ├── prompts.py              # LLM'e gönderilen talimatlar
│   ├── llm.py                  # Gemini API istemcisi (yedek model desteğiyle)
│   ├── generator.py            # Plan + içerik adımları
│   ├── images.py               # Pixabay'den fotoğraf arama
│   ├── pages.py                # Sayfa sırası ve düzen kararı
│   ├── themes.py               # Renk temaları
│   └── pptx_builder.py         # Sunumu .pptx dosyasına çizer
├── ui/                         # Streamlit arayüzünün görsel parçaları
│   ├── components.py           # Karşılama alanı, özellik kartları, alt bilgi
│   ├── preview.py              # Slaytların canlı HTML önizlemesi
│   └── style.css               # Arayüz ve önizleme stilleri
├── evaluation/                 # Değerlendirme
│   ├── test_cases.py           # 24 test örneği
│   ├── checks.py               # Otomatik kalite kontrolleri
│   ├── pricing.py              # Gemini fiyatları (maliyet hesabı)
│   ├── run.py                  # Testleri çalıştırır, results/ altına yazar
│   ├── report.py               # Sonuçlardan RAPOR.md üretir
│   ├── export_decks.py         # Test sunumlarını .pptx olarak kaydeder
│   ├── gozlemler.md            # Rapora eklenen elle yazılmış yorumlar
│   ├── results/                # Ham sonuçlar (üretilen sunumlar dahil, JSON)
│   └── RAPOR.md                # Değerlendirme raporu
└── docs/
    ├── PROMPT_VE_MODEL.md      # Prompt tasarımı ve model seçimi gerekçeleri
    ├── DEMO_SENARYOSU.md       # Demo videosu senaryosu
    ├── proje_sunumu.py         # Proje sunumunu projenin kendi koduyla üretir
    └── Proje_Sunumu.pptx       # Kısa sunum
```

Çekirdek paket arayüzü hiç bilmez; aynı kodu hem web arayüzü (`app.py`) hem
komut satırı (`main.py`) kullanır.

## Kurulum

```bash
pip install -r requirements.txt
```

`.env.example` dosyasını `.env` olarak kopyalayın ve anahtarları yazın:

```
GEMINI_API_KEY=...   # zorunlu: https://aistudio.google.com/apikey
PIXABAY_API_KEY=...  # isteğe bağlı (fotoğraflar için): https://pixabay.com/api/docs/
```

## Kullanım

**Web arayüzü:**

```bash
streamlit run app.py
```

**Komut satırı:**

```bash
python main.py "Yapay Zekanın Eğitimdeki Rolü" --slides 6 --tone Eğitici --theme Orman
```

Dosya `outputs/` klasörüne kaydedilir.

## Değerlendirme

Proje klasöründen:

```bash
python -m evaluation.run --pause 10 --name main      # 24 test örneğini çalıştırır (~10 dk)
python -m evaluation.report                          # evaluation/RAPOR.md dosyasını üretir
python -m evaluation.export_decks                    # test sunumlarını outputs/degerlendirme/ altına kaydeder
```

Bir modeli tek başına ölçmek için (yedek modeller ve fotoğraflar kapalı):

```bash
python -m evaluation.run --model gemini-3.1-flash-lite --limit 6 --no-fallback --no-images --pause 20 --name cmp-gemini-3.1-flash-lite
```

`--pause`, ücretsiz katmanın dakikalık istek sınırına takılmamak için örnekler arasında bekler.

Proje sunumunu yeniden üretmek için: `python -m docs.proje_sunumu`

Fotoğraflar [Pixabay](https://pixabay.com) tarafından sağlanmaktadır.
