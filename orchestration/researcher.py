"""
orchestration/researcher.py — Node 3: Multi-source legal retrieval.

Retrieval strategy (in priority order):
  1. Corpus RAG (ChromaDB): search the persistent, authoritative legal corpus.
     Filtered by ip_type and resolved_jurisdiction for precision.
  2. Tavily web search (fallback): live web search using the English query.
     Used when the corpus returns < MIN_CORPUS_RESULTS relevant chunks.

Query decomposition:
  For complex legal questions (e.g. "Can I patent an Ayurvedic formulation?")
  the researcher generates up to 3 targeted sub-queries to surface all relevant
  statutory provisions (patent exclusions, BDA clearance, TKDL prior art separately).

Output:
  source_catalog: dict[int, SourceItem] — immutable numbered source list used
  by drafter for inline [n] citations and by verifier for grounding checks.
"""

import re
from pydantic import BaseModel, Field
from langchain_tavily import TavilySearch
from langchain_core.tools import StructuredTool

from corpus.store import similarity_search, corpus_count
from orchestration.state import OrchestratorState, SourceItem

_MIN_CORPUS_RESULTS = 3   # fall back to Tavily if corpus returns fewer than this
_MAX_CORPUS_RESULTS = 8   # max chunks to pull from corpus per query
_MAX_TAVILY_RESULTS = 5   # max results from Tavily fallback
_MAX_QUERIES = 3          # max sub-queries to generate for a complex question


# ── Query decomposition schema ─────────────────────────────────────────────────

class QueryDecomposition(BaseModel):
    queries: list[str] = Field(
        ...,
        description=(
            "List of 1–3 focused English search queries that together cover the full "
            "legal question. Each query should target one statutory or regulatory aspect."
        ),
    )


_DECOMPOSE_SYSTEM = """\
You are a legal search strategist for an Indian IP law assistant.
Given a legal question and target jurisdiction scope, decompose it into 1–3 focused English search queries.
Each query should target a distinct statutory or regulatory aspect.

Rules:
- Use precise legal terminology (act names, section numbers, treaty names).
- Keep queries concise and keyword-focused (not full sentences).
- Maximum 3 queries. For simple questions, 1 is enough.
- If jurisdiction scope is 'BOTH', ensure queries cover both Indian domestic law and international treaties/frameworks where relevant.
- If jurisdiction scope is 'IN', focus exclusively on Indian statutes.
- If jurisdiction scope is 'INTL', focus exclusively on international conventions/treaties.

Examples:
  "Can I patent a traditional Ayurvedic formulation?" (Scope: BOTH)
  → ["Indian Patents Act Section 3p traditional knowledge exclusion",
     "Biological Diversity Act Section 6 NBA clearance before patent filing",
     "TRIPS Article 27 traditional medicine patentability international"]

  "What is the Nagoya Protocol?" (Scope: INTL)
  → ["Nagoya Protocol Access Benefit Sharing CBD overview"]

  "How do I register a trade mark in India?" (Scope: IN)
  → ["Trade Marks Act 1999 registration procedure India",
     "IP India trade mark application process"]
"""


def _decompose_queries(question: str, jurisdiction: str, model) -> list[str]:
    """Use the LLM to generate focused sub-queries for complex legal questions."""
    decomposer = model.with_structured_output(QueryDecomposition)
    prompt = f"Question: {question}\nTarget Jurisdiction Scope: {jurisdiction}"
    result: QueryDecomposition = decomposer.invoke([
        {"role": "system", "content": _DECOMPOSE_SYSTEM},
        {"role": "user", "content": prompt},
    ])
    return (result.queries or [question])[:_MAX_QUERIES]


def _rag_search(
    queries: list[str],
    jurisdiction: str,
    ip_type: str,
) -> dict[int, SourceItem]:
    """
    Run RAG retrieval from the corpus vector store.
    Returns a numbered source catalog starting at 1.
    Deduplicates by URL.
    """
    if corpus_count() == 0:
        return {}

    jur_filter = None if jurisdiction == "BOTH" else jurisdiction
    seen_urls: set[str] = set()
    catalog: dict[int, SourceItem] = {}

    for query in queries:
        results = similarity_search(
            query=query,
            n_results=_MAX_CORPUS_RESULTS,
            jurisdiction=jur_filter,
            ip_type=ip_type if ip_type != "general" else None,
        )
        for r in results:
            url = r["source_url"] or r["source_name"]
            if url in seen_urls:
                continue
            seen_urls.add(url)
            n = len(catalog) + 1
            catalog[n] = SourceItem(
                number=n,
                title=r["source_name"] or url,
                url=url,
                content=r["text"],
            )

    return catalog


