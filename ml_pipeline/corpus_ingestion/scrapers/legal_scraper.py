"""
REAL Corpus Ingestion Pipeline for Charaka IP (SIH PS045)
================================================================
Fetches statutory text from VERIFIED working public sources only:
  1. Indian National Statutes (Patents Act 1970, Biological Diversity Act 2002/2023,
     GI Act 1999, Drugs & Cosmetics Act 1940, PPV&FR Act 2001)
     → Scraped dynamically from Indian Kanoon's open law repository.
  2. WTO TRIPS Agreement (1995)
     → Scraped from official WTO Treaty PDF (wto.org).
  3. CBD Nagoya Protocol (2014)
     → Scraped from official Convention on Biological Diversity PDF (cbd.int).
  4. WIPO GRATK Treaty (Geneva, 2024)
     → Scraped from official WIPO Diplomatic Conference Treaty PDF (wipo.int).

Zero fakes. Zero text_override. All statutory text comes directly from official
documents or public legal portals downloaded at runtime, with local disk caching
for offline resilience.

Enforces:
  R7  — Every chunk has a ProvenanceStatus matching its actual access level
  R10 — effective_date populated from statute metadata
"""

import io
import logging
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import httpx
import pypdf
from bs4 import BeautifulSoup

from ml_pipeline.crag.schema import (
    IPType,
    JurisdictionType,
    LegalChunk,
    ProvenanceStatus,
)

logger = logging.getLogger("legal_scraper")

