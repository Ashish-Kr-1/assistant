# Charaka IP — Comprehensive Project Review & Implementation Report
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

### 1.3 The Solution: Charaka IP
**Charaka IP** is an authoritative, zero-hallucination, multilingual, Corrective Retrieval-Augmented Generation (CRAG) AI assistant engineered to resolve these challenges. It guarantees:
- **100% Real Statutory Ingestion**: Zero synthetic law, zero hand-typed fallback text, zero `text_override`. All legal chunks are dynamically scraped from Indian Kanoon, WTO, CBD, WIPO, and official gazette compendiums.
- **Code-Enforced Legal Guardrails (Rules R1–R10)**: Non-negotiable programmatic constraints that enforce safe abstention, zero uncited claims, sentence entailment verification, jurisdiction separation, paid-source consent, provenance tracking, and classification gating.
- **Canonical Single Source of Truth**: Centralized formulation taxonomy and compendium of 71 authoritative Ayurvedic texts.
- **Defensive Prior-Art Pointers**: Directs users to the Traditional Knowledge Digital Library (TKDL) via bilateral patent office NDAs without improperly leaking confidential databases into generative context.

---

## 2. End-to-End System Architecture

```
                                  USER QUERY
                                      │
                                      ▼
                        Phase 1: Intent & Entity Classifier
                      (11 Intents, Entity Extraction, Routing)
                                      │
              ┌───────────────────────┴───────────────────────┐
              ▼                                               ▼
     [INNOVATION_INTAKE]                               [LEGAL_QUERY / DIRECT]
              │                                               │
              ▼                                               │
   Phase 2: Innovation Intake Agent                           │
  (Progressive Q&A, CaseORM, Profile)                         │
              │                                               │
              ▼                                               │
   Phase 3: Case Assessment Agent                             │
   (Deterministic 5-Subpart Mapping):                         │
    - 3.1 Normalization & Completeness                        │
    - 3.2 5-Tier Product Classification                       │
    - 3.3 IP Domain & Section 3(p) Analysis                   │
    - 3.4 Multi-Jurisdiction Regulatory Map                   │
    - 3.5 Prioritized Research Plan                           │
              │                                               │
              ▼                                               │
   Phase 4: Research Engine & Report Generator                │
   (Executes Recommended Queries via CRAG)                    │
              │                                               │
              └───────────────────────┬───────────────────────┘
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
                                         - 16-Section Research Report
                                         - Assessment Summary Panel
                                         - Direct Grounded Legal Q&A
```

---

## 3. What Has Been Done (Completed Implementations by Phase)

### 3.1 Phase 1 — Intent & Entity Classification Layer
- **Architecture**: Dual-layer classifier combining fast, deterministic regex/keyword rule matching (`ml_pipeline/classifier/intent_rules.py`) with an LLM classifier (`ml_pipeline/classifier/intent_classifier.py`) enforcing strict Pydantic JSON schemas (`ml_pipeline/schemas/intent_schema.py`).
- **11 Supported Intent Classes**:
  1. `INNOVATION_INTAKE`: User describes a product, formulation, or invention for intake.
  2. `CASE_STATUS`: Inquiries regarding active case progress or status.
  3. `LEGAL_QUERY`: Direct questions on statutes (e.g., Section 3(p), Section 3(d), Section 6 BDA, WIPO GRATK).
  4. `PATENTABILITY_ASSESSMENT`: Patent inquiries and novelty criteria.
  5. `REGULATORY_GUIDANCE`: AYUSH, FSSAI Ayurveda Aahara, or CDSCO pathways.
  6. `ABS_GUIDANCE`: Biodiversity Act, NBA approval, SBB intimation, and fee calculations.
  7. `TRADEMARK_SEARCH`: Brand names, marks, distinctiveness under Trade Marks Act 1999.
  8. `PRIOR_ART_SEARCH`: TKDL, patent novelty anticipation, prior published formulations.
  9. `HUMAN_ESCALATION`: Requests for certified AYUSH patent attorney / IP facilitator.
  10. `GREETING`: Polite greetings and conversational openers.
  11. `OUT_OF_SCOPE`: Graceful deflection of questions unrelated to Ayurveda or IP.
