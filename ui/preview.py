"""Slaytların tarayıcıdaki HTML önizlemesi.

.pptx dosyasındaki yerleşimi taklit eder ve aynı sayfa listesini
(pages.plan_pages) kullanır. Ölçüler slayt genişliğine oranlıdır (CSS'teki
'cqw' birimi), bu yüzden önizleme her ekran boyutunda .pptx ile aynı oranda
görünür. Tema değişince API'ye gitmeden anında yeniden çizilir.

Not: Streamlit HTML'i Markdown olarak işler; girintili satırlar kod bloğuna
dönüşmesin diye HTML parçaları boşluksuz, tek satır halinde üretilir.
"""

import base64
from html import escape

from presentation_generator.models import Presentation
from presentation_generator.pages import Images, Page, plan_pages
from presentation_generator.pptx_builder import card_text_size
from presentation_generator.themes import Theme


def render_previews(presentation: Presentation, theme: Theme, images: Images) -> str:
    """Tüm slaytların önizlemesini tek bir HTML ızgarası olarak döndürür."""
    figures = "".join(
        f'<figure class="pv-item">{DRAWERS[page.kind](page, presentation)}'
        f'<figcaption>{page.number}</figcaption></figure>'
        for page in plan_pages(presentation, images)
    )
    return f'<div class="pv-grid" style="{_theme_variables(theme)}">{figures}</div>'


# --- Sayfa türleri ---------------------------------------------------------


def _cover(page: Page, presentation: Presentation) -> str:
    text = (f'<div class="pv-cover-title">{escape(presentation.title)}</div>'
            '<div class="pv-bar"></div>'
            f'<div class="pv-cover-subtitle">{escape(presentation.subtitle)}</div>')
    if page.image:
        return _slide(f'{_photo(page.image, "pv-photo-cover")}<div class="pv-cover">{text}</div>',
                      dark=True)
    return _slide(f'<div class="pv-center">{text}</div>', dark=True)


def _agenda(page: Page, presentation: Presentation) -> str:
    items = "".join(f"<li><b>{index:02d}</b>{escape(slide.title)}</li>"
                    for index, slide in enumerate(presentation.slides, start=1))
    compact = " pv-compact" if len(presentation.slides) > 6 else ""
    return _slide(
        '<div class="pv-agenda-panel"><div class="pv-agenda-title">Gündem</div>'
        '<div class="pv-bar"></div></div>'
        f'<ol class="pv-agenda-list{compact}">{items}</ol>'
        f'{_footer(page.number, extra_class="pv-footer-agenda")}'
    )


def _bullets(page: Page, presentation: Presentation) -> str:
    body = _heading(page.slide.title) + _bullet_list(page.slide.bullets)
    return _slide(f'<div class="pv-content">{body}</div>{_footer(page.number, presentation.title)}')


def _image(page: Page, presentation: Presentation) -> str:
    body = _heading(page.slide.title) + _bullet_list(page.slide.bullets)
    return _slide(
        f'<div class="pv-content pv-narrow">{body}</div>{_photo(page.image, "pv-photo-side")}'
        f'{_footer(page.number, presentation.title, extra_class="pv-footer-narrow")}'
    )


def _cards(page: Page, presentation: Presentation) -> str:
    cards = "".join(f'<div class="pv-card"><b>{index:02d}</b><span>{escape(bullet)}</span></div>'
                    for index, bullet in enumerate(page.slide.bullets, start=1))
    dense = " pv-dense" if card_text_size(page.slide.bullets) < 18 else ""  # .pptx ile aynı kural
    body = f'{_heading(page.slide.title)}<div class="pv-cards{dense}">{cards}</div>'
    return _slide(f'<div class="pv-content">{body}</div>{_footer(page.number, presentation.title)}')


def _comparison(page: Page, presentation: Presentation) -> str:
    columns = "".join(
        f'<div class="pv-column"><div class="pv-column-title">{escape(column.title)}</div>'
        f'<div class="pv-column-body">{_bullet_list(column.bullets)}</div></div>'
        for column in page.slide.columns
    )
    body = f'{_heading(page.slide.title)}<div class="pv-columns">{columns}</div>'
    return _slide(f'<div class="pv-content">{body}</div>{_footer(page.number, presentation.title)}')


def _highlight(page: Page, presentation: Presentation) -> str:
    background = (_photo(page.image, "pv-photo-full") + '<div class="pv-overlay"></div>'
                  if page.image else "")
    return _slide(
        f'{background}<div class="pv-center">'
        f'<div class="pv-highlight-title">{escape(page.slide.title)}</div>'
        '<div class="pv-bar"></div>'
        f'<div class="pv-highlight-text">{escape(page.slide.highlight)}</div>'
        f'</div>{_footer(page.number)}',
        dark=True,
    )


def _takeaways(page: Page, presentation: Presentation) -> str:
    rows = "".join(f'<div class="pv-takeaway">{escape(takeaway)}</div>'
                   for takeaway in presentation.takeaways[:3])
    body = f'{_heading("Önemli Çıkarımlar")}<div class="pv-takeaways">{rows}</div>'
    return _slide(f'<div class="pv-content">{body}</div>{_footer(page.number, presentation.title)}')


def _closing(page: Page, presentation: Presentation) -> str:
    return _slide(
        '<div class="pv-center"><div class="pv-closing-title">Teşekkürler!</div>'
        '<div class="pv-bar"></div><div class="pv-cover-subtitle">Sorularınız?</div></div>',
        dark=True,
    )


DRAWERS = {
    "cover": _cover,
    "agenda": _agenda,
    "image": _image,
    "cards": _cards,
    "comparison": _comparison,
    "highlight": _highlight,
    "bullets": _bullets,
    "takeaways": _takeaways,
    "closing": _closing,
}


# --- Yardımcılar -----------------------------------------------------------


def _slide(inner_html: str, dark: bool = False) -> str:
    return f'<div class="pv-slide{" pv-dark" if dark else ""}">{inner_html}</div>'


def _heading(title: str) -> str:
    return f'<div class="pv-heading">{escape(title)}</div><div class="pv-bar"></div>'


def _bullet_list(bullets: list[str]) -> str:
    return '<ul class="pv-bullets">' + "".join(f"<li>{escape(b)}</li>" for b in bullets) + "</ul>"


def _footer(number: int, title: str = "", extra_class: str = "") -> str:
    """Alt bilgi: solda sunum başlığı, sağda sayfa numarası."""
    return (f'<div class="pv-footer {extra_class}"><span>{escape(title)}</span>'
            f'<span>{number}</span></div>')


def _photo(image: bytes, css_class: str) -> str:
    """Fotoğrafı sayfaya gömer (base64); 'cover' ile kutuyu doldurup taşanı kırpar."""
    data = base64.b64encode(image).decode()
    return f'<div class="pv-photo {css_class}" style="background-image:url(data:image/jpeg;base64,{data})"></div>'


def _theme_variables(theme: Theme) -> str:
    """Temanın renk ve yazı tiplerini CSS değişkenlerine çevirir (style.css bunları kullanır)."""
    colors = {
        "dark": theme.dark, "accent": theme.accent, "background": theme.background,
        "surface": theme.surface, "heading": theme.heading, "text": theme.text,
        "muted": theme.muted, "on-dark": theme.on_dark,
    }
    variables = [f"--{name}:#{color}" for name, color in colors.items()]
    variables += [f"--heading-font:'{theme.heading_font}'", f"--body-font:'{theme.body_font}'"]
    return ";".join(variables)
