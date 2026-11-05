"""Presentation nesnesini python-pptx ile .pptx dosyasına dönüştürür.

Sayfaların sırası ve düzeni pages.plan_pages() ile belirlenir; bu dosya her
sayfa türünü boş (blank) bir slayt üzerine çizer. Böylece yerleşim, renk ve
yazı tipi tamamen bizim kontrolümüzde olur.
"""

import re
from io import BytesIO

from pptx import Presentation as PptxDeck
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.slide import Slide as PptxSlide
from pptx.text.text import TextFrame
from pptx.util import Inches, Pt

from .models import Presentation
from .pages import Images, Page, plan_pages
from .themes import DEFAULT_THEME, Theme

SLIDE_WIDTH = Inches(13.333)  # 16:9
SLIDE_HEIGHT = Inches(7.5)
MARGIN = Inches(0.7)
CONTENT_WIDTH = SLIDE_WIDTH - 2 * MARGIN
CONTENT_TOP = Inches(2)  # başlık ve vurgu çizgisinin altı
FOOTER_TOP = Inches(6.85)
BLANK_LAYOUT = 6  # varsayılan şablondaki boş slayt düzeni
BAR_WIDTH = Inches(2)
GAP = Inches(0.3)  # kartlar ve sütunlar arası boşluk


def build_pptx(presentation: Presentation, theme: Theme = DEFAULT_THEME,
               images: Images | None = None) -> bytes:
    """Sunumu oluşturur ve .pptx dosyasının içeriğini bayt olarak döndürür."""
    deck = PptxDeck()
    deck.slide_width = SLIDE_WIDTH
    deck.slide_height = SLIDE_HEIGHT

    for page in plan_pages(presentation, images or {}):
        draw = DRAWERS[page.kind]
        slide = draw(deck, page, presentation, theme)
        if page.slide:
            slide.notes_slide.notes_text_frame.text = page.slide.notes

    buffer = BytesIO()
    deck.save(buffer)
    return buffer.getvalue()


def file_name_for(title: str) -> str:
    """Sunum başlığından güvenli bir dosya adı üretir: 'Yapay Zekâ' -> 'yapay-zeka.pptx'."""
    ascii_title = title.translate(str.maketrans("çğıöşüâÇĞİÖŞÜÂ", "cgiosuaCGIOSUA"))
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")
    return f"{slug or 'sunum'}.pptx"


# --- Sayfa türleri ---------------------------------------------------------
# Hepsi aynı imzaya sahiptir: (deck, page, presentation, theme) -> slayt


def _draw_cover(deck: PptxDeck, page: Page, presentation: Presentation, theme: Theme) -> PptxSlide:
    """Kapak: fotoğraf varsa solda başlık + sağda fotoğraf, yoksa ortalanmış başlık."""
    slide = _new_slide(deck, theme.dark)

    if page.image:
        image_left = Inches(7.3)
        _add_picture_fill(slide, page.image, left=image_left, width=SLIDE_WIDTH - image_left)
        text_width = image_left - MARGIN - Inches(0.6)
        align, bar_left = PP_ALIGN.LEFT, MARGIN
    else:
        text_width = CONTENT_WIDTH
        align, bar_left = PP_ALIGN.CENTER, _centered(BAR_WIDTH)

    _add_text(slide, presentation.title, top=Inches(1.6), height=Inches(2.4), width=text_width,
              size=40, color=theme.on_dark, font=theme.heading_font, bold=True,
              align=align, anchor=MSO_ANCHOR.BOTTOM)
    _add_accent_bar(slide, left=bar_left, top=Inches(4.2), theme=theme)
    _add_text(slide, presentation.subtitle, top=Inches(4.5), height=Inches(1.4), width=text_width,
              size=20, color=theme.muted, font=theme.body_font, align=align, anchor=MSO_ANCHOR.TOP)
    return slide


