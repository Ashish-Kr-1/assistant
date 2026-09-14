"""
Process-wide cached CRAGPipeline instance.

Both /api/v1/query (direct legal Q&A) and the Phase 4 Research Engine (case
research/report generation) need the same indexed corpus + pipeline. This
module gives them a single shared instance instead of each maintaining its
own VectorStoreManager and re-indexing the foundational corpus separately.
"""

import logging
import threading

from ml_pipeline.crag.graph import CRAGPipeline
from ml_pipeline.embeddings.vector_store_manager import VectorStoreManager

logger = logging.getLogger("pipeline_singleton")

_pipeline_instance: CRAGPipeline = None
_lock = threading.Lock()


def get_crag_pipeline() -> CRAGPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        with _lock:
            if _pipeline_instance is None:
                logger.info("Initializing shared CRAG pipeline...")
                from scripts.seed_corpus import get_foundational_corpus
                manager = VectorStoreManager()
                corpus = get_foundational_corpus()
                manager.index_chunks(corpus)
                _pipeline_instance = CRAGPipeline(vector_store=manager)
    return _pipeline_instance
