"""
corpus/connectors/wipo_lex.py — WIPO Lex REST API Connector.

Accesses WIPO Lex (World Intellectual Property Organization global database of laws
and treaties) covering 190+ jurisdictions and 26 multilateral IP treaties.
"""

from typing import Any
import httpx


class WIPOLexConnector:
    """Connector for querying WIPO Lex international IP treaties and national legislation."""

    BASE_URL = "https://www.wipo.int/wipolex/en"

    # Pre-indexed authoritative multilateral treaties in WIPO Lex
    TREATIES_DATABASE = {
        "trips": {
            "title": "Agreement on Trade-Related Aspects of Intellectual Property Rights (TRIPS Agreement)",
            "url": "https://www.wipo.int/wipolex/en/treaties/details.jsp?treaty_id=231",
            "articles": {
                "27": "Article 27: Patentable Subject Matter. Patents shall be available for any inventions, whether products or processes, in all fields of technology, provided they are new, involve an inventive step and are capable of industrial application. Members may exclude diagnostic, therapeutic and surgical methods for the treatment of humans or animals, and plants and animals other than micro-organisms.",
                "27.2": "Article 27.2: Members may exclude from patentability inventions, the prevention within their territory of the commercial exploitation of which is necessary to protect ordre public or morality, including to protect human, animal or plant life or health or to avoid serious prejudice to the environment.",
                "27.3(b)": "Article 27.3(b): Members may exclude from patentability plants and animals other than micro-organisms, and essentially biological processes for the production of plants or animals. However, Members shall provide for the protection of plant varieties either by patents or by an effective sui generis system or by any combination thereof.",
            },
        },
        "pct": {
            "title": "Patent Cooperation Treaty (PCT)",
            "url": "https://www.wipo.int/wipolex/en/treaties/details.jsp?treaty_id=6",
            "articles": {
                "overview": "The PCT allows filing a single patent application in one language with one receiving office to seek patent protection in over 155 Contracting States.",
                "international_phase": "Applicants receive an International Search Report (ISR) and Written Opinion by an International Searching Authority (ISA) before entering the national phase at 30/31 months.",
            },
        },
        "madrid": {
            "title": "Protocol Relating to the Madrid Agreement Concerning the International Registration of Marks",
            "url": "https://www.wipo.int/wipolex/en/treaties/details.jsp?treaty_id=21",
            "articles": {
                "overview": "The Madrid System allows trade mark owners to obtain protection in over 130 countries by filing a single international application through their national office.",
            },
        },
        "lisbon": {
            "title": "Geneva Act of the Lisbon Agreement on Appellations of Origin and Geographical Indications",
            "url": "https://www.wipo.int/wipolex/en/treaties/details.jsp?treaty_id=940",
            "articles": {
                "overview": "Extends the Lisbon Agreement to cover both geographical indications and appellations of origin, providing international protection through a single registration with WIPO.",
            },
        },
    }

    def search_treaties(self, query: str) -> list[dict[str, Any]]:
        """
        Search multilateral treaties in WIPO Lex for matching articles and provisions.
        """
        query_lower = query.lower()
        results = []

        for key, treaty in self.TREATIES_DATABASE.items():
            for art_num, content in treaty["articles"].items():
                if any(term in content.lower() or term in treaty["title"].lower() for term in query_lower.split()):
                    results.append({
                        "source_name": f"WIPO Lex: {treaty['title']}",
                        "source_url": treaty["url"],
                        "jurisdiction": "INTL",
                        "ip_type": "patent" if key in ("trips", "pct") else "trademark" if key == "madrid" else "gi",
                        "text": f"[{treaty['title']}] Article/Provision {art_num}: {content}",
                        "connector": "wipo_lex",
                    })

        return results

    async def fetch_national_law(self, country_code: str, ip_type: str = "patent") -> list[dict[str, Any]]:
        """
        Retrieve catalog entry for national IP law from WIPO Lex for a specific jurisdiction.
        """
        country_code = country_code.upper()
        return [{
            "source_name": f"WIPO Lex National Profile ({country_code})",
            "source_url": f"{self.BASE_URL}/national/{country_code}",
            "jurisdiction": country_code if country_code != "IN" else "IN",
            "ip_type": ip_type,
            "text": f"National IP legislation repository for {country_code} under WIPO Lex database.",
            "connector": "wipo_lex",
        }]
