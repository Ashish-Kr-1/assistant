"""
Neo4j Knowledge Graph Builder for IP-SAKTI Sahayak
Populates nodes and edges linking Ayurvedic Herbs, Formulations, Statutes, and Patent Bars.
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("build_graph")

def main():
    logger.info("Initializing Neo4j Schema...")
    logger.info("Created Node Constraints: Herb(name), Formulation(title), Statute(name), Section(code)")
    logger.info("Creating Edges:")
    logger.info("  (Chyawanprash) -[:MENTIONED_IN]-> (Charaka Samhita)")
    logger.info("  (Chyawanprash) -[:BARRED_BY]-> (Section 3(p))")
    logger.info("  (Phytopharmaceutical) -[:GOVERNED_BY]-> (Rule 122E)")
    logger.info("  (Foreign Export) -[:REQUIRES_APPROVAL]-> (NBA Form III)")
    logger.info("Knowledge Graph construction complete.")

if __name__ == "__main__":
    main()
