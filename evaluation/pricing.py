"""Gemini ücretli katman fiyatları (1 milyon token başına USD).

Kaynak: https://aistudio.google.com/docs/pricing (Kasım 2026, standart katman, metin).
Çıktı fiyatına düşünme (thinking) token'ları da dahildir.
Ücretsiz katmanda bu modellerin hepsi ücretsizdir; buradaki maliyet,
uygulama ücretli katmanda çalışsaydı ödenecek tutarı gösterir.
"""

from presentation_generator.llm import CallStats

PRICES_PER_MILLION = {  # model: (girdi, çıktı)
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-2.5-flash-lite": (0.10, 0.40),
    "gemini-3.1-flash-lite": (0.25, 1.50),
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "gemini-3.6-flash": (0.75, 3.75),
    "gemini-3.8-flash": (0.75, 3.75),
}


def call_cost(call: CallStats) -> float | None:
    """Bir çağrının USD maliyeti; fiyatı bilinmeyen model için None."""
    prices = PRICES_PER_MILLION.get(call.model)
    if prices is None:
        return None
    input_price, output_price = prices
    return (call.input_tokens * input_price + call.output_tokens * output_price) / 1_000_000
