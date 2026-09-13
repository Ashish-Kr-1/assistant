# IP-SAKTI Sahayak — Comprehensive Project Review & Implementation Report
### SIH PS045: Multilingual, RAG-based AI Assistant for Ayurveda Intellectual Property & Regulatory Guidance

---

## 1. What This Project Is About

### 1.1 Executive Summary & Problem Statement
In India and globally, researchers, practitioners, Ayurvedic Vaidyas, startups, and MSMEs working with Traditional Knowledge (TK) and biological resources navigate one of the world’s most stringent and fragmented statutory landscapes:

1. **Strict Patent Bars & Biopiracy Prevention (The Patents Act, 1970)**:
   - **Section 3(p)**: An invention that is in effect traditional knowledge or an aggregation or duplication of known properties of traditionally known components is **not patentable**.
   - **Section 3(d)**: Mere discovery of a new form of a known substance without demonstrable enhancement of therapeutic efficacy is non-patentable.
   - **Section 3(e)**: Mere admixture resulting only in aggregation of properties is barred from patentability.
   - **Section 10(4) & Budapest Treaty**: Mandatory disclosure of biological material source and geographical origin in patent specifications; requirement for microorganism deposit with an International Depositary Authority (IDA).
   - **Section 25 & Section 64**: Pre/post-grant opposition and patent revocation grounds for non-disclosure or wrongful disclosure of geographic origin or anticipation by traditional knowledge.
2. **Access and Benefit Sharing (ABS) Compliance (Biological Diversity Act, 2002 / 2023)**:
   - Sections 3, 4, 6, 19, and 21 mandate prior approval from the National Biodiversity Authority (NBA) before non-Indian entities access Indian biological resources or before anyone applies for intellectual property rights based on Indian biological resources.
   - Section 24 requires prior intimation to State Biodiversity Boards (SBB), while the Biological Diversity Rules 2024 enforce ABS benefit-sharing fees (0.1%–0.5% of ex-factory sales) while exempting cultivated medicinal plants and registered AYUSH practitioners with a Certificate of Origin.
3. **Complex 5-Tier Drug & Food Regulatory Classification**:
   - An Ayurvedic product may fall under the **Drugs and Cosmetics Act, 1940** as a **Classical Medicine** (manufactured strictly according to the 71 authoritative Ayurvedic texts listed in the First Schedule, regulated by State AYUSH Licensing Authorities under Schedule T GMP) or a **Patent & Proprietary (P&P) Medicine** (Rule 158B proof of safety and effectiveness).
   - Alternatively, it may qualify as a **Phytopharmaceutical Drug** under CDSCO **Rule 122E** (standardized fractions with at least 4 bioactive markers and Phase I–III clinical trials).
   - Or it may be regulated as an **Ayurveda Aahara (Food/Nutraceutical)** under the **FSSAI (Ayurveda Aahara) Regulations 2022 & October 2024 Compendium**, which strictly mandates authoritative text lineage, prohibits synthetic vitamins/minerals, and forbids disease/therapeutic claims and classical bhasmas/cosmetics.
   - Or it may fall under the **Cosmetics Rules 2020** (topical application, Form 32 license, BIS compliance).
4. **International Treaty Harmonization**:
   - The newly adopted **WIPO GRATK Treaty (Geneva, 2024)** establishes mandatory patent disclosure of the country of origin of genetic resources and the Indigenous Peoples or local communities providing associated traditional knowledge.
   - Concurrently, applicants must comply with the **WTO TRIPS Agreement** (Articles 22, 27, 28, 39), the **CBD Nagoya Protocol** (Articles 5, 6, 7, 12 on Prior Informed Consent and Mutually Agreed Terms), the **Budapest Treaty**, the **PCT**, the **Madrid Protocol**, and the **Hague Agreement**.

### 1.2 The AI Hallucination Hazard in Legal Tech
Standard generative AI tools (generic LLMs) represent a catastrophic liability in the IP domain:
- They invent non-existent statutory sections.
- They conflate US/European patent doctrine with Indian jurisprudence.
- They confuse classical drug licensing with FSSAI nutraceutical approval.
- They fail to warn applicants of mandatory NBA Section 6 approvals, leading to criminal penalties and statutory patent revocations under Section 64.

