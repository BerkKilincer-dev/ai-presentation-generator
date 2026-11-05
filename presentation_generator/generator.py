"""Sunum üretim adımları: önce plan, sonra içerik.

İşi iki adıma bölmenin nedeni: LLM önce sunumun bütününü (akışı) düşünür,
ardından her slaytı bu akışa uygun şekilde doldurur. Tek seferde
istemekten daha tutarlı sonuç verir.
"""

from .llm import GeminiClient
from .models import DeckContent, Presentation, PresentationPlan, PresentationRequest
from .prompts import build_content_prompt, build_plan_prompt


class PresentationGenerator:
    def __init__(self, llm: GeminiClient):
        self._llm = llm

    def create_plan(self, request: PresentationRequest) -> PresentationPlan:
        """1. adım: konudan slayt başlıklarını ve akışı çıkarır."""
        prompt = build_plan_prompt(request)
        return self._llm.generate(prompt, PresentationPlan)

    def write_content(
        self, request: PresentationRequest, plan: PresentationPlan
    ) -> Presentation:
        """2. adım: her slaytın düzenini, maddelerini ve konuşmacı notunu yazar."""
        prompt = build_content_prompt(request, plan)
        content = self._llm.generate(prompt, DeckContent)
        return Presentation(
            title=plan.title,
            subtitle=plan.subtitle,
            image_query=plan.image_query,
            slides=content.slides,
            takeaways=content.takeaways,
        )

    def generate(self, request: PresentationRequest) -> Presentation:
        """İki adımı arka arkaya çalıştırır."""
        plan = self.create_plan(request)
        return self.write_content(request, plan)
