"""Slaytlar için Pixabay'den fotoğraf bulur.

Pixabay ücretsiz bir stok fotoğraf servisidir: https://pixabay.com/api/docs/
Bir fotoğraf bulunamazsa ya da istek başarısız olursa o slayt resimsiz çizilir;
resim yüzünden sunumun tamamı hiçbir zaman başarısız olmaz.
"""

from concurrent.futures import ThreadPoolExecutor

import httpx

SEARCH_URL = "https://pixabay.com/api/"
TIMEOUT_SECONDS = 15
CANDIDATES_PER_QUERY = 5  # aynı fotoğraf iki slayta düşerse yedekten seçebilmek için


class PixabayClient:
    def __init__(self, api_key: str):
        self._api_key = api_key

    def find_all(self, queries: dict[str, str]) -> dict[str, bytes]:
        """Her yer için bir fotoğraf bulur; aynı fotoğrafı iki yerde kullanmaz.

        queries: {fotoğraf yeri: arama sorgusu}. Aramalar ve indirmeler aynı anda
        (paralel) yapılır. Sonuç: {fotoğraf yeri: fotoğraf}; bulunamayanlar yer almaz.
        """
        unique_queries = list(dict.fromkeys(q for q in queries.values() if q))
        with ThreadPoolExecutor(max_workers=6) as pool:
            candidates = dict(zip(unique_queries, pool.map(self._search, unique_queries)))
            chosen_urls = _pick_unique(queries, candidates)
            images = pool.map(self._download, chosen_urls.values())
        return {place: image for place, image in zip(chosen_urls, images) if image}

    def _search(self, query: str) -> list[dict]:
        """Sorguya uyan fotoğrafların listesini döndürür; hata olursa boş liste."""
        try:
            response = httpx.get(
                SEARCH_URL,
                params={
                    "key": self._api_key,
                    "q": query[:100],  # Pixabay en fazla 100 karakter kabul eder
                    "image_type": "photo",
                    "orientation": "vertical",  # slaytlardaki fotoğraf alanı dikey
                    "safesearch": "true",
                    "per_page": CANDIDATES_PER_QUERY,
                },
                timeout=TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            return response.json()["hits"]
        except httpx.HTTPError:
            return []

    @staticmethod
    def _download(url: str) -> bytes | None:
        try:
            response = httpx.get(url, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.content
        except httpx.HTTPError:
            return None


def _pick_unique(queries: dict[str, str], candidates: dict[str, list[dict]]) -> dict[str, str]:
    """Her yer için daha önce seçilmemiş ilk fotoğrafı seçer: {yer: fotoğraf adresi}."""
    used_ids: set[int] = set()
    chosen: dict[str, str] = {}
    for place, query in queries.items():
        hit = next((h for h in candidates.get(query, []) if h["id"] not in used_ids), None)
        if hit:
            used_ids.add(hit["id"])
            chosen[place] = hit["largeImageURL"]
    return chosen
