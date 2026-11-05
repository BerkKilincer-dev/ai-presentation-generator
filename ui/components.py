"""Sayfanın sabit görsel parçaları: stil, karşılama alanı, özellikler ve alt bilgi."""

from html import escape
from pathlib import Path

import streamlit as st

STYLE_FILE = Path(__file__).with_name("style.css")

FEATURES = [
    ("🧠", "Akıllı içerik",
     "Hedef kitlene ve seçtiğin tona göre yazılmış slaytlar ve konuşmacı notları."),
    ("🖼️", "Otomatik görseller",
     "Her slayta konuyla uyumlu, yüksek çözünürlüklü fotoğraflar."),
    ("🎨", "Hazır temalar",
     "Tek tıkla tema değiştir, sunumunu PowerPoint dosyası olarak indir."),
]


def inject_styles() -> None:
    """style.css dosyasını sayfaya ekler."""
    st.markdown(f"<style>{STYLE_FILE.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def brand() -> None:
    """Sol üstteki küçük uygulama adı."""
    st.markdown('<div class="brand">📊 Konudan Sunum Oluşturucu</div>', unsafe_allow_html=True)


def hero() -> None:
    """Karşılama sayfasının başlık alanı."""
    st.markdown(
        '<div class="hero">'
        '<div class="hero-badge">✨ Yapay zekâ destekli sunum hazırlayıcı</div>'
        '<div class="hero-title">Konunu yaz,<br><span>sunumun hazır olsun.</span></div>'
        '<div class="hero-text">Slaytların planlanması, içeriğin yazılması ve görsellerin '
        'seçilmesi saniyeler içinde. Sen sadece indir ve sun.</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def features() -> None:
    """Karşılama sayfasının altındaki üç özellik kartı."""
    cards = "".join(
        f'<div class="feature"><div class="feature-icon">{icon}</div>'
        f'<b>{title}</b><p>{text}</p></div>'
        for icon, title, text in FEATURES
    )
    st.markdown(f'<div class="features">{cards}</div>', unsafe_allow_html=True)


def result_header(title: str, subtitle: str, meta: str) -> None:
    """Sonuç sayfasının başlığı."""
    st.markdown(
        '<div class="result-header">'
        f'<div class="result-meta">{escape(meta)}</div>'
        f'<div class="result-title">{escape(title)}</div>'
        f'<div class="result-subtitle">{escape(subtitle)}</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def footer() -> None:
    st.markdown(
        '<div class="app-footer">Sunumlar PowerPoint (.pptx) formatında indirilir · '
        'Görseller <a href="https://pixabay.com" target="_blank">Pixabay</a> tarafından sağlanır'
        '</div>',
        unsafe_allow_html=True,
    )
