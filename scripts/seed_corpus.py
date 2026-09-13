"""
Corpus Seeding Script for IP-SAKTI Sahayak (SIH PS045)
Populates Qdrant with authoritative statutory sections, rules, treaties, and illustrative TKDL records.
Enforces rules R7 (provenance labeling) and R10 (version stamping).
Uses RealLegalScraper backed by disk cache (Indian Kanoon, WTO TRIPS, CBD Nagoya, WIPO GRATK).
"""

import logging
from typing import List

from ml_pipeline.crag.schema import JurisdictionType, LegalChunk
from ml_pipeline.embeddings.vector_store_manager import VectorStoreManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("seed_corpus")


def get_foundational_corpus() -> List[LegalChunk]:
    """
    Returns the foundational legal corpus by scraping (or reading disk-cached copies of)
    verified live sources: Indian Kanoon for Indian Central Acts, official WTO/CBD/WIPO
    treaty PDFs, and the TKDL illustrative entry (marked MOCK_PENDING_ACCESS per Rule R7).

    Per CLAUDE.md's "Zero Hallucination" / "Zero text_override" rules: if a source fails
    to scrape, it is simply omitted (see failed_ids logging below) rather than replaced
    with hand-typed placeholder law. A smaller corpus correctly causes Rule R1 (safe
    abstention) to trigger for queries it can no longer support — that is intended
    behavior, not a defect to mask with a fake fallback.
    """
    from ml_pipeline.corpus_ingestion.scrapers.legal_scraper import (
        RealLegalScraper,
        get_tkdl_mock_entries,
        get_verified_sources,
    )

    scraper = RealLegalScraper()
    sources = get_verified_sources()
    chunks, failed_ids = scraper.scrape_all(sources)
    scraper.close()

    if failed_ids:
        logger.warning(f"{len(failed_ids)}/{len(sources)} statutory sources failed to scrape: {failed_ids}")
    logger.info(f"Loaded {len(chunks)}/{len(sources)} real statutory chunks via RealLegalScraper.")

    return chunks + get_tkdl_mock_entries()


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
