# Prompt Tasarımı ve Model Seçimi

Bu belge, LLM'e verilen talimatların neden bu şekilde yazıldığını ve hangi modelin
neden seçildiğini anlatır. Prompt'ların kendisi [`presentation_generator/prompts.py`](../presentation_generator/prompts.py),
yanıt şemaları [`presentation_generator/models.py`](../presentation_generator/models.py) dosyasındadır.

## 1. Genel yaklaşım

### İki aşamalı üretim

Sunum tek bir istekle değil, iki ayrı LLM çağrısıyla üretilir:

| Adım | Girdi | Çıktı (şema) |
|---|---|---|
| 1. Plan | Konu, hedef kitle, ton, slayt sayısı | `PresentationPlan`: başlık, alt başlık, kapak fotoğrafı sorgusu, slayt başlıkları ve her slaytın amacı |
| 2. İçerik | Aynı bilgiler + 1. adımın planı | `DeckContent`: her slaytın düzeni, maddeleri, fotoğraf sorgusu, konuşmacı notu ve sunumun 3 ana çıkarımı |

**Neden?** Model önce sunumun bütününü (akışı) düşünür, sonra her slaytı bu akışa göre
doldurur. Tek istekte hem akışı hem içeriği isteyince slaytlar arasında tekrar ve kopukluk
daha sık görülür. Ayrıca kullanıcı arayüzünde 1. adım biter bitmez slayt başlıkları
gösterilebiliyor; bekleme süresi daha kısa hissediliyor.

### Yapılandırılmış çıktı (structured output)

LLM'den serbest metin değil, JSON istenir. JSON'un yapısı Pydantic modelleriyle tanımlanır
ve Gemini'ye `response_schema` olarak verilir; dönen yanıt aynı modelle doğrulanır.

- Yanıtı ayrıştırmak için düzenli ifade ya da metin işleme gerekmez.
- Şemaya uymayan yanıt `LLMError` ile reddedilir; bozuk bir sunum asla oluşmaz.
- Şemadaki alan açıklamaları (`Field(description=...)`) prompt'un bir parçası gibi çalışır.
- Düzen alanı `Literal["image", "cards", "comparison", "highlight"]` olduğu için model
  tanımsız bir düzen uyduramaz.

### Parametreler

| Parametre | Değer | Gerekçe |
|---|---|---|
| `temperature` | 0.7 | Aynı konuda tekrar üretildiğinde farklı ama tutarlı sunumlar ("Yeniden oluştur" butonu bunun için var). |
| `response_mime_type` | `application/json` | Sadece JSON yanıt. |
| `response_schema` | Pydantic modeli | Yanıtın yapısını garanti eder. |

## 2. Sistem talimatı

```
Sen ödüllü bir sunum tasarımcısı ve içerik yazarısın. ...
- Tüm metinleri Türkçe yaz (sadece image_query alanları İngilizce).
- Genel geçer, boş cümleler kurma; her madde somut bir bilgi, örnek, neden veya sonuç içersin.
- Bilgi uydurma; emin olmadığın sayı, tarih ve isimleri kullanma.
- image_query: ... somut ve fotoğraflanabilir bir sorgu ... soyut kelimeler kullanma.
```

| Kural | Gerekçe |
|---|---|
| Rol tanımı | Modeli "bilgi veren" değil "sunum hazırlayan" bir bakış açısına sokar; kısa, slayta uygun cümleler kurar. |
| Türkçe, fotoğraf sorgusu İngilizce | Kullanıcılar Türkçe sunum istiyor; stok fotoğraf servisleri İngilizce aramada çok daha iyi sonuç veriyor. Konu İngilizce yazılsa bile içerik Türkçe kalıyor (test setindeki "Machine learning basics" örneği bunu sınar). |
| Somutluk | İlk denemelerde maddeler "Verimliliği artırır" gibi genel cümlelerdi. |
| Uydurmama | Sunumlarda en riskli hata uydurma istatistiktir; model emin olmadığı sayıları yazmamaya yönlendirilir. |
| Somut fotoğraf sorgusu | "sustainable energy concept" sorgusu için çamaşır makinesi fotoğrafı geldi. Soyut kelimeler yasaklanınca alakasız fotoğraflar belirgin şekilde azaldı. |

## 3. Plan prompt'u

- **Hedef kitle ve ton** her iki adıma da verilir. Ton için tek kelime değil, ne anlama
  geldiğini anlatan bir cümle gönderilir (`TONE_GUIDES`), ör. *Eğitici: "Sade bir dille
  anlat, kavramları günlük hayattan örneklerle açıkla."*
- **Başlıklar en fazla 7 kelime:** Slayt tasarımında başlık alanı sınırlı; uzun başlıklar taşar.
- **"Tam olarak N slayt":** Kullanıcının seçtiği sayı korunur (değerlendirmede kontrol edilir).
- **Akış kalıbı:** giriş ve önem → ana konular → sonuç/gelecek.
- **Kapak, gündem, özet, kapanış eklenmez:** Bu sayfaları kod ekliyor; model eklerse tekrar olur.

## 4. İçerik prompt'u