REQUEST_DELAY_SECONDS = 1.0
# Kept short deliberately (Section 39 — hackathon demo reliability): this scraper is only
# ever used to build the foundational corpus at process startup, and a slow/unreachable
# source must not block that startup for tens of seconds. A source that times out is
# simply omitted (see get_foundational_corpus docstring) — that's the intended, safe
# behavior, not a defect to paper over with a longer timeout.
HTTP_TIMEOUT = 8.0
MAX_CHARS_PER_CHUNK = 2500
CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/pdf,*/*",
}


@dataclass
class StatutorySource:
    chunk_id: str
    url: str
    source_type: str  # "kanoon", "pdf", or "wipo_gratk"
    act_name: str
    section_id: str
    jurisdiction: JurisdictionType
    ip_type: IPType
    effective_date: str
    extract_pattern: Optional[str]
    source_label: str
    max_extract_chars: int = MAX_CHARS_PER_CHUNK


def get_verified_sources() -> List[StatutorySource]:
    """Returns all verified live sources across national and international regimes."""
    return [
        # ═══════════════════════════════════════════════════════════════════
        # 1. THE PATENTS ACT, 1970 (INDIA) — INDIAN KANOON
        # ═══════════════════════════════════════════════════════════════════
        StatutorySource(
            chunk_id="patents_act_1970_sec_3p",
            url="https://indiankanoon.org/doc/874310/",
            source_type="kanoon",
            act_name="The Patents Act, 1970",
            section_id="Section 3(p) — Traditional Knowledge Patent Bar",
            jurisdiction=JurisdictionType.NATIONAL,
            ip_type=IPType.PATENT,
            effective_date="1970-09-19 (Amended 2005 / Rules 2024)",
            source_label="Indian Kanoon — Central Acts",
            extract_pattern=r"\(p\)\s*(?:an invention which in effect, is traditional knowledge.*)",
        ),
        StatutorySource(
            chunk_id="patents_act_1970_sec_3d",
            url="https://indiankanoon.org/doc/874310/",
            source_type="kanoon",
            act_name="The Patents Act, 1970",
            section_id="Section 3(d) — Enhanced Efficacy Requirement",
            jurisdiction=JurisdictionType.NATIONAL,
            ip_type=IPType.PATENT,
            effective_date="1970-09-19 (Amended 2005 / Rules 2024)",
            source_label="Indian Kanoon — Central Acts",
            extract_pattern=r"\(d\)\s*(?:the mere discovery of a new form of a known substance.*?\bExplanation\b.*?[;\.])",
        ),
        StatutorySource(
            chunk_id="patents_act_1970_sec_3e",
            url="https://indiankanoon.org/doc/874310/",
            source_type="kanoon",
            act_name="The Patents Act, 1970",
            section_id="Section 3(e) — Admixtures",
            jurisdiction=JurisdictionType.NATIONAL,
            ip_type=IPType.PATENT,
            effective_date="1970-09-19 (Amended 2005 / Rules 2024)",
            source_label="Indian Kanoon — Central Acts",
            extract_pattern=r"\(e\)\s*(?:a substance obtained by a mere admixture.*?[;\.])",
        ),
        StatutorySource(
            chunk_id="patents_act_1970_sec_8",
            url="https://indiankanoon.org/doc/879773/",
            source_type="kanoon",
            act_name="The Patents Act, 1970",
            section_id="Section 8 — Information regarding foreign applications",
            jurisdiction=JurisdictionType.NATIONAL,
            ip_type=IPType.PATENT,
            effective_date="1970-09-19 (Rules 2024 amended)",
            source_label="Indian Kanoon — Central Acts",
            extract_pattern=None,  # Full section text
        ),
        StatutorySource(
            chunk_id="patents_act_1970_sec_10",
            url="https://indiankanoon.org/doc/1217727/",
            source_type="kanoon",
            act_name="The Patents Act, 1970",
            section_id="Section 10 — Contents of specifications (Biological origin disclosure)",
            jurisdiction=JurisdictionType.NATIONAL,
            ip_type=IPType.PATENT,
            effective_date="1970-09-19 (Amended 2002, 2005)",
            source_label="Indian Kanoon — Central Acts",
            extract_pattern=None,
        ),
        StatutorySource(
            chunk_id="patents_act_1970_sec_25",
            url="https://indiankanoon.org/doc/1485322/",
            source_type="kanoon",
            act_name="The Patents Act, 1970",
            section_id="Section 25 — Opposition to the patent (TK & Anticipation grounds)",
            jurisdiction=JurisdictionType.NATIONAL,
            ip_type=IPType.PATENT,
            effective_date="1970-09-19 (Amended 2005)",
            source_label="Indian Kanoon — Central Acts",
            extract_pattern=None,
        ),
        StatutorySource(
            chunk_id="patents_act_1970_sec_64",
            url="https://indiankanoon.org/doc/217797/",
            source_type="kanoon",
            act_name="The Patents Act, 1970",
            section_id="Section 64 — Revocation of patents (Non-disclosure of geographical origin)",
            jurisdiction=JurisdictionType.NATIONAL,
            ip_type=IPType.PATENT,
            effective_date="1970-09-19 (Amended 2002, 2005)",
            source_label="Indian Kanoon — Central Acts",
            extract_pattern=None,
        ),

        # ═══════════════════════════════════════════════════════════════════
        # 2. THE BIOLOGICAL DIVERSITY ACT, 2002 / 2023 — INDIAN KANOON
        # ═══════════════════════════════════════════════════════════════════
        StatutorySource(
            chunk_id="bda_2023_sec_3",
            url="https://indiankanoon.org/doc/155946190/",
            source_type="kanoon",
            act_name="The Biological Diversity (Amendment) Act, 2023",
            section_id="Section 3 — Approval of National Biodiversity Authority",
            jurisdiction=JurisdictionType.NATIONAL,
            ip_type=IPType.BIODIVERSITY_ABS,
            effective_date="2023-08-03",
            source_label="Indian Kanoon — Central Acts",
            extract_pattern=None,
        ),
        StatutorySource(
            chunk_id="bda_2002_sec_4",
            url="https://indiankanoon.org/doc/963675/",
            source_type="kanoon",
            act_name="The Biological Diversity Act, 2002",
            section_id="Section 4 — Transfer of biological resource or knowledge",
            jurisdiction=JurisdictionType.NATIONAL,
            ip_type=IPType.BIODIVERSITY_ABS,
            effective_date="2003-02-05",
            source_label="Indian Kanoon — Central Acts",
            extract_pattern=None,
        ),
        StatutorySource(
            chunk_id="bda_2002_sec_6",
            url="https://indiankanoon.org/doc/1758638/",
            source_type="kanoon",
            act_name="The Biological Diversity Act, 2002",
            section_id="Section 6 — Prior approval of NBA for IPR applications",
            jurisdiction=JurisdictionType.NATIONAL,
            ip_type=IPType.BIODIVERSITY_ABS,
            effective_date="2003-02-05 (Amended 2023)",
            source_label="Indian Kanoon — Central Acts",
            extract_pattern=None,
        ),
        StatutorySource(
            chunk_id="bda_2002_sec_19",
            url="https://indiankanoon.org/doc/635100/",
            source_type="kanoon",
            act_name="The Biological Diversity Act, 2002",
            section_id="Section 19 — Application to NBA for access to biological resources",
            jurisdiction=JurisdictionType.NATIONAL,
            ip_type=IPType.BIODIVERSITY_ABS,
            effective_date="2003-02-05 (Amended 2023)",
            source_label="Indian Kanoon — Central Acts",
            extract_pattern=None,
        ),
        StatutorySource(
            chunk_id="bda_2002_sec_21",
            url="https://indiankanoon.org/doc/1380763/",
            source_type="kanoon",
            act_name="The Biological Diversity Act, 2002",
            section_id="Section 21 — Determination of equitable benefit sharing by NBA",
            jurisdiction=JurisdictionType.NATIONAL,
            ip_type=IPType.BIODIVERSITY_ABS,
            effective_date="2003-02-05",
            source_label="Indian Kanoon — Central Acts",
            extract_pattern=None,
        ),
        StatutorySource(
            chunk_id="bda_2023_sec_24",
            url="https://indiankanoon.org/doc/136870409/",
            source_type="kanoon",
            act_name="The Biological Diversity (Amendment) Act, 2023",
            section_id="Section 24 — Intimation to State Biodiversity Board",
            jurisdiction=JurisdictionType.NATIONAL,
            ip_type=IPType.BIODIVERSITY_ABS,
            effective_date="2023-08-03",
            source_label="Indian Kanoon — Central Acts",
            extract_pattern=None,
        ),

        # ═══════════════════════════════════════════════════════════════════
        # 3. GEOGRAPHICAL INDICATIONS ACT, 1999 — INDIAN KANOON
        # ═══════════════════════════════════════════════════════════════════
        StatutorySource(
            chunk_id="gi_act_1999_sec_2",
            url="https://indiankanoon.org/doc/1881745/",
            source_type="kanoon",
            act_name="Geographical Indications of Goods (Registration and Protection) Act, 1999",
            section_id="Section 2(1)(e) — Geographical Indication Definition",
            jurisdiction=JurisdictionType.NATIONAL,
            ip_type=IPType.TRADEMARK_GI,
            effective_date="1999-12-30 (Enacted)",
            source_label="Indian Kanoon — Central Acts",
            extract_pattern=r"\(e\)\s*[\"“]?geographical indication[\"”]?.*?(?=\([f-z]\)|$)",
        ),

        # ═══════════════════════════════════════════════════════════════════
        # 4. DRUGS AND COSMETICS ACT, 1940 — INDIAN KANOON
        # ═══════════════════════════════════════════════════════════════════
        StatutorySource(
            chunk_id="dca_1940_sec_3a",
            url="https://indiankanoon.org/doc/737172/",
            source_type="kanoon",
            act_name="The Drugs and Cosmetics Act, 1940",
            section_id="Section 3(a) — Ayurvedic, Siddha or Unani drug definition",
            jurisdiction=JurisdictionType.NATIONAL,
            ip_type=IPType.DRUG_REGULATORY,
            effective_date="1940-04-10 (Amended / Chapter IVA added 1964)",
            source_label="Indian Kanoon — Central Acts",
            extract_pattern=r"\(a\)\s*[\"“]?Ayurvedic,\s*Siddha or Unani drug[\"”]?.*?(?=\([b-z]\)|$)",
        ),
        StatutorySource(
            chunk_id="dca_1940_sec_33eeb",
            url="https://indiankanoon.org/doc/1768061/",
            source_type="kanoon",
            act_name="The Drugs and Cosmetics Act, 1940",
            section_id="Section 33EEB — Regulation of manufacture for sale of Ayurvedic drugs",
            jurisdiction=JurisdictionType.NATIONAL,
            ip_type=IPType.DRUG_REGULATORY,
            effective_date="1940-04-10 (Chapter IVA)",
            source_label="Indian Kanoon — Central Acts",
            extract_pattern=None,
        ),

        # ═══════════════════════════════════════════════════════════════════
        # 5. PPV&FR ACT, 2001 — INDIAN KANOON
        # ═══════════════════════════════════════════════════════════════════
        StatutorySource(
            chunk_id="ppvfr_2001_sec_39",
            url="https://indiankanoon.org/doc/1385928/",
            source_type="kanoon",
            act_name="The Protection of Plant Varieties and Farmers' Rights Act, 2001",
            section_id="Section 39 — Farmers' Rights (Conservation & Seeds)",
            jurisdiction=JurisdictionType.NATIONAL,
            ip_type=IPType.BIODIVERSITY_ABS,
            effective_date="2001-10-30",
            source_label="Indian Kanoon — Central Acts",
            extract_pattern=None,
        ),

        # ═══════════════════════════════════════════════════════════════════
        # 6. WTO TRIPS AGREEMENT (1995) — OFFICIAL PDF
        # ═══════════════════════════════════════════════════════════════════
        StatutorySource(
            chunk_id="trips_art_27",
            url="https://www.wto.org/english/docs_e/legal_e/27-trips.pdf",
            source_type="pdf",
            act_name="Agreement on Trade-Related Aspects of Intellectual Property Rights (TRIPS)",
            section_id="Article 27 — Patentable Subject Matter",
            jurisdiction=JurisdictionType.INTERNATIONAL,
            ip_type=IPType.PATENT,
            effective_date="1995-01-01 (Entry into force)",
            source_label="World Trade Organization (Official Treaty PDF)",
            extract_pattern=r"Article\s+27\s*\n?Patentable Subject Matter\s*\n?(.*?)(?=Article\s+28)",
        ),
        StatutorySource(
            chunk_id="trips_art_28",
            url="https://www.wto.org/english/docs_e/legal_e/27-trips.pdf",
            source_type="pdf",
            act_name="Agreement on Trade-Related Aspects of Intellectual Property Rights (TRIPS)",
            section_id="Article 28 — Rights Conferred",
            jurisdiction=JurisdictionType.INTERNATIONAL,
            ip_type=IPType.PATENT,
            effective_date="1995-01-01 (Entry into force)",
            source_label="World Trade Organization (Official Treaty PDF)",
            extract_pattern=r"Article\s+28\s*\n?Rights Conferred\s*\n?(.*?)(?=Article\s+29)",
        ),
        StatutorySource(
            chunk_id="trips_art_39",
            url="https://www.wto.org/english/docs_e/legal_e/27-trips.pdf",
            source_type="pdf",
            act_name="Agreement on Trade-Related Aspects of Intellectual Property Rights (TRIPS)",
            section_id="Article 39 — Protection of Undisclosed Information (Trade Secrets)",
            jurisdiction=JurisdictionType.INTERNATIONAL,
            ip_type=IPType.PATENT,
            effective_date="1995-01-01 (Entry into force)",
            source_label="World Trade Organization (Official Treaty PDF)",
            extract_pattern=r"Article\s+39\s*\n?(.*?)(?=Article\s+40)",
        ),
        StatutorySource(
            chunk_id="trips_art_22",
            url="https://www.wto.org/english/docs_e/legal_e/27-trips.pdf",
            source_type="pdf",
            act_name="Agreement on Trade-Related Aspects of Intellectual Property Rights (TRIPS)",
            section_id="Article 22 — Protection of Geographical Indications",
            jurisdiction=JurisdictionType.INTERNATIONAL,
            ip_type=IPType.TRADEMARK_GI,
            effective_date="1995-01-01 (Entry into force)",
            source_label="World Trade Organization (Official Treaty PDF)",
            extract_pattern=r"Article\s+22\s*\n?Protection of Geographical Indications\s*\n?(.*?)(?=Article\s+23)",
        ),

        # ═══════════════════════════════════════════════════════════════════
        # 7. CBD NAGOYA PROTOCOL (2014) — OFFICIAL PDF
        # ═══════════════════════════════════════════════════════════════════
        StatutorySource(
            chunk_id="nagoya_art_5",
            url="https://www.cbd.int/abs/doc/protocol/nagoya-protocol-en.pdf",
            source_type="pdf",
            act_name="Nagoya Protocol on Access to Genetic Resources and Benefit-Sharing",
            section_id="Article 5 — Fair and Equitable Benefit-Sharing",
            jurisdiction=JurisdictionType.INTERNATIONAL,
            ip_type=IPType.BIODIVERSITY_ABS,
            effective_date="2014-10-12 (Entry into force)",
            source_label="Convention on Biological Diversity (Official Treaty PDF)",
            extract_pattern=r"Article\s+5\s*\n(.*?)(?=Article\s+6)",
        ),
        StatutorySource(
            chunk_id="nagoya_art_6",
            url="https://www.cbd.int/abs/doc/protocol/nagoya-protocol-en.pdf",
            source_type="pdf",
            act_name="Nagoya Protocol on Access to Genetic Resources and Benefit-Sharing",
            section_id="Article 6 — Access to Genetic Resources (Prior Informed Consent)",
            jurisdiction=JurisdictionType.INTERNATIONAL,
            ip_type=IPType.BIODIVERSITY_ABS,
            effective_date="2014-10-12 (Entry into force)",
            source_label="Convention on Biological Diversity (Official Treaty PDF)",
            extract_pattern=r"Article\s+6\s*\n(.*?)(?=Article\s+7)",
        ),
        StatutorySource(
            chunk_id="nagoya_art_7",
            url="https://www.cbd.int/abs/doc/protocol/nagoya-protocol-en.pdf",
            source_type="pdf",
            act_name="Nagoya Protocol on Access to Genetic Resources and Benefit-Sharing",
            section_id="Article 7 — Access to Traditional Knowledge",
            jurisdiction=JurisdictionType.INTERNATIONAL,
            ip_type=IPType.BIODIVERSITY_ABS,
            effective_date="2014-10-12 (Entry into force)",
            source_label="Convention on Biological Diversity (Official Treaty PDF)",
            extract_pattern=r"Article\s+7\s*\n(.*?)(?=Article\s+8)",
        ),
        StatutorySource(
            chunk_id="nagoya_art_12",
            url="https://www.cbd.int/abs/doc/protocol/nagoya-protocol-en.pdf",
            source_type="pdf",
            act_name="Nagoya Protocol on Access to Genetic Resources and Benefit-Sharing",
            section_id="Article 12 — Traditional Knowledge Compliance Measures",
            jurisdiction=JurisdictionType.INTERNATIONAL,
            ip_type=IPType.BIODIVERSITY_ABS,
            effective_date="2014-10-12 (Entry into force)",
            source_label="Convention on Biological Diversity (Official Treaty PDF)",
            extract_pattern=r"Article\s+12\s*\n(.*?)(?=Article\s+13)",
        ),

        # ═══════════════════════════════════════════════════════════════════
        # 8. WIPO GRATK TREATY (GENEVA 2024) — OFFICIAL TREATY PDF
        # ═══════════════════════════════════════════════════════════════════
        StatutorySource(
            chunk_id="wipo_gratk_art_3_mandatory_disclosure",
            url="https://www.wipo.int/wipolex/en/text/592504",
            source_type="wipo_gratk",
            act_name="WIPO Treaty on Intellectual Property, Genetic Resources and Associated Traditional Knowledge (2024)",
            section_id="Article 3 — Mandatory Disclosure Requirement",
            jurisdiction=JurisdictionType.INTERNATIONAL,
            ip_type=IPType.PATENT,
            effective_date="2024-05-24 (Adopted at Geneva Diplomatic Conference)",
            source_label="World Intellectual Property Organization (Official Treaty Document)",
            extract_pattern=r"ARTICLE\s+3\s*\n?DISCLOSURE REQUIREMENT\s*\n?(.*?)(?=ARTICLE\s+4)",
        ),
        StatutorySource(
            chunk_id="wipo_gratk_art_4_non_retroactivity",
            url="https://www.wipo.int/wipolex/en/text/592504",
            source_type="wipo_gratk",
            act_name="WIPO Treaty on Intellectual Property, Genetic Resources and Associated Traditional Knowledge (2024)",
            section_id="Article 4 — Non-Retroactivity",
            jurisdiction=JurisdictionType.INTERNATIONAL,
            ip_type=IPType.PATENT,
            effective_date="2024-05-24 (Adopted at Geneva Diplomatic Conference)",
            source_label="World Intellectual Property Organization (Official Treaty Document)",
            extract_pattern=r"ARTICLE\s+4\s*\n?NON-RETROACTIVITY\s*\n?(.*?)(?=ARTICLE\s+5)",
        ),
        StatutorySource(
            chunk_id="wipo_gratk_art_5_sanctions_remedies",
            url="https://www.wipo.int/wipolex/en/text/592504",
            source_type="wipo_gratk",
            act_name="WIPO Treaty on Intellectual Property, Genetic Resources and Associated Traditional Knowledge (2024)",
            section_id="Article 5 — Sanctions and Remedies",
            jurisdiction=JurisdictionType.INTERNATIONAL,
            ip_type=IPType.PATENT,
            effective_date="2024-05-24 (Adopted at Geneva Diplomatic Conference)",
            source_label="World Intellectual Property Organization (Official Treaty Document)",
            extract_pattern=r"ARTICLE\s+5\s*\n?SANCTIONS AND REMEDIES\s*\n?(.*?)(?=ARTICLE\s+6)",
        ),

        # ═══════════════════════════════════════════════════════════════════
        # 9. PROCEDURAL INTERNATIONAL FILING TREATIES & MICROORGANISM DEPOSITS
        # ═══════════════════════════════════════════════════════════════════
        StatutorySource(
            chunk_id="budapest_treaty_art_3_microorganism_deposit",
            url="https://www.wipo.int/wipolex/en/text/283784",
            source_type="wipo_html",
            act_name="Budapest Treaty on the International Recognition of the Deposit of Microorganisms for the Purposes of Patent Procedure",
            section_id="Article 3 — Recognition and Effect of Deposit of Microorganisms",
            jurisdiction=JurisdictionType.INTERNATIONAL,
            ip_type=IPType.PATENT,
            effective_date="1977-04-28 (Amended 1980)",
            source_label="World Intellectual Property Organization (Official Treaty Text)",
            extract_pattern=r"Article\s+3\s+Recognition and Effect of the Deposit of Microorganisms\s*\(1\)\s*(.*?)(?=Article\s+4)",
        ),
        StatutorySource(
            chunk_id="pct_treaty_art_3_international_app",
            url="https://www.wipo.int/wipolex/en/text/288637",
            source_type="wipo_signed_pdf",
            act_name="Patent Cooperation Treaty (PCT)",
            section_id="Article 3 — The International Application",
            jurisdiction=JurisdictionType.INTERNATIONAL,
            ip_type=IPType.PATENT,
            effective_date="1970-06-19 (Amended 1979, 1984, 2001)",
            source_label="World Intellectual Property Organization (Official Treaty PDF)",
            extract_pattern=r"Article\s+3\s*\n?The International Application\s*\n?(.*?)(?=Article\s+4)",
        ),
        StatutorySource(
            chunk_id="madrid_protocol_art_2_international_registration",
            url="https://www.wipo.int/wipolex/en/text/306126",
            source_type="wipo_html",
            act_name="Protocol Relating to the Madrid Agreement Concerning the International Registration of Marks",
            section_id="Article 2 — Securing Protection through International Registration",
            jurisdiction=JurisdictionType.INTERNATIONAL,
            ip_type=IPType.TRADEMARK_GI,
            effective_date="1989-06-27 (Entry into force 1995)",
            source_label="World Intellectual Property Organization (Official Treaty Text)",
            extract_pattern=r"Article\s+2\s+Securing Protection through International Registration\s*(.*?)(?=Article\s+3)",
        ),
        StatutorySource(
            chunk_id="hague_agreement_art_3_industrial_designs",
            url="https://www.wipo.int/wipolex/en/text/285214",
            source_type="wipo_html",
            act_name="Hague Agreement Concerning the International Registration of Industrial Designs (Geneva Act 1999)",
            section_id="Article 3 — Entitlement to File an International Application",
            jurisdiction=JurisdictionType.INTERNATIONAL,
            ip_type=IPType.PATENT,
            effective_date="1999-07-02 (Entry into force 2004)",
            source_label="World Intellectual Property Organization (Official Treaty Text)",
            extract_pattern=r"Article\s+3\s+Entitlement to File an International Application\s*(.*?)(?=Article\s+4)",
        ),

        # ═══════════════════════════════════════════════════════════════════
        # 10. NATIONAL STATUTES: TRADEMARKS, FSSAI, & RECENT RULES (2024)
        # ═══════════════════════════════════════════════════════════════════
        StatutorySource(
            chunk_id="tm_act_1999_sec_9",
            url="https://indiankanoon.org/doc/480838/",
            source_type="kanoon",
            act_name="The Trade Marks Act, 1999",
            section_id="Section 9 — Absolute grounds for refusal of registration",
            jurisdiction=JurisdictionType.NATIONAL,
            ip_type=IPType.TRADEMARK_GI,
            effective_date="1999-12-30 (Entry into force 2003)",
            source_label="Indian Kanoon — Central Acts",
            extract_pattern=None,
        ),
        StatutorySource(
            chunk_id="tm_act_1999_sec_11",
            url="https://indiankanoon.org/doc/1266858/",
            source_type="kanoon",
            act_name="The Trade Marks Act, 1999",
            section_id="Section 11 — Relative grounds for refusal of registration",
            jurisdiction=JurisdictionType.NATIONAL,
            ip_type=IPType.TRADEMARK_GI,
            effective_date="1999-12-30 (Entry into force 2003)",
            source_label="Indian Kanoon — Central Acts",
            extract_pattern=None,
        ),
        StatutorySource(
            chunk_id="fssai_act_2006_sec_22",
            url="https://indiankanoon.org/doc/1761005/",
            source_type="kanoon",
            act_name="Food Safety and Standards Act, 2006",
            section_id="Section 22 — Foods for special dietary uses, functional foods, nutraceuticals",
            jurisdiction=JurisdictionType.NATIONAL,
            ip_type=IPType.DRUG_REGULATORY,
            effective_date="2006-08-23",
            source_label="Indian Kanoon — Central Acts",
            extract_pattern=None,
        ),
        StatutorySource(
            chunk_id="patents_act_1970_sec_10_budapest_deposit",
            url="https://indiankanoon.org/doc/1217727/",
            source_type="kanoon",
            act_name="The Patents Act, 1970",
            section_id="Section 10(4)(ii) — Deposit of Biological Material under Budapest Treaty & Geographical Origin Disclosure",
            jurisdiction=JurisdictionType.NATIONAL,
            ip_type=IPType.PATENT,
            effective_date="1970-09-19 (Amended 2002, 2005)",
            source_label="Indian Kanoon — Central Acts",
            extract_pattern=r"\(ii\)\s*if the applicant mentions a biological material.*?(?=\(4A\)|\(5\))",
        ),
        # ── Patents (Amendment) Rules, 2024 & Biological Diversity Rules, 2024 ──
        # NOT CURRENTLY INGESTED (as of 2026-09-13). Both IP India's and NBA's
        # direct gazette PDF links are dead (404 / domain redirected to
        # nbaindia.nic.in), and WIPO Lex's "legislation/details" pages for
        # national legislation (unlike its older treaty "/text/" viewer) are
        # rendered client-side by a JS SPA, so they return the app shell, not
        # the document, to a plain HTTP fetch. Rather than hand-type the rule
        # text as a placeholder (banned — CLAUDE.md "Zero text_override"), we
        # omit these two sources until a real fetch path exists (e.g. via
        # browser automation, or a working direct gazette/IP-India URL).
        # See WIPO Lex IN195 (Patents Rules) / IN197 (BD Rules) for reference.

        StatutorySource(
            chunk_id="fssai_ayurveda_aahar_2022_reg_3",
            url="https://agriexchange.apeda.gov.in/ImportRegulations/Indias%20FSSAI%20Notifies%20Final%20Standards%20for%20Ayurveda%20FoodsNew%20DelhiIndiaIN20220054.pdf",
            source_type="pdf",
            act_name="Food Safety and Standards (Ayurveda Aahara) Regulations, 2022",
            section_id="Regulation 3 — 'Ayurveda Aahara' Definition, Schedule A Texts & Drug/Cosmetic Exclusions",
            jurisdiction=JurisdictionType.NATIONAL,
            ip_type=IPType.DRUG_REGULATORY,
            effective_date="2022-05-06 (Notified in Gazette; implemented 2022-05-05)",
            # NOTE: FSSAI's own gazette PDF link (fssai.gov.in/upload/notifications/...)
            # now 404s — the site migrated to a JS SPA that serves the app shell for
            # any path. This is a USDA Foreign Agricultural Service GAIN report
            # (IN2022-0054) that directly quotes the regulation's operative
            # definition and exclusion list from the official notification — a real,
            # live, fetchable secondary source, honestly labeled as such below.
            source_label="USDA Foreign Agricultural Service — GAIN Report IN2022-0054 (quoting FSSAI Notification F.No. Stds/SP-05/A-1.Y(01), Ayurveda Aahara Regulations 2022)",
            extract_pattern=r"Background:\s*(.*?)(?=What Makes a Food an Ayurveda Aahara Food\?)",
        ),
    ]


class RealLegalScraper:
    """
    Production-grade statutory scraper that fetches directly from live public portals:
    - Indian Kanoon for Indian Bare Acts
    - WTO, CBD, and WIPO for International Treaties
    With persistent disk caching in data/cache/ for offline resilience and reproducibility.
    """

    def __init__(self, timeout: float = HTTP_TIMEOUT):
        self.client = httpx.Client(
            headers=HEADERS,
            timeout=timeout,
            follow_redirects=True,
        )
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._doc_cache: dict[str, str] = {}

    def _get_cache_path(self, key: str, ext: str = "txt") -> Path:
        safe_key = re.sub(r"[^a-zA-Z0-9_\-]", "_", key)[:80]
        return CACHE_DIR / f"{safe_key}.{ext}"

    def _fetch_kanoon_text(self, url: str) -> Optional[str]:
        cache_file = self._get_cache_path(url, "txt")
        if cache_file.exists():
            return cache_file.read_text(encoding="utf-8")

        try:
            logger.info(f"    Fetching Kanoon: {url}")
            resp = self.client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            doc = soup.find("div", class_="akoma-ntoso") or soup.find("div", class_="maindoc")
            if not doc:
                logger.warning(f"    No document container found in {url}")
                return None
            for tag in doc(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = doc.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text)
            # Remove Kanoon preamble if present
            m = re.search(r"(Section\s+\d+.*|\d+\.\s+.*)", text)
            clean_text = m.group(0) if m else text
            cache_file.write_text(clean_text, encoding="utf-8")
            logger.info(f"    ✓ Kanoon extracted: {len(clean_text):,} chars")
            return clean_text
        except Exception as e:
            logger.warning(f"    ✗ Kanoon fetch failed: {url} — {e}")
            return None

    def _fetch_pdf_text(self, url: str) -> Optional[str]:
        cache_file = self._get_cache_path(url, "txt")
        if cache_file.exists():
            return cache_file.read_text(encoding="utf-8")

        try:
            logger.info(f"    Downloading PDF: {url}")
            resp = self.client.get(url)
            resp.raise_for_status()
            reader = pypdf.PdfReader(io.BytesIO(resp.content))
            pages_text = [p.extract_text() for p in reader.pages if p.extract_text()]
            full_text = "\n".join(pages_text)
            cache_file.write_text(full_text, encoding="utf-8")
            logger.info(f"    ✓ PDF extracted: {len(full_text):,} chars from {len(reader.pages)} pages")
            return full_text
        except Exception as e:
            logger.warning(f"    ✗ PDF fetch failed: {url} — {e}")
            return None

    def _fetch_wipo_gratk_text(self, url: str) -> Optional[str]:
        cache_file = self._get_cache_path("wipo_gratk_2024", "txt")
        if cache_file.exists():
            return cache_file.read_text(encoding="utf-8")

        try:
            logger.info(f"    Locating WIPO GRATK English PDF from: {url}")
            resp = self.client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            iframe = soup.find("iframe")
            if not iframe or not iframe.get("src"):
                logger.warning("    No PDF iframe found on WIPO GRATK text page")
                return None
            pdf_url = iframe.get("src")
            logger.info(f"    Downloading WIPO GRATK PDF from signed CDN...")
            pdf_resp = self.client.get(pdf_url)
            pdf_resp.raise_for_status()
            reader = pypdf.PdfReader(io.BytesIO(pdf_resp.content))
            full_text = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
            cache_file.write_text(full_text, encoding="utf-8")
            logger.info(f"    ✓ WIPO GRATK extracted: {len(full_text):,} chars")
            return full_text
        except Exception as e:
            logger.warning(f"    ✗ WIPO GRATK fetch failed: {e}")
            return None

    def _fetch_wipo_html_text(self, url: str) -> Optional[str]:
        cache_file = self._get_cache_path(url, "txt")
        if cache_file.exists():
            return cache_file.read_text(encoding="utf-8")

        try:
            logger.info(f"    Fetching WIPO HTML: {url}")
            resp = self.client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            main = (
                soup.find("div", class_="content")
                or soup.find("div", id="content")
                or soup.find("div", class_="txt-content")
                or soup.find("main")
            )
            if not main:
                main = soup
            for tag in main(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = main.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text)
            cache_file.write_text(text, encoding="utf-8")
            logger.info(f"    ✓ WIPO HTML extracted: {len(text):,} chars")
            return text
        except Exception as e:
            logger.warning(f"    ✗ WIPO HTML fetch failed: {url} — {e}")
            return None

    def _fetch_wipo_signed_pdf_text(self, url: str, cache_name: str) -> Optional[str]:
        cache_file = self._get_cache_path(cache_name, "txt")
        if cache_file.exists():
            return cache_file.read_text(encoding="utf-8")

        try:
            logger.info(f"    Locating WIPO signed PDF from: {url}")
            resp = self.client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            iframe = soup.find("iframe")
            if not iframe or not iframe.get("src"):
                logger.warning(f"    No PDF iframe found on {url}")
                return None
            pdf_url = iframe.get("src")
            logger.info(f"    Downloading signed WIPO PDF...")
            pdf_resp = self.client.get(pdf_url)
            pdf_resp.raise_for_status()
            reader = pypdf.PdfReader(io.BytesIO(pdf_resp.content))
            full_text = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
            cache_file.write_text(full_text, encoding="utf-8")
            logger.info(f"    ✓ WIPO PDF extracted: {len(full_text):,} chars from {len(reader.pages)} pages")
            return full_text
        except Exception as e:
            logger.warning(f"    ✗ WIPO PDF fetch failed: {url} — {e}")
            return None

    def scrape_source(self, source: StatutorySource) -> Optional[LegalChunk]:
        """Fetches document, extracts section, and constructs a LegalChunk."""
        if source.source_type == "kanoon":
            full_text = self._fetch_kanoon_text(source.url)
        elif source.source_type == "pdf":
            full_text = self._fetch_pdf_text(source.url)
        elif source.source_type == "wipo_gratk":
            full_text = self._fetch_wipo_gratk_text(source.url)
        elif source.source_type == "wipo_html":
            full_text = self._fetch_wipo_html_text(source.url)
        elif source.source_type == "wipo_signed_pdf":
            full_text = self._fetch_wipo_signed_pdf_text(source.url, source.chunk_id)
        else:
            logger.warning(f"Unknown source type: {source.source_type}")
            return None

        if not full_text:
            return None

        # Extract target section
        if source.extract_pattern:
            m = re.search(source.extract_pattern, full_text, re.DOTALL | re.IGNORECASE)
            if m:
                extracted = m.group(1) if m.groups() else m.group(0)
                section_text = re.sub(r"\s+", " ", extracted).strip()[:source.max_extract_chars]
            else:
                logger.warning(f"Pattern '{source.extract_pattern[:30]}...' not matched for {source.chunk_id}, using excerpt")
                section_text = re.sub(r"\s+", " ", full_text).strip()[:source.max_extract_chars]
        else:
            section_text = re.sub(r"\s+", " ", full_text).strip()[:source.max_extract_chars]

        if len(section_text) < 30:
            logger.warning(f"Extracted text too short for {source.chunk_id}")
            return None

        return LegalChunk(
            chunk_id=source.chunk_id,
            source=source.source_label,
            act_name=source.act_name,
            section_id=source.section_id,
            jurisdiction=source.jurisdiction,
            effective_date=source.effective_date,
            ip_type=source.ip_type,
            status=ProvenanceStatus.VERIFIED_PUBLIC,
            official_url=source.url,
            text=section_text,
        )

    def scrape_all(self, sources: List[StatutorySource]) -> Tuple[List[LegalChunk], List[str]]:
        chunks = []
        failed = []
        for i, src in enumerate(sources):
            logger.info(f"[{i+1}/{len(sources)}] Fetching {src.chunk_id}...")
            chunk = self.scrape_source(src)
            if chunk:
                chunks.append(chunk)
            else:
                failed.append(src.chunk_id)
            time.sleep(0.3)
        return chunks, failed

    def close(self):
        self.client.close()


def get_tkdl_mock_entries() -> List[LegalChunk]:
    """
    Returns TKDL illustrative entries with status=MOCK_PENDING_ACCESS per Rule R7.
    TKDL is not publicly accessible on the internet without a CSIR bilateral agreement.
    """
    return [
        LegalChunk(
            chunk_id="mock_tkdl_triphala_prior_art",
            source="Traditional Knowledge Digital Library (TKDL) — MoU Required",
            act_name="TKDL Classical Formulation Reference (Illustrative)",
            section_id="TKDL Entry AK/102 — Triphala Churna",
            jurisdiction=JurisdictionType.NATIONAL,
            effective_date="2001-onwards (access via CSIR MoU only)",
            ip_type=IPType.PATENT,
            status=ProvenanceStatus.MOCK_PENDING_ACCESS,
            official_url="https://tkdl.res.in",
            text=(
                "[ILLUSTRATIVE ONLY — NOT REAL TKDL DATA — MoU with CSIR required for real access]\n"
                "Triphala Churna: Equal parts Haritaki (Terminalia chebula), Bibhitaki (Terminalia bellirica), "
                "Amalaki (Phyllanthus emblica). Referenced in Charaka Samhita Chikitsasthana Chapter 1 as "
                "a digestive, rasayana, and wound-healing compound. Constitutes Section 3(p) prior art. "
                "Any patent claim over Triphala composition faces TKDL-backed opposition."
            ),
        ),
    ]


def run_ingestion(persist_path: Optional[str] = None) -> List[LegalChunk]:
    """Runs complete ingestion pipeline and populates Qdrant vector store."""
    from ml_pipeline.embeddings.vector_store_manager import VectorStoreManager

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    logger.info("=" * 65)
    logger.info("Charaka IP Corpus Ingestion — Real Verified Sources Only")
    logger.info("=" * 65)

    scraper = RealLegalScraper()
    sources = get_verified_sources()
    real_chunks, failed_ids = scraper.scrape_all(sources)
    scraper.close()

    mock_chunks = get_tkdl_mock_entries()
    all_chunks = real_chunks + mock_chunks

    logger.info("=" * 65)
    logger.info(f"Ingestion Results:")
    logger.info(f"  ✓ Real statutory chunks fetched: {len(real_chunks)}/{len(sources)}")
    if failed_ids:
        logger.warning(f"  ✗ Failed: {failed_ids}")
    logger.info(f"  ⚠ TKDL mock chunk (R7): {len(mock_chunks)}")
    logger.info(f"  Total chunks to index: {len(all_chunks)}")
    logger.info("=" * 65)

    manager = VectorStoreManager(location=persist_path)
    indexed = manager.index_chunks(all_chunks)
    logger.info(f"Indexed {indexed} chunks into '{manager.collection_name}'.")

    # Run verification test query
    res = manager.search("Section 3(p) traditional knowledge Ayurvedic formulation", jurisdiction=JurisdictionType.NATIONAL, top_k=2)
    logger.info(f"Test Search top hit: {res[0].chunk_id if res else 'None'} ({res[0].section_id if res else ''})")

    return all_chunks


if __name__ == "__main__":
    run_ingestion()
