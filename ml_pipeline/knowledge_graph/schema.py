class KnowledgeGraphSchema:
    """
    Neo4j Knowledge Graph Schema definition for Charaka IP.
    Links Ayurvedic Herbs, Formulations, Statutes, Patent Bars, and ABS Obligations.
    """

    NODE_TYPES = [
        "Herb",              # e.g., Curcuma longa, Withania somnifera
        "Formulation",       # e.g., Chyawanprash, Triphala, Standardized Extract
        "AuthoritativeText", # e.g., Charaka Samhita, Sharangadhara Samhita
        "Statute",           # e.g., Patents Act 1970, Biological Diversity Act 2023
        "Section",           # e.g., Section 3(p), Section 3(d), Rule 122E
        "TreatyArticle",     # e.g., WIPO GRATK Article 3, Nagoya Article 5
        "PatentBar"          # e.g., Prior Art, Admixture Bar
    ]

    RELATIONSHIPS = [
        "MENTIONED_IN",       # (Formulation) -> (AuthoritativeText)
        "CONTAINS_HERB",      # (Formulation) -> (Herb)
        "GOVERNED_BY",        # (Formulation) -> (Statute)
        "BARRED_BY",          # (Formulation) -> (Section) [e.g. Sec 3(p)]
        "REQUIRES_APPROVAL",  # (Herb/Formulation) -> (Statute) [e.g. NBA Form I]
        "PROTECTED_IN"        # (Formulation) -> (Database) [e.g. TKDL]
    ]
