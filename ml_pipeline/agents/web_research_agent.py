"""
Live Web Research Agent (multilingual detection + Tavily-grounded citations).

Ported from the standalone "Charak IP" prototype (~/Desktop/Charak IP/agent.py) into this
repo's conventions: it reuses ml_pipeline.crag.llm_factory.get_llm() instead of building its
own model, so it inherits the same provider fallback (Cohere -> OpenAI -> Gemini -> None) and
never assumes an API key is present (CLAUDE.md rule 5) — every entry point degrades to a
plain, honest "unavailable" result instead of raising when a key is missing.

Two things this module exists to provide:
1. Real language detection: a structured-output LLM call identifies the user's language and
   script (Devanagari Hindi vs romanized "Hinglish" vs English) and produces an English query
   for retrieval. Falls back to a Devanagari-regex heuristic when no LLM is configured.
2. Live web search with structurally-unfakeable citations: every Tavily result is tagged with
   a [n] marker as it's returned, and the final source list is rebuilt in code from that same
   bookkeeping — a citation can only ever point at a URL a search actually returned, mirroring
   Charak IP's design exactly. Never trusted from the model's own prose.
"""

import os
import re
import logging
from typing import Optional

from pydantic import BaseModel, Field

from ml_pipeline.crag.llm_factory import get_llm

logger = logging.getLogger("web_research_agent")

_DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")

# Longer-running than a quick single-shot detection/generation call: translating a full answer,
# or a tool-calling search agent loop, needs more than the fast LLM_TIMEOUT_SECONDS default that
# the rest of the pipeline relies on for a quick heuristic fallback (llm_factory.get_llm).
_LONG_CALL_TIMEOUT_SECONDS = float(os.getenv("WEB_RESEARCH_TIMEOUT_SECONDS", "25"))

_SCOPE_SYSTEM_PROMPT = """You are Charak IP, a research assistant scoped ONLY to these topics:
1. Intellectual property law: patents, trademarks, geographical indications (GI), and copyright.
2. Ayurveda and AYUSH regulatory matters (licensing, classification, traditional knowledge protection, etc.).

Scope rule: if a question is not about one of those topics, politely decline and say this
assistant only covers IP law and Ayurveda/AYUSH regulatory topics. Do not answer the off-topic
question even partially, and do not call the search tool for it.

Research rule: for every in-scope question, you MUST call the `web_search` tool at least once
before answering, using English search terms. Never answer an in-scope question from memory
alone. You may call the tool again with a refined query if the first results are insufficient.

Citation rule — this is the most important rule, follow it exactly:
- Every result the `web_search` tool returns is already tagged with a marker like [1], [2], [3]
  at the start of that result.
- Every sentence in your answer that states a fact from a result MUST end with that exact same
  marker, e.g.: "The Nagoya Protocol supplements the CBD [1]. It entered into force in 2014 [2]."
- Copy the bracket numbers exactly as given. Never invent your own numbering, never renumber,
  and never cite a number that wasn't in the tool output.
- Do NOT write your own "Sources" heading or list at the end of your answer — the application
  appends a verified one automatically after your response.

No-relevant-results rule: if the search tool returns no usable results for the question, say so
plainly and do not include any citation markers or answer from your own general knowledge instead.
"""

_DETECTION_SYSTEM_PROMPT = """You are a language pre-processing step for a research assistant.
Given a user's question, fill in:
- language_name: the human language AND script of the input, e.g. "English", "Hindi (Devanagari
  script)", "Hinglish (Hindi words spelled in Latin/Roman letters, mixed with English)".
- is_english: true only if the input is plain English.
- english_query: the question rewritten as an effective English web search query (concise and
  keyword-focused, not necessarily a full grammatical sentence).

Judge language_name by the ACTUAL SCRIPT of the input text: if the input contains Devanagari
characters, it is Hindi (Devanagari) — never call Devanagari text "Hinglish". Only call it
"Hinglish" when the input itself is written in Latin/Roman letters but uses Hindi words/grammar.
"""


class LanguageDetection(BaseModel):
    language_name: str = Field(description="Human language and script the user wrote in")
    is_english: bool = Field(description="True if the question is already in English")
    english_query: str = Field(description="The question rewritten as an English web search query")
    heuristic_only: bool = Field(
        default=False,
        description="True when detection fell back to a regex heuristic because no LLM was available",
    )