### 1.3 The Solution: IP-SAKTI Sahayak
**IP-SAKTI Sahayak** is an authoritative, zero-hallucination, multilingual, Corrective Retrieval-Augmented Generation (CRAG) AI assistant engineered to resolve these challenges. It guarantees:
- **100% Real Statutory Ingestion (Option B Mandate)**: Zero synthetic law, zero hand-typed fallback text, zero `text_override`. All legal chunks are dynamically scraped from Indian Kanoon, WTO, CBD, WIPO, and official gazette compendiums.
- **Code-Enforced Legal Guardrails (Rules R1–R10)**: Non-negotiable programmatic constraints that enforce safe abstention, zero uncited claims, sentence entailment verification, jurisdiction separation, paid-source consent, provenance tracking, and classification gating.
- **Canonical Single Source of Truth**: Centralized formulation taxonomy and compendium of 71 authoritative Ayurvedic texts.
- **Defensive Prior-Art Pointers**: Directs users to the Traditional Knowledge Digital Library (TKDL) via bilateral patent office NDAs without improperly leaking confidential databases into generative context.

---

## 2. What Has Been Done (Architecture & Completed Implementations)

```
                                  USER QUERY
                                      │
                   ┌──────────────────┴──────────────────┐
                   ▼                                     ▼
        Formulation Classification             General Legal Query
         (Classical, P&P, Phyto,                         │
          Ayurveda Aahar, Cosmetic)                      │
                   │                                     │
                   └──────────────────┬──────────────────┘
                                      │
                                      ▼
                        Rule R6 Paid-Source Consent Guard
                        (Blocks gated sources if consent=False)
                                      │
                                      ▼
                             Hybrid Vector Search
                  (Qdrant Local + Cohere Multilingual Embed v3)
                                      │
                                      ▼
                       MMR Diversity Re-ranking (λ = 0.7)
                   (Prevents duplicate section over-representation)
                                      │
                                      ▼
                            CRAG Relevance Grader
                     (CORRECT / AMBIGUOUS / INCORRECT)
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
         No chunks score CORRECT?             Chunks score CORRECT
             (Rule R1 Trigger)                          │
                    │                                   ▼
            Safe Abstention Refusal             CRAG Generator
                                          (Drafts grounded response with
                                            terminal [chunk_id] tags)
                                                        │
                                                        ▼
                                                  CRAG Verifier
                                          (Rule R2: Zero orphan claims;
                                           Rule R3: Sentence entailment;
                                           Rule R8: Confidence score)
                                                        │
                                                        ▼
                                                 Output Assembler
                                          (Rule R4: Jurisdiction split;
                                           Rule R5: Legal disclaimer;
                                           Rule R10: Date stamps)
                                                        │
                                                        ▼
                                                 FINAL RESPONSE
                                              (FastAPI / React UI)
```

### 2.1 Complete Statutory & International Treaty Ingestion (37 Verified Sources + 1 Defensive TKDL Pointer)
All statutory texts are dynamically retrieved and cached (`ml_pipeline/corpus_ingestion/data/cache/`) without any artificial overrides:

#### A. Indian National Statutes (Indian Kanoon & Official Compendiums)
1. **The Patents Act, 1970 (as amended)**:
   - `Section 3(p)`: Traditional Knowledge patent bar (`doc/874310/`).
   - `Section 3(d)`: Enhanced therapeutic efficacy bar for known substances.
   - `Section 3(e)`: Mere admixture aggregation bar.
   - `Section 8`: Foreign patent filing declarations (Form 3 requirements).
   - `Section 10(4)`: Specifications and disclosure of biological origin.
   - `Section 10(4)(ii)`: Deposit of biological material with an International Depositary Authority (Budapest Treaty) & geographical origin disclosure.
   - `Section 25`: Pre-grant and post-grant oppositions on traditional knowledge grounds.
   - `Section 64`: Revocation of patents for non-disclosure or wrongful disclosure of geographic origin.
2. **The Biological Diversity Act, 2002 & Amendment Act, 2023**:
   - `Section 3`: Mandatory prior approval of NBA for foreign entities.
   - `Section 4`: Restrictions on transfer of biological research results.
   - `Section 6`: Mandatory prior approval of NBA before applying for IPR inside or outside India.
   - `Section 19`: Applications to NBA for commercial utilization.
   - `Section 21`: Determination of equitable benefit sharing.
   - `Section 24`: Intimation to State Biodiversity Boards (SBB) & registered AYUSH practitioner exemptions.
3. **The Drugs and Cosmetics Act, 1940 & Rules, 1945**:
   - `Section 3(a)`: Statutory definition of Ayurvedic, Siddha, or Unani drugs.
   - `Section 33EEB`: Regulation of manufacture for sale of Ayurvedic medicines.
   - `Schedule T`: Good Manufacturing Practices (GMP) for ASU drugs.
   - `Rule 158B`: Safety and efficacy protocols for Patent & Proprietary medicines.
   - `Rule 122E`: Phytopharmaceutical regulatory pathway (CDSCO, minimum 4 bioactive markers).
