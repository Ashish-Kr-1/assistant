"""
corpus/sources.py — Registry of all authoritative legal sources for the Charaka IP corpus.

Every source has:
  - name: human-readable label
  - url: canonical URL of the source
  - jurisdiction: "IN" (India) or "INTL" (International)
  - ip_types: list of IP domains this source covers
  - fetch_type: "pdf" | "html" | "api"
  - refresh_days: how many days between scheduled re-fetches
  - notes: any special handling notes

Add new sources here; the ingest pipeline reads this registry.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CorpusSource:
    name: str
    url: str
    jurisdiction: str           # "IN" or "INTL"
    ip_types: list[str]         # patent, trademark, gi, copyright, ayush, abs, tkdl
    fetch_type: str             # "pdf" | "html" | "api"
    refresh_days: int = 30      # re-fetch cadence in days
    notes: str = ""


# ── Indian Open Authoritative Sources ─────────────────────────────────────────

INDIA_CODE_SOURCES: list[CorpusSource] = [
    CorpusSource(
        name="Patents Act 1970",
        url="https://www.indiacode.nic.in/handle/123456789/1392",
        jurisdiction="IN",
        ip_types=["patent"],
        fetch_type="html",
        notes="Primary statute. Sections 3(p), 3(e), 3(d) critical for AYUSH/TKDL.",
    ),
    CorpusSource(
        name="Trade Marks Act 1999",
        url="https://www.indiacode.nic.in/handle/123456789/2064",
        jurisdiction="IN",
        ip_types=["trademark"],
        fetch_type="html",
    ),
    CorpusSource(
        name="Copyright Act 1957",
        url="https://www.indiacode.nic.in/handle/123456789/1367",
        jurisdiction="IN",
        ip_types=["copyright"],
        fetch_type="html",
    ),
    CorpusSource(
        name="Geographical Indications of Goods Act 1999",
        url="https://www.indiacode.nic.in/handle/123456789/1396",
        jurisdiction="IN",
        ip_types=["gi"],
        fetch_type="html",
    ),
    CorpusSource(
        name="Biological Diversity Act 2002",
        url="https://www.indiacode.nic.in/handle/123456789/2046",
        jurisdiction="IN",
        ip_types=["abs", "patent"],
        fetch_type="html",
        notes="Section 6 mandatory NBA clearance before IP filing.",
    ),
    CorpusSource(
        name="Drugs and Cosmetics Act 1940",
        url="https://www.indiacode.nic.in/handle/123456789/2265",
        jurisdiction="IN",
        ip_types=["ayush"],
        fetch_type="html",
        notes="Chapter IV-A, Rule 158-B for ASU formulations.",
    ),
    CorpusSource(
        name="Protection of Plant Varieties and Farmers Rights Act 2001",
        url="https://www.indiacode.nic.in/handle/123456789/2015",
        jurisdiction="IN",
        ip_types=["patent", "gi"],
        fetch_type="html",
    ),
]

IPINDIA_SOURCES: list[CorpusSource] = [
    CorpusSource(
        name="IP India Patent Examination Guidelines",
        url="https://ipindia.gov.in/writereaddata/Portal/IPOGuidelinesManuals/1_81_1_patent-examination-guidelines.pdf",
        jurisdiction="IN",
        ip_types=["patent"],
        fetch_type="pdf",
        notes="Section on biotech/pharma/AYUSH patentability.",
    ),
    CorpusSource(
        name="IP India Trade Marks Manual",
        url="https://ipindia.gov.in/writereaddata/Portal/IPOGuidelinesManuals/1_38_1_TM-Manual.pdf",
        jurisdiction="IN",
        ip_types=["trademark"],
        fetch_type="pdf",
    ),
    CorpusSource(
        name="IP India GI Registry — Registered GIs",
        url="https://ipindia.gov.in/geographical-indications.htm",
        jurisdiction="IN",
        ip_types=["gi"],
        fetch_type="html",
        notes="Public list of registered GI tags in India.",
    ),
]

TKDL_SOURCES: list[CorpusSource] = [
    CorpusSource(
        name="TKDL — Traditional Knowledge Digital Library (Public Disclosures)",
        url="https://www.tkdl.res.in",
        jurisdiction="IN",
        ip_types=["tkdl", "patent"],
        fetch_type="html",
        notes="Public prior-art disclosures. Full database requires institutional access.",
        refresh_days=90,
    ),
]

NBA_ABS_SOURCES: list[CorpusSource] = [
    CorpusSource(
        name="National Biodiversity Authority — ABS Guidelines",
        url="https://nbaindia.org/content/23/19/1/guideline.html",
        jurisdiction="IN",
        ip_types=["abs"],
        fetch_type="html",
        notes="Access and Benefit Sharing guidelines under BDA 2002 Section 6.",
    ),
    CorpusSource(
        name="National Biodiversity Authority — Standard Material Transfer Agreement",
        url="https://nbaindia.org/content/73/49/1/smta.html",
        jurisdiction="IN",
        ip_types=["abs"],
        fetch_type="html",
    ),
]

AYUSH_SOURCES: list[CorpusSource] = [
    CorpusSource(
        name="AYUSH Ministry — Drugs & Cosmetics Act Rules (ASU Section)",
        url="https://ayush.gov.in/about-the-systems/ayurveda",
        jurisdiction="IN",
        ip_types=["ayush"],
        fetch_type="html",
        notes="Rule 158-B; ASU licensing and classification.",
    ),
    CorpusSource(
        name="Ayurvedic Pharmacopoeia of India (Vol I)",
        url="https://pharmacopoeia.ayush.gov.in",
        jurisdiction="IN",
        ip_types=["ayush"],
        fetch_type="html",
        notes="Official pharmacopoeial standards for Ayurvedic formulations.",
        refresh_days=180,
    ),
]

# ── International Open Authoritative Sources ───────────────────────────────────

INTERNATIONAL_SOURCES: list[CorpusSource] = [
    CorpusSource(
        name="TRIPS Agreement (WTO)",
        url="https://www.wto.org/english/docs_e/legal_e/27-trips_01_e.htm",
        jurisdiction="INTL",
        ip_types=["patent", "trademark", "gi", "copyright"],
        fetch_type="html",
        notes="Articles 27–34 on patent eligibility; 27.3(b) on biological/TKDL exclusions.",
    ),
    CorpusSource(
        name="Convention on Biological Diversity (CBD)",
        url="https://www.cbd.int/doc/legal/cbd-en.pdf",
        jurisdiction="INTL",
        ip_types=["abs"],
        fetch_type="pdf",
    ),
    CorpusSource(
        name="Nagoya Protocol on ABS",
        url="https://www.cbd.int/abs/doc/protocol/nagoya-protocol-en.pdf",
        jurisdiction="INTL",
        ip_types=["abs"],
        fetch_type="pdf",
        notes="Articles 5–7 on benefit sharing; India ratified 2012.",
    ),
    CorpusSource(
        name="Patent Cooperation Treaty (PCT)",
        url="https://wipolex-res.wipo.int/edocs/lexdocs/treaties/en/pct/trt_pct.pdf",
        jurisdiction="INTL",
        ip_types=["patent"],
        fetch_type="pdf",
    ),
    CorpusSource(
        name="Madrid Protocol (International TM Registration)",
        url="https://wipolex-res.wipo.int/edocs/lexdocs/treaties/en/madrid_p/trt_madrid_p.pdf",
        jurisdiction="INTL",
        ip_types=["trademark"],
        fetch_type="pdf",
    ),
    CorpusSource(
        name="Lisbon Agreement (GI / Appellations of Origin)",
        url="https://wipolex-res.wipo.int/edocs/lexdocs/treaties/en/lisbon/trt_lisbon.pdf",
        jurisdiction="INTL",
        ip_types=["gi"],
        fetch_type="pdf",
    ),
    CorpusSource(
        name="Berne Convention (Copyright)",
        url="https://wipolex-res.wipo.int/edocs/lexdocs/treaties/en/berne/trt_berne_001en.pdf",
        jurisdiction="INTL",
        ip_types=["copyright"],
        fetch_type="pdf",
    ),
]

# ── Master registry ────────────────────────────────────────────────────────────

ALL_SOURCES: list[CorpusSource] = (
    INDIA_CODE_SOURCES
    + IPINDIA_SOURCES
    + TKDL_SOURCES
    + NBA_ABS_SOURCES
    + AYUSH_SOURCES
    + INTERNATIONAL_SOURCES
)


def sources_for(ip_type: str | None = None, jurisdiction: str | None = None) -> list[CorpusSource]:
    """Filter the registry by ip_type and/or jurisdiction."""
    results = ALL_SOURCES
    if ip_type:
        results = [s for s in results if ip_type in s.ip_types]
    if jurisdiction:
        results = [s for s in results if s.jurisdiction == jurisdiction.upper()]
    return results
