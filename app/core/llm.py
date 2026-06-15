"""LLM providers behind a common interface, used both for answer generation and as
the LLM-as-judge in evaluation.

MockLLM lets the whole pipeline run offline (no API key) for plumbing/CI tests — it
returns a deterministic grounded-looking answer citing [1]. Swap in a real provider
for actual Bangla generation quality.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.config import Settings


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system: str, user: str, temperature: float = 0.0) -> str: ...


class OpenAILLM(LLMProvider):
    def __init__(self, model: str, api_key: str):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(self, system, user, temperature=0.0):
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=temperature,
        )
        return resp.choices[0].message.content.strip()


class GeminiLLM(LLMProvider):
    def __init__(self, model: str, api_key: str):
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def generate(self, system, user, temperature=0.0):
        resp = self.model.generate_content(
            f"{system}\n\n{user}",
            generation_config={"temperature": temperature},
        )
        return resp.text.strip()


class GroqLLM(LLMProvider):
    """Groq is OpenAI-API compatible and hosts open models (Llama, etc.)."""
    def __init__(self, model: str, api_key: str):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        self.model = model

    def generate(self, system, user, temperature=0.0):
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=temperature,
        )
        return resp.choices[0].message.content.strip()


class MockLLM(LLMProvider):
    """Offline stand-in. For generation it returns the first context line + a [1]
    citation; for judging it returns '1' (used by tests / smoke runs only)."""
    def generate(self, system, user, temperature=0.0):
        if "JUDGE" in system.upper():
            return "1"
        first_line = next((ln for ln in user.splitlines() if ln.strip()), "")
        return f"{first_line[:160]} [1]"


def get_llm(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider
    if provider == "mock":
        return MockLLM()
    if provider == "gemini":
        return GeminiLLM(settings.llm_model, settings.gemini_api_key)
    if provider == "groq":
        return GroqLLM(settings.llm_model, settings.groq_api_key)
    return OpenAILLM(settings.llm_model, settings.openai_api_key)
