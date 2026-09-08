from typing import Dict, Any

class QueryRouterAgent:
    """
    Multi-Agent Router Agent.
    Routes incoming queries to the National (India) vs International RAG pipeline branch,
    and detects whether formulation classification wizard or ABS calculation is needed.
    """

    @staticmethod
    def route_query(query: str, explicit_jurisdiction: str = None) -> Dict[str, Any]:
        lower_q = query.lower()
        
        # Jurisdiction determination
        if explicit_jurisdiction in ["national", "international"]:
            jurisdiction = explicit_jurisdiction
        elif any(k in lower_q for k in ["wipo", "trips", "nagoya", "cbd", "pct", "madrid", "budapest", "export", "foreign"]):
            jurisdiction = "international"
        else:
            jurisdiction = "national"

        # Intent detection
        needs_classification = any(k in lower_q for k in ["classify", "classical", "generic", "phytopharmaceutical", "aahar", "cosmetic", "category"])
        needs_abs = any(k in lower_q for k in ["abs", "benefit sharing", "nba", "sbb", "biodiversity", "biological resource"])

        return {
            "jurisdiction": jurisdiction,
            "intents": {
                "general_rag": True,
                "needs_classification_wizard": needs_classification,
                "needs_abs_calculator": needs_abs
            },
            "suggested_pipeline": f"{jurisdiction}_rag_pipeline"
        }
