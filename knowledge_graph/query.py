"""
knowledge_graph/query.py — Multi-hop traversal and semantic query engine over the
Charaka IP Knowledge Graph.
"""

from typing import Any
import networkx as nx
from knowledge_graph.builder import get_knowledge_graph
from knowledge_graph.schema import EdgeType


def _score_node_relevance(
    node_id: str,
    data: dict[str, Any],
    query_lower: str,
    ip_type: str,
    jurisdiction: str,
) -> float:
    """Heuristic relevance scoring for knowledge graph nodes."""
    score = 0.0
    text_corpus = f"{data.get('name', '')} {data.get('description', '')} {data.get('citation', '')}".lower()

    # Exact term matches
    keywords = [
        "section 3(p)", "3(p)", "traditional knowledge", "tkdl",
        "biodiversity", "nba", "clearance", "abs", "nagoya", "trips",
        "ayurveda", "ayush", "rule 158-b", "patent", "admixture", "synergy",
        "section 3(e)", "section 3(d)", "trade mark", "trademark", "gi", "copyright"
    ]
    for kw in keywords:
        if kw in query_lower and kw in text_corpus:
            score += 2.5

    # IP type affinity
    node_ip = data.get("ip_type", "general")
    if ip_type and node_ip == ip_type:
        score += 2.0
    elif ip_type == "general":
        score += 0.5

    # Jurisdiction match
    node_jur = data.get("jurisdiction", "IN")
    if jurisdiction == "BOTH" or node_jur == jurisdiction:
        score += 1.0

    return score


def query_knowledge_graph(
    query: str,
    ip_type: str = "general",
    jurisdiction: str = "BOTH",
    abs_required: bool = False,
    tkdl_required: bool = False,
    max_nodes: int = 5,
) -> list[dict[str, Any]]:
    """
    Execute multi-hop traversal on the knowledge graph based on query intent.

    Returns a list of structured graph findings:
    [
        {
            "node_id": str,
            "title": str,
            "citation": str,
            "statutory_text": str,
            "relationships": [
                {
                    "relation": str,
                    "target_title": str,
                    "description": str,
                    "mandatory": bool,
                }
            ]
        }
    ]
    """
    g = get_knowledge_graph()
    query_lower = query.lower()

    # Special intent boosters
    boost_nodes: set[str] = set()
    if "3(p)" in query_lower or "traditional knowledge" in query_lower or tkdl_required:
        boost_nodes.update(["SEC_PATENTS_3P", "DB_TKDL"])
    if "ayurved" in query_lower or "formulation" in query_lower or "patent" in query_lower:
        boost_nodes.update(["SEC_PATENTS_3P", "SEC_PATENTS_3E"])
    if abs_required or "nagoya" in query_lower or "nba" in query_lower or "biodiversity" in query_lower or "biological" in query_lower:
        boost_nodes.update(["SEC_BDA_6_CLEARANCE", "AUTH_NBA", "INTL_NAGOYA_PROTOCOL", "FORM_NBA_III"])
    if "licensing" in query_lower or "rule 158" in query_lower or "asu" in query_lower:
        boost_nodes.update(["RULE_AYUSH_158B", "DB_API_PHARMACOPOEIA"])

    # Score all nodes
    scored_nodes = []
    for node_id, data in g.nodes(data=True):
        score = _score_node_relevance(node_id, data, query_lower, ip_type, jurisdiction)
        if node_id in boost_nodes:
            score += 5.0
        if score > 0:
            scored_nodes.append((score, node_id, data))

    scored_nodes.sort(key=lambda x: x[0], reverse=True)
    top_candidates = [item[1] for item in scored_nodes[:max_nodes]]

    results = []
    for node_id in top_candidates:
        node_data = g.nodes[node_id]

        # Multi-hop: collect outgoing and incoming mandatory relationships
        relations = []

        # Outgoing edges
        for _, target, edge_data in g.out_edges(node_id, data=True):
            target_data = g.nodes.get(target, {})
            relations.append({
                "direction": "out",
                "relation": edge_data.get("edge_type", EdgeType.CITES),
                "target_title": target_data.get("name", target),
                "target_citation": target_data.get("citation", ""),
                "description": edge_data.get("description", ""),
                "mandatory": edge_data.get("mandatory", False),
            })

        # Incoming edges (e.g. databases that act as prior art, or statutes that mandate clearance)
        for source, _, edge_data in g.in_edges(node_id, data=True):
            source_data = g.nodes.get(source, {})
            relations.append({
                "direction": "in",
                "relation": edge_data.get("edge_type", EdgeType.CITES),
                "target_title": source_data.get("name", source),
                "target_citation": source_data.get("citation", ""),
                "description": edge_data.get("description", ""),
                "mandatory": edge_data.get("mandatory", False),
            })

        results.append({
            "node_id": node_id,
            "title": node_data.get("name", node_id),
            "node_type": node_data.get("node_type", ""),
            "citation": node_data.get("citation", ""),
            "description": node_data.get("description", ""),
            "relationships": relations,
        })

    return results


def format_kg_insights(kg_results: list[dict[str, Any]]) -> str:
    """
    Format knowledge graph traversal results into a clear legal relation block
    for injection into researcher snippets and drafter context.
    """
    if not kg_results:
        return ""

    lines = ["--- Knowledge Graph Statutory Topologies & Mandatory Linkages ---"]
    for item in kg_results:
        lines.append(f"• Provision / Entity: {item['title']} ({item['citation']})")
        lines.append(f"  Summary: {item['description']}")
        for rel in item.get("relationships", []):
            mand_tag = " [MANDATORY COMPLIANCE]" if rel.get("mandatory") else ""
            lines.append(
                f"  └─ ({rel['relation']}{mand_tag}) ──> {rel['target_title']}: {rel['description']}"
            )
    return "\n".join(lines)