def _draw_agenda(deck: PptxDeck, page: Page, presentation: Presentation, theme: Theme) -> PptxSlide:
    """Gündem: solda koyu panelde başlık, sağda numaralı slayt başlıkları."""
    slide = _new_slide(deck, theme.background)

    panel_width = Inches(4.3)
    panel = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, panel_width, SLIDE_HEIGHT)
    _fill_shape(panel, theme.dark)
    _add_text(slide, "Gündem", top=Inches(2.6), height=Inches(1.2), width=panel_width - 2 * MARGIN,
              size=40, color=theme.on_dark, font=theme.heading_font, bold=True,
              anchor=MSO_ANCHOR.BOTTOM)
    _add_accent_bar(slide, left=MARGIN, top=Inches(4), theme=theme)

    list_left = panel_width + Inches(0.8)
    list_width = SLIDE_WIDTH - list_left - MARGIN
    frame = _new_text_frame(slide, list_left, Inches(0.8), list_width, Inches(5.9))
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE

    size = 20 if len(presentation.slides) <= 6 else 17
    for index, content in enumerate(presentation.slides, start=1):
        paragraph = frame.paragraphs[0] if index == 1 else frame.add_paragraph()
        paragraph.space_after = Pt(size * 0.9)
        number = paragraph.add_run()
        number.text = f"{index:02d}    "
        _style_font(number.font, size, theme.accent, theme.heading_font, bold=True)
        title = paragraph.add_run()
        title.text = content.title
        _style_font(title.font, size, theme.text, theme.body_font)

    _add_footer(slide, page.number, theme, left=list_left, width=list_width)
    return slide


def _draw_bullets(deck: PptxDeck, page: Page, presentation: Presentation, theme: Theme) -> PptxSlide:
    """Düz liste: başlık ve tam genişlikte maddeler."""
    slide = _new_slide(deck, theme.background)
    _add_heading(slide, page.slide.title, width=CONTENT_WIDTH, theme=theme)
    _add_bullets(slide, page.slide.bullets, width=CONTENT_WIDTH, theme=theme)
    _add_footer(slide, page.number, theme, title=presentation.title)
    return slide


def _draw_image(deck: PptxDeck, page: Page, presentation: Presentation, theme: Theme) -> PptxSlide:
    """Maddeler solda, fotoğraf sağda (slaytın sağ kenarına kadar)."""
    slide = _new_slide(deck, theme.background)
    image_left = Inches(8)
    text_width = image_left - MARGIN - Inches(0.5)

    _add_heading(slide, page.slide.title, width=text_width, theme=theme)
    _add_bullets(slide, page.slide.bullets, width=text_width, theme=theme)
    _add_picture_fill(slide, page.image, left=image_left, width=SLIDE_WIDTH - image_left)
    _add_footer(slide, page.number, theme, title=presentation.title, width=text_width)
    return slide


def _draw_cards(deck: PptxDeck, page: Page, presentation: Presentation, theme: Theme) -> PptxSlide:
    """Her madde numaralı bir kartta, kartlar yan yana."""
    slide = _new_slide(deck, theme.background)
    _add_heading(slide, page.slide.title, width=CONTENT_WIDTH, theme=theme)

    bullets = page.slide.bullets
    card_width = (CONTENT_WIDTH - GAP * (len(bullets) - 1)) // len(bullets)
    text_size = card_text_size(bullets)
    for index, bullet in enumerate(bullets):
        left = MARGIN + index * (card_width + GAP)
        _add_card(slide, f"{index + 1:02d}", bullet, left=left, width=card_width,
                  text_size=text_size, theme=theme)

    _add_footer(slide, page.number, theme, title=presentation.title)
    return slide