- **Entity Extraction**: Automatically extracts formulation name, botanical/herbal ingredients, therapeutic indications, target jurisdictions, development stage, applicant type, and prior art / TK basis.
- **API Endpoint**: `POST /api/v1/intent/classify` with fallback mechanisms for offline testing.
- **Test Coverage**: 40 unit and API tests (`ml_pipeline/tests/test_intent_classifier.py` and `backend/tests/test_intent_api.py`).

### 3.2 Phase 2 — Innovation Intake & Case Lifecycle Management
- **Persistence Layer**: Multi-backend architecture supporting PostgreSQL (production) with automatic local SQLite fallback (`ipsakti_cases.db`) using SQLAlchemy ORM (`backend/app/db/models.py`).
- **Domain Schemas**: `InnovationProfile`, `IntakeState`, `IntakeResponse`, `Case` (`ml_pipeline/schemas/case_schema.py`).
- **Case Lifecycle State Machine**:
  - `INTAKE_IN_PROGRESS`: Iterative intake gathering required fields.
  - `READY_FOR_RESEARCH`: Minimum necessary fields gathered; auto-triggers Phase 3 assessment.
  - `RESEARCH_COMPLETED`: Phase 4 preliminary research report compiled.
  - `ESCALATED`: High-risk or complex case escalated for certified attorney review.
- **Intake Agent (`InnovationIntakeAgent`)**:
  - Progressive questioning strategy: Asks for one missing dimension at a time without overwhelming the user.
  - Strict anti-hallucination: Never invents fields or ingredients; records provenance flags (`USER_STATED` vs `EXTRACTED_UNCONFIRMED`).
  - Deduplication: Merges ingredients cleanly, preventing duplicates across multiple chat turns.
- **REST Endpoints**:
  - `POST /api/v1/cases`: Create a new innovation case for a conversation.
  - `GET /api/v1/cases/active`: Retrieve active case associated with a conversation.
  - `GET /api/v1/cases/{id}`: Fetch complete case data including profile, assessment, and research report.
  - `POST /api/v1/cases/{id}/intake`: Process progressive intake messages.
  - `PATCH /api/v1/cases/{id}`: Directly update or correct profile fields.
- **Test Coverage**: 24 tests verifying progressive intake, ingredient accumulation, ownership security, and error handling (`backend/tests/test_case_intake.py`).

### 3.3 Phase 3 — Innovation Classification & Legal Domain Mapping
Fully deterministic, zero-LLM transformation pipeline (`ml_pipeline/agents/case_assessment_agent.py`) divided into exactly 5 subparts:
1. **3.1 Case Normalization**:
   - Validates and sanitizes `InnovationProfile`.
   - Cleans ingredient strings and standardizes target jurisdictions into canonical ISO codes (`INDIA`, `USA`, `EU`, `UK`, `GERMANY`, `JAPAN`, `CANADA`, `AUSTRALIA`).
   - Computes profile completeness score (`MINIMAL`, `PARTIAL`, `SUBSTANTIAL`, `COMPREHENSIVE`).
2. **3.2 Product / Formulation Classification**:
   - Maps innovation to the canonical 5-tier statutory taxonomy (`CLASSICAL_MEDICINE`, `PROPRIETARY_MEDICINE`, `PHYTOPHARMACEUTICAL`, `AYURVEDA_AAHAR`, `COSMETIC`, `AMBIGUOUS`).
   - Cross-references against the complete compendium of 71 authoritative Ayurvedic texts (First Schedule of DCA 1940).
   - Identifies mandatory regulatory triggers (Schedule T GMP, Rule 158B safety/efficacy evidence, Rule 122E with 4 bioactive markers, FSSAI 2022 prohibition on synthetic additives and therapeutic claims).
3. **3.3 IP Domain Classification**:
   - Rigorously evaluates patent bars:
     - **Section 3(p)**: Triggered for classical formulations or known properties of traditional herbs.
     - **Section 3(d)**: Evaluates whether enhancement of therapeutic efficacy is demonstrated.
     - **Section 3(e)**: Flags mere admixture risks when combining known herbs.
     - **Section 10(4)**: Flags mandatory biological source and geographic origin disclosure.
     - **Budapest Treaty**: Flags biological material deposit requirements when microbial strains/fungi are involved.
   - Secondary IP Regimes: Evaluates Trademark distinctiveness (Trade Marks Act 1999), Trade Secrets (TRIPS Art 39), and Plant Varieties (PPVFR Act 2001).
   - TKDL Pointer: Flags defensive prior art reference without exposing non-public records.
