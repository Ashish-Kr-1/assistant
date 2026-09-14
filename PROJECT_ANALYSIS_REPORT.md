# IP-SAKTI Sahayak (SIH PS045) — Comprehensive Project Analysis Report

**Date:** September 14, 2026  
**System:** IP-SAKTI Sahayak (PS045)  
**Domain:** Multilingual, Source-Cited AI Assistant for Intellectual Property & Regulatory Guidance in Ayurveda across National (India) and International Regimes  

---

## 1. Executive Summary & Problem Domain

Researchers, Ayurvedic practitioners (Vaidyas), MSMEs, and biotech startups working with Indian biological resources and Traditional Knowledge (TK) face a uniquely stringent, multi-statute regulatory and intellectual property environment:

1. **Strict Patent Bars & Biopiracy Prevention (The Patents Act, 1970)**:
   - **Section 3(p)**: Inventions that are essentially traditional knowledge or aggregations/duplications of known properties of traditionally known components are non-patentable.
   - **Section 3(d)**: Mere discovery of a new form of a known substance without demonstrable enhancement of therapeutic efficacy is barred.
   - **Section 3(e)**: Mere admixtures resulting only in the aggregation of properties are non-patentable.
   - **Section 10(4) & Budapest Treaty**: Mandatory disclosure of the geographical origin and source of biological materials; deposit requirement for biological materials with an International Depositary Authority (IDA).
   - **Section 25 & 64**: Pre-grant and post-grant opposition, and statutory revocation of patents for non-disclosure or wrongful disclosure of geographic origin or anticipation by traditional knowledge.

2. **Access and Benefit Sharing (ABS) Liability (Biological Diversity Act, 2002 / 2023 Amendment)**:
   - Sections 3, 4, 6, 19, and 21 mandate prior approval from the **National Biodiversity Authority (NBA)** before non-Indian entities access Indian biological resources or before any entity applies for IP rights based on research conducted on Indian biological materials.
   - Section 24 requires prior intimation to **State Biodiversity Boards (SBB)**.
   - The **Biological Diversity Rules 2024** impose ABS benefit-sharing fees (0.1%–0.5% of ex-factory sales) while establishing statutory exemptions for cultivated medicinal plants (with Certificate of Origin) and registered AYUSH practitioners.

3. **5-Tier Regulatory Classification Landscape**:
   - **Classical Ayurvedic Medicines**: Manufactured strictly in accordance with the 71 authoritative texts listed in the First Schedule of the *Drugs and Cosmetics Act, 1940*, regulated by State AYUSH Licensing Authorities under Schedule T Good Manufacturing Practices (GMP).
   - **Patent & Proprietary (P&P) Medicines**: Regulated under Rule 158B of the *Drugs and Cosmetics Rules, 1945*, requiring published literature or clinical trial proof of safety and effectiveness.
   - **Phytopharmaceutical Drugs**: Regulated under CDSCO Rule 122E, requiring purified, standardized active fractions with at least 4 bioactive markers and Phase I–III clinical trials.
   - **Ayurveda Aahara (Food Supplements / Nutraceuticals)**: Governed by the *FSSAI (Ayurveda Aahara) Regulations 2022 & October 2024 Compendium*, strictly prohibiting synthetic additives, chemical fortificants, therapeutic/disease cure claims, and classical bhasmas or cosmetic applications.
   - **Cosmetics**: Governed by the *Cosmetics Rules 2020* (topical application, Form 32 license, BIS standard compliance).

4. **International Treaty Compliance & Global Protection**:
   - **WIPO GRATK Treaty (Geneva, 2024)**: Article 3 mandates patent applicants to disclose the country of origin of genetic resources and the indigenous peoples or local communities who provided associated traditional knowledge.
   - **CBD & Nagoya Protocol (2014)**: Enforces Prior Informed Consent (PIC) and Mutually Agreed Terms (MAT) for fair and equitable benefit sharing.
   - **WTO TRIPS Agreement**: Articles 22, 27, 28, and 39 governing patentability standards, undisclosed information, and Geographical Indications (e.g., Navara rice, Nilambur teak).

5. **The AI Hallucination Liability in Legal Tech**:
   - Generic large language models frequently invent non-existent statutory sections, conflate US/EPC patent doctrines with Indian law, fail to flag mandatory NBA approval requirements, and confuse classical drug licensing with FSSAI regulations.
   - **IP-SAKTI Sahayak** solves this via **LangGraph Corrective Retrieval-Augmented Generation (CRAG)** backed by strict code-enforced legal guardrails.

---

## 2. System Architecture & Components

