"""
GET /knowledge-graph

Returns a static-but-domain-accurate knowledge graph of Ayurvedic IP entities.
The graph mirrors the schema defined in ml_pipeline/knowledge_graph/schema.py.
When Neo4j is eventually wired, this endpoint can be updated to query the live graph.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/knowledge-graph")
def get_knowledge_graph():
    """
    Returns nodes and edges for the Charaka IP domain knowledge graph.
    Node types: Herb, Formulation, AuthoritativeText, Statute, Section, TreatyArticle, PatentBar
    Edge types mirror KnowledgeGraphSchema.RELATIONSHIPS
    """
    nodes = [
        # ── Herbs ──────────────────────────────────────────────
        {"id": "h1", "label": "Curcuma longa\n(Turmeric)", "type": "Herb", "group": "herb"},
        {"id": "h2", "label": "Withania somnifera\n(Ashwagandha)", "type": "Herb", "group": "herb"},
        {"id": "h3", "label": "Emblica officinalis\n(Amla)", "type": "Herb", "group": "herb"},
        {"id": "h4", "label": "Terminalia chebula\n(Haritaki)", "type": "Herb", "group": "herb"},
        {"id": "h5", "label": "Tinospora cordifolia\n(Giloy)", "type": "Herb", "group": "herb"},
        {"id": "h6", "label": "Boswellia serrata\n(Shallaki)", "type": "Herb", "group": "herb"},

        # ── Formulations ───────────────────────────────────────
        {"id": "f1", "label": "Chyawanprash", "type": "Formulation", "group": "formulation"},
        {"id": "f2", "label": "Triphala", "type": "Formulation", "group": "formulation"},
        {"id": "f3", "label": "Ashwagandha\nStandardized Extract", "type": "Formulation", "group": "formulation"},
        {"id": "f4", "label": "Boswellia\nPhytopharmaceutical", "type": "Formulation", "group": "formulation"},
        {"id": "f5", "label": "Turmeric Curcumin\nNutraceutical", "type": "Formulation", "group": "formulation"},

        # ── Authoritative Texts ────────────────────────────────
        {"id": "t1", "label": "Charaka Samhita", "type": "AuthoritativeText", "group": "text"},
        {"id": "t2", "label": "Ashtanga Hridayam", "type": "AuthoritativeText", "group": "text"},
        {"id": "t3", "label": "Sharangadhara\nSamhita", "type": "AuthoritativeText", "group": "text"},

        # ── Statutes ───────────────────────────────────────────
        {"id": "s1", "label": "Patents Act 1970\n(Amended 2005)", "type": "Statute", "group": "statute"},
        {"id": "s2", "label": "Biological Diversity\nAct 2002", "type": "Statute", "group": "statute"},
        {"id": "s3", "label": "Drugs & Cosmetics\nAct 1940", "type": "Statute", "group": "statute"},
        {"id": "s4", "label": "TKDL (Traditional\nKnowledge Digital Library)", "type": "Statute", "group": "statute"},

        # ── Sections ───────────────────────────────────────────
        {"id": "sec1", "label": "Section 3(p)\nTK Exclusion", "type": "Section", "group": "section"},
        {"id": "sec2", "label": "Section 3(d)\nEnhanced Efficacy", "type": "Section", "group": "section"},
        {"id": "sec3", "label": "Rule 122E\nPhytopharmaceutical", "type": "Section", "group": "section"},
        {"id": "sec4", "label": "NBA Form I\nAccess Approval", "type": "Section", "group": "section"},
        {"id": "sec5", "label": "NBA Form III\nExport Approval", "type": "Section", "group": "section"},

        # ── Treaty Articles ────────────────────────────────────
        {"id": "tr1", "label": "Nagoya Protocol\nArticle 5", "type": "TreatyArticle", "group": "treaty"},
        {"id": "tr2", "label": "WIPO GRATK\nArticle 3", "type": "TreatyArticle", "group": "treaty"},
        {"id": "tr3", "label": "CBD Article 8(j)\nTK Protection", "type": "TreatyArticle", "group": "treaty"},

        # ── Patent Bars ────────────────────────────────────────
        {"id": "pb1", "label": "Prior Art Bar\n(Known Formulation)", "type": "PatentBar", "group": "patentbar"},
        {"id": "pb2", "label": "Admixture Bar\n(Simple Combination)", "type": "PatentBar", "group": "patentbar"},
    ]

    edges = [
        # Formulation → Herb (CONTAINS_HERB)
        {"source": "f1", "target": "h3", "relation": "CONTAINS_HERB"},
        {"source": "f2", "target": "h3", "relation": "CONTAINS_HERB"},
        {"source": "f2", "target": "h4", "relation": "CONTAINS_HERB"},
        {"source": "f3", "target": "h2", "relation": "CONTAINS_HERB"},
        {"source": "f4", "target": "h6", "relation": "CONTAINS_HERB"},
        {"source": "f5", "target": "h1", "relation": "CONTAINS_HERB"},
        {"source": "f1", "target": "h5", "relation": "CONTAINS_HERB"},

        # Formulation → AuthoritativeText (MENTIONED_IN)
        {"source": "f1", "target": "t1", "relation": "MENTIONED_IN"},
        {"source": "f2", "target": "t1", "relation": "MENTIONED_IN"},
        {"source": "f2", "target": "t3", "relation": "MENTIONED_IN"},
        {"source": "f3", "target": "t2", "relation": "MENTIONED_IN"},

        # Formulation → Statute (GOVERNED_BY)
        {"source": "f1", "target": "s1", "relation": "GOVERNED_BY"},
        {"source": "f3", "target": "s1", "relation": "GOVERNED_BY"},
        {"source": "f4", "target": "s3", "relation": "GOVERNED_BY"},
        {"source": "f5", "target": "s3", "relation": "GOVERNED_BY"},
        {"source": "f2", "target": "s2", "relation": "GOVERNED_BY"},

        # Formulation → Section (BARRED_BY)
        {"source": "f1", "target": "sec1", "relation": "BARRED_BY"},
        {"source": "f2", "target": "sec1", "relation": "BARRED_BY"},
        {"source": "f5", "target": "sec2", "relation": "BARRED_BY"},
        {"source": "f4", "target": "sec3", "relation": "GOVERNED_BY"},

        # Herb/Formulation → Statute (REQUIRES_APPROVAL)
        {"source": "h1", "target": "sec4", "relation": "REQUIRES_APPROVAL"},
        {"source": "f3", "target": "sec5", "relation": "REQUIRES_APPROVAL"},

        # Formulation → TKDL (PROTECTED_IN)
        {"source": "f1", "target": "s4", "relation": "PROTECTED_IN"},
        {"source": "f2", "target": "s4", "relation": "PROTECTED_IN"},

        # Section → Statute (parent relationship)
        {"source": "sec1", "target": "s1", "relation": "PART_OF"},
        {"source": "sec2", "target": "s1", "relation": "PART_OF"},
        {"source": "sec3", "target": "s3", "relation": "PART_OF"},
        {"source": "sec4", "target": "s2", "relation": "PART_OF"},
        {"source": "sec5", "target": "s2", "relation": "PART_OF"},

        # Patent Bars ← Sections
        {"source": "pb1", "target": "sec1", "relation": "TRIGGERED_BY"},
        {"source": "pb2", "target": "sec1", "relation": "TRIGGERED_BY"},

        # Treaty → Statute
        {"source": "tr1", "target": "s2", "relation": "IMPLEMENTED_BY"},
        {"source": "tr3", "target": "s2", "relation": "IMPLEMENTED_BY"},
        {"source": "tr2", "target": "s1", "relation": "IMPLEMENTED_BY"},
    ]

    # Node type descriptions for the legend / tooltip
    node_type_meta = {
        "Herb":             {"color": "#3f9152", "description": "Medicinal plant ingredient"},
        "Formulation":      {"color": "#0e4a52", "description": "Ayurvedic product or extract"},
        "AuthoritativeText":{"color": "#8b5cf6", "description": "Classical Ayurvedic text"},
        "Statute":          {"color": "#dd8a3e", "description": "Indian or international law"},
        "Section":          {"color": "#c2732a", "description": "Specific statutory provision"},
        "TreatyArticle":    {"color": "#0ea5e9", "description": "International treaty clause"},
        "PatentBar":        {"color": "#ef4444", "description": "Patent exclusion ground"},
    }

    relation_meta = {
        "CONTAINS_HERB":     {"label": "Contains Herb",   "color": "#3f9152"},
        "MENTIONED_IN":      {"label": "Mentioned In",    "color": "#8b5cf6"},
        "GOVERNED_BY":       {"label": "Governed By",     "color": "#dd8a3e"},
        "BARRED_BY":         {"label": "Barred By",       "color": "#ef4444"},
        "REQUIRES_APPROVAL": {"label": "Requires Approval","color": "#c2732a"},
        "PROTECTED_IN":      {"label": "Protected In",    "color": "#0e4a52"},
        "PART_OF":           {"label": "Part Of",         "color": "#94a3b8"},
        "TRIGGERED_BY":      {"label": "Triggered By",    "color": "#ef4444"},
        "IMPLEMENTED_BY":    {"label": "Implemented By",  "color": "#0ea5e9"},
    }

    return {
        "nodes": nodes,
        "edges": edges,
        "node_type_meta": node_type_meta,
        "relation_meta": relation_meta,
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "node_types": list(node_type_meta.keys()),
        }
    }