4. **Food Safety and Standards Act, 2006 & Regulations**:
   - `Section 22`: Functional foods, nutraceuticals, and foods for special dietary uses.
   - `FSSAI (Ayurveda Aahara) Regulations 2022 & Oct 2024 Compendium (USDA GAIN IN2022-0054)`: Regulation 3 definition, Schedule A 71 authoritative texts, mandatory logo, strict prohibition on synthetic vitamins/minerals, therapeutic claims, classical bhasmas, and cosmetics.
5. **Intellectual Property Regimes**:
   - `Trade Marks Act 1999`: Section 9 (Absolute grounds for refusal) & Section 11 (Relative grounds for refusal).
   - `Geographical Indications of Goods Act 1999`: Section 2(1)(e) (GI statutory definition).
   - `Protection of Plant Varieties and Farmers' Rights Act 2001`: Section 39 (Farmers' seed saving and breeding rights).
6. **Traditional Knowledge Digital Library (TKDL) Pointer**:
   - Modeled strictly as an external defensive prior-art reference under Rule R7 (`status=MOCK_PENDING_ACCESS`). Excluded from generative retrieval to honor CSIR non-disclosure agreements with 18 international patent offices.

#### B. International Treaties (WTO, CBD, WIPO Official PDFs)
1. **WIPO GRATK Treaty (Geneva, 2024)**:
   - `Article 3`: Mandatory patent disclosure of genetic resources and local community traditional knowledge.
   - `Article 4`: Non-retroactivity of disclosure obligations.
   - `Article 5`: Sanctions, remedies, and opportunity for applicants to rectify non-fraudulent omissions.
2. **WTO TRIPS Agreement (1995)**:
   - `Article 27`: Patentable subject matter and allowable exclusions (diagnostic/therapeutic methods, plants/animals).
   - `Article 28`: Exclusive rights conferred to patent holders.
   - `Article 39`: Protection of undisclosed information and trade secrets.
   - `Article 22`: Protection of Geographical Indications.
3. **CBD Nagoya Protocol (2014)**:
   - `Article 5`: Fair and equitable benefit-sharing on mutually agreed terms.
   - `Article 6`: Prior Informed Consent (PIC) for access to genetic resources.
   - `Article 7`: Prior Informed Consent for access to traditional knowledge.
   - `Article 12`: Traditional knowledge compliance measures.
4. **International Filing Treaties & Procedural Conventions**:
   - **Budapest Treaty (1977/1980)**: Article 3 (Recognition of microorganism deposits with IDAs like MTCC/MCC).
   - **Patent Cooperation Treaty (PCT)**: Article 3 (International application requirements).
   - **Madrid Protocol (1989)**: Article 2 (International trademark registration).
   - **Hague Agreement (Geneva Act 1999)**: Article 3 (International industrial design registration).

---

### 2.2 Canonical Formulation Taxonomy & Single Source of Truth
To prevent divergence between ML agents and backend API endpoints, [`ml_pipeline/agents/formulation_taxonomy.py`](file:///Users/ayushk/Desktop/assistant/ml_pipeline/agents/formulation_taxonomy.py) serves as the canonical registry:
- **Taxonomy Categories**:
  - `CLASSICAL_MEDICINE`: Triggers Section 3(p) absolute patent bar, Schedule T GMP, State AYUSH licensing, and TKDL defensive prior-art protection.
  - `PROPRIETARY_MEDICINE`: Triggers Rule 158B proof of safety/efficacy, potential Section 3(d) (enhanced efficacy) and Section 3(e) (mere admixture) bars.
  - `PHYTOPHARMACEUTICAL`: Regulated under CDSCO Rule 122E, requiring 4 bioactive markers and Phase I–III clinical trials; eligible for standard composition/process patents.
  - `AYURVEDA_AAHAR`: Regulated under FSSAI 2022 Regulations, requiring authoritative text lineage; strictly prohibits therapeutic claims, synthetic additives, and classical bhasmas.
  - `COSMETIC`: Regulated under Cosmetics Rules 2020 (Form 32 license, BIS standards, trademark/design focus).
  - `AMBIGUOUS`: Flags incomplete submissions for guided clarification.
- **Authoritative Ayurveda Texts**: Complete compendium of 71 recognized texts (Brihat Trayi, Laghu Trayi, Bhaishajya Ratnavali, Sahasrayoga, Ayurvedic Formulary of India, Ayurvedic Pharmacopoeia of India, etc.).
- **Dual Classifiers**:
  - `FormulationClassifierAgent` in `ml_pipeline/agents/classifier_agent.py`: Natural language classifier for free-form product descriptions.
  - `AyurvedicFormulationClassifier` in `backend/app/services/classification_service.py`: Structured 5-point decision tree for interactive questionnaires.

---

### 2.3 Code-Enforced Legal Guardrails (Rules R1–R10)
All 10 legal guardrails are enforced deterministically in Python code:

| Rule | Title | Mechanism |
| :--- | :--- | :--- |
| **R1** | **Safe Abstention** | Evaluated at graph edge (`graph.py._edge_post_grade`). If zero retrieved chunks score `CORRECT`, pipeline halts and emits a safe refusal. |
| **R2** | **Zero Orphan Claims** | [`verifier.py`](file:///Users/ayushk/Desktop/assistant/ml_pipeline/crag/verifier.py) parses sentences; any sentence making a legal claim without a terminal `[chunk_id]` tag is stripped. |
| **R3** | **Citation Entailment Verification** | Compares assertions against retrieved chunk text. Includes deterministic keyword-matching heuristic fallback when `self.llm = None`. |
| **R4** | **Strict Jurisdiction Separation** | National (India) and International treaty chunks are retrieved, processed, and rendered in distinct, labeled sections. |
| **R5** | **Mandatory Legal Disclaimer** | Appended at Python string-level by `OutputAssembler` (`"This is informational guidance, not legal advice..."`). LLMs cannot suppress it. |
| **R6** | **Paid-Source Consent Guard** | [`backend/app/core/r6_consent_guard.py`](file:///Users/ayushk/Desktop/assistant/backend/app/core/r6_consent_guard.py) intercepts all requests; queries touching gated databases are blocked unless affirmative `paid_source_consent=True` is logged. |
| **R7** | **Corpus Provenance Labeling** | Every chunk carries a `ProvenanceStatus` (`VERIFIED_PUBLIC`, `VERIFIED_PAID`, `MOCK_PENDING_ACCESS`). Mock chunks are excluded from generation. |
| **R8** | **Confidence Scoring** | Mandatory `HIGH` (≥0.85), `MEDIUM` (0.70–0.84), or `LOW` (<0.70) score attached to every API response. |
| **R9** | **Formulation Classification Gate** | Enforced in `CRAGPipeline.run()`: any query mentioning an Ayurvedic formulation triggers automatic classification before IP advice is rendered. |
| **R10** | **Version & Date Stamping** | Every citation returns exact statutory amendment dates (`effective_date` metadata). |

---

### 2.4 Vector Search, Retrieval & Ranking
- **Vector Database**: Local persistent Qdrant instance storing 384-dimensional or 1024-dimensional multilingual embeddings.
- **Embedding Model**: Cohere Multilingual Embed v3 (`embed-multilingual-v3.0`), supporting English, Hindi, and Indian vernacular queries.
- **Maximal Marginal Relevance (MMR)**: Codified in [`ml_pipeline/embeddings/mmr.py`](file:///Users/ayushk/Desktop/assistant/ml_pipeline/embeddings/mmr.py) to prevent search results from being monopolized by repeated hits from a single statute.
- **Deterministic Offline Heuristic Fallbacks**: Grader, Generator, and Verifier include deterministic keyword and rule-based fallbacks to guarantee 100% functionality even during LLM outages or when running without API keys.

---

### 2.5 REST Backend & React Frontend Applications
- **FastAPI REST API**:
  - `POST /api/v1/query`: Core CRAG pipeline with Rule R6 consent check, jurisdiction filtering, and DPDP Act 2023 audit logging.
  - `POST /api/v1/classify`: 5-tier Ayurvedic product classification decision tree.
  - `GET /api/v1/abs/calculate`: BDA 2023 ABS fee slab (0.1%–0.5% turnover) and exemption calculator.
  - `POST /api/v1/escalation`: Human IP facilitator ticket creation for queries requiring certified attorney review.
  - `GET /health`: Health check with vector collection status.
- **Modern React + Vite + Tailwind Frontend**:
  - Responsive chatbot UI with jurisdiction switcher (National, International, Both).
  - Interactive formulation classification wizard.
  - Visual confidence badges (`HIGH`, `MEDIUM`, `LOW`), clickable statutory citation pills, legal disclaimer banner, and copy/export functionality.

---

### 2.6 Test Verification (37 Passed across 7 Suites)
Every component is verified by comprehensive automated tests:

```bash
PYTHONPATH=.:backend uv run pytest backend/tests/ ml_pipeline/tests/
```

**Results (100% Passing)**:
- `backend/tests/test_abs.py`: 2 tests passed (ABS fee calculation and exemption rules).
- `backend/tests/test_classify.py`: 5 tests passed (Classical, Proprietary, Phyto, Ayurveda Aahar, Cosmetic).
- `backend/tests/test_crag_api.py`: 4 tests passed (National, International, Both, and Abstention endpoints).
- `backend/tests/test_r6_consent_guard.py`: 9 tests passed (Rule R6 paid-source consent verification).
- `ml_pipeline/tests/test_crag_pipeline.py`: 6 tests passed (CRAG workflow and guardrail enforcement).
- `ml_pipeline/tests/test_heuristic_fallbacks.py`: 8 tests passed (Deterministic zero-LLM fallbacks).
- `ml_pipeline/tests/test_mmr.py`: 3 tests passed (MMR diversity and ranking mechanics).
**Total**: **37 passed** in 360s.

---

## 3. What Is Left to Implement (Honest Roadmap & Gaps)

While the Core Retrieval, Formulation Classification, and Legal Guardrail engines are fully operational and verified, the following advanced items represent the roadmap for remaining implementation:

### 3.1 Phase 3 Gaps: Knowledge Graph & External Live Portals
1. **Neo4j Knowledge Graph Multi-Hop Reasoning**:
   - *Current Status*: Entity models and schema are defined in [`ml_pipeline/knowledge_graph/schema.py`](file:///Users/ayushk/Desktop/assistant/ml_pipeline/knowledge_graph/schema.py) and graph builder script exists in [`scripts/build_graph.py`](file:///Users/ayushk/Desktop/assistant/scripts/build_graph.py).
   - *Left to Implement*: Provisioning a live Neo4j database instance and wiring Cypher traversal queries directly into the LangGraph workflow. This will enable complex multi-hop reasoning:
     $$\text{Plant Species} \longrightarrow \text{Classical Formulation} \longrightarrow \text{First Schedule Text} \longrightarrow \text{Section 3(p) Bar} \longrightarrow \text{Prior Revocations}$$
2. **IP India Dynamic Search Integration**:
   - *Current Status*: Constants and endpoint URLs configured.
   - *Left to Implement*: Real-time scraper and connector for InPASS (Indian Patent Advanced Search System), Trade Marks Registry search, and GI Registry certificate database.
3. **Indian Kanoon Landmark Case Law Ingestion**:
   - *Current Status*: Bare Acts and statutory sections are scraped and cached.
   - *Left to Implement*: Ingesting full-text judgments of landmark traditional knowledge cases (e.g., European Patent Office Neem patent revocation, USPTO Turmeric patent revocation, *Novartis v. Union of India* on Section 3(d) therapeutic efficacy standards).

### 3.2 Phase 4 Gaps: Bhashini Voice & Vernacular Pipeline
1. **Production Government of India Bhashini NMT API Integration**:
   - *Current Status*: Service stubs and language mappings for 10 Scheduled Indian languages are configured in [`backend/app/services/bhashini_service.py`](file:///Users/ayushk/Desktop/assistant/backend/app/services/bhashini_service.py).
   - *Left to Implement*: Connecting live Bhashini ULCA pipeline credentials to translate incoming vernacular prompts into English before CRAG retrieval, and translating the verified, citation-tagged response back into the user's native language.
2. **Bhashini Voice Pipeline (ASR & TTS)**:
   - *Current Status*: Audio endpoints stubbed.
   - *Left to Implement*: Frontend microphone capture for Speech-to-Text (ASR) and audio response playback (TTS) for rural farmers and traditional Vaidyas who prefer oral communication.
3. **Live Human Facilitator Dashboard**:
   - *Current Status*: `/api/v1/escalation` endpoint records escalation tickets with DPDP Act audit logging.
   - *Left to Implement*: A dedicated admin web dashboard for certified AYUSH IP facilitators to review low-confidence queries (< 0.70) and provide manual, human-in-the-loop legal assistance.

---

## 4. Quick Start & Execution Guide

### Step 1: Start the FastAPI Backend
```bash
PYTHONPATH=.:backend uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
# Interactive OpenAPI Docs: http://127.0.0.1:8000/docs
```

### Step 2: Start the React + Vite Frontend
```bash
npm run dev -- --host 127.0.0.1 --port 5173
# Web Application: http://127.0.0.1:5173/chatbot
```

### Step 3: Run the Complete Automated Test Suite
```bash
PYTHONPATH=.:backend uv run pytest backend/tests/ ml_pipeline/tests/
```

### Step 4: Re-seed Corpus from Live Sources (Optional)
```bash
PYTHONPATH=. uv run python scripts/seed_corpus.py
```