def _draw_comparison(deck: PptxDeck, page: Page, presentation: Presentation,
                     theme: Theme) -> PptxSlide:
    """İki sütunlu karşılaştırma: her sütunun renkli bir başlığı ve maddeleri var."""
    slide = _new_slide(deck, theme.background)
    _add_heading(slide, page.slide.title, width=CONTENT_WIDTH, theme=theme)

    column_width = (CONTENT_WIDTH - GAP) // 2
    header_colors = [(theme.dark, theme.on_dark), (theme.accent, theme.dark)]  # (zemin, yazı)
    for index, (column, (fill, text_color)) in enumerate(zip(page.slide.columns, header_colors)):
        left = MARGIN + index * (column_width + GAP)

        header = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, Inches(2.2),
                                        column_width, Inches(0.7))
        _fill_shape(header, fill)
        header_frame = header.text_frame
        header_frame.margin_left = Inches(0.3)
        header_frame.paragraphs[0].text = column.title
        header_frame.paragraphs[0].alignment = PP_ALIGN.LEFT
        _style_font(header_frame.paragraphs[0].font, 20, text_color, theme.heading_font, bold=True)

        body = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, Inches(2.9),
                                      column_width, Inches(3.1))
        _fill_shape(body, theme.surface)
        body_frame = body.text_frame
        body_frame.word_wrap = True
        body_frame.vertical_anchor = MSO_ANCHOR.TOP
        body_frame.margin_left = body_frame.margin_right = body_frame.margin_top = Inches(0.3)
        _fill_bullets(body_frame, column.bullets, size=18, theme=theme)

    _add_footer(slide, page.number, theme, title=presentation.title)
    return slide


def _draw_highlight(deck: PptxDeck, page: Page, presentation: Presentation,
                    theme: Theme) -> PptxSlide:
    """Tek büyük ana mesaj. Fotoğraf varsa arka planda, üzerinde koyu yarı saydam katman."""
    slide = _new_slide(deck, theme.dark)
    if page.image:
        _add_picture_fill(slide, page.image, left=0, width=SLIDE_WIDTH)
        _add_overlay(slide, theme.dark, opacity=0.82)

    _add_text(slide, page.slide.title, top=Inches(1.5), height=Inches(0.6), size=18,
              color=theme.accent, font=theme.body_font, bold=True, align=PP_ALIGN.CENTER)
    _add_accent_bar(slide, left=_centered(BAR_WIDTH), top=Inches(2.3), theme=theme)
    _add_text(slide, page.slide.highlight, top=Inches(2.6), height=Inches(3), size=36,
              color=theme.on_dark, font=theme.heading_font, bold=True,
              align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.TOP)
    _add_footer(slide, page.number, theme)
    return slide


def _draw_takeaways(deck: PptxDeck, page: Page, presentation: Presentation,
                    theme: Theme) -> PptxSlide:
    """Önemli çıkarımlar: her biri solunda renkli şerit olan bir satırda."""
    slide = _new_slide(deck, theme.background)
    _add_heading(slide, "Önemli Çıkarımlar", width=CONTENT_WIDTH, theme=theme)

    row_height = Inches(1.15)
    for index, takeaway in enumerate(presentation.takeaways[:3]):
        top = Inches(2.3) + index * (row_height + GAP)
        row = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, MARGIN, top, CONTENT_WIDTH, row_height)
        _fill_shape(row, theme.surface)
        stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, MARGIN, top, Inches(0.12), row_height)
        _fill_shape(stripe, theme.accent)
        _add_text(slide, takeaway, left=MARGIN + Inches(0.5), top=top, height=row_height,
                  width=CONTENT_WIDTH - Inches(0.8), size=20, color=theme.text, font=theme.body_font)

    _add_footer(slide, page.number, theme, title=presentation.title)
    return slide


def _draw_closing(deck: PptxDeck, page: Page, presentation: Presentation, theme: Theme) -> PptxSlide:
    """Kapanış: teşekkür ve soru daveti."""
    slide = _new_slide(deck, theme.dark)
    _add_text(slide, "Teşekkürler!", top=Inches(2.6), height=Inches(1.3), size=48,
              color=theme.on_dark, font=theme.heading_font, bold=True, align=PP_ALIGN.CENTER)
    _add_accent_bar(slide, left=_centered(BAR_WIDTH), top=Inches(4.0), theme=theme)
    _add_text(slide, "Sorularınız?", top=Inches(4.2), height=Inches(0.8), size=24,
              color=theme.muted, font=theme.body_font, align=PP_ALIGN.CENTER)
    return slide


DRAWERS = {
    "cover": _draw_cover,
    "agenda": _draw_agenda,
    "image": _draw_image,
    "cards": _draw_cards,
    "comparison": _draw_comparison,
    "highlight": _draw_highlight,
    "bullets": _draw_bullets,
    "takeaways": _draw_takeaways,
    "closing": _draw_closing,
}


