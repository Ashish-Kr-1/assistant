"""
knowledge_graph/builder.py — Populates the Charaka IP Knowledge Graph with
statutory provisions, cross-statute clearance rules, authorities, treaties, and
TKDL prior-art relationships using NetworkX.
"""

import networkx as nx
from knowledge_graph.schema import EdgeType, KGEdge, KGNode, NodeType

_GRAPH_INSTANCE = None


def build_charak_knowledge_graph() -> nx.MultiDiGraph:
    """
    Build and return a fully populated NetworkX MultiDiGraph representing
    the complex legal and regulatory topology of Indian IP and AYUSH law.
    """
    g = nx.MultiDiGraph()

    # ─────────────────────────────────────────────────────────────────────────
    # 1. NODES
    # ─────────────────────────────────────────────────────────────────────────

    nodes = [
        # --- Statutes & Treaties ---
        KGNode(
            id="IN_PATENTS_ACT_1970",
            name="Patents Act 1970 (India)",
            node_type=NodeType.STATUTE,
            jurisdiction="IN",
            ip_type="patent",
            description="The primary legislation governing patent grants, examinations, and non-patentable subject matter in India.",
            citation="https://www.indiacode.nic.in/handle/123456789/1392",
        ),
        KGNode(
            id="IN_BDA_2002",
            name="Biological Diversity Act 2002 (India)",
            node_type=NodeType.STATUTE,
            jurisdiction="IN",
            ip_type="abs",
            description="Law regulating access to biological resources occurring in India and equitable sharing of benefits.",
            citation="https://www.indiacode.nic.in/handle/123456789/2046",
        ),
        KGNode(
            id="IN_DRUGS_ACT_1940",
            name="Drugs and Cosmetics Act 1940 (India)",
            node_type=NodeType.STATUTE,
            jurisdiction="IN",
            ip_type="ayush",
            description="Governs the manufacture, sale, and distribution of drugs, including Ayurveda, Siddha, and Unani (ASU) medicines under Chapter IV-A.",
            citation="https://www.indiacode.nic.in/handle/123456789/2381",
        ),
        KGNode(
            id="IN_TM_ACT_1999",
            name="Trade Marks Act 1999 (India)",
            node_type=NodeType.STATUTE,
            jurisdiction="IN",
            ip_type="trademark",
            description="Regulates registration and protection of trademarks, prevention of fraudulent marks, and passing off in India.",
            citation="https://www.indiacode.nic.in/handle/123456789/1993",
        ),
        KGNode(
            id="IN_GI_ACT_1999",
            name="Geographical Indications of Goods Act 1999 (India)",
            node_type=NodeType.STATUTE,
            jurisdiction="IN",
            ip_type="gi",
            description="Provides for registration and enhanced legal protection of geographical indications relating to goods, including agricultural and traditional goods.",
            citation="https://www.indiacode.nic.in/handle/123456789/1986",
        ),
        KGNode(
            id="IN_COPYRIGHT_ACT_1957",
            name="Copyright Act 1957 (India)",
            node_type=NodeType.STATUTE,
            jurisdiction="IN",
            ip_type="copyright",
            description="Governs copyright protection for original literary, dramatic, musical, artistic works, sound recordings, and computer programs.",
            citation="https://www.indiacode.nic.in/handle/123456789/1367",
        ),
        KGNode(
            id="INTL_TRIPS_AGREEMENT",
            name="TRIPS Agreement (WTO)",
            node_type=NodeType.TREATY,
            jurisdiction="INTL",
            ip_type="patent",
            description="Agreement on Trade-Related Aspects of Intellectual Property Rights administered by the WTO setting global minimum standards.",
            citation="https://www.wto.org/english/docs_e/legal_e/27-trips_01_e.htm",
        ),
        KGNode(
            id="INTL_CBD_1992",
            name="Convention on Biological Diversity (CBD 1992)",
            node_type=NodeType.TREATY,
            jurisdiction="INTL",
            ip_type="abs",
            description="International treaty establishing sovereign national rights over biological resources, Prior Informed Consent (PIC), and fair benefit sharing.",
            citation="https://www.cbd.int/convention/text/",
        ),
        KGNode(
            id="INTL_NAGOYA_PROTOCOL",
            name="Nagoya Protocol on ABS (2010)",
            node_type=NodeType.TREATY,
            jurisdiction="INTL",
            ip_type="abs",
            description="Supplementary agreement to the CBD providing a transparent legal framework for Access and Benefit-Sharing of genetic resources and traditional knowledge.",
            citation="https://www.cbd.int/abs/",
        ),
        KGNode(
            id="INTL_MADRID_PROTOCOL",
            name="Madrid Protocol (WIPO)",
            node_type=NodeType.TREATY,
            jurisdiction="INTL",
            ip_type="trademark",
            description="International system for the registration and management of marks in multiple jurisdictions via a single application.",
            citation="https://www.wipo.int/madrid/en/",
        ),
        KGNode(
            id="INTL_LISBON_SYSTEM",
            name="Lisbon Agreement & Geneva Act (WIPO)",
            node_type=NodeType.TREATY,
            jurisdiction="INTL",
            ip_type="gi",
            description="International system for the protection of Appellations of Origin and Geographical Indications.",
            citation="https://www.wipo.int/lisbon/en/",
        ),

        # --- Key Sections & Articles ---
        KGNode(
            id="SEC_PATENTS_3P",
            name="Section 3(p) — Traditional Knowledge Exclusion",
            node_type=NodeType.SECTION,
            jurisdiction="IN",
            ip_type="patent",
            description="Statutory bar excluding an invention which in effect is traditional knowledge or which is an aggregation or duplication of known properties of traditionally known component or components.",
            citation="Patents Act 1970 §3(p)",
            metadata={"statutory_bar": True, "requires_synergy_proof": True},
        ),
        KGNode(
            id="SEC_PATENTS_3E",
            name="Section 3(e) — Mere Admixture Exclusion",
            node_type=NodeType.SECTION,
            jurisdiction="IN",
            ip_type="patent",
            description="Excludes substances obtained by a mere admixture resulting only in aggregation of the properties of the components thereof, unless synergistic effect is scientifically demonstrated.",
            citation="Patents Act 1970 §3(e)",
            metadata={"requires_synergy_proof": True},
        ),
        KGNode(
            id="SEC_PATENTS_3D",
            name="Section 3(d) — Enhanced Efficacy Standard",
            node_type=NodeType.SECTION,
            jurisdiction="IN",
            ip_type="patent",
            description="Excludes mere discovery of a new form of a known substance which does not result in the enhancement of the known efficacy (Novartis AG v. Union of India standard).",
            citation="Patents Act 1970 §3(d)",
            metadata={"landmark_case": "Novartis AG v. Union of India (2013)"},
        ),
        KGNode(
            id="SEC_PATENTS_6_ORIGIN",
            name="Section 10(4)(d)(ii) & Section 6 — Biological Origin Disclosure",
            node_type=NodeType.SECTION,
            jurisdiction="IN",
            ip_type="patent",
            description="Mandates that the patent specification disclose the source and geographical origin of the biological material in the specification, and obtain NBA permission where applicable.",
            citation="Patents Act 1970 §10(4)(d)(ii)",
        ),
        KGNode(
            id="SEC_BDA_6_CLEARANCE",
            name="Section 6 BDA — Mandatory NBA Clearance for IPR",
            node_type=NodeType.SECTION,
            jurisdiction="IN",
            ip_type="abs",
            description="No person shall apply for any intellectual property right, in or outside India, for any invention based on any research or information on a biological resource obtained from India, without obtaining previous approval of the National Biodiversity Authority.",
            citation="Biological Diversity Act 2002 §6(1)",
            metadata={"mandatory_prior_approval": True, "form": "Form III"},
        ),
        KGNode(
            id="SEC_BDA_3_FOREIGN",
            name="Section 3 BDA — Access by Non-Indian Entities",
            node_type=NodeType.SECTION,
            jurisdiction="IN",
            ip_type="abs",
            description="Prohibits non-citizens, non-residents, and companies with foreign participation/equity from obtaining any biological resource or associated knowledge without previous approval of the NBA.",
            citation="Biological Diversity Act 2002 §3",
        ),
        KGNode(
            id="RULE_AYUSH_158B",
            name="Rule 158-B Drugs & Cosmetics Rules — ASU Drug Licensing",
            node_type=NodeType.RULE,
            jurisdiction="IN",
            ip_type="ayush",
            description="Prescribes licensing criteria for classical Ayurvedic formulations (cited in 54 authoritative books) vs. Patent or Proprietary ASU medicines (requiring safety and proof of effectiveness studies).",
            citation="Drugs & Cosmetics Rules 1945, Rule 158-B",
        ),
        KGNode(
            id="SEC_TM_9_DESCRIPTIVE",
            name="Section 9 TM Act — Absolute Grounds for Refusal",
            node_type=NodeType.SECTION,
            jurisdiction="IN",
            ip_type="trademark",
            description="Prohibits registration of marks that lack distinctive character or consist exclusively of signs or indications designating the kind, quality, or medicinal properties (e.g. generic Sanskrit herb names).",
            citation="Trade Marks Act 1999 §9",
        ),
        KGNode(
            id="SEC_GI_8_PROPRIETOR",
            name="Section 8 & 9 GI Act — Registration & Prohibitions",
            node_type=NodeType.SECTION,
            jurisdiction="IN",
            ip_type="gi",
            description="Regulates who can register a GI (producers' association) and prohibits registration of generic, misleading, or deceptive names.",
            citation="Geographical Indications of Goods Act 1999 §8, §9",
        ),
        KGNode(
            id="ART_TRIPS_27",
            name="TRIPS Article 27 — Patentable Subject Matter",
            node_type=NodeType.ARTICLE,
            jurisdiction="INTL",
            ip_type="patent",
            description="Mandates patents for any inventions in all fields of technology, but permits exclusions for public order, morality, diagnostic/therapeutic methods, and plants/animals under Art 27.2 and 27.3(b).",
            citation="TRIPS Agreement Art. 27",
        ),
        KGNode(
            id="ART_NAGOYA_5",
            name="Nagoya Protocol Article 5 — Fair and Equitable Benefit-Sharing",
            node_type=NodeType.ARTICLE,
            jurisdiction="INTL",
            ip_type="abs",
            description="Directs benefits arising from utilization of genetic resources and traditional knowledge to be shared in a fair and equitable manner with indigenous and local communities.",
            citation="Nagoya Protocol Art. 5",
        ),

        # --- Authorities & Databases ---
        KGNode(
            id="AUTH_NBA",
            name="National Biodiversity Authority (NBA)",
            node_type=NodeType.AUTHORITY,
            jurisdiction="IN",
            ip_type="abs",
            description="Statutory autonomous body established under BDA 2002 based in Chennai; grants Form III approvals and enters benefit-sharing agreements before patent grants.",
            citation="https://nbaindia.org",
        ),
        KGNode(
            id="AUTH_IPO",
            name="Indian Patent Office (CGPDTM)",
            node_type=NodeType.AUTHORITY,
            jurisdiction="IN",
            ip_type="patent",
            description="Controller General of Patents, Designs and Trade Marks under DPIIT, Ministry of Commerce and Industry.",
            citation="https://ipindia.gov.in",
        ),
        KGNode(
            id="AUTH_AYUSH_MINISTRY",
            name="Ministry of AYUSH",
            node_type=NodeType.AUTHORITY,
            jurisdiction="IN",
            ip_type="ayush",
            description="Union ministry responsible for developing education, research, and regulatory frameworks for Ayurveda, Yoga & Naturopathy, Unani, Siddha, Sowa-Rigpa, and Homoeopathy.",
            citation="https://ayush.gov.in",
        ),
        KGNode(
            id="DB_TKDL",
            name="Traditional Knowledge Digital Library (TKDL)",
            node_type=NodeType.DATABASE,
            jurisdiction="IN",
            ip_type="tkdl",
            description="Pioneering digital repository containing over 450,000 formulations from classical Indian medicine texts in 5 international languages (English, German, French, Japanese, Spanish) used as defensive prior art.",
            citation="https://tkdl.res.in",
        ),
        KGNode(
            id="DB_API_PHARMACOPOEIA",
            name="Ayurvedic Pharmacopoeia of India (API)",
            node_type=NodeType.DATABASE,
            jurisdiction="IN",
            ip_type="ayush",
            description="Legal document published by Pharmacopoeia Commission for Indian Medicine & Homoeopathy (PCIM&H) defining pharmacopoeial identity and purity standards.",
            citation="https://pcimh.gov.in",
        ),
        KGNode(
            id="FORM_NBA_III",
            name="NBA Form III — IPR Clearance Application",
            node_type=NodeType.FORM,
            jurisdiction="IN",
            ip_type="abs",
            description="Statutory application submitted to the NBA under Rule 18 of Biological Diversity Rules for obtaining approval before applying for IPR on biological inventions.",
            citation="Biological Diversity Rules 2004, Rule 18",
        ),
    ]

    for n in nodes:
        g.add_node(n.id, **n.model_dump())

    # ─────────────────────────────────────────────────────────────────────────
    # 2. EDGES (Legal Relationships)
    # ─────────────────────────────────────────────────────────────────────────

    edges = [
        # Indian Patents Act -> Sections
        KGEdge(
            source="IN_PATENTS_ACT_1970",
            target="SEC_PATENTS_3P",
            edge_type=EdgeType.CONTAINS,
            description="Excludes traditional knowledge and component aggregation from patentability.",
        ),
        KGEdge(
            source="IN_PATENTS_ACT_1970",
            target="SEC_PATENTS_3E",
            edge_type=EdgeType.CONTAINS,
            description="Excludes mere admixtures without demonstrated synergy.",
        ),
        KGEdge(
            source="IN_PATENTS_ACT_1970",
            target="SEC_PATENTS_3D",
            edge_type=EdgeType.CONTAINS,
            description="Excludes new forms of known substances without enhanced therapeutic efficacy.",
        ),
        KGEdge(
            source="IN_PATENTS_ACT_1970",
            target="SEC_PATENTS_6_ORIGIN",
            edge_type=EdgeType.CONTAINS,
            description="Mandates specification disclosure of biological source and geographical origin.",
        ),

        # Section 3(p) <-> TKDL (Prior Art)
        KGEdge(
            source="DB_TKDL",
            target="SEC_PATENTS_3P",
            edge_type=EdgeType.IS_PRIOR_ART_FOR,
            description="TKDL records provide conclusive prior art defeating novelty and triggering §3(p) rejections.",
            mandatory=True,
        ),

        # Patents Act Section 6 <-> Biological Diversity Act Section 6 (Mandatory Clearance)
        KGEdge(
            source="SEC_PATENTS_6_ORIGIN",
            target="SEC_BDA_6_CLEARANCE",
            edge_type=EdgeType.REQUIRES_CLEARANCE,
            description="Using Indian biological resources in a patent application legally triggers mandatory NBA clearance under BDA Section 6.",
            mandatory=True,
        ),
        KGEdge(
            source="SEC_BDA_6_CLEARANCE",
            target="AUTH_NBA",
            edge_type=EdgeType.REQUIRES_CLEARANCE,
            description="Patent applicants must obtain formal prior approval from the NBA.",
            mandatory=True,
        ),
        KGEdge(
            source="SEC_BDA_6_CLEARANCE",
            target="FORM_NBA_III",
            edge_type=EdgeType.REQUIRES_CLEARANCE,
            description="NBA approval must be applied for using Form III under Rule 18.",
            mandatory=True,
        ),

        # BDA <-> Treaties
        KGEdge(
            source="IN_BDA_2002",
            target="INTL_CBD_1992",
            edge_type=EdgeType.IMPLEMENTS,
            description="Biological Diversity Act 2002 was enacted to give domestic effect to India's commitments under the CBD 1992.",
        ),
        KGEdge(
            source="IN_BDA_2002",
            target="INTL_NAGOYA_PROTOCOL",
            edge_type=EdgeType.IMPLEMENTS,
            description="NBA ABS mechanisms enforce the fair and equitable benefit-sharing requirements of the Nagoya Protocol.",
        ),
        KGEdge(
            source="SEC_BDA_6_CLEARANCE",
            target="ART_NAGOYA_5",
            edge_type=EdgeType.COMPLIES_WITH,
            description="Section 6 approval process ensures compliance with international benefit-sharing rules.",
        ),

        # Treaties <-> Patents
        KGEdge(
            source="IN_PATENTS_ACT_1970",
            target="INTL_TRIPS_AGREEMENT",
            edge_type=EdgeType.COMPLIES_WITH,
            description="India's Patents Act is TRIPS-compliant while utilizing Article 27.2 and 27.3(b) flexibilities for traditional knowledge exclusions.",
        ),
        KGEdge(
            source="SEC_PATENTS_3P",
            target="ART_TRIPS_27",
            edge_type=EdgeType.CITES,
            description="India's §3(p) traditional knowledge exclusion is justified under TRIPS Art 27 flexibilities and public order provisions.",
        ),

        # AYUSH / Drugs Act relationships
        KGEdge(
            source="IN_DRUGS_ACT_1940",
            target="RULE_AYUSH_158B",
            edge_type=EdgeType.CONTAINS,
            description="Chapter IV-A and Rule 158-B prescribe regulatory licensing for Ayurvedic, Siddha, and Unani drugs.",
        ),
        KGEdge(
            source="RULE_AYUSH_158B",
            target="DB_API_PHARMACOPOEIA",
            edge_type=EdgeType.CITES,
            description="Licensing of classical ASU drugs requires adherence to Ayurvedic Pharmacopoeia of India standards.",
        ),
        KGEdge(
            source="RULE_AYUSH_158B",
            target="AUTH_AYUSH_MINISTRY",
            edge_type=EdgeType.REGULATES,
            description="Ministry of AYUSH sets and oversees ASU licensing standards.",
        ),

        # Trademark / GI / Copyright
        KGEdge(
            source="IN_TM_ACT_1999",
            target="SEC_TM_9_DESCRIPTIVE",
            edge_type=EdgeType.CONTAINS,
            description="Section 9 bars registration of generic or descriptive Ayurvedic terms.",
        ),
        KGEdge(
            source="IN_TM_ACT_1999",
            target="INTL_MADRID_PROTOCOL",
            edge_type=EdgeType.COMPLIES_WITH,
            description="Indian trade mark applicants can seek international protection through the Madrid System.",
        ),
        KGEdge(
            source="IN_GI_ACT_1999",
            target="SEC_GI_8_PROPRIETOR",
            edge_type=EdgeType.CONTAINS,
            description="Protects traditional origin products and prevents deceptive registrations.",
        ),
        KGEdge(
            source="IN_GI_ACT_1999",
            target="INTL_LISBON_SYSTEM",
            edge_type=EdgeType.COMPLIES_WITH,
            description="International recognition of Indian GIs under Lisbon Agreement / Geneva Act.",
        ),
    ]

    for e in edges:
        g.add_edge(e.source, e.target, key=e.edge_type.value, **e.model_dump())

    return g


def get_knowledge_graph() -> nx.MultiDiGraph:
    """Singleton getter for the compiled Charaka IP Knowledge Graph."""
    global _GRAPH_INSTANCE
    if _GRAPH_INSTANCE is None:
        _GRAPH_INSTANCE = build_charak_knowledge_graph()
    return _GRAPH_INSTANCE