def _tavily_search(queries: list[str]) -> dict[int, SourceItem]:
    """
    Fallback: live Tavily web search.
    Returns a numbered source catalog starting at 1.
    """
    tavily = TavilySearch(max_results=_MAX_TAVILY_RESULTS, topic="general", search_depth="advanced")
    seen_urls: set[str] = set()
    catalog: dict[int, SourceItem] = {}

    for query in queries:
        try:
            raw = tavily.invoke({"query": query})
            results = raw.get("results") if isinstance(raw, dict) else []
            for r in (results or []):
                url = r.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                n = len(catalog) + 1
                catalog[n] = SourceItem(
                    number=n,
                    title=r.get("title") or url,
                    url=url,
                    content=r.get("content", ""),
                )
        except Exception:
            continue

    return catalog


def _renumber(catalog: dict[int, SourceItem]) -> dict[int, SourceItem]:
    """Ensure catalog is contiguously numbered from 1."""
    return {i: SourceItem(**{**item, "number": i}) for i, item in enumerate(catalog.values(), start=1)}


def researcher_node(state: OrchestratorState, model) -> OrchestratorState:
    """
    LangGraph node. Performs multi-source retrieval:
      1. Decompose the query into sub-queries
      2. Search the RAG corpus
      3. Fall back to Tavily if corpus is thin
      4. Merge, deduplicate, and renumber the source catalog
    """
    question = state.get("english_query") or state["raw_question"]
    jurisdiction = state.get("resolved_jurisdiction", "BOTH")
    ip_type = state.get("ip_type", "general")

    # Step 1: Decompose
    queries = _decompose_queries(question, jurisdiction, model)

    # Step 2: RAG retrieval
    catalog = _rag_search(queries, jurisdiction, ip_type)

    # Step 3: Tavily fallback if corpus too thin
    if len(catalog) < _MIN_CORPUS_RESULTS:
        tavily_catalog = _tavily_search(queries)
        # Append Tavily results after corpus results, avoiding URL duplicates
        corpus_urls = {item["url"] for item in catalog.values()}
        for item in tavily_catalog.values():
            if item["url"] not in corpus_urls:
                n = len(catalog) + 1
                catalog[n] = SourceItem(**{**item, "number": n})

    # Step 4: Query Knowledge Graph for multi-hop statutory linkages
    try:
        from knowledge_graph.query import query_knowledge_graph, format_kg_insights
        kg_results = query_knowledge_graph(
            query=question,
            ip_type=ip_type,
            jurisdiction=jurisdiction,
            abs_required=state.get("_abs_flag", False),
            tkdl_required=state.get("_tkdl_flag", False),
            max_nodes=4,
        )
        kg_insights = format_kg_insights(kg_results)

        # Append top KG provisions into catalog so drafter can cite statutory relationships
        existing_urls = {item["url"] for item in catalog.values()}
        for node in kg_results[:2]:
            url = node.get("citation") or f"https://www.indiacode.nic.in"
            if url not in existing_urls:
                existing_urls.add(url)
                rel_summary = "; ".join(
                    f"{r['relation']} -> {r['target_title']}"
                    for r in node.get("relationships", [])[:2]
                )
                content = f"{node.get('description', '')}. Statutory relationships: {rel_summary}."
                n = len(catalog) + 1
                catalog[n] = SourceItem(
                    number=n,
                    title=f"Statutory Framework: {node.get('title', '')}",
                    url=url,
                    content=content,
                )
    except Exception:
        kg_insights = ""

    # Step 5: Query Live Connectors (WIPO Lex, IP India, Manupatra, SCC Online)
    try:
        from corpus.connectors import (
            IPIndiaLiveConnector,
            ManupatraConnector,
            SCCOnlineConnector,
            WIPOLexConnector,
        )

        connector_results = []
        if jurisdiction in ("INTL", "BOTH"):
            connector_results.extend(WIPOLexConnector().search_treaties(question))

        if jurisdiction in ("IN", "BOTH"):
            ip_con = IPIndiaLiveConnector()
            connector_results.extend(ip_con.search_inpass(question))
            connector_results.extend(ip_con.search_gi_registry(question))
            connector_results.extend(ManupatraConnector().search_case_law(question))
            connector_results.extend(SCCOnlineConnector().search_headnotes(question))

        existing_urls = {item["url"] for item in catalog.values()}
        for item in connector_results[:3]:
            url = item.get("source_url", "")
            if url and url not in existing_urls:
                existing_urls.add(url)
                n = len(catalog) + 1
                catalog[n] = SourceItem(
                    number=n,
                    title=item.get("source_name", url),
                    url=url,
                    content=item.get("text", ""),
                )
    except Exception:
        pass

    # Step 6: Renumber contiguously
    catalog = _renumber(catalog)

    return {
        "search_queries": queries,
        "source_catalog": catalog,
        "kg_insights": kg_insights,
    }