def detect_language(text: str, llm=None) -> LanguageDetection:
    """Detects the user's language/script. Uses a structured-output LLM call when a model is
    available; otherwise falls back to a deterministic Devanagari-script regex so the caller
    never crashes or silently mistranslates just because no API key is configured."""
    text = text or ""
    llm = llm if llm is not None else get_llm(temperature=0.0)

    if llm is not None:
        try:
            detector = llm.with_structured_output(LanguageDetection)
            result = detector.invoke(
                [
                    {"role": "system", "content": _DETECTION_SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ]
            )
            if _DEVANAGARI_RE.search(text) and "hinglish" in result.language_name.lower():
                result = result.model_copy(update={"language_name": "Hindi (Devanagari script)"})
            return result
        except Exception as e:
            logger.warning(f"LLM language detection failed, using heuristic fallback: {e}")

    if _DEVANAGARI_RE.search(text):
        return LanguageDetection(
            language_name="Hindi (Devanagari script)",
            is_english=False,
            english_query=text,
            heuristic_only=True,
        )
    return LanguageDetection(
        language_name="English",
        is_english=True,
        english_query=text,
        heuristic_only=True,
    )


def web_search_available() -> bool:
    return bool(os.getenv("TAVILY_API_KEY"))


_NATIONAL_DOMAINS = ("indiacode.nic.in", "ipindia.gov.in", "indiankanoon.org", ".gov.in", "nba.nic.in")
_INTERNATIONAL_DOMAINS = ("wipo.int", "wto.org", "cbd.int", "un.org", "wipolex.wipo.int")


def _guess_jurisdiction(url: str) -> Optional[str]:
    url = (url or "").lower()
    if any(d in url for d in _NATIONAL_DOMAINS):
        return "national"
    if any(d in url for d in _INTERNATIONAL_DOMAINS):
        return "international"
    return None


def _build_search_tool():
    """Builds a fresh web_search tool plus its citation-state dict. Fresh per call so numbering
    always restarts at 1. Results come back pre-tagged with [n] markers, and the real
    (title, url) pairs are recorded in `sources` as they're handed out, keyed by that same
    number — the single source of truth used later to rebuild the real citation list."""
    from langchain_tavily import TavilySearch

    tavily = TavilySearch(max_results=5, topic="general", search_depth="advanced")
    sources: dict[int, dict] = {}
    url_to_number: dict[str, int] = {}

    def web_search(query: str) -> str:
        raw = tavily.invoke({"query": query})
        results = raw.get("results") if isinstance(raw, dict) else None
        if not results:
            return "No results found for this query."
        blocks = []
        for result in results:
            url = result.get("url")
            if not url:
                continue
            content = result.get("content", "")
            if url in url_to_number:
                n = url_to_number[url]
            else:
                n = len(sources) + 1
                url_to_number[url] = n
                sources[n] = {
                    "number": n,
                    "title": result.get("title") or url,
                    "url": url,
                    "jurisdiction": _guess_jurisdiction(url),
                    "content": content,
                }
            blocks.append(f"[{n}] {sources[n]['title']}\n{content}")
        return "\n\n".join(blocks) if blocks else "No results found for this query."

    from langchain_core.tools import StructuredTool

    tool = StructuredTool.from_function(
        func=web_search,
        name="web_search",
        description=(
            "Search the web for current information on IP law or Ayurveda/AYUSH regulatory "
            "topics. Input: an English search query string. Results come back already tagged "
            "like [1], [2] — cite those exact tags in your answer."
        ),
    )
    return tool, sources


_TRAILING_CITATION_LINE_RE = re.compile(r"^\[\d+\]\s.*https?://\S+", re.IGNORECASE)
_CITATION_GROUP_RE = re.compile(r"\[([\d,\s]+)\]")


def _strip_model_written_sources(text: str) -> str:
    """Drops any citation-list block (and its heading line) the model wrote at the end despite
    being told not to. Language-agnostic: looks for the trailing `[n] ... https://...` line
    pattern rather than a literal heading word."""
    lines = text.rstrip().split("\n")
    i = len(lines)
    while i > 0 and _TRAILING_CITATION_LINE_RE.match(lines[i - 1].strip()):
        i -= 1
    if i > 0 and i < len(lines) and 0 < len(lines[i - 1].strip()) <= 40 and "http" not in lines[i - 1]:
        i -= 1
    return "\n".join(lines[:i]).rstrip()


_ANNOTATE_PROMPT = """Below are numbered source snippets and a drafted answer written from them.

Rewrite the answer, inserting an inline citation marker like [1] or [2] immediately after every
sentence that states a fact, using the number of the source snippet that supports it. If a
sentence draws on more than one source, write separate markers like [2][3], not [2,3]. Reuse a
number for multiple sentences if needed. Do not change the wording, meaning, or language of the
answer otherwise. Do not add a Sources list or heading. Do not add a citation to a sentence that
isn't a factual claim (e.g. a plain transition sentence). Return only the annotated answer text,
nothing else.

Source snippets:
{sources_block}

Drafted answer:
{draft}
"""


def _annotate_with_citations(draft: str, sources: dict, llm) -> str:
    """Second pass: asks the model to insert [n] markers into an already-written answer,
    grounded against the numbered source snippets actually returned by the search tool. This
    mechanical annotate-existing-text task is far more reliable than asking a model to remember
    to weave citation tokens into prose while it composes the answer in the same turn it's also
    deciding whether/how to call a tool."""
    sources_block = "\n\n".join(
        f"[{s['number']}] {s['title']}\n{s.get('content', '')[:500]}" for s in sources.values()
    )
    prompt = _ANNOTATE_PROMPT.format(sources_block=sources_block, draft=draft)
    response = llm.invoke([{"role": "user", "content": prompt}])
    return _message_text(response).strip()


def _find_cited_numbers(text: str) -> set[int]:
    numbers = set()
    for group in _CITATION_GROUP_RE.findall(text):
        for part in re.split(r"[,\s]+", group.strip()):
            if part.isdigit():
                numbers.add(int(part))
    return numbers


def _message_text(message) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") in (None, "text"):
                parts.append(block.get("text", ""))
        return "".join(parts)
    return str(content)


def run_web_research(query: str, jurisdiction: str = "national", llm=None) -> dict:
    """Runs one query through a fresh scoped agent with live web search, returning
    {"answer", "citations", "detected_language", "english_query", "used_web_search"}.

    Degrades gracefully (used_web_search=False, no exception) whenever no LLM or no
    TAVILY_API_KEY is configured — the caller decides what to do with an unavailable result.
    """
    llm = llm if llm is not None else get_llm(temperature=0.0, timeout_seconds=_LONG_CALL_TIMEOUT_SECONDS)
    detection = detect_language(query, llm=llm)

    if llm is None or not web_search_available():
        reason = "no LLM provider configured" if llm is None else "TAVILY_API_KEY not configured"
        logger.info(f"Live web research unavailable ({reason}); skipping.")
        return {
            "answer": "",
            "citations": [],
            "detected_language": detection.language_name,
            "english_query": detection.english_query,
            "used_web_search": False,
        }

    try:
        from langchain.agents import create_agent

        search_tool, sources = _build_search_tool()
        agent = create_agent(model=llm, tools=[search_tool], system_prompt=_SCOPE_SYSTEM_PROMPT)

        user_message = (
            f"User's question (written in {detection.language_name}): {query}\n\n"
            f"English translation, for the search tool only: {detection.english_query}\n\n"
            f"Search using English terms. Copy the [n] tags from the search results as your "
            f"citation markers. Do not add a Sources heading or list yourself."
        )
        result = agent.invoke({"messages": [{"role": "user", "content": user_message}]})
        raw_answer = _message_text(result["messages"][-1])
        body = _strip_model_written_sources(raw_answer)

        # The model is unreliable at remembering to weave [n] markers into prose while it's
        # also deciding whether/how to call the search tool in the same turn. A second,
        # mechanical annotate-existing-text pass — grounded against the source snippets the
        # tool actually returned — is far more reliable (mirrors the Charak IP prototype this
        # was ported from). Only worth running if the search actually returned something.
        if sources:
            try:
                annotated = _annotate_with_citations(body, sources, llm)
                if annotated:
                    body = annotated
            except Exception as e:
                logger.warning(f"Citation annotation pass failed, using un-annotated draft: {e}")

        cited_numbers = _find_cited_numbers(body)
        cited_sources = [sources[n] for n in sorted(cited_numbers) if n in sources]

        return {
            "answer": body,
            "citations": cited_sources,
            "detected_language": detection.language_name,
            "english_query": detection.english_query,
            "used_web_search": bool(cited_sources),
        }
    except Exception as e:
        logger.warning(f"Live web research failed, degrading gracefully: {e}")
        return {
            "answer": "",
            "citations": [],
            "detected_language": detection.language_name,
            "english_query": detection.english_query,
            "used_web_search": False,
        }


def translate_answer(text: str, language_name: str, llm=None) -> str:
    """Translates an already-composed answer into the user's language, preserving every
    [chunk_id] / [n] citation marker exactly as-is. Returns the original text unchanged when no
    LLM is available or the language is already English — never raises."""
    if not text or not language_name or language_name.lower().startswith("english"):
        return text

    llm = llm if llm is not None else get_llm(temperature=0.0, timeout_seconds=_LONG_CALL_TIMEOUT_SECONDS)
    if llm is None:
        return text

    prompt = (
        f"Translate the following answer into {language_name}, matching the natural script/style "
        f"a native speaker would use. Do not change, translate, remove, or renumber any bracketed "
        f"citation marker such as [1] or [some_chunk_id] — copy those exactly as they appear. "
        f"Do not add any commentary. Return only the translated text.\n\n{text}"
    )
    try:
        response = llm.invoke(prompt)
        translated = _message_text(response).strip()
        return translated or text
    except Exception as e:
        logger.warning(f"Answer translation failed, keeping original language: {e}")
        return text
