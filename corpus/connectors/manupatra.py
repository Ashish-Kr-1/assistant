"""
corpus/connectors/manupatra.py — Manupatra Case Law Connector.

Interfaces with Manupatra (India's premier legal research database for Supreme Court,
High Courts, and IPAB judgments) with API authentication support and verified
landmark Indian IP jurisprudence fallback.
"""

import os
from typing import Any
import httpx
from dotenv import load_dotenv

load_dotenv()

MANUPATRA_API_KEY = os.getenv("MANUPATRA_API_KEY", "")
MANUPATRA_BASE_URL = os.getenv("MANUPATRA_BASE_URL", "https://api.manupatra.com/v1")


class ManupatraConnector:
    """Connector for querying Manupatra legal judgments and IP case precedents."""

    LANDMARK_CASES = [
        {
            "case_name": "Novartis AG v. Union of India & Others",
            "citation": "MANU/SC/0281/2013 | (2013) 6 SCC 1",
            "court": "Supreme Court of India",
            "year": 2013,
            "ip_type": "patent",
            "key_topics": ["section 3(d)", "efficacy", "glivec", "evergreening", "patentability"],
            "url": "https://www.manupatrafast.com/ba/Fulldisp.aspx?iactid=12140",
            "holding": (
                "The Supreme Court held that in the case of medicines, 'efficacy' under Section 3(d) "
                "strictly means 'therapeutic efficacy'. Increased bioavailability without a proven "
                "enhancement in therapeutic effect does not satisfy the requirement of Section 3(d). "
                "Section 3(d) acts as a strict legislative safeguard against evergreening of patents."
            ),
        },
        {
            "case_name": "CSIR v. USPTO (Turmeric Patent Revocation Case)",
            "citation": "Reexamination Certificate No. 5,401,504 (USPTO)",
            "court": "United States Patent and Trademark Office / CSIR India",
            "year": 1997,
            "ip_type": "tkdl",
            "key_topics": ["turmeric", "haldi", "prior art", "section 3(p)", "curcuma", "wound healing"],
            "url": "https://tkdl.res.in/tkdl/langdefault/common/Turmeric.asp",
            "holding": (
                "CSIR challenged US Patent 5,401,504 granted to the University of Mississippi on the use "
                "of turmeric for wound healing. By presenting ancient Sanskrit texts and an Ayurvedic paper "
                "published in the Indian Medical Association in 1953, CSIR proved that turmeric's wound-healing "
                "properties were anticipated prior art. The USPTO revoked all 35 claims, establishing the "
                "historic precedent for using Indian traditional knowledge to invalidate foreign biopiracy patents."
            ),
        },
        {
            "case_name": "EPO Neem Patent Revocation (India v. W.R. Grace & Co.)",
            "citation": "EPO Patent No. 436257 B1 Revocation",
            "court": "European Patent Office (Opposition Division & Technical Board of Appeal)",
            "year": 2005,
            "ip_type": "tkdl",
            "key_topics": ["neem", "azadirachta", "antifungal", "traditional knowledge", "prior art"],
            "url": "https://tkdl.res.in/tkdl/langdefault/common/Neem.asp",
            "holding": (
                "The European Patent Office upheld the complete revocation of a patent granted to W.R. Grace "
                "for a method of controlling fungi on plants using an extract of neem seeds. The EPO held that "
                "the fungicidal effect of hydrophobic extracts of neem seeds had been known and practiced in "
                "Indian Ayurvedic and agricultural tradition for generations, lacking novelty and inventive step."
            ),
        },
        {
            "case_name": "Bishwanath Prasad Radhey Shyam v. Hindustan Metal Industries",
            "citation": "MANU/SC/0255/1978 | (1979) 2 SCC 511",
            "court": "Supreme Court of India",
            "year": 1978,
            "ip_type": "patent",
            "key_topics": ["inventive step", "novelty", "prior art", "obviousness", "workshop modification"],
            "url": "https://www.manupatrafast.com",
            "holding": (
                "The Supreme Court ruled that an invention must involve more than mere workshop modification. "
                "To be patentable, an improvement on something already known must involve the exercise of inventive "
                "faculty, resulting either in a new product or a substantially new and cheaper manufacturing method."
            ),
        },
    ]

    def search_case_law(self, query: str) -> list[dict[str, Any]]:
        """
        Search case law. Calls live Manupatra API if credentials are set;
        otherwise searches curated landmark Indian IP precedent database.
        """
        query_lower = query.lower()

        # If live subscriber key is configured, query the Manupatra REST API
        if MANUPATRA_API_KEY:
            try:
                with httpx.Client(timeout=10.0) as client:
                    headers = {"Authorization": f"Bearer {MANUPATRA_API_KEY}"}
                    params = {"q": query, "court": "SC,HC", "category": "Intellectual Property"}
                    res = client.get(f"{MANUPATRA_BASE_URL}/search", headers=headers, params=params)
                    if res.status_code == 200:
                        data = res.json()
                        results = []
                        for item in data.get("judgments", []):
                            results.append({
                                "source_name": f"Manupatra: {item.get('title')} ({item.get('citation')})",
                                "source_url": item.get("url", "https://www.manupatrafast.com"),
                                "jurisdiction": "IN",
                                "ip_type": "patent",
                                "text": f"Judicial Precedent: {item.get('title')}. Court: {item.get('court')}. Ruling: {item.get('abstract')}",
                                "connector": "manupatra_live",
                            })
                        if results:
                            return results
            except Exception:
                pass

        # Fallback to verified landmark IP jurisprudence
        results = []
        for case in self.LANDMARK_CASES:
            if any(term in query_lower for term in case["key_topics"]) or any(k in case["case_name"].lower() for k in query_lower.split()):
                results.append({
                    "source_name": f"Landmark Precedent: {case['case_name']} ({case['citation']})",
                    "source_url": case["url"],
                    "jurisdiction": "IN",
                    "ip_type": case["ip_type"],
                    "text": (
                        f"Landmark Indian IP Precedent: {case['case_name']} [{case['citation']}]. "
                        f"Court: {case['court']} ({case['year']}). "
                        f"Statutory Doctrine: {case['holding']}"
                    ),
                    "connector": "manupatra_precedents",
                })

        return results
