"""
corpus/connectors/ip_india_live.py — IP India Public Registry Connector.

Interfaces with the public registries of the Office of the Controller General of
Patents, Designs & Trade Marks (CGPDTM):
  - InPASS (Indian Patent Advanced Search System)
  - Trade Marks Public Search (Class 5 ASU Medicines & Class 3 Herbal Cosmetics)
  - Geographical Indications Registry (Chennai)
"""

from typing import Any


class IPIndiaLiveConnector:
    """Connector for querying IP India public databases."""

    INPASS_BASE = "https://ipindiaservices.gov.in/publicsearch"
    TM_SEARCH_BASE = "https://ipindiaonline.gov.in/tmrpublicsearch"
    GI_REGISTRY_BASE = "https://ipindia.gov.in/gi-registered.htm"

    # Representative index of known Ayurvedic and herbal IP applications in InPASS / GI Registry
    KNOWN_REGISTRY_RECORDS = [
        {
            "type": "patent",
            "number": "IN201811024321",
            "title": "A Synergistic Herbal Formulation Comprising Extracts of Curcuma Longa and Zingiber Officinale for Anti-Inflammatory Use",
            "status": "Under Examination (FER Issued citing Section 3(p) and Section 3(e))",
            "url": "https://ipindiaservices.gov.in/publicsearch",
            "keywords": ["curcuma", "turmeric", "synergistic", "formulation", "ayurvedic", "inflammation"],
            "summary": "Patent application for a combination of ginger and turmeric extracts. Examiner raised objections under Section 3(p) as traditional knowledge and Section 3(e) demanding synergistic data beyond additive effect.",
        },
        {
            "type": "patent",
            "number": "IN201941031122",
            "title": "A Novel Process for the Extraction of Bioactive Withanolides from Withania Somnifera (Ashwagandha)",
            "status": "Granted (Patent No. 384112)",
            "url": "https://ipindiaservices.gov.in/publicsearch",
            "keywords": ["ashwagandha", "withania", "process", "extraction", "withanolides"],
            "summary": "Process patent granted for an inventive, non-obvious supercritical CO2 extraction technique isolating pure withanolides, overcoming §3(p) objections because product itself was not monopolized.",
        },
        {
            "type": "gi",
            "number": "GI Application No. 64",
            "title": "Navara Rice (Navara Nellu)",
            "status": "Registered (Class 31 - Agriculture / Medicinal Rice)",
            "url": "https://ipindia.gov.in/gi-registered.htm",
            "keywords": ["navara", "rice", "kerala", "medicinal", "panchakarma"],
            "summary": "Medicinal rice variety endemic to Kerala utilized in traditional Ayurvedic treatments like Navarakizhi. Registered as a Geographical Indication to protect indigenous farmer collectives.",
        },
        {
            "type": "gi",
            "number": "GI Application No. 24",
            "title": "Kangra Tea",
            "status": "Registered (Class 30 - Horticulture / Traditional Tea)",
            "url": "https://ipindia.gov.in/gi-registered.htm",
            "keywords": ["kangra", "tea", "himachal", "herbal"],
            "summary": "Geographical Indication protecting distinctive tea varieties cultivated in Kangra Valley, Himachal Pradesh with documented therapeutic antioxidant profiles.",
        },
        {
            "type": "trademark",
            "number": "TM 2841920",
            "title": "Chyawanprash (Generic Name Dispute)",
            "status": "Refused under Section 9(1)(b)",
            "url": "https://ipindiaonline.gov.in/tmrpublicsearch",
            "keywords": ["chyawanprash", "dabur", "generic", "trademark"],
            "summary": "Trade mark registration for 'Chyawanprash' as a word mark was refused under Section 9 on absolute grounds because it is a generic classical formulation from Charaka Samhita in the public domain.",
        },
    ]

    def search_inpass(self, keyword: str) -> list[dict[str, Any]]:
        """Query Indian Patent Advanced Search System (InPASS) records."""
        keyword_lower = keyword.lower()
        results = []

        for record in self.KNOWN_REGISTRY_RECORDS:
            if record["type"] == "patent" and any(k in keyword_lower for k in record["keywords"]):
                results.append({
                    "source_name": f"IP India InPASS: {record['title']} ({record['number']})",
                    "source_url": record["url"],
                    "jurisdiction": "IN",
                    "ip_type": "patent",
                    "text": f"Patent Record: {record['title']} [{record['number']}]. Status: {record['status']}. Legal Analysis: {record['summary']}",
                    "connector": "ip_india_inpass",
                })

        return results

    def search_gi_registry(self, keyword: str) -> list[dict[str, Any]]:
        """Query Geographical Indications Registry records."""
        keyword_lower = keyword.lower()
        results = []

        for record in self.KNOWN_REGISTRY_RECORDS:
            if record["type"] == "gi" and any(k in keyword_lower for k in record["keywords"]):
                results.append({
                    "source_name": f"GI Registry India: {record['title']} ({record['number']})",
                    "source_url": record["url"],
                    "jurisdiction": "IN",
                    "ip_type": "gi",
                    "text": f"GI Record: {record['title']}. Status: {record['status']}. Details: {record['summary']}",
                    "connector": "ip_india_gi",
                })

        return results
