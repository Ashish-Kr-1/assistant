"""
orchestration/graph.py — LangGraph StateGraph compiler for Charaka IP.

Node sequence:
  gatekeeper → router → researcher → drafter → verifier → presenter
                  ↑_________retry_loop (max 1)___|

Conditional edges:
  after gatekeeper: if out-of-scope → refusal node (short-circuit)
                    if in-scope     → router → researcher → drafter → verifier

  after verifier:   if verified OR retry_count >= 1 → presenter
                    if not verified AND retry_count == 0 → drafter (retry with feedback)
"""

from functools import partial

from langgraph.graph import END, StateGraph

from orchestration.gatekeeper import gatekeeper_node
from orchestration.router import router_node
from orchestration.researcher import researcher_node
from orchestration.drafter import drafter_node
from orchestration.verifier import verifier_node
from orchestration.presenter import presenter_node, refusal_node
from orchestration.state import OrchestratorState, Route

_MAX_RETRIES = 1


# ── Conditional edge functions ─────────────────────────────────────────────────

def _route_after_gatekeeper(state: OrchestratorState) -> str:
    """After gatekeeper: refuse if out-of-scope, else continue to router."""
    if not state.get("is_in_scope", True):
        return Route.REFUSE
    return "router"


def _route_after_verifier(state: OrchestratorState) -> str:
    """After verifier: retry drafter once if verification failed and catalog exists, else present."""
    retry_count = state.get("retry_count", 0)
    is_verified = state.get("is_verified", True)
    catalog = state.get("source_catalog", {})

    if not is_verified and bool(catalog) and retry_count < _MAX_RETRIES:
        return "retry_drafter"
    return "presenter"


def _retry_drafter_node(state: OrchestratorState, model) -> OrchestratorState:
    """Increment retry counter and re-run the drafter with verification feedback."""
    current_retry = state.get("retry_count", 0)
    new_retry_count = current_retry + 1
    state_with_retry = {**state, "retry_count": new_retry_count}
    result = drafter_node(state_with_retry, model)
    return {**result, "retry_count": new_retry_count}


# ── Graph builder ──────────────────────────────────────────────────────────────

def build_graph(model):
    """
    Build and compile the Charaka IP LangGraph StateGraph.

    Args:
        model: A LangChain chat model instance (Cohere or OpenAI).

    Returns:
        A compiled LangGraph runnable.
    """
    graph = StateGraph(OrchestratorState)

    # ── Register nodes (bind model where needed) ───────────────────────────────
    graph.add_node("gatekeeper",    partial(gatekeeper_node,  model=model))
    graph.add_node("router",        partial(router_node,       model=model))
    graph.add_node("researcher",    partial(researcher_node,   model=model))
    graph.add_node("drafter",       partial(drafter_node,      model=model))
    graph.add_node("verifier",      partial(verifier_node,     model=model))
    graph.add_node("retry_drafter", partial(_retry_drafter_node, model=model))
    graph.add_node("presenter",     partial(presenter_node,    model=model))
    graph.add_node("refusal",       refusal_node)

    # ── Entry point ────────────────────────────────────────────────────────────
    graph.set_entry_point("gatekeeper")

    # ── Edges ──────────────────────────────────────────────────────────────────
    graph.add_conditional_edges(
        "gatekeeper",
        _route_after_gatekeeper,
        {
            Route.REFUSE: "refusal",
            "router": "router",
        },
    )
    graph.add_edge("router",        "researcher")
    graph.add_edge("researcher",    "drafter")
    graph.add_edge("drafter",       "verifier")
    graph.add_conditional_edges(
        "verifier",
        _route_after_verifier,
        {
            "retry_drafter": "retry_drafter",
            "presenter": "presenter",
        },
    )
    graph.add_edge("retry_drafter", "verifier")    # re-verify revised draft to update confidence & flags
    graph.add_edge("presenter",     END)
    graph.add_edge("refusal",       END)

    return graph.compile()


# ── Public API ─────────────────────────────────────────────────────────────────

def run(
    question: str,
    model,
    jurisdiction: str = "both",
) -> OrchestratorState:
    """
    Run the full Charaka IP orchestration pipeline for a single question.

    Args:
        question: The user's raw question (any language).
        model: A LangChain chat model instance.
        jurisdiction: "india", "international", or "both".

    Returns:
        The final OrchestratorState dict after all nodes have run.
    """
    compiled = build_graph(model)
    initial_state: OrchestratorState = {
        "raw_question": question,
        "jurisdiction": jurisdiction,
        "retry_count": 0,
        "is_in_scope": True,
    }
    return compiled.invoke(initial_state)