# --- Yardımcı çizim fonksiyonları -----------------------------------------


def _new_slide(deck: PptxDeck, background: RGBColor) -> PptxSlide:
    """Verilen arka plan rengiyle boş bir slayt ekler."""
    slide = deck.slides.add_slide(deck.slide_layouts[BLANK_LAYOUT])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = background
    return slide


def _add_heading(slide: PptxSlide, title: str, *, width: int, theme: Theme) -> None:
    """İçerik slaytlarının başlığı ve altındaki vurgu çizgisi."""
    _add_text(slide, title, top=Inches(0.4), height=Inches(1.1), width=width, size=32,
              color=theme.heading, font=theme.heading_font, bold=True, anchor=MSO_ANCHOR.BOTTOM)
    _add_accent_bar(slide, left=MARGIN, top=Inches(1.6), theme=theme)


def _add_footer(slide: PptxSlide, number: int, theme: Theme, *, title: str = "",
                left: int = MARGIN, width: int = CONTENT_WIDTH) -> None:
    """Alt bilgi: solda sunum başlığı (isteğe bağlı), sağda sayfa numarası."""
    if title:
        _add_text(slide, title, left=left, top=FOOTER_TOP, height=Inches(0.4), width=width,
                  size=11, color=theme.muted, font=theme.body_font)
    _add_text(slide, str(number), left=left, top=FOOTER_TOP, height=Inches(0.4), width=width,
              size=12, color=theme.muted, font=theme.body_font, align=PP_ALIGN.RIGHT)


def _add_text(slide: PptxSlide, text: str, *, top: int, height: int, size: int,
              color: RGBColor, font: str, left: int = MARGIN, width: int = CONTENT_WIDTH,
              bold: bool = False, align: PP_ALIGN = PP_ALIGN.LEFT,
              anchor: MSO_ANCHOR = MSO_ANCHOR.MIDDLE) -> None:
    """Tek paragraflık bir metin kutusu ekler."""
    frame = _new_text_frame(slide, left, top, width, height)
    frame.vertical_anchor = anchor

    paragraph = frame.paragraphs[0]
    paragraph.text = text
    paragraph.alignment = align
    _style_font(paragraph.font, size, color, font, bold)


def _add_bullets(slide: PptxSlide, bullets: list[str], *, width: int, theme: Theme) -> None:
    """Başlığın altına madde listesi ekler."""
    frame = _new_text_frame(slide, MARGIN, CONTENT_TOP, width, Inches(4.7))
    _fill_bullets(frame, bullets, size=20, theme=theme)


def _fill_bullets(frame: TextFrame, bullets: list[str], *, size: int, theme: Theme) -> None:
    """Her maddeyi renkli madde işaretli ayrı bir paragraf olarak yazar."""
    for index, bullet in enumerate(bullets):
        # Metin kutusu boş bir paragrafla gelir; ilk maddeyi ona yazarız.
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.text = bullet
        paragraph.alignment = PP_ALIGN.LEFT
        paragraph.space_after = Pt(size * 0.7)
        _set_bullet(paragraph, theme.accent, indent=Pt(size * 1.1))
        _style_font(paragraph.font, size, theme.text, theme.body_font)


def _set_bullet(paragraph, color: RGBColor, indent: int) -> None:
    """Paragrafa renkli madde işareti ve asılı girinti ekler (python-pptx'te hazır yok).

    XML şemasında madde işareti, yazı tipi ayarından (defRPr) önce gelmelidir;
    bu yüzden yazı tipi bu fonksiyondan sonra ayarlanır.
    """
    properties = paragraph._p.get_or_add_pPr()
    properties.set("marL", str(int(indent)))  # metnin soldan girintisi
    properties.set("indent", str(-int(indent)))  # ilk satır (işaret) sola taşar

    bullet_color = properties.makeelement(qn("a:buClr"), {})
    bullet_color.append(properties.makeelement(qn("a:srgbClr"), {"val": str(color)}))
    properties.append(bullet_color)
    properties.append(properties.makeelement(qn("a:buChar"), {"char": "•"}))