### Düzen seçimi

Model her slayt için dört düzenden birini seçer; her düzenin **ne zaman** kullanılacağı yazılıdır:

| Düzen | Kural |
|---|---|
| `image` | Maddeler ve fotoğraf. En sık kullanılacak düzen. |
| `cards` | 3-4 eşit önemde kavram, tür, adım veya örnek varsa. |
| `comparison` | İki tarafı karşılaştırırken (avantaj/dezavantaj, önce/sonra). |
| `highlight` | Tek çarpıcı ana mesaj; sunumda en fazla 1 kez. |

Ek olarak "art arda iki slaytta aynı düzeni kullanma" kuralı tekdüzeliği önler.

### Uzunluk sınırları düzene göre

Sınırlar slayt tasarımından gelir: kartlar dar olduğu için kart maddeleri 6-10 kelime,
resimli slayt maddeleri 8-14 kelime, vurgu cümlesi en fazla 15 kelime. Böylece metin hiçbir
düzende taşmaz.

### Kötü / iyi örnek (contrastive example)

```
Kötü: "Tanı süreçlerini hızlandırır."
İyi:  "Görüntü analizi, radyologların tümörleri daha erken fark etmesine yardım eder."
```

Sadece "somut yaz" demek yetmedi; tek bir karşıt örnek eklenince maddeler belirgin şekilde
somutlaştı. Tam bir örnek sunum (few-shot) yerine tek satırlık örnek seçildi: hem token
maliyeti düşük kalıyor hem de model örneğin konusunu kopyalamıyor.

### Konuşmacı notları

"Slayttaki maddeleri aynen tekrar etme; açıklama, örnek veya bağlam ekle ve sonraki slayta
geçişi hazırla." İlk sürümlerde notlar maddelerin cümle haline getirilmiş kopyasıydı.

### Önemli çıkarımlar

İçerik adımında sunumun 3 ana çıkarımı da istenir; "Önemli Çıkarımlar" sayfası bunlardan çizilir.
Ayrı bir LLM çağrısı gerekmez.

## 5. Prompt'un gelişimi

Prompt, uygulama gerçek konularla denendikçe adım adım geliştirildi:

| Gözlenen sorun | Yapılan değişiklik | Sonuç |
|---|---|---|
| Maddeler kısa ve genel ("Tanı süreçlerini hızlandırır") | Kelime aralığı (8-14) + kötü/iyi örnek | Maddeler iddia + somut ayrıntı içeriyor |
| Alakasız fotoğraf (soyut sorgu → çamaşır makinesi) | Soyut kelimeleri yasaklayan kural | Sorgular nesne/sahne odaklı |
| Tüm slaytlar aynı görünüyor | Düzen menüsü + çeşitlilik kuralı | Bir sunumda 3-4 farklı düzen |
| Notlar maddeleri tekrar ediyor | "Tekrar etme, bağlam ekle, geçişi hazırla" | Notlar slayta bilgi ekliyor |
| Karşılaştırma ve vurgu slaytlarında model maddeleri boş bırakıyor | Maddeler sadece `image` ve `cards` için isteniyor | Gereksiz token üretimi azaldı, kontroller düzene göre yapılıyor |
| Değerlendirme (v1): kart maddeleri sık sık 10 kelimeyi aşıyor, kartlardan taşıyor | Kural netleştirildi: "EN FAZLA 10 kelime; kartlar dar, uzun cümle sığmaz" | Kurala uyan sunum oranı %67 → %92 (24 örnek, v2) |

Prompt'la çözülmeyen ya da çözülmemesi gereken sorunlar kodda çözüldü:

- **Aynı fotoğraf iki slaytta:** Model aynı sorguyu iki kez yazabiliyor. Fotoğraflar sorguya
  değil yere göre eşleniyor ve kullanılan fotoğraf tekrar seçilmiyor (`images.py`).
- **Seçilen düzen uygulanamıyor** (ör. karşılaştırmada iki sütun yok, fotoğraf bulunamadı):
  Slayt düz madde listesi olarak çiziliyor (`pages.resolve_layout`).
- **Model kart kuralına yine de uymazsa:** Kart maddeleri uzunsa punto otomatik küçülüyor
  (`pptx_builder.card_text_size`); metin hiçbir durumda karttan taşmıyor.

## 6. Model seçimi

### Neden Gemini?

- **Ücretsiz katman:** Geliştirme ve değerlendirme ücretsiz yapılabildi; ücretli katmanda da sunum başına maliyet çok düşük.
- **Yapılandırılmış çıktı desteği:** `response_schema` ile Pydantic şeması doğrudan verilebiliyor.
- **Türkçe:** Türkçe metin kalitesi sunum içeriği için yeterli; dil kuralı testlerde hiç çiğnenmedi.
- **Model ailesi:** Aynı API ile farklı hız/maliyet seviyesinde modeller var; yedek model zinciri kurmak kolay.

### Adaylar

