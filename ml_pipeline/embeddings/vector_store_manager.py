from typing import List, Dict, Any

class VectorStoreManager:
    """
    Qdrant / Milvus Vector Store Client for hybrid dense + sparse BM25 legal retrieval.
    Enforces metadata filtering by Jurisdiction ('national' vs 'international').
    """

    def __init__(self, collection_name: str = "ayurveda_ip_corpus"):
        self.collection_name = collection_name

    def search_hybrid(self, query: str, jurisdiction: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Executes vector search filtered by jurisdiction.
        """
        # Mock structured response for RAG pipeline testing
        return [
            {
                "score": 0.92,
                "text": "Section 3(p) of the Indian Patents Act 1970 bars patenting of traditional knowledge or aggregations of known properties.",
                "metadata": {
                    "statute": "The Patents Act, 1970",
                    "section": "3(p)",
                    "jurisdiction": jurisdiction,
                    "official_url": "https://indiacode.nic.in"
                }
            }
        ]
