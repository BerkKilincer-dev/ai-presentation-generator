"""Streamlit web arayüzü.

İki sayfası var:
    Karşılama  konu ve ayarlar girilir, sunum oluşturulur
    Sonuç      slayt önizlemesi, tema seçimi ve indirme

Çalıştırmak için:
    streamlit run app.py
"""

import time
from dataclasses import dataclass
from typing import get_args

import streamlit as st

from presentation_generator.config import ConfigError, load_settings
from presentation_generator.generator import PresentationGenerator
from presentation_generator.images import PixabayClient
from presentation_generator.llm import GeminiClient, LLMError
from presentation_generator.models import Presentation, PresentationRequest, Tone
from presentation_generator.pages import Images, Page, plan_pages
from presentation_generator.pptx_builder import build_pptx, file_name_for
from presentation_generator.themes import DEFAULT_THEME_NAME, THEMES
from ui import components
from ui.preview import render_previews

EXAMPLE_TOPICS = ["Yapay zekâ ve eğitim", "Yenilenebilir enerji", "Uzay keşfi", "Sağlıklı beslenme"]
TONES = list(get_args(Tone))
THEME_ICONS = {"Lacivert": "🔵", "Orman": "🟢", "Mercan": "🔴", "Gece": "⚫"}
PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


@dataclass
class Result:
    """Üretilen sunum. Tema değişince tekrar üretmemek için oturumda saklanır."""

    request: PresentationRequest
    presentation: Presentation
    images: Images
    seconds: float


@st.cache_resource
def get_services() -> tuple[PresentationGenerator, PixabayClient | None]:
    """İstemcileri bir kez oluşturur, sonraki çalıştırmalarda tekrar kullanır."""
    settings = load_settings()
    pixabay = PixabayClient(settings.pixabay_api_key) if settings.pixabay_api_key else None
    return PresentationGenerator(GeminiClient(settings)), pixabay


# --- Butonların tetiklediği işlemler ---------------------------------------


def use_example() -> None:
    """Örnek konulardan biri seçilince konu kutusunu doldurur."""
    if st.session_state.example:
        st.session_state.topic = st.session_state.example


def start_over() -> None:
    """Sonucu silip karşılama sayfasına döner."""
    del st.session_state.result


def regenerate() -> None:
    """Aynı ayarlarla yeni bir sunum oluşturulmasını ister."""
    st.session_state.pending_request = st.session_state.result.request


# --- Karşılama sayfası -----------------------------------------------------


def render_landing(pending_request: PresentationRequest | None) -> None:
    components.hero()
    _, center, _ = st.columns([1, 4, 1])
    with center:
        request = render_form() or pending_request
        if request:
            generate(request)
    components.features()


def render_form() -> PresentationRequest | None:
    """Girdi formunu çizer; gönderilirse kullanıcının isteğini döndürür."""
    with st.form("request_form"):
        topic = st.text_input("Ne hakkında bir sunum hazırlayalım?", key="topic", max_chars=200,
                              placeholder="Örn: Yapay zekânın sağlık sektörüne etkileri")
        with st.expander("⚙️ Sunum ayarları"):
            audience = st.text_input("Hedef kitle", value="Genel izleyici",
                                     help="Örn: Lise öğrencileri, yöneticiler, yazılımcılar")
            tone_col, count_col = st.columns(2)
            tone = tone_col.selectbox("Anlatım tonu", TONES)
            slide_count = count_col.slider("İçerik slaytı sayısı", min_value=3, max_value=10,
                                           value=6, help="Kapak, gündem, özet ve kapanış "
                                                         "slaytları otomatik eklenir.")
        submitted = st.form_submit_button("✨ Sunumumu Oluştur", type="primary", width="stretch")

    st.pills("Fikir mi lazım? Bir örnek seç:", EXAMPLE_TOPICS, key="example", on_change=use_example)

    if not submitted:
        return None
    if len(topic.strip()) < 3:
        st.warning("Lütfen sunumun konusunu yazın.")
        return None
    return PresentationRequest(topic=topic, audience=audience or "Genel izleyici",
                               tone=tone, slide_count=slide_count)