```
                                      USER QUERY (Web UI / REST API)
                                                    │
                             ┌──────────────────────┴──────────────────────┐
                             ▼                                             ▼
                Formulation Classification Gate                     General Legal Query
             (Classical, P&P, Phytopharmaceutical,                         │
               Ayurveda Aahar, or Cosmetic)                                │
                             │                                             │
                             └──────────────────────┬──────────────────────┘
                                                    │
                                                    ▼
                                     Rule R6 Consent Guard
                               (Verifies consent for gated sources)
                                                    │
                                                    ▼
                                           CRAG State Graph
                                     (LangGraph State Machine)
                                                    │
                    ┌───────────────────────────────┴───────────────────────────────┐
                    ▼                                                               ▼
        Retrieve (VectorStoreManager)                                ABS Pointer (Rule Engine)
    - Cohere Multilingual Embed v3 / Hash Fallback               - Deterministic botanical check
    - Qdrant Local Payload Filtering (R4 Isolation)              - Biological Diversity Act 2023
    - MMR Diversity Re-ranking (λ = 0.7)                         - Fee calculation & NBA forms
                    │
                    ▼
          Grade (RelevanceGrader)
      - LLM / Deterministic Overlap Pass
      - Outcome: CORRECT / AMBIGUOUS / INCORRECT
                    │
       ┌────────────┴────────────┬────────────────────────┐
       ▼ (All INCORRECT)         ▼ (AMBIGUOUS)            ▼ (At least 1 CORRECT)
    Abstain (Rule R1)         Fallback Retrieval       Generate (GroundedGenerator)
  - Zero-hallucination        (Expands search in        - Citation-forced synthesis:
    safe refusal message       same jurisdiction)          "[chunk_id] at period end"
  - Escalate to human                                     - Strict regime separation (R4)
                                                                  │
                                                                  ▼
                                                        Verify (CitationVerifier)
                                                        - Rule R2: Strip orphan claims
                                                        - Rule R3: Sentence entailment
                                                        - Rule R8: Compute confidence
                                                                  │
                                                                  ▼
                                                      Assemble (OutputAssembler)
                                                      - Hardcode Disclaimer (R5)
                                                      - Attach Date/Version stamps (R10)
                                                      - Format Citations & ABS flags
                                                                  │
                                                                  ▼
                                                         FINAL API RESPONSE
                                                       (FastAPI -> React Client)
```

### 2.1 Machine Learning Pipeline (`ml_pipeline/`)
* **LangGraph State Graph (`ml_pipeline/crag/graph.py`)**:
  * Implements `CRAGPipeline` with nodes: `retrieve`, `grade`, `fallback`, `generate`, `verify`, `assemble`, and `abstain`.
  * For cross-jurisdictional queries (`jurisdiction="both"`), executes two isolated pipeline runs and presents separate, unblended sections.
* **Hybrid Vector Retrieval (`ml_pipeline/embeddings/vector_store_manager.py`)**:
  * Qdrant collection with payload-level filtering on `jurisdiction` (National vs International) and `status` (excluding mock/provisional chunks).
  * Cohere `embed-multilingual-v3.0` (1024-dim) for high-accuracy semantic embeddings across Indian languages, with a deterministic 384-dim hash embedding fallback for offline and continuous integration environments.
  * Maximal Marginal Relevance (MMR, $\lambda = 0.7$) diversification preventing statutory section redundancy.
* **Real Corpus Ingestion & Provenance (`ml_pipeline/corpus_ingestion/scrapers/legal_scraper.py`)**:
  * Zero synthetic law (`text_override` prohibited).
  * Dynamic scraping from Indian Kanoon (bare acts), official WTO TRIPS PDFs, CBD Nagoya Protocol PDFs, and WIPO GRATK Treaty PDFs, backed by local disk caching (`ml_pipeline/corpus_ingestion/data/cache/`).
  * Explicit provenance labeling: `VERIFIED_PUBLIC`, `VERIFIED_PAID`, and `MOCK_PENDING_ACCESS` (defensive TKDL pointer).
* **Ayurvedic Taxonomy & Classifier (`ml_pipeline/agents/classifier_agent.py` & `formulation_taxonomy.py`)**:
  * Built-in registry of all 71 authoritative First Schedule texts (*Charaka Samhita*, *Sushruta Samhita*, *Ashtanga Hridaya*, etc.).
  * Programmatic classifier routing users through statutory criteria.