4. **3.4 Jurisdiction & Regulatory Mapping**:
   - Maps target jurisdictions to their governing authorities (CDSCO, FDA CFSAN/CDER, EMA, MHRA, BfArM).
   - Identifies Access & Benefit Sharing (ABS) mandates: India BDA 2023 NBA approval vs Nagoya Protocol due diligence for EU/Germany.
5. **3.5 Research Plan Generation**:
   - Generates prioritized research tasks (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
   - Produces formulation-specific `recommended_crag_queries` for Phase 4 retrieval.
- **REST Endpoints**:
  - Automatically triggered upon case reaching `READY_FOR_RESEARCH`.
  - `POST /api/v1/cases/{id}/assess`: Idempotent endpoint to trigger or re-run Phase 3 assessment.
- **Test Coverage**: 23 tests verifying classification accuracy, Section 3(p) triggers, regulatory mapping, and plan generation (`backend/tests/test_case_assessment.py`).

### 3.4 Phase 4 — Research Engine & Preliminary Report Generation
- **Research Engine (`ml_pipeline/agents/research_engine.py`)**:
  - Automatically consumes Phase 3 `CaseAssessment` and orchestrates CRAG retrieval for all recommended queries.
  - Leverages process-wide singleton CRAG pipeline (`ml_pipeline/crag/pipeline_singleton.py`) for efficient, in-memory execution.
  - Enforces all Rules R1–R10 on every retrieval sub-query (zero orphan claims, sentence entailment, jurisdiction separation, confidence scoring).
- **Source Tier Classification**:
  - `Tier 1`: Official statutory portals, WIPO, WTO, CBD, AYUSH gazette.
  - `Tier 2`: Treaties, conventions, protocols, official acts.
  - `Tier 3`: Indian Kanoon and case law repositories.
  - `Tier 4`: Secondary / reference documentation.
- **Evidence & Risk Aggregation**:
  - Categorizes findings into discrete risk items (`HIGH`, `MEDIUM`, `LOW`) with statutory grounds (e.g., Section 3(p) TK bar risk, Section 6 NBA approval requirement, Rule 158B clinical evidence burden).
  - Explicitly surfaces `evidence_gaps` rather than hallucinating missing legal facts.
- **16-Section Structured Markdown Report (`CaseReport`)**:
  1. Executive Summary
  2. Innovation Profile
  3. User's Objective
  4. Product/Formulation Classification
  5. IP Domain Mapping
  6. Patent & Prior-Art Research
  7. Traditional Knowledge Assessment
  8. Biodiversity / ABS Assessment
  9. Regulatory Considerations
  10. Trademark / Other IP Considerations
  11. International Jurisdiction Analysis
  12. Risk Assessment
  13. Evidence Gaps
  14. Recommended Next Steps
  15. Human Review / Escalation Package
  16. Sources & Evidence (All verified citations with exact statutory dates)
- **Rule R5 Statutory Disclaimer**: Injected at string level — cannot be bypassed or suppressed by LLMs.
- **REST Endpoint**: `POST /api/v1/cases/{id}/report` (idempotent; auto-runs Phase 3 if not yet evaluated).
- **Test Coverage**: 13 tests covering generation, report structure, idempotency, evidence traceability, and exception safety (`backend/tests/test_case_report.py`).

### 3.5 Code-Enforced Legal Guardrails (Rules R1–R10)
All 10 legal guardrails are enforced deterministically in Python code:

| Rule | Title | Mechanism |
| :--- | :--- | :--- |
| **R1** | **Safe Abstention** | Evaluated at graph edge (`graph.py._edge_post_grade`). If zero retrieved chunks score `CORRECT`, pipeline halts and emits a safe refusal. |
| **R2** | **Zero Orphan Claims** | [`verifier.py`](file:///Users/ayushk/Desktop/assistant/ml_pipeline/crag/verifier.py) parses sentences; any sentence making a legal claim without a terminal `[chunk_id]` tag is stripped. |
| **R3** | **Citation Entailment Verification** | Compares assertions against retrieved chunk text with heuristic and NLI evaluation. |
| **R4** | **Strict Jurisdiction Separation** | National (India) and International treaty chunks are retrieved, processed, and rendered in distinct, labeled sections. |
| **R5** | **Mandatory Legal Disclaimer** | Appended at Python string-level by `OutputAssembler` (`"This is informational guidance, not legal advice..."`). LLMs cannot suppress it. |
| **R6** | **Paid-Source Consent Guard** | [`backend/app/core/r6_consent_guard.py`](file:///Users/ayushk/Desktop/assistant/backend/app/core/r6_consent_guard.py) intercepts all requests; queries touching gated databases are blocked unless affirmative `paid_source_consent=True` is logged. |
| **R7** | **Corpus Provenance Labeling** | Every chunk carries a `ProvenanceStatus` (`VERIFIED_PUBLIC`, `VERIFIED_PAID`, `MOCK_PENDING_ACCESS`). Mock chunks are excluded from generation. |
| **R8** | **Confidence Scoring** | Mandatory `HIGH` (≥0.85), `MEDIUM` (0.70–0.84), or `LOW` (<0.70) score attached to every API response. |
| **R9** | **Formulation Classification Gate** | Enforced in `CRAGPipeline.run()`: any query mentioning an Ayurvedic formulation triggers automatic classification before IP advice is rendered. |
| **R10** | **Version & Date Stamping** | Every citation returns exact statutory amendment dates (`effective_date` metadata). |

### 3.6 Frontend UI & Interactive Chatbot
- **Modern React + Vite Frontend** (`frontend/src/`):
  - **Conversational Chatbot**: Full conversational interaction supporting intent classification, case creation, and progressive intake.
  - **Rich Markdown Message Rendering**: Uses `react-markdown` with syntax-highlighted code blocks, bold emphasis, structured lists, and tables.
  - **Inline Phase 3 Assessment Panel**: Renders an executive card displaying classification badges, IP posture, target jurisdictions, prioritized research tasks, and statutory risk warnings.
  - **Phase 4 Research Report Modal**: Viewable and downloadable 16-section legal research report.
  - **Dynamic Follow-up Chips**: Contextual question chips generated from assessment recommendations.
  - **Case Switcher & Confirmation Dialogs**: Seamless context preservation with explicit user confirmation when initiating new innovation cases.
  - **Multilingual UI Support**: Interface language selector and voice recording controls.

---

## 4. Comprehensive Test Verification

### 4.1 Test Summary
All test suites pass with **100% success rate** across backend APIs, data models, ML pipelines, and CRAG retrieval:

```
============================= test session starts ==============================
platform darwin -- Python 3.12.13, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/ayushk/Desktop/assistant
collected 137 items

backend/tests/test_abs.py ..                                             [  1%]
backend/tests/test_case_assessment.py .......................            [ 18%]
backend/tests/test_case_intake.py ........................               [ 35%]
backend/tests/test_case_report.py .............                          [ 45%]
backend/tests/test_classify.py .....                                     [ 48%]
backend/tests/test_crag_api.py ....                                      [ 51%]
backend/tests/test_intent_api.py .........                               [ 58%]
backend/tests/test_r6_consent_guard.py .........                         [ 64%]
ml_pipeline/tests/test_crag_pipeline.py ......                           [ 69%]
ml_pipeline/tests/test_heuristic_fallbacks.py ........                   [ 75%]
ml_pipeline/tests/test_intent_classifier.py ...........................  [ 94%]
....                                                                     [ 97%]
ml_pipeline/tests/test_mmr.py ...                                        [100%]

======================= 137 passed, 5 warnings in 26.48s =======================
```

### 4.2 Breakdown by Test Suite

| Test Suite | Tests Passed | Focus Area |
| :--- | :---: | :--- |
| `backend/tests/test_abs.py` | 2 | BDA 2023 ABS fee slab (0.1%-0.5%) & AYUSH practitioner exemptions |
| `backend/tests/test_case_assessment.py` | 23 | Phase 3 deterministic 5-subpart classification & regulatory mapping |
| `backend/tests/test_case_intake.py` | 24 | Phase 2 progressive intake, entity extraction, deduplication & state |
| `backend/tests/test_case_report.py` | 13 | Phase 4 research engine, 16-section report assembly, risk & evidence gaps |
| `backend/tests/test_classify.py` | 5 | 5-tier Ayurvedic product classification decision tree |
| `backend/tests/test_crag_api.py` | 4 | National, International, Both, and Safe Abstention endpoints |
| `backend/tests/test_intent_api.py` | 9 | REST API for multi-intent recognition and entity extraction |
| `backend/tests/test_r6_consent_guard.py` | 9 | Rule R6 paid-source consent verification and blocking |
| `ml_pipeline/tests/test_crag_pipeline.py` | 6 | End-to-end CRAG retrieval, relevance grading, and citation verification |
| `ml_pipeline/tests/test_heuristic_fallbacks.py` | 8 | Deterministic zero-LLM fallbacks for grading and verification |
| `ml_pipeline/tests/test_intent_classifier.py` | 31 | Rule-based and LLM-based intent and entity extraction logic |
| `ml_pipeline/tests/test_mmr.py` | 3 | Maximal Marginal Relevance diversity and re-ranking mechanics |
| **Total Automated Tests** | **137** | **100% Passing (0 failures, 0 regressions)** |

### 4.3 Frontend Build Verification
The React + Vite frontend compiles cleanly with zero production bundle errors:
```bash
$ npm run build
vite v8.2.2 building client environment for production...
✓ 94 modules transformed.
dist/index.html                   0.80 kB │ gzip:   0.43 kB
dist/assets/index-DIx2fqdK.css   26.29 kB │ gzip:   5.77 kB
dist/assets/index-s0NcgcQ9.js   306.72 kB │ gzip: 100.16 kB
✓ built in 177ms
```

---

## 5. What Is Left to Implement (Future Roadmap & Gaps)

While the Core Retrieval, Intent Classification, Progressive Intake, Phase 3 Assessment, Phase 4 Research Engine, and Legal Guardrail engines are fully operational and verified, the following advanced items represent the roadmap for remaining implementation:

### 5.1 Knowledge Graph Multi-Hop Reasoning
- **Current Status**: Entity models and graph schema are defined in `ml_pipeline/knowledge_graph/schema.py`, and a graph builder script exists in `scripts/build_graph.py`.
- **Left to Implement**: Provisioning a live Neo4j database instance and wiring Cypher traversal queries directly into the LangGraph workflow. This will enable complex multi-hop reasoning:
  $$\text{Plant Species} \longrightarrow \text{Classical Formulation} \longrightarrow \text{First Schedule Text} \longrightarrow \text{Section 3(p) Bar} \longrightarrow \text{Prior Revocations}$$

### 5.2 IP India Dynamic Portal Integration
- **Current Status**: Endpoint constants and target schemas configured.
- **Left to Implement**: Real-time scraper and connector for InPASS (Indian Patent Advanced Search System), Trade Marks Registry search, and GI Registry certificate database.

### 5.3 Full Bhashini Speech & Translation Integration
- **Current Status**: Service stubs and language mappings for 10 Scheduled Indian languages are configured in `backend/app/services/bhashini_service.py`. Audio recording UI exists in the frontend.
- **Left to Implement**: Connecting live Government of India Bhashini ULCA credentials for ASR (Speech-to-Text) and TTS (Text-to-Speech) for rural farmers and traditional Vaidyas.

### 5.4 Certified Facilitator Admin Dashboard
- **Current Status**: `/api/v1/escalation` endpoint records escalation tickets with DPDP Act audit logging and human review packages.
- **Left to Implement**: A dedicated administrative web portal for certified AYUSH IP facilitators to review low-confidence queries (< 0.70) and provide certified human-in-the-loop assistance.

---

## 6. Quick Start & Execution Guide

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

### Step 3: Run the Complete Automated Test Suite (137 Tests)
```bash
COHERE_API_KEY="" PYTHONPATH=.:backend uv run pytest backend/tests/ ml_pipeline/tests/
```

### Step 4: Re-seed Corpus from Live Sources (Optional)
```bash
PYTHONPATH=. uv run python scripts/seed_corpus.py
```
