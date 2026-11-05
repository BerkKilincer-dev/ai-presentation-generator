"""Slaytlar için Pixabay'den fotoğraf bulur.

Pixabay ücretsiz bir stok fotoğraf servisidir: https://pixabay.com/api/docs/

Pixabay sonuçları popülerliğe göre sıralar ve sorgudaki kelimelerden yalnızca
biri eşleşse bile fotoğraf döndürür; ilk sonucu almak alakasız fotoğraflara yol
açar ("student holding apple" -> elmalı turta). Bu yüzden birçok aday alınır ve
etiketleri sorguyla en çok örtüşen fotoğraf seçilir.

Slaytın kendi sorgusuna yeterince uyan fotoğraf yoksa, sunumun genel konusunun
(kapak sorgusunun) adaylarından biri kullanılır; böylece slaytlar fotoğrafsız
kalmaz ve konulan fotoğraf her zaman sunumun konusuyla ilgili olur.
"""

from concurrent.futures import ThreadPoolExecutor

import httpx

from .models import COVER_PHOTO

SEARCH_URL = "https://pixabay.com/api/"
TIMEOUT_SECONDS = 15
CANDIDATES_PER_QUERY = 30  # alakalı fotoğrafı seçebilmek için geniş bir aday havuzu
STRONG_MATCH = 2  # "alakalı" sayılmak için sorgudan etiketlerde geçmesi gereken kelime sayısı


class PixabayClient:
    def __init__(self, api_key: str):
        self._api_key = api_key

    def find_all(self, queries: dict[str, str]) -> dict[str, bytes]:
        """Her yer için en alakalı fotoğrafı bulur; aynı fotoğrafı iki yerde kullanmaz.

        queries: {fotoğraf yeri: arama sorgusu}. Aramalar ve indirmeler aynı anda
        (paralel) yapılır. Sonuç: {fotoğraf yeri: fotoğraf}; bulunamayanlar yer almaz.
        """
        unique_queries = list(dict.fromkeys(q for q in queries.values() if q))
        with ThreadPoolExecutor(max_workers=6) as pool:
            candidates = dict(zip(unique_queries, pool.map(self._search, unique_queries)))
            chosen_urls = _pick_best(queries, candidates)
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


def relevance(query: str, hit: dict) -> int:
    """Sorgudaki anlamlı kelimelerden kaçı fotoğrafın etiketlerinde geçiyor."""
    tag_words = {_stem(word) for word in hit["tags"].lower().replace(",", " ").split()}
    query_words = [_stem(word) for word in query.lower().split() if len(word) > 2]
    return sum(word in tag_words for word in query_words)


def _stem(word: str) -> str:
    """Basit kök bulma: 'panels' -> 'panel', 'working' -> 'work' (eşleşmeyi esnetmek için)."""
    for suffix in ("ing", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def _pick_best(queries: dict[str, str], candidates: dict[str, list[dict]]) -> dict[str, str]:
    """Her yer için daha önce seçilmemiş en uygun fotoğrafı seçer: {yer: fotoğraf adresi}.

    Sırayla denenir:
      1. Yerin kendi sorgusuna güçlü uyan fotoğraf (en az 2 kelime eşleşir).
      2. Sunumun genel konusuna (kapak sorgusuna) uyan fotoğraf.
      3. Yerin kendi sorgusuna kısmen uyan fotoğraf (1 kelime eşleşir).
    Yeni arama yapılmaz; zaten çekilmiş adaylar kullanılır.
    """
    topic_query = queries.get(COVER_PHOTO, "")
    used_ids: set[int] = set()
    chosen: dict[str, str] = {}
    for place, query in queries.items():
        attempts = [(query, min(STRONG_MATCH, len(query.split()))), (topic_query, 1), (query, 1)]
        for attempt_query, needed in attempts:
            hit = _best_match(attempt_query, candidates.get(attempt_query, []), used_ids, needed)
            if hit:
                used_ids.add(hit["id"])
                chosen[place] = hit["largeImageURL"]
                break
    return chosen


def _best_match(query: str, hits: list[dict], used_ids: set[int], needed: int) -> dict | None:
    """Kullanılmamış adaylar içinde sorguya en çok uyanı; yeterince uymuyorsa None.

    Eşit puanlı adaylar arasında Pixabay'in sırası (popülerlik) korunur.
    """
    unused = [hit for hit in hits if hit["id"] not in used_ids]
    best = max(unused, key=lambda hit: relevance(query, hit), default=None)
    return best if best and relevance(query, best) >= needed else None
