from typing import List, Dict, Any

class LegalHierarchyChunker:
    """
    Structure-aware legal chunker that splits acts, rules, and treaties by Section, Rule,
    or Article boundaries, attaching key statutory metadata.
    """

    @staticmethod
    def chunk_legal_text(raw_text: str, statute_name: str, jurisdiction: str) -> List[Dict[str, Any]]:
        """
        Splits text by Section/Rule markers and attaches metadata.
        """
        sections = raw_text.split("\n\nSection ")
        chunks = []
        
        for idx, sec in enumerate(sections):
            if not sec.strip():
                continue
            header_line = sec.strip().split("\n")[0]
            chunks.append({
                "chunk_id": f"{statute_name.lower().replace(' ', '_')}_sec_{idx+1}",
                "text": f"Section {sec.strip()}",
                "metadata": {
                    "statute": statute_name,
                    "jurisdiction": jurisdiction,
                    "section_title": header_line[:100],
                    "chunk_index": idx
                }
            })
        return chunks