* **Deterministic ABS Pointer (`ml_pipeline/crag/abs_pointer.py`)**:
  * Non-generative botanical lookup (*Withania somnifera*, *Curcuma longa*, *Commiphora mukul*, *Azadirachta indica*, *Rauvolfia serpentina*, *Triphala*, etc.).
  * Direct evaluation of BDA 2023 exemptions (AYUSH practitioner exemption under Section 7 Proviso, cultivation certificates, NBA Form I/III requirements).

### 2.2 Backend Web Service (`backend/`)
* **FastAPI Application (`backend/app/main.py`)**:
  * Structured routes under `/api/v1`:
    * `POST /query`: Core CRAG pipeline execution with citation extraction, confidence scoring, and ABS guidance.
    * `POST /classify`: Product categorization wizard.
    * `GET /abs/calculate`: Deterministic calculation of benefit-sharing fees (0.1% to 0.5% turnover) and form routing.
    * `POST /bhashini/translate`: Multilingual translation integration for 22 scheduled Indian languages.
    * `POST /escalation/connect`: Routing low-confidence cases to registered IP Facilitators and Patent Agents.
* **DPDP Act 2023 Privacy Engine (`backend/app/core/dpdp_logger.py`)**:
  * Strict adherence to India's Digital Personal Data Protection Act 2023.
  * SHA-256 cryptographic hashing of queries for audit logs; zero storage of raw user queries without affirmative consent.
* **Rule R6 Consent Guard (`backend/app/core/r6_consent_guard.py`)**:
  * Prevents unauthorized access to gated or paid sources.
  * Enforces single-query, explicit, individually logged user permission; past consents are never reused.

### 2.3 Frontend Client (`frontend/`)
* **React 19 + Vite SPA (`frontend/src/`)**:
  * Real-time conversational interface (`ChatBot.jsx`) featuring:
    * Jurisdiction toggle: **National (India)**, **International**, or **Both**.
    * Expandable statutory citations drawer displaying section, act, and gazette links.
    * Visual confidence score badges (**HIGH**, **MEDIUM**, **LOW**).
    * Dynamic follow-up recommendations.
    * Human Facilitator escalation modal.
  * Reverse proxy integration in `vite.config.js` forwarding `/api` calls to the FastAPI backend.

### 2.4 Infrastructure & Deployment (`docker/`)
* Multi-container `docker-compose.yml` defining:
  * `frontend`: React SPA served via Nginx.
  * `backend`: FastAPI Python application.
  * `vector_db`: Qdrant v1.7.4.
  * `knowledge_graph`: Neo4j 5.16.0 (schema linking Herbs, Formulations, Statutes, and Patent Bars).
  * `postgres_db`: PostgreSQL 16 Alpine.

---

## 3. The 10 Code-Enforced Legal Guardrails (Rules R1–R10)

| Rule | Requirement | Code Enforcement Location |
| :--- | :--- | :--- |
| **R1** | **Safe Abstention**: No answer without verified/graded sources. | `ml_pipeline/crag/graph.py::_edge_post_grade` — Generator is bypassed completely when retrieved chunks fail grading. |
| **R2** | **No Orphan Claims**: Every statutory/factual claim requires a citation. | `ml_pipeline/crag/verifier.py::audit_and_sanitize` — Regex and citation parser strips ungrounded legal propositions. |
| **R3** | **Citation Entailment**: Every citation must substantiate the claim. | `ml_pipeline/crag/verifier.py::verify_sentence_entailment` — Verifies logical entailment between claim text and cited chunks. |
| **R4** | **Strict Jurisdiction Isolation**: National and International regimes never blend. | `ml_pipeline/embeddings/vector_store_manager.py` (Qdrant filter) + `ml_pipeline/crag/generator.py` (isolated sections). |
| **R5** | **Mandatory Statutory Disclaimer**: Non-removable standing disclaimer. | `ml_pipeline/crag/assembler.py::assemble_response` — Standing legal disclaimer appended to every response. |
| **R6** | **Paid-Source Access Consent**: Explicit per-query permission required. | `backend/app/core/r6_consent_guard.py` — Single-query scope, individually hashed and logged. |
| **R7** | **Corpus Provenance Labeling**: Mock data excluded from answers. | `ml_pipeline/crag/schema.py::ProvenanceStatus` — `MOCK_PENDING_ACCESS` filtered out of vector retrieval. |
| **R8** | **Mandatory Confidence Level**: Clear signal on output validity. | `ml_pipeline/crag/assembler.py` — Calculates entailment ratio: `HIGH` ($\ge 0.85$), `MEDIUM` ($\ge 0.70$), `LOW` ($< 0.70$). |
| **R9** | **Formulation Classification Gate**: Taxonomy precedes IP advice. | `ml_pipeline/crag/graph.py::run` — Halts generic IP queries to clarify product classification first. |
| **R10** | **Statutory Version Stamping**: Date tracking on all chunks. | `ml_pipeline/crag/schema.py::LegalChunk` — `effective_date` field mandatory on all corpus items. |

