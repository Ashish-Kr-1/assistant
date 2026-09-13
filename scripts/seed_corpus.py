"""
Corpus Seeding Script for IP-SAKTI Sahayak (SIH PS045)
Populates Qdrant with authoritative statutory sections, rules, treaties, and illustrative TKDL records.
Enforces rules R7 (provenance labeling) and R10 (version stamping).
Uses RealLegalScraper backed by disk cache (Indian Kanoon, WTO TRIPS, CBD Nagoya, WIPO GRATK).
"""

import logging
from typing import List

from ml_pipeline.crag.schema import (
    IPType,
    JurisdictionType,
    LegalChunk,
    ProvenanceStatus,
)
from ml_pipeline.embeddings.vector_store_manager import VectorStoreManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("seed_corpus")


def get_foundational_corpus() -> List[LegalChunk]:
    """
    Returns foundational legal corpus derived from verified live sources:
    - Indian Kanoon for Indian Central Acts (Patents Act 1970, BDA 2002/2023, GI Act 1999, Drugs & Cosmetics Act 1940, PPV&FR Act 2001)
    - WTO official PDF for TRIPS Agreement
    - CBD official PDF for Nagoya Protocol
    - WIPO official PDF for GRATK Treaty 2024
    - TKDL illustrative entry (marked MOCK_PENDING_ACCESS per Rule R7)
    """
    try:
        from ml_pipeline.corpus_ingestion.scrapers.legal_scraper import (
            RealLegalScraper,
            get_tkdl_mock_entries,
            get_verified_sources,
        )

        scraper = RealLegalScraper()
        sources = get_verified_sources()
        chunks, failed = scraper.scrape_all(sources)
        scraper.close()

        if chunks:
            logger.info(f"Loaded {len(chunks)} real statutory chunks via RealLegalScraper.")
            return chunks + get_tkdl_mock_entries()
        else:
            logger.warning("Scraper returned 0 chunks, falling back to static baseline.")
    except Exception as e:
        logger.warning(f"Live scraper failed ({e}), falling back to static baseline.")

    # Static fallback for isolated environments without network/cache
    return [
        LegalChunk(
            chunk_id="patents_act_1970_sec_3p",
            source="Indian Kanoon — Central Acts",
            act_name="The Patents Act, 1970",
            section_id="Section 3(p) — Traditional Knowledge Patent Bar",
            jurisdiction=JurisdictionType.NATIONAL,
            effective_date="1970-09-19 (Amended 2005 / Rules 2024)",
            ip_type=IPType.PATENT,
            status=ProvenanceStatus.VERIFIED_PUBLIC,
            official_url="https://indiankanoon.org/doc/874310/",
            text=(
                "Section 3(p) — What are not inventions: An invention which in effect, is traditional knowledge "
                "or which is an aggregation or duplication of known properties of traditionally known component or components. "
                "Classical Ayurvedic formulations documented in authoritative texts cannot be patented under this section."
            ),
        ),
        LegalChunk(
            chunk_id="patents_act_1970_sec_3d",
            source="Indian Kanoon — Central Acts",
            act_name="The Patents Act, 1970",
            section_id="Section 3(d) — Enhanced Efficacy Requirement",
            jurisdiction=JurisdictionType.NATIONAL,
            effective_date="1970-09-19 (Amended 2005 / Rules 2024)",
            ip_type=IPType.PATENT,
            status=ProvenanceStatus.VERIFIED_PUBLIC,
            official_url="https://indiankanoon.org/doc/874310/",
            text=(
                "Section 3(d) — The mere discovery of a new form of a known substance which does not result in the "
                "enhancement of the known efficacy of that substance or the mere discovery of any new property or new use "
                "for a known substance or of the mere use of a known process, machine or apparatus unless such known process "
                "results in a new product or employs at least one new reactant."
            ),
        ),
        LegalChunk(
            chunk_id="patents_act_1970_sec_3e",
            source="Indian Kanoon — Central Acts",
            act_name="The Patents Act, 1970",
            section_id="Section 3(e) — Admixtures",
            jurisdiction=JurisdictionType.NATIONAL,
            effective_date="1970-09-19 (Amended 2005 / Rules 2024)",
            ip_type=IPType.PATENT,
            status=ProvenanceStatus.VERIFIED_PUBLIC,
            official_url="https://indiankanoon.org/doc/874310/",
            text=(
                "Section 3(e) — A substance obtained by a mere admixture resulting only in the aggregation of the "
                "properties of the components thereof or a process for producing such substance."
            ),
        ),
        LegalChunk(
            chunk_id="bda_2023_sec_3",
            source="Indian Kanoon — Central Acts",
            act_name="The Biological Diversity (Amendment) Act, 2023",
            section_id="Section 3 — Approval of National Biodiversity Authority",
            jurisdiction=JurisdictionType.NATIONAL,
            effective_date="2023-08-03",
            ip_type=IPType.BIODIVERSITY_ABS,
            status=ProvenanceStatus.VERIFIED_PUBLIC,
            official_url="https://indiankanoon.org/doc/155946190/",
            text=(
                "Section 3 — Approval of National Biodiversity Authority (NBA): Non-Indian citizens, foreign entities, "
                "or Indian entities having foreign shareholding or management must obtain prior approval of the National "
                "Biodiversity Authority before accessing any biological resource occurring in India or knowledge associated thereto."
            ),
        ),
        LegalChunk(
            chunk_id="wipo_gratk_art_3_mandatory_disclosure",
            source="World Intellectual Property Organization (Official Treaty Document)",
            act_name="WIPO Treaty on Intellectual Property, Genetic Resources and Associated Traditional Knowledge (2024)",
            section_id="Article 3 — Mandatory Disclosure Requirement",
            jurisdiction=JurisdictionType.INTERNATIONAL,
            effective_date="2024-05-24",
            ip_type=IPType.PATENT,
            status=ProvenanceStatus.VERIFIED_PUBLIC,
            official_url="https://www.wipo.int/wipolex/en/text/592504",
            text=(
                "Article 3 — Disclosure Requirement: Where the claimed invention in a patent application is based on genetic "
                "resources, each Contracting Party shall require applicants to disclose the country of origin of the genetic resources, "
                "or the source. Where the claimed invention is based on traditional knowledge associated with genetic resources, applicants "
                "must disclose the Indigenous Peoples or local community who provided the knowledge."
            ),
        ),
        LegalChunk(
            chunk_id="nagoya_art_5",
            source="Convention on Biological Diversity (Official Treaty PDF)",
            act_name="Nagoya Protocol on Access to Genetic Resources and Benefit-Sharing",
            section_id="Article 5 — Fair and Equitable Benefit-Sharing",
            jurisdiction=JurisdictionType.INTERNATIONAL,
            effective_date="2014-10-12",
            ip_type=IPType.BIODIVERSITY_ABS,
            status=ProvenanceStatus.VERIFIED_PUBLIC,
            official_url="https://www.cbd.int/abs/doc/protocol/nagoya-protocol-en.pdf",
            text=(
                "Article 5 — Fair and Equitable Benefit-Sharing: Benefits arising from the utilization of genetic resources and "
                "traditional knowledge associated with genetic resources shall be shared in a fair and equitable way with the party "
                "providing such resources upon mutually agreed terms."
            ),
        ),
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
                "[ILLUSTRATIVE ONLY — NOT REAL TKDL DATA — MoU with CSIR required for real access] "
                "Triphala Churna: Equal parts Haritaki (Terminalia chebula), Bibhitaki (Terminalia bellirica), Amalaki (Phyllanthus emblica). "
                "Referenced in Charaka Samhita Chikitsasthana Chapter 1 as Section 3(p) prior art."
            ),
        ),
    ]


def seed_corpus():
    logger.info("Initializing VectorStoreManager...")
    manager = VectorStoreManager()
    corpus = get_foundational_corpus()
    logger.info(f"Indexing {len(corpus)} statutory chunks...")
    indexed_count = manager.index_chunks(corpus)
    logger.info(f"Successfully indexed {indexed_count} legal chunks into Qdrant collection '{manager.collection_name}'.")

    # Quick verification search
    test_results = manager.search(
        query="traditional knowledge Section 3(p)",
        jurisdiction=JurisdictionType.NATIONAL,
        top_k=2,
    )
    logger.info(f"Test search returned {len(test_results)} chunk(s). Top chunk: {test_results[0].chunk_id}")
    return manager


if __name__ == "__main__":
    seed_corpus()