def card_text_size(bullets: list[str]) -> int:
    """Kart metninin punto büyüklüğü: madde uzunsa küçültülür ki karttan taşmasın."""
    longest = max(len(bullet.split()) for bullet in bullets)
    return 18 if longest <= 10 else 15


def _add_card(slide: PptxSlide, number: str, text: str, *, left: int, width: int,
              text_size: int, theme: Theme) -> None:
    """Köşeleri yuvarlatılmış kart: üstte büyük numara, altında madde metni."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, Inches(2.3),
                                  width, Inches(3.4))
    card.adjustments[0] = 0.06  # köşe yuvarlaklığı
    _fill_shape(card, theme.surface)

    frame = card.text_frame
    frame.word_wrap = True
    frame.vertical_anchor = MSO_ANCHOR.TOP
    frame.margin_left = frame.margin_right = frame.margin_top = Inches(0.3)

    number_paragraph = frame.paragraphs[0]
    number_paragraph.text = number
    number_paragraph.space_after = Pt(12)
    _style_font(number_paragraph.font, 32, theme.accent, theme.heading_font, bold=True)

    text_paragraph = frame.add_paragraph()
    text_paragraph.text = text
    _style_font(text_paragraph.font, text_size, theme.text, theme.body_font)

    for paragraph in frame.paragraphs:
        paragraph.alignment = PP_ALIGN.LEFT  # şekillerde metin varsayılan olarak ortalıdır


def _add_picture_fill(slide: PptxSlide, image: bytes, *, left: int, width: int) -> None:
    """Fotoğrafı slaytın tüm yüksekliğini dolduracak şekilde ekler.

    Fotoğrafın oranı kutuya uymuyorsa, oranı bozmadan taşan kenarları kırpılır.
    """
    picture = slide.shapes.add_picture(BytesIO(image), left, 0, width, SLIDE_HEIGHT)

    image_width, image_height = picture.image.size
    image_ratio = image_width / image_height
    box_ratio = width / SLIDE_HEIGHT

    if image_ratio > box_ratio:  # fotoğraf kutudan geniş: sağdan ve soldan kırp
        crop = (1 - box_ratio / image_ratio) / 2
        picture.crop_left = picture.crop_right = crop
    else:  # fotoğraf kutudan uzun: üstten ve alttan kırp
        crop = (1 - image_ratio / box_ratio) / 2
        picture.crop_top = picture.crop_bottom = crop


def _add_overlay(slide: PptxSlide, color: RGBColor, opacity: float) -> None:
    """Fotoğrafın üstündeki yazı okunsun diye tüm slayta yarı saydam renkli katman ekler."""
    overlay = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_WIDTH, SLIDE_HEIGHT)
    _fill_shape(overlay, color)
    # python-pptx saydamlığı desteklemez; rengin XML'ine alpha değeri ekleriz (100000 = opak).
    color_xml = overlay._element.spPr.find(qn("a:solidFill"))[0]
    color_xml.append(color_xml.makeelement(qn("a:alpha"), {"val": str(int(opacity * 100000))}))


def _add_accent_bar(slide: PptxSlide, *, left: int, top: int, theme: Theme) -> None:
    """Başlıkların altındaki ince renkli çizgi."""
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, BAR_WIDTH, Inches(0.08))
    _fill_shape(bar, theme.accent)


def _new_text_frame(slide: PptxSlide, left: int, top: int, width: int, height: int) -> TextFrame:
    """Boş bir metin kutusu ekler."""
    box = slide.shapes.add_textbox(left, top, width, height)
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = frame.margin_right = 0  # metin, vurgu çizgisiyle aynı hizada başlasın
    return frame


def _fill_shape(shape, color: RGBColor) -> None:
    """Şekli düz renkle doldurur; kenarlık ve gölgeyi kaldırır."""
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    shape.shadow.inherit = False


def _style_font(font, size: int, color: RGBColor, name: str, bold: bool = False) -> None:
    font.name = name
    font.size = Pt(size)
    font.bold = bold
    font.color.rgb = color


def _centered(width: int) -> int:
    """Verilen genişlikteki bir şekli yatayda ortalamak için gereken sol konum."""
    return (SLIDE_WIDTH - width) // 2
