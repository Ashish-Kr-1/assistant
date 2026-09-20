"""
orchestration/drafter.py — Node 4: Legal answer drafting.

Drafts a grounded legal answer from the source catalog, with:
  - Strict inline [n] citation markers after every factual sentence
  - Jurisdiction-separated sections when resolved_jurisdiction == "BOTH"
  - Answer written in the user's detected language/script
  - No model-generated Sources heading or list (that is code-injected by presenter)
"""

from orchestration.state import OrchestratorState, SourceItem

_MAX_SNIPPET_CHARS = 600    # truncate long snippets to keep prompt manageable


def _build_sources_block(catalog: dict[int, SourceItem]) -> str:
    """Format the source catalog as a numbered block for the drafter prompt."""
    lines = []
    for n, item in catalog.items():
        snippet = item["content"][:_MAX_SNIPPET_CHARS].replace("\n", " ")
        lines.append(f"[{n}] {item['title']}\n    Source: {item['url']}\n    Snippet: {snippet}")
    return "\n\n".join(lines)


_DRAFTER_SYSTEM = """\
You are a senior Indian IP law researcher and Ayurveda/AYUSH regulatory specialist
working as part of Charaka IP, a legal research assistant.

You are given numbered source snippets retrieved from authoritative legal documents
(statutes, treaties, pharmacopoeial standards, regulatory guidelines). Write a
precise, well-structured legal answer using ONLY those sources.

Citation rules (MOST IMPORTANT — follow exactly):
- Every sentence that states a fact MUST end with the bracket tag of the source it
  comes from, e.g.: "Section 3(p) bars the patenting of traditional knowledge [1]."
- If a sentence draws on multiple sources: "[2][3]" — not "[2,3]".
- Use the exact numbers from the source list. Never invent or renumber.
- Do NOT write a Sources heading or list — that is added automatically.

Jurisdiction rules:
- If jurisdiction is "BOTH": write two clearly separated sections:
    === India ===
    [Indian statutory analysis]

    === International ===
    [International treaty analysis]
- If jurisdiction is "IN": only Indian law.
- If jurisdiction is "INTL": only international law.

No-results rule:
- If the sources contain no relevant information, say so plainly in the user's
  language. Do not answer from your own general knowledge.

Language rule:
- Write the final answer in the language specified. Keep [n] citation markers as
  plain bracketed numbers in every language.
"""


def drafter_node(state: OrchestratorState, model) -> OrchestratorState:
    """
    LangGraph node. Produces a cited legal draft from the source catalog.
    """
    catalog = state.get("source_catalog", {})
    language = state.get("language_name", "English")
    jurisdiction = state.get("resolved_jurisdiction", "BOTH")
    question = state["raw_question"]
    english_query = state.get("english_query", question)
    retry_feedback = state.get("verification_feedback")

    if not catalog:
        no_results_msg = (
            f"No authoritative sources were found for this query. "
            f"Please consult a registered patent agent or IP attorney for: {question}"
        )
        return {"draft_answer": no_results_msg}

    sources_block = _build_sources_block(catalog)

    # Build user message
    user_parts = [
        f"User's question (in {language}): {question}",
        f"English search query used: {english_query}",
        f"Jurisdiction scope: {jurisdiction}",
        f"",
        f"Source snippets:",
        sources_block,
        f"",
        f"Write the answer in {language}. Follow all citation, jurisdiction, and language rules exactly.",
    ]

    if jurisdiction == "BOTH":
        user_parts.append(
            "\nMANDATORY TWO-SECTION FORMAT:\n"
            "Because jurisdiction scope is 'BOTH', you MUST divide your answer into two clearly demarcated sections:\n\n"
            "=== India ===\n"
            "[Detailed analysis under Indian law, Patents Act, BDA, AYUSH regulations, citing Indian sources with [n] markers]\n\n"
            "=== International ===\n"
            "[Detailed analysis under international treaties, TRIPS, PCT, Nagoya Protocol, CBD, foreign guidelines with [n] markers]\n"
        )
    elif jurisdiction == "IN":
        user_parts.append("\nMANDATORY SCOPE: Focus exclusively on Indian statutory law and regulations with inline [n] citations.")
    elif jurisdiction == "INTL":
        user_parts.append("\nMANDATORY SCOPE: Focus exclusively on International law, treaties, and comparative frameworks with inline [n] citations.")

    # Domain specialist context
    sub_agent_insights = []
    ip_type = state.get("ip_type", "general")
    if ip_type == "patent":
        from orchestration.sub_agents.patent_agent import PATENT_EXPERT_PROMPT
        sub_agent_insights.append(PATENT_EXPERT_PROMPT)
    elif ip_type == "trademark":
        from orchestration.sub_agents.trademark_agent import TRADEMARK_EXPERT_PROMPT
        sub_agent_insights.append(TRADEMARK_EXPERT_PROMPT)
    elif ip_type == "gi":
        from orchestration.sub_agents.gi_agent import GI_EXPERT_PROMPT
        sub_agent_insights.append(GI_EXPERT_PROMPT)
    elif ip_type == "copyright":
        from orchestration.sub_agents.copyright_agent import COPYRIGHT_EXPERT_PROMPT
        sub_agent_insights.append(COPYRIGHT_EXPERT_PROMPT)
    elif ip_type == "ayush":
        from orchestration.sub_agents.ayush_agent import AYUSH_EXPERT_PROMPT
        sub_agent_insights.append(AYUSH_EXPERT_PROMPT)
    elif ip_type == "abs":
        from orchestration.sub_agents.abs_agent import ABS_EXPERT_PROMPT
        sub_agent_insights.append(ABS_EXPERT_PROMPT)
    elif ip_type == "tkdl":
        from orchestration.sub_agents.tkdl_agent import TKDL_EXPERT_PROMPT
        sub_agent_insights.append(TKDL_EXPERT_PROMPT)

    if state.get("_abs_flag"):
        from orchestration.sub_agents.abs_agent import ABS_EXPERT_PROMPT
        if ABS_EXPERT_PROMPT not in sub_agent_insights:
            sub_agent_insights.append(ABS_EXPERT_PROMPT)

    if state.get("_tkdl_flag"):
        from orchestration.sub_agents.tkdl_agent import TKDL_EXPERT_PROMPT
        if TKDL_EXPERT_PROMPT not in sub_agent_insights:
            sub_agent_insights.append(TKDL_EXPERT_PROMPT)

    if sub_agent_insights:
        user_parts.append("\n--- Specialized Legal Domain Standards ---\n" + "\n\n".join(sub_agent_insights))

    kg_insights = state.get("kg_insights")
    if kg_insights:
        user_parts.append(f"\n{kg_insights}")

    if retry_feedback:
        user_parts.append(
            f"\n--- REVISION REQUIRED ---\n"
            f"A citation verifier flagged the following issues with your previous draft:\n"
            f"{retry_feedback}\n"
            f"Fix ONLY the flagged issues. Do not change any other part of the answer."
        )

    user_message = "\n".join(user_parts)

    response = model.invoke([
        {"role": "system", "content": _DRAFTER_SYSTEM},
        {"role": "user", "content": user_message},
    ])

    # Extract text from content (handles both str and list-of-blocks providers)
    content = response.content
    if isinstance(content, str):
        draft = content
    elif isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") in (None, "text"):
                parts.append(block.get("text", ""))
        draft = "".join(parts)
    else:
        draft = str(content)

    return {"draft_answer": draft.strip()}