def generate(request: PresentationRequest) -> None:
    """Sunumu adım adım oluşturur; başarılı olursa sonuç sayfasına geçer."""
    started = time.perf_counter()
    try:
        generator, pixabay = get_services()
        with st.status("Sunumun hazırlanıyor...", expanded=True) as status:
            st.write("🧭 Sunumun akışı planlanıyor...")
            plan = generator.create_plan(request)
            st.markdown("\n".join(f"{i}. {s.title}" for i, s in enumerate(plan.slides, start=1)))

            st.write("✍️ Slaytlar ve konuşmacı notları yazılıyor...")
            presentation = generator.write_content(request, plan)

            images = {}
            if pixabay:
                st.write("🖼️ Görseller seçiliyor...")
                images = pixabay.find_all(presentation.photo_queries())

            status.update(label="Sunumun hazır!", state="complete")

    except ConfigError:
        st.error("Uygulama henüz yapılandırılmamış. Lütfen yöneticiyle iletişime geçin.")
        return
    except LLMError as exc:
        st.error("Sunum şu anda oluşturulamadı. Lütfen birkaç saniye sonra tekrar deneyin.")
        with st.expander("Teknik ayrıntılar"):
            st.code(str(exc), language=None)
        return

    st.session_state.result = Result(request, presentation, images, time.perf_counter() - started)
    st.rerun()


# --- Sonuç sayfası ---------------------------------------------------------


def render_result_page(result: Result) -> None:
    presentation = result.presentation
    pages = plan_pages(presentation, result.images)

    brand_col, back_col = st.columns([4, 1], vertical_alignment="center")
    with brand_col:
        components.brand()
    back_col.button("← Yeni sunum", on_click=start_over, width="stretch")

    components.result_header(
        presentation.title, presentation.subtitle,
        meta=f"{len(pages)} slayt · {result.seconds:.0f} saniyede hazırlandı",
    )

    preview_col, panel_col = st.columns([3, 1], gap="large")
    with panel_col:
        theme_name = render_side_panel(result, len(pages))
    with preview_col:
        slides_tab, notes_tab = st.tabs(["Slaytlar", "Konuşmacı notları"])
        with slides_tab:
            st.markdown(render_previews(presentation, THEMES[theme_name], result.images),
                        unsafe_allow_html=True)
        with notes_tab:
            render_notes(pages)


def render_side_panel(result: Result, page_count: int) -> str:
    """Tema seçimi ve indirme; seçilen temanın adını döndürür."""
    with st.container(border=True):
        theme_name = st.radio("Tema", list(THEMES), key="theme",
                              index=list(THEMES).index(DEFAULT_THEME_NAME),
                              format_func=lambda name: f"{THEME_ICONS[name]}  {name}")
        # Tema sadece çizimi etkiler: değişince .pptx API'ye gitmeden yeniden oluşur.
        st.download_button(
            "⬇️ PowerPoint olarak indir",
            data=build_pptx(result.presentation, THEMES[theme_name], result.images),
            file_name=file_name_for(result.presentation.title),
            mime=PPTX_MIME,
            type="primary",
            width="stretch",
        )
        st.caption(f"{page_count} slayt · {len(result.images)} görsel · konuşmacı notları dahil")

    st.button("🔄 Yeniden oluştur", on_click=regenerate, width="stretch",
              help="Aynı konu ve ayarlarla farklı bir sunum oluşturur.")
    return theme_name


def render_notes(pages: list[Page]) -> None:
    """Her içerik slaytının konuşmacı notunu gösterir."""
    st.caption("Bu notlar PowerPoint dosyasında her slaytın not bölümüne de eklenir.")
    for page in pages:
        if page.slide:
            with st.container(border=True):
                st.markdown(f"**{page.number}. {page.slide.title}**")
                st.write(page.slide.notes)


def main() -> None:
    st.set_page_config(page_title="Konudan Sunum Oluşturucu", page_icon="📊", layout="wide")
    components.inject_styles()

    pending_request = st.session_state.pop("pending_request", None)
    if "result" in st.session_state and not pending_request:
        render_result_page(st.session_state.result)
    else:
        render_landing(pending_request)

    components.footer()


main()