Fiyatlar [Gemini API fiyat sayfasından](https://aistudio.google.com/docs/pricing) (Kasım 2026, ücretli katman, 1 milyon token başına):

| Model | Girdi | Çıktı | Not |
|---|---|---|---|
| `gemini-2.5-flash` | $0.30 | $2.50 | Kullanımdan kaldırıldı; 1 Aralık 2026'dan sonra istekler `gemini-3.5-flash-lite`'a yönlendirilecek |
| `gemini-3.1-flash-lite` | $0.25 | $1.50 | En ucuz 3.x modeli |
| `gemini-3.5-flash-lite` | $0.30 | $2.50 | `gemini-2.5-flash`'ın resmi devamı |
| `gemini-3.8-flash` | $0.75 | $3.75 | En güçlü Flash modeli (1 Ocak 2027'de fiyat 2 katına çıkıyor) |

### Ölçüm

Her model aynı 6 test örneğiyle, **yedek modeller kapalı** ve fotoğraflar kapalı olarak
çalıştırıldı (yani her model kendi başına ölçüldü; prompt'un kart kuralı netleştirilmeden önceki
sürümüyle). Kalite puanı, prompt kurallarını denetleyen 11 otomatik kontrolden gelir
(ayrıntı: [değerlendirme raporu](../evaluation/RAPOR.md)).

| Model | Başarılı | Kalite | Ort. süre | Çıktı token | Sunum başına |
|---|---|---|---|---|---|
| **`gemini-3.1-flash-lite`** | **6/6** | **%95,5** | **10,4 sn** | 1.937 | **$0,0033** |
| `gemini-3.5-flash-lite` | 1/6 (5 kez 503: aşırı yoğun) | %100 (1 örnek) | 14,8 sn | 2.056 | $0,0056 |
| `gemini-2.5-flash` | 0/6 (429: ücretsiz kota doldu) | — | — | — | — |
| `gemini-3.8-flash` | 0/6 (429: ücretsiz kota doldu) | — | — | — | — |

Seçilen model, iyileştirilmiş prompt'la 24 örneklik ana değerlendirmede **24/24 başarı,
%99,2 kalite, medyan 10,9 sn ve sunum başına $0,0031** sonucunu verdi.

`gemini-2.5-flash`, aynı gün yapılan ilk ölçüm turunda (prompt'un bir önceki sürümüyle)
6/6 başarılıydı; ortalama **31 sn** sürdü, sunum başına **$0,0154** tuttu. Çıktı token'ının
büyük kısmı (ortalama ~6.000) modelin "düşünme" (thinking) token'larıydı; bu da hem süreyi
hem maliyeti artırıyor.

### Karar: `gemini-3.1-flash-lite`

| Ölçüt | Gerekçe |
|---|---|
| Kalite | Ölçülebilen modeller arasında en tutarlı sonuç: 6 örneğin hepsinde yüksek kalite (`gemini-3.5-flash-lite`'ın %100'ü tek örneğe dayanıyor). Sunum içeriği için ek "düşünme" gerekmiyor; yapılandırılmış çıktı ve somut kurallar yeterli. |
| Gecikme | Ortalama ~10 sn; `gemini-2.5-flash`'tan yaklaşık 3 kat hızlı. Kullanıcının beklediği süre doğrudan deneyimi etkiliyor. |
| Maliyet | Sunum başına ~$0,003; `gemini-2.5-flash`'tan yaklaşık 5 kat ucuz. |
| Erişilebilirlik | Test boyunca (6 karşılaştırma + 2 × 24 ana değerlendirme örneği) her istek bu modelle tamamlandı; yedek modele hiç gerek kalmadı. Diğer adaylar aynı gün 429/503 hatalarıyla yanıt vermedi. |
| Gelecek | `gemini-2.5-flash` kullanımdan kalkıyor; seçilen model güncel ailede. |

Daha güçlü `gemini-3.8-flash` bu görev için gerekli değil: görev akıl yürütme değil, kurallara
uygun ve yapılandırılmış içerik üretimi. Üstelik 5 kat daha pahalı ve test sırasında hiç yanıt vermedi.

### Yedek model zinciri

```
gemini-3.1-flash-lite  →  gemini-3.5-flash-lite  →  gemini-2.5-flash
```

Asıl model 429 (kota), 500/503 (yoğunluk), 504 ya da zaman aşımı döndürürse istek otomatik
olarak sıradakine gider. Ölçümler, Gemini modellerinin ücretsiz katmanda zaman zaman yanıt
vermediğini açıkça gösterdi; yedek zinciri olmadan canlı bir demoda bu doğrudan hata demek.
Her model ayrıca kendi içinde 2 kez yeniden denenir. Kullanıcıya teknik hata yerine anlaşılır
bir mesaj gösterilir; hangi modelin hangi kodla yanıt vermediği "Teknik ayrıntılar" altında görünür.

### Ölçümü tekrarlamak

```bash
python -m evaluation.run --model gemini-2.5-flash --limit 6 --no-fallback --no-images --pause 20 --name cmp-gemini-2.5-flash
python -m evaluation.report
```

Ücretsiz katmanın günlük kotası her gün sıfırlanır; kota nedeniyle ölçülemeyen modeller ertesi
gün bu komutla yeniden ölçülüp rapora eklenebilir.
