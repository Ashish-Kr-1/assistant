"""
Structure-aware legal chunker for statutory texts, rules, and treaties (CRAG.md §3.1).
Enforces metadata preservation for rules R7 (provenance) and R10 (version stamping).
"""

import re
from typing import List, Optional
from ml_pipeline.crag.schema import LegalChunk, JurisdictionType, IPType, ProvenanceStatus


class LegalHierarchyChunker:
    """
    Splits legal documents (Acts, Rules, Treaties, Gazettes) by Section, Rule, or Article boundaries,
    ensuring each statutory chunk retains its provenance and version metadata.
    """

    SECTION_PATTERN = re.compile(
        r"(?:^|\n\n)(?P<marker>(?:Section|Rule|Article)\s+(?P<id>[0-9A-Za-z\(\)]+)[^\n]*)\n(?P<body>(?:(?!(?:Section|Rule|Article)\s+[0-9A-Za-z\(\)]+).|\n)*)",
        re.MULTILINE
    )

    @classmethod
    def chunk_document(
        cls,
        raw_text: str,
        act_name: str,
        jurisdiction: JurisdictionType,
        effective_date: str,
        source: str = "India Code",
        ip_type: IPType = IPType.GENERAL,
        status: ProvenanceStatus = ProvenanceStatus.VERIFIED_PUBLIC,
        official_url: Optional[str] = None
    ) -> List[LegalChunk]:
        """
        Parses raw text and generates structured LegalChunk instances.
        """
        matches = list(cls.SECTION_PATTERN.finditer(raw_text))
        chunks: List[LegalChunk] = []

        if not matches:
            # Fallback if text doesn't contain standard Section/Rule/Article headers
            paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
            for idx, para in enumerate(paragraphs):
                chunk_id = f"{cls._slugify(act_name)}_para_{idx+1}"
                chunks.append(
                    LegalChunk(
                        chunk_id=chunk_id,
                        source=source,
                        act_name=act_name,
                        section_id=f"Paragraph {idx+1}",
                        jurisdiction=jurisdiction,
                        effective_date=effective_date,
                        ip_type=ip_type,
                        status=status,
                        official_url=official_url,
                        text=para
                    )
                )
            return chunks

        for idx, match in enumerate(matches):
            marker = match.group("marker").strip()
            section_num = match.group("id").strip()
            body = match.group("body").strip()
            full_chunk_text = f"{marker}\n\n{body}" if body else marker

            chunk_id = f"{cls._slugify(act_name)}_sec_{section_num.lower().replace('(', '').replace(')', '')}"
            chunks.append(
                LegalChunk(
                    chunk_id=chunk_id,
                    source=source,
                    act_name=act_name,
                    section_id=marker.split(":")[0].strip() if ":" in marker else marker[:50],
                    jurisdiction=jurisdiction,
                    effective_date=effective_date,
                    ip_type=ip_type,
                    status=status,
                    official_url=official_url,
                    text=full_chunk_text
                )
            )

        return chunks

    @staticmethod
    def _slugify(text: str) -> str:
        cleaned = re.sub(r"[^\w\s-]", "", text.lower())
        return re.sub(r"[-\s]+", "_", cleaned)