---

## 4. Test Suite Execution & Verification

The complete test suite was executed via the project's virtual environment:

```bash
PYTHONPATH=.:backend uv run pytest ml_pipeline/tests/ backend/tests/ -v
```

### Verification Results:
* **Total Tests Executed:** 39
* **Passed:** 39 (100% pass rate)
* **Execution Breakdown:**
  * **CRAG Pipeline Integration (`ml_pipeline/tests/test_crag_pipeline.py`)**: 8/8 passed
    - Classical formulation Section 3(p) retrieval and citation.
    - WIPO GRATK Treaty mandatory disclosure retrieval.
    - Rule R1 safe abstention on unsupported queries.
    - Rule R9 formulation classification gate trigger.
    - ABS botanical pointer trigger.
    - Rule R7 mock chunk exclusion.
    - Rule R4 database-level jurisdiction filtering.
    - Cross-jurisdiction dual pipeline execution.
  * **Heuristic Fallback Engine (`ml_pipeline/tests/test_heuristic_fallbacks.py`)**: 8/8 passed
    - Offline grading (substantial overlap, ambiguous overlap, incorrect on zero overlap).
    - Legal boilerplate penalization.
    - Deterministic sentence entailment verification.
  * **MMR Semantic Diversification (`ml_pipeline/tests/test_mmr.py`)**: 4/4 passed
    - Redundancy penalization.
    - Pure relevance when $\lambda = 1.0$.
    - Integration with vector store search.
  * **ABS Compliance Service (`backend/tests/test_abs.py`)**: 2/2 passed
    - AYUSH practitioner exemption verification under BDA 2023.
    - Foreign entity Form III requirement and fee calculation.
  * **Formulation Classifier (`backend/tests/test_classify.py`)**: 5/5 passed
    - Classical medicine categorization.
    - Phytopharmaceutical categorization under Rule 122E.
    - Ayurveda Aahara categorization under FSSAI 2022.
    - Cosmetic categorization under Cosmetics Rules 2020.
    - 71 First Schedule texts agent matching.
  * **CRAG Backend API (`backend/tests/test_crag_api.py`)**: 4/4 passed
    - `/api/v1/query` National Section 3(p).
    - `/api/v1/query` International WIPO treaty.
    - `/api/v1/query` Safe abstention (Rule R1).
    - `/api/v1/query` Classification gate (Rule R9).
  * **Rule R6 Consent Guard (`backend/tests/test_r6_consent_guard.py`)**: 8/8 passed
    - Gated source identification.
    - Dynamic consent prompt generation.
    - Single-query permission grant / denial.
    - Query SHA-256 anonymization (DPDP compliance).
    - Citation stripping on consent refusal.

---

## 5. Architectural Assessment & Strategic Recommendations

### Key Strengths
1. **Uncompromising Statutory Fidelity**: The elimination of synthetic legal fallbacks ensures that answers are legally defensible and fully traceable.
2. **Dual-Layer Robustness**: The coexistence of LLM-based processing (Cohere/OpenAI) with deterministic heuristic fallbacks ensures zero downtime in air-gapped or network-constrained settings.
3. **Regulatory Completeness**: Deep, up-to-date integration of the Biological Diversity (Amendment) Act 2023, the 2024 Biological Diversity Rules, and the 2024 WIPO GRATK Treaty.

### Strategic Roadmap
1. **Neo4j Multi-Hop Graph-RAG**:
   - The graph schema in `scripts/build_graph.py` and `ml_pipeline/knowledge_graph/schema.py` provides a foundation for linking Herbs $\leftrightarrow$ Formulations $\leftrightarrow$ Bioactive Markers $\leftrightarrow$ Statutes. Connecting this graph directly to the hybrid retrieval stage will enhance cross-herb prior-art queries.
2. **Bhashini Pipeline Integration**:
   - Populate production Bhashini credentials in `.env` (`BHASHINI_API_KEY`, `BHASHINI_PIPELINE_ID`) to activate live ASR (voice input), NMT (text translation across 22 scheduled languages), and TTS (voice output).
3. **Pydantic V2 Cleanups**:
   - Migrate deprecated Pydantic V1 style settings (`class Config` in `backend/app/core/config.py`) to `ConfigDict` to ensure compatibility with future Pydantic V3 releases.
