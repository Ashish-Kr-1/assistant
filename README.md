# IP-SAKTI Sahayak (SIH PS045)
> **Multilingual, Source-Cited AI Assistant for Ayurveda Intellectual Property & Regulatory Guidance across National & International Regimes**

[![Python 3.12](https://img.shields.io/badge/python-3.12+-0f382c.svg)](backend/)
[![React 18](https://img.shields.io/badge/react-18.0+-61dafb.svg)](frontend/)
[![Vite](https://img.shields.io/badge/vite-8.2+-646cff.svg)](frontend/)
[![Tests](https://img.shields.io/badge/tests-137%2F137%20passing-brightgreen.svg)](backend/tests/)
[![Guardrails](https://img.shields.io/badge/legal%20guardrails-Rules%20R1--R10-orange.svg)](ml_pipeline/crag/)
[![DPDP Act Compliant](https://img.shields.io/badge/DPDP_2023-Privacy_Compliant-green.svg)](docs/dpdp_compliance_policy.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-gold.svg)](LICENSE)

---

## 🌟 Executive Summary & Problem Statement

In India and globally, researchers, practitioners, Ayurvedic Vaidyas, startups, and MSMEs working with Traditional Knowledge (TK) and biological resources navigate one of the world’s most stringent and fragmented statutory landscapes:

1. **Strict Patent Bars & Biopiracy Prevention (The Patents Act, 1970)**:
   - **Section 3(p)**: Inventions that are in effect traditional knowledge or an aggregation/duplication of known properties of traditionally known components are **statutorily non-patentable**.
   - **Section 3(d)**: Mere discovery of a new form of a known substance without demonstrable enhancement of therapeutic efficacy is barred.
   - **Section 3(e)**: Mere admixture resulting only in aggregation of properties is non-patentable.
   - **Section 10(4) & Budapest Treaty**: Mandatory disclosure of biological material source and geographical origin; deposit of microorganisms with an International Depositary Authority (IDA).
   - **Section 25 & Section 64**: Pre/post-grant opposition and patent revocation grounds for non-disclosure or wrongful disclosure of geographic origin or anticipation by traditional knowledge.
2. **Access and Benefit Sharing (ABS) Compliance (Biological Diversity Act, 2002 / 2023)**:
   - Sections 3, 4, 6, 19, and 21 mandate prior approval from the National Biodiversity Authority (NBA) before accessing biological resources or applying for IP rights based on Indian biological resources.
   - Section 24 requires prior intimation to State Biodiversity Boards (SBB), with ABS fee slabs (0.1%–0.5% ex-factory sales) under the Biological Diversity Rules 2024 (exempting registered AYUSH practitioners and cultivated medicinal plants).
3. **Complex 5-Tier Drug & Food Regulatory Classification**:
   - **Classical Medicine** (Drugs & Cosmetics Act 1940): Strictly according to the 71 authoritative Ayurvedic texts listed in the First Schedule, regulated under Schedule T GMP.
   - **Patent & Proprietary (P&P) Medicine**: Governed by Rule 158B proof of safety and effectiveness.
   - **Phytopharmaceutical Drug**: Governed by CDSCO Rule 122E (standardized fractions with ≥4 bioactive markers and Phase I–III clinical trials).
   - **Ayurveda Aahara (Food/Nutraceutical)**: Regulated by FSSAI 2022 Regulations & Oct 2024 Compendium (strictly requires authoritative text lineage, prohibits synthetic vitamins/minerals, therapeutic disease claims, and classical bhasmas).
   - **Cosmetic**: Regulated under Cosmetics Rules 2020 (Form 32 license, BIS compliance).
4. **International Treaty Harmonization**:
   - **WIPO GRATK Treaty (Geneva, 2024)**: Mandatory patent disclosure of genetic resources and local community traditional knowledge.
   - **WTO TRIPS Agreement** (Articles 22, 27, 28, 39), **CBD Nagoya Protocol** (Articles 5, 6, 7, 12 on Prior Informed Consent & Mutually Agreed Terms), **Budapest Treaty**, **PCT**, **Madrid Protocol**, and **Hague Agreement**.

### The AI Hallucination Hazard in Legal Tech
Standard generative LLMs present a catastrophic risk: they invent non-existent statutory sections, conflate US/European doctrines with Indian jurisprudence, confuse drug licensing with food standards, and fail to warn of mandatory NBA approvals (risking criminal penalties and patent revocation under Section 64).

### The Solution: IP-SAKTI Sahayak
**IP-SAKTI Sahayak** is an authoritative, zero-hallucination, multilingual, Corrective Retrieval-Augmented Generation (CRAG) AI assistant engineered to resolve these challenges through **100% Real Statutory Ingestion**, **Deterministic Code-Enforced Legal Guardrails (Rules R1–R10)**, a **Canonical Single Source of Truth for Ayurvedic Formulations**, and **Defensive TKDL Pointers**.

---

## 🏗 System Architecture & End-to-End Flow

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
                                         - Inline Assessment Card
                                         - Grounded Legal Answers
```

---

## 🧩 The 4-Phase System Implementation

### Phase 1: Intent & Entity Classification Layer
- **Dual-Layer Architecture**: High-speed deterministic regex/keyword matching (`ml_pipeline/classifier/intent_rules.py`) combined with structured JSON LLM classification (`ml_pipeline/classifier/intent_classifier.py`) and robust offline heuristic fallback.
- **11 Supported Intent Classes**:
  - `INNOVATION_INTAKE`: User describes a new Ayurvedic product, recipe, or technology.
  - `CASE_STATUS`: User checks active case progress.
  - `LEGAL_QUERY`: Direct questions on statutes (Section 3(p), Section 3(d), Section 6 BDA, WIPO GRATK).
  - `PATENTABILITY_ASSESSMENT`: Questions regarding patent bars and novelty criteria.
  - `REGULATORY_GUIDANCE`: AYUSH, FSSAI Ayurveda Aahara, or CDSCO pathways.
  - `ABS_GUIDANCE`: BDA 2023 approval requirements, SBB intimation, and fee calculations.
  - `TRADEMARK_SEARCH`: Brand names, marks, distinctiveness under Trade Marks Act 1999.
  - `PRIOR_ART_SEARCH`: TKDL, published literature, anticipation checks.
  - `HUMAN_ESCALATION`: Requests for certified patent attorneys or AYUSH facilitators.
  - `GREETING`: Conversational pleasantries.
  - `OUT_OF_SCOPE`: Safe deflection of questions unrelated to Ayurveda or IP.
- **Entity Extraction**: Automatically extracts formulation name, botanical ingredients, therapeutic indications, target jurisdictions, development stage, applicant type, and prior art basis.

### Phase 2: Innovation Intake & Case Lifecycle Management
- **Persistence Store**: Dual-backend architecture with PostgreSQL (production) and automatic local SQLite fallback (`ipsakti_cases.db`) using SQLAlchemy ORM (`backend/app/db/models.py`).
- **Conversational Intake Agent (`InnovationIntakeAgent`)**:
  - **Progressive Questioning**: Promptly asks for missing fields (ingredients, TK lineage, target jurisdictions, intended use) one dimension at a time.
  - **Zero-Hallucination Provenance**: Records provenance flags (`USER_STATED` vs `EXTRACTED_UNCONFIRMED`).
  - **Ingredient Deduplication**: Merges and deduplicates herbal components across multi-turn interactions.
- **Lifecycle State Machine**: `INTAKE_IN_PROGRESS` → `READY_FOR_RESEARCH` → `RESEARCH_COMPLETED` (or `ESCALATED`).

### Phase 3: Innovation Classification & Legal Domain Mapping
A **100% deterministic, zero-LLM** pipeline (`ml_pipeline/agents/case_assessment_agent.py`) divided into 5 modular subparts:
1. **3.1 Case Normalization**: Validates `InnovationProfile`, standardizes jurisdiction aliases to ISO codes (`INDIA`, `USA`, `EU`, `UK`, `GERMANY`), and scores completeness (`MINIMAL` to `COMPREHENSIVE`).
2. **3.2 Product Classification**: Maps formulations into the 5-tier statutory taxonomy, verifying lineage against the First Schedule's 71 authoritative Ayurvedic texts.
3. **3.3 IP Domain Classification**: Rigorously analyzes patent eligibility:
   - **Section 3(p)**: Flags traditional knowledge anticipation.
   - **Section 3(d)**: Flags enhancement of therapeutic efficacy requirements.
   - **Section 3(e)**: Flags mere admixture risks.
   - **Section 10(4)**: Flags mandatory biological source and geographical origin disclosure.
   - **Budapest Treaty**: Flags IDA microorganism deposit requirements.
   - Secondary IP: Analyzes Trademark distinctiveness, Trade Secrets (TRIPS Art 39), and Plant Varieties (PPVFR Act 2001).
4. **3.4 Jurisdiction & Regulatory Mapping**: Maps target countries to competent authorities (CDSCO, FDA, EMA, MHRA, BfArM) and Access & Benefit Sharing (ABS) mandates (India BDA 2023 vs EU/Germany Nagoya Protocol).
5. **3.5 Research Plan Generation**: Produces prioritized research tasks (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) and recommended CRAG queries for Phase 4.

### Phase 4: Research Engine & Preliminary Report Generation
- **Research Engine (`ml_pipeline/agents/research_engine.py`)**: Consumes the Phase 3 assessment and executes recommended queries through the CRAG retrieval pipeline using a process-wide singleton vector store.
- **Source Tier Classification**:
  - `Tier 1`: Official statutory portals, WIPO, WTO, CBD, AYUSH gazettes.
  - `Tier 2`: Treaties, conventions, protocols.
  - `Tier 3`: Indian Kanoon and court judgments.
  - `Tier 4`: Reference documents and secondary materials.
- **Evidence & Risk Aggregation**: Identifies statutory risk items (`HIGH`, `MEDIUM`, `LOW`), notes evidence gaps, and produces a Human Escalation Package.
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
  16. Sources & Evidence (all citations with exact dates and chunk references)

---

## 🛡 Code-Enforced Legal Guardrails (Rules R1–R10)

All 10 legal guardrails are enforced deterministically in Python code:

| Rule | Title | Mechanism |
| :--- | :--- | :--- |
| **R1** | **Safe Abstention** | If zero retrieved chunks score `CORRECT`, the pipeline halts and emits a safe refusal. |
| **R2** | **Zero Orphan Claims** | Sentences asserting legal claims without a terminal `[chunk_id]` citation are stripped. |
| **R3** | **Citation Entailment Verification** | Programmatically verifies assertions against chunk text with deterministic keyword and NLI matching. |
| **R4** | **Strict Jurisdiction Separation** | National (India) and International treaty chunks are retrieved, processed, and rendered in distinct, labeled sections. |
| **R5** | **Mandatory Legal Disclaimer** | Appended at Python string-level by `OutputAssembler` (`"This is informational guidance, not legal advice..."`). LLMs cannot suppress it. |
| **R6** | **Paid-Source Consent Guard** | Blocks queries touching gated databases unless affirmative `paid_source_consent=True` is verified. |
| **R7** | **Corpus Provenance Labeling** | Every chunk carries a `ProvenanceStatus` (`VERIFIED_PUBLIC`, `VERIFIED_PAID`, `MOCK_PENDING_ACCESS`). Mock chunks are excluded from generation. |
| **R8** | **Confidence Scoring** | Mandatory `HIGH` (≥0.85), `MEDIUM` (0.70–0.84), or `LOW` (<0.70) score attached to every API response. |
| **R9** | **Formulation Classification Gate** | Queries mentioning an Ayurvedic formulation trigger automatic classification before IP advice is rendered. |
| **R10** | **Version & Date Stamping** | Every citation returns exact statutory amendment dates (`effective_date` metadata). |

---

## 🧪 Comprehensive Automated Test Verification

Every component is tested with **137 automated tests passing with 100% pass rate (0 failures, 0 regressions)**:

```bash
COHERE_API_KEY="" PYTHONPATH=.:backend uv run pytest backend/tests/ ml_pipeline/tests/
```

### Test Suite Breakdown

| Test Suite | Passing Tests | Verified Scope |
| :--- | :---: | :--- |
| `backend/tests/test_abs.py` | **2** | BDA 2023 ABS fee slab (0.1%–0.5%) & AYUSH practitioner exemptions |
| `backend/tests/test_case_assessment.py` | **23** | Phase 3 deterministic 5-subpart classification & regulatory mapping |
| `backend/tests/test_case_intake.py` | **24** | Phase 2 progressive intake, entity extraction, deduplication & state |
| `backend/tests/test_case_report.py` | **13** | Phase 4 research engine, 16-section report assembly, risk & evidence gaps |
| `backend/tests/test_classify.py` | **5** | 5-tier Ayurvedic product classification decision tree |
| `backend/tests/test_crag_api.py` | **4** | National, International, Both, and Safe Abstention endpoints |
| `backend/tests/test_intent_api.py` | **9** | REST API for multi-intent recognition and entity extraction |
| `backend/tests/test_r6_consent_guard.py` | **9** | Rule R6 paid-source consent verification and blocking |
| `ml_pipeline/tests/test_crag_pipeline.py` | **6** | End-to-end CRAG retrieval, relevance grading, and citation verification |
| `ml_pipeline/tests/test_heuristic_fallbacks.py` | **8** | Deterministic zero-LLM fallbacks for grading and verification |
| `ml_pipeline/tests/test_intent_classifier.py` | **31** | Rule-based and LLM-based intent and entity extraction logic |
| `ml_pipeline/tests/test_mmr.py` | **3** | Maximal Marginal Relevance (MMR) diversity and re-ranking |
| **Total Automated Tests** | **137** | **137 passed in 26.48s (100% pass rate)** |

### Frontend Build Verification
The React + Vite frontend compiles with zero errors:
```bash
vite v8.2.2 building client environment for production...
✓ 94 modules transformed in 177ms (dist/ ready for production).
```

---

## 💻 Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy ORM, Pydantic v2, Qdrant Client, SQLite / PostgreSQL.
- **Frontend**: React 18, Vite, Vanilla CSS Modules / Tailwind, React Markdown, Lucide Icons.
- **AI / Retrieval**: Qdrant Vector Store, Cohere Multilingual Embed v3 (`embed-multilingual-v3.0`), Maximal Marginal Relevance (MMR), Google Gemini 2.5 Flash / Cohere Chat.
- **Testing**: Pytest, TestClient, AnyIO.

---

## 🚀 Quick Start Guide

### 1. Clone & Configure
```bash
git clone https://github.com/Ashish-Kr-1/assistant.git
cd assistant
cp .env.example .env
```

### 2. Run the FastAPI Backend
```bash
# Using uv or virtual environment:
PYTHONPATH=.:backend uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
* Interactive OpenAPI Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3. Run the React + Vite Frontend
```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```
* Web Application: [http://127.0.0.1:5173/chatbot](http://127.0.0.1:5173/chatbot)

### 4. Run the Full Test Suite
```bash
COHERE_API_KEY="" PYTHONPATH=.:backend uv run pytest backend/tests/ ml_pipeline/tests/
```

### 5. Re-seed the Statutory Legal Corpus (Optional)
```bash
PYTHONPATH=. uv run python scripts/seed_corpus.py
```

---

## 📡 Key REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/intent/classify` | Multi-intent classification & entity extraction |
| `POST` | `/api/v1/cases` | Create a new innovation case |
| `GET` | `/api/v1/cases/active` | Get active case for conversation |
| `GET` | `/api/v1/cases/{id}` | Retrieve complete case profile, assessment & report |
| `POST` | `/api/v1/cases/{id}/intake` | Submit progressive conversational intake message |
| `PATCH` | `/api/v1/cases/{id}` | Update or patch case profile fields |
| `POST` | `/api/v1/cases/{id}/assess` | Trigger Phase 3 deterministic assessment |
| `POST` | `/api/v1/cases/{id}/report` | Trigger Phase 4 CRAG research & preliminary report |
| `POST` | `/api/v1/query` | Direct CRAG legal Q&A with Rule R6 consent check |
| `POST` | `/api/v1/classify` | 5-tier Ayurvedic product classification decision tree |
| `GET` | `/api/v1/abs/calculate` | BDA 2023 ABS fee slab & practitioner exemption calculator |
| `POST` | `/api/v1/escalation` | Create human IP facilitator escalation ticket |
| `GET` | `/health` | System health check and collection status |

---

## 🔮 Future Roadmap

1. **Neo4j Knowledge Graph Multi-Hop Reasoning**: Wire Cypher traversal queries into the LangGraph workflow (`Plant Species → Classical Formulation → First Schedule Text → Section 3(p) Bar → Prior Revocations`).
2. **InPASS & IP India Live Search Integration**: Dynamic scraper for InPASS, Trade Marks Registry, and GI certificates.
3. **Government of India Bhashini ULCA Speech Pipeline**: Real-time ASR (Speech-to-Text) and TTS (Text-to-Speech) for traditional Vaidyas and farmers across 22 Scheduled Indian languages.
4. **Certified Facilitator Admin Dashboard**: Web portal for certified AYUSH IP facilitators to review low-confidence queries (< 0.70) and provide manual legal assistance.

---

## 📄 License & Compliance

- **License**: Distributed under the MIT License. See [LICENSE](LICENSE) for details.
- **DPDP Act 2023 Notice**: No user query data is stored without explicit consent. Cryptographic session hashing is enforced for audit logs.
- **Statutory Disclaimer**: *Information provided by IP-SAKTI Sahayak is for informational and research guidance purposes only and does not constitute formal legal advice.*
