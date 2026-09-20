"""
Corpus Seeding Script for Charaka IP (SIH PS045)
Populates Qdrant with authoritative statutory sections, rules, treaties, and illustrative TKDL records.
Enforces rules R7 (provenance labeling) and R10 (version stamping).
Uses RealLegalScraper backed by disk cache (Indian Kanoon, WTO TRIPS, CBD Nagoya, WIPO GRATK).
"""

import json
import logging
from pathlib import Path
from typing import List
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from ml_pipeline.crag.schema import JurisdictionType, LegalChunk
from ml_pipeline.embeddings.vector_store_manager import VectorStoreManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("seed_corpus")

CORPUS_CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / "foundational_corpus.json"


def get_foundational_corpus(force_refresh: bool = False) -> List[LegalChunk]:
    """
    Returns the foundational legal corpus.
    Loads from data/foundational_corpus.json (<5ms) if available, otherwise falls back
    to scraping live verified sources and writing the cache.
    """
    if not force_refresh and CORPUS_CACHE_FILE.exists():
        try:
            with open(CORPUS_CACHE_FILE, "r", encoding="utf-8") as f:
                raw_list = json.load(f)
            chunks = [
                LegalChunk.model_validate(item) if hasattr(LegalChunk, "model_validate") else LegalChunk(**item)
                for item in raw_list
            ]
            if len(chunks) >= 38:
                logger.info(f"Loaded {len(chunks)} pre-cached legal chunks from {CORPUS_CACHE_FILE.name} in <5ms.")
                return chunks
        except Exception as e:
            logger.warning(f"Failed to read corpus cache {CORPUS_CACHE_FILE}: {e}. Falling back to scraper.")

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

    all_chunks = chunks + get_tkdl_mock_entries()

    # Save to disk cache for fast future startup
    try:
        CORPUS_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        dumped = [
            c.model_dump() if hasattr(c, "model_dump") else c.dict()
            for c in all_chunks
        ]
        with open(CORPUS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(dumped, f, indent=2, ensure_ascii=False)
        logger.info(f"Cached {len(all_chunks)} legal chunks to {CORPUS_CACHE_FILE}.")
    except Exception as e:
        logger.warning(f"Could not write corpus cache: {e}")

    return all_chunks


def seed_corpus(force_reindex: bool = False):
    logger.info("Initializing VectorStoreManager...")
    manager = VectorStoreManager()
    if not force_reindex and manager.count() >= 38:
        logger.info(f"Qdrant collection '{manager.collection_name}' already contains {manager.count()} chunks. Re-indexing skipped.")
        return manager

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
    if test_results:
        logger.info(f"Test search returned {len(test_results)} chunk(s). Top chunk: {test_results[0].chunk_id}")
    return manager


if __name__ == "__main__":
    seed_corpus()
