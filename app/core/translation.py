"""Translation for the English-pivot retrieval arm of the experiment.

Native arm (retrieval_lang='bn'): embed Bangla text directly.
Pivot arm  (retrieval_lang='en'): translate Bangla -> English, then embed/retrieve in
English space. This isolates *where* multilingual retrieval helps or hurts.

Implemented prompt-based via the configured LLM to avoid an extra dependency. For
reproducible large runs, swap in a dedicated MT system (e.g. NLLB / Google Translate)
and cache the translations — see the note in run_eval.py.
"""
from __future__ import annotations

from app.core.llm import LLMProvider

_SYS = "You are a precise translator. Translate the user's text to {target}. Output only the translation, nothing else."


def translate(text: str, target_lang: str, llm: LLMProvider) -> str:
    target = "English" if target_lang == "en" else "Bangla"
    return llm.generate(_SYS.format(target=target), text, temperature=0.0)
