"""Sunum temaları: renkler ve yazı tipleri.

Tema sadece .pptx çizilirken kullanılır; LLM'i etkilemez. Bu yüzden tema
değiştirmek için API'ye tekrar gitmeye gerek yoktur.
"""

from dataclasses import dataclass

from pptx.dml.color import RGBColor

_hex = RGBColor.from_string  # "1F3A5F" -> RGBColor


@dataclass(frozen=True)
class Theme:
    dark: RGBColor  # kapak, kapanış ve vurgu slaytlarının arka planı
    accent: RGBColor  # vurgu çizgileri, kart numaraları
    background: RGBColor  # içerik slaytlarının arka planı
    surface: RGBColor  # kartların arka planı
    heading: RGBColor  # içerik slaytı başlıkları
    text: RGBColor  # madde metinleri
    muted: RGBColor  # alt başlık, sayfa numarası
    on_dark: RGBColor = _hex("FFFFFF")  # koyu zemin üzerindeki metin
    heading_font: str = "Calibri"
    body_font: str = "Calibri"


THEMES = {
    "Lacivert": Theme(
        dark=_hex("1F3A5F"), accent=_hex("F29E4C"), background=_hex("FFFFFF"),
        surface=_hex("F1F4F8"), heading=_hex("1F3A5F"), text=_hex("333333"),
        muted=_hex("9AA5B1"),
    ),
    "Orman": Theme(
        dark=_hex("1E3D32"), accent=_hex("E9B949"), background=_hex("FAF8F3"),
        surface=_hex("EEEAE0"), heading=_hex("1E3D32"), text=_hex("2F2F2F"),
        muted=_hex("A3A391"), heading_font="Georgia",
    ),
    "Mercan": Theme(
        dark=_hex("2B2D42"), accent=_hex("EF6F5E"), background=_hex("FFFFFF"),
        surface=_hex("FDF0EE"), heading=_hex("2B2D42"), text=_hex("3A3A3A"),
        muted=_hex("A0A0B0"), heading_font="Segoe UI Semibold", body_font="Segoe UI",
    ),
    "Gece": Theme(
        dark=_hex("0F1420"), accent=_hex("4FD1C5"), background=_hex("1A2030"),
        surface=_hex("252D40"), heading=_hex("FFFFFF"), text=_hex("D6DBE4"),
        muted=_hex("7D879A"),
    ),
}

DEFAULT_THEME_NAME = "Lacivert"
DEFAULT_THEME = THEMES[DEFAULT_THEME_NAME]
