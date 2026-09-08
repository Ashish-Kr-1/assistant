from typing import Dict, List, Any

class StatutoryCitationValidator:
    """
    Validates and enriches statutory citations across National (India) and International legal corpora.
    Prevents legal hallucinations by matching citations against verified statute registry keys.
    """

    KNOWN_CITATIONS = {
        "PATENTS_ACT_SEC_3P": {
            "statute": "The Patents Act, 1970 (as amended)",
            "section": "Section 3(p)",
            "jurisdiction": "National (India)",
            "official_url": "https://indiacode.nic.in/handle/123456789/1392",
            "title": "Inventions which are Traditional Knowledge not patentable",
            "summary": "An invention which, in effect, is traditional knowledge or which is an aggregation or duplication of known properties of traditionally known component or components is not patentable."
        },
        "PATENTS_RULES_2024_RULE_24": {
            "statute": "The Patents (Amendment) Rules, 2024",
            "rule": "Rule 24B",
            "jurisdiction": "National (India)",
            "official_url": "https://ipindia.gov.in/rules-patents.htm",
            "title": "Expedited Examination of Patent Applications",
            "summary": "Revised timeline for filing Request for Examination (RFE) reduced from 48 months to 31 months from filing date."
        },
        "BDA_2023_SEC_3": {
            "statute": "The Biological Diversity (Amendment) Act, 2023",
            "section": "Section 3 & 40",
            "jurisdiction": "National (India)",
            "official_url": "http://nbaindia.org/content/26/59/1/rules.html",
            "title": "Regulation of Access to Biological Resources & AYUSH Practitioner Exemption",
            "summary": "Exempts registered AYUSH practitioners and cultivated bio-resources from prior NBA access approval, while tightening commercial compliance."
        },
        "WIPO_GRATK_2024_ART_3": {
            "treaty": "WIPO Treaty on Intellectual Property, Genetic Resources and Associated Traditional Knowledge (2024)",
            "article": "Article 3",
            "jurisdiction": "International",
            "official_url": "https://www.wipo.int/diplomatic-conferences/en/genetic-resources/",
            "title": "Mandatory Disclosure Requirement",
            "summary": "Patent applicants must disclose the country of origin of genetic resources and indigenous community/traditional knowledge source if invention is directly based on TK/GR."
        },
        "NAGOYA_PROTO_ART_5": {
            "treaty": "Nagoya Protocol on Access and Benefit-sharing (CBD)",
            "article": "Article 5",
            "jurisdiction": "International",
            "official_url": "https://www.cbd.int/abs/text/",
            "title": "Fair and Equitable Benefit-sharing",
            "summary": "Requires benefits arising from the utilization of genetic resources and associated TK to be shared in a fair and equitable way with providing party/indigenous communities."
        }
    }

    @classmethod
    def get_citation_detail(cls, citation_key: str) -> Dict[str, Any]:
        return cls.KNOWN_CITATIONS.get(citation_key, {
            "statute": "Unverified Statute Reference",
            "jurisdiction": "Unknown",
            "summary": "Citation pending registry lookup.",
            "official_url": "https://indiacode.nic.in"
        })

    @classmethod
    def enrich_response_citations(cls, text: str, citation_keys: List[str]) -> List[Dict[str, Any]]:
        enriched = []
        for key in citation_keys:
            if key in cls.KNOWN_CITATIONS:
                enriched.append(cls.KNOWN_CITATIONS[key])
        return enriched
