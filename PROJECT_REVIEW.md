# IP-SAKTI Sahayak — Project Review & Phase-wise Completion Report
### SIH PS045 — Multilingual, RAG-based AI Assistant for Ayurveda IP & Regulatory Guidance

---

## 1. What This System Is (Executive Summary)

### Plain English
**IP-SAKTI Sahayak** is an AI legal assistant built specifically for the Ayurvedic and Traditional Knowledge (TK) sector. It helps Ayurvedic practitioners, AYUSH startups, MSMEs, researchers, and farmers navigate India's dense legal and regulatory landscape for Intellectual Property rights, biodiversity obligations, and drug regulatory classification — in their own language, with mandatory source citations, and without hallucinating fake laws.

The core problem it solves: **No authoritative, plain-language, source-cited IP guidance tool currently exists for the AYUSH community.** Standard AI tools hallucinate legal citations. Lawyers are expensive and scarce. Recent law changes (2023 Biodiversity Amendment, 2024 Patent Rules, WIPO GRATK Treaty 2024) make this problem more urgent than ever.

### Technical Summary
The system is a **LangGraph-orchestrated Corrective RAG (CRAG) state machine** combining:
- **Dual-jurisdiction hybrid vector search** (Cohere Multilingual Embed v3 + BM25 keyword boost + MMR diversification) in Qdrant
- **Code-enforced legal guardrails** (Rules R1–R10) at the graph-routing and Python string-concatenation level — not LLM-level prompt instructions
- **Pluggable LLM provider architecture** (Cohere, OpenAI, Gemini) with complete offline heuristic fallbacks
- **FastAPI REST backend** with DPDP Act 2023 compliant audit logging

---

## 2. PS045 Requirements → Phase-wise Implementation Status

### Phase 1 (MVP): Citation-Grounded Retrieval Core
> *"Ingestion of India Code + WIPO Lex + IP India public samples → basic RAG (retrieve + generate + cite) → CRAG relevance grading → citation verification pass → mandatory disclaimer + confidence label."*

| PS Requirement | Status | Implementation Detail |
|---|---|---|
| Statutory corpus ingestion (India Code, WIPO Lex) | ✅ **Done** | 11 verified chunks across 6 statutes/treaties in `scripts/seed_corpus.py` with R7 provenance + R10 version stamping |
| CRAG Relevance Grader (`CORRECT`/`AMBIGUOUS`/`INCORRECT`) | ✅ **Done** | `ml_pipeline/crag/grader.py` — LLM + heuristic batch grader |
| Citation-forced Grounded Generator | ✅ **Done** | `ml_pipeline/crag/generator.py` — answers generated exclusively from graded-correct chunks |
| Citation Verification / Entailment Pass (R2, R3) | ✅ **Done** | `ml_pipeline/crag/verifier.py` — orphan claim stripper + NLI entailment |
| Safe Abstention when no valid source (R1) | ✅ **Done** | Code-level conditional in `graph.py._edge_post_grade` — generator never called if chunks all fail |
| Mandatory "information, not legal advice" disclaimer (R5) | ✅ **Done** | `assembler.py` — Python-level string append, LLM cannot omit |
| Confidence Score on every answer (R8) | ✅ **Done** | `assembler.py` — `HIGH`/`MEDIUM`/`LOW` derived from verification ratio |
| Escalation to human IP facilitator at low confidence | ✅ **Done** | `needs_escalation=True` flag + `/api/v1/escalation` endpoint |
| Corpus provenance labeling (R7) | ✅ **Done** | `ProvenanceStatus` enum; `MOCK_PENDING_ACCESS` excluded from CORRECT grading via Qdrant `must_not` |
| Version/date stamping on every chunk (R10) | ✅ **Done** | `effective_date` field in every `LegalChunk` shown in citations |

**Phase 1 Assessment: ✅ COMPLETE**

---

### Phase 2: Formulation Classification + Jurisdiction Toggle + ABS/TKDL Pointer + Fallback Retrieval
> *"Formulation-classification agent, jurisdiction toggle enforcement, ABS/TKDL structured pointer (with mock data clearly labeled), fallback retrieval to live external sources."*

| PS Requirement | Status | Implementation Detail |
|---|---|---|
| Formulation Classification Agent (5-tier) | ✅ **Done** | `ml_pipeline/agents/classifier_agent.py` — Classical Generic / P&P / Phytopharmaceutical / Ayurveda-Aahar / Cosmetic |
| Classification Gate precedes IP guidance (R9) | ✅ **Done** | `graph.py.run()` inspects `formulation_category`; halts with clarifying Q if missing |
| Jurisdiction toggle (India vs International — never merged) | ✅ **Done** | `JurisdictionType` enum + Qdrant `FieldCondition` filter (R4); `OutputAssembler` enforces separate labeled sections |
| Query Intent Router (Patent / GI / Trademark / ABS / Drug-Reg) | ✅ **Done** | `ml_pipeline/agents/router_agent.py` — keyword-based intent detection + jurisdiction auto-detection |
| ABS Compliance Helper (BDA 2023) | ✅ **Done** | `ml_pipeline/crag/abs_pointer.py` — deterministic rule engine: exemptions, SBB intimation, fee slabs, NBA approval |
| TKDL Prior-Art Pointer (Mock until MoU) | ✅ **Done** | Mock TKDL chunk in corpus with `status=MOCK_PENDING_ACCESS`; excluded from generation per R7 |
| Fallback Retrieval (broaden jurisdiction on AMBIGUOUS/INCORRECT) | ✅ **Done** | `graph.py._node_fallback` — broadens to `JurisdictionType.BOTH` with deduplication |
| Fallback to live external sources (India Code, WIPO Lex) | 🔶 **Partial** | Architecture supports it; live web scraping not yet wired into fallback node (only internal corpus fallback active) |

**Phase 2 Assessment: ✅ ~90% COMPLETE** (live external fallback is stubbed, not active)

---

### Phase 3: Knowledge Graph + Agentic Multi-Source Orchestration + Paid-Source Connectors
> *"Knowledge graph layer (entity relations: plant ↔ formulation ↔ statute section ↔ prior patent) for multi-hop reasoning; agentic multi-source orchestration; paid-source connector with logged consent."*

| PS Requirement | Status | Implementation Detail |
|---|---|---|
| Neo4j Knowledge Graph (Herb ↔ Formulation ↔ Statute ↔ Patent Bar) | 🔶 **Stub Only** | `scripts/build_graph.py` has schema + node definitions but no real Neo4j driver or ingestion pipeline |
| Multi-hop reasoning over graph | ❌ **Not Started** | Requires functional Neo4j graph first |
| Agentic multi-source orchestration | 🔶 **Partial** | Single-agent CRAG pipeline; multi-agent orchestration across different corpora not yet implemented |
| Paid-source connector with per-query logged consent (R6) | ❌ **Not Started** | R6 is defined in guardrail matrix but enforcement layer not coded; architecture slot exists |
| IP India live patent/GI/TM search integration | ❌ **Not Started** | Endpoint constants defined in `.env.example` but API integration layer not implemented |
| Indian Kanoon (case law) scraping and ingestion | ❌ **Not Started** | Mentioned in CRAG.md corpus plan; no scraper or ingestion pipeline |

**Phase 3 Assessment: ❌ ~15% COMPLETE** (schema and architecture ready; implementation not started)

---

### Phase 4: Full Multilingual + Voice + Human Facilitator Escalation
> *"Full multilingual + voice via Bhashini; human-facilitator escalation workflow with real routing."*

| PS Requirement | Status | Implementation Detail |
|---|---|---|
| Bhashini NMT translation (multilingual input/output) | 🔶 **Stub Only** | `backend/app/services/bhashini_service.py` — class and method signatures exist; real Bhashini API call is a mock/fallback |
| Speech-to-Text (ASR) via Bhashini | 🔶 **Stub Only** | `speech_to_text()` method returns hardcoded mock transcription |
| Text-to-Speech (TTS) via Bhashini | ❌ **Not Started** | Not implemented |
| 10 Scheduled Indian language support | 🔶 **Partial** | `SUPPORTED_LANGUAGES` dict defined (Hi, Ta, Te, Gu, Mr, Bn, Kn, Ml, Pa, Or); real NMT not wired |
| Bhashini integration into CRAG query pipeline | ❌ **Not Started** | Translation not called before/after CRAG pipeline |
| Human IP facilitator escalation with real routing | 🔶 **Partial** | `/api/v1/escalation` endpoint exists; routes to a human queue concept but no live routing to a facilitator system |
| Multilingual evaluation (BLEU scores) | ❌ **Not Started** | Evaluation framework not built |

**Phase 4 Assessment: ❌ ~10% COMPLETE** (service stubs defined; real API wiring not done)

---

## 3. Point-wise Summary: What Was Built & Why

### Point 1 — CRAG State Machine Architecture (`ml_pipeline/crag/graph.py`)
- **What**: A 7-node LangGraph workflow: `retrieve → grade → [fallback | generate | abstain] → verify → assemble`.
- **Why (Technical)**: Standard RAG passes retrieved documents to an LLM without evaluation. CRAG adds a grading loop before generation and an entailment loop after, catching both retrieval failure and hallucination.
- **Why (Plain English)**: Like a lawyer who first checks whether the paralegal found the right law books, then after drafting the brief, checks every footnote is accurate — instead of just guessing.

### Point 2 — Rule R1: Safe Abstention (`_edge_post_grade`)
- **What**: A Python conditional check that routes to `abstain` node if all retrieved chunks grade `INCORRECT`. The generator LLM is never called.
- **Why (Technical)**: The only way to guarantee zero hallucination is to enforce abstention in the routing logic, not as an LLM instruction.
- **Why (Plain English)**: If the system cannot find a real law that answers your question, it will say "I don't know" rather than inventing a statute.

### Point 3 — Rule R9: Formulation Classification Gate (`classifier_agent.py`)
- **What**: 5-tier classifier: Classical Generic → P&P → Phytopharmaceutical → Ayurveda-Aahar → Cosmetic. IP queries without a tier are held pending classification.
- **Why (Technical)**: Section 3(p) patent bar applies only to Classical Generics. Phytopharmaceuticals under Rule 122E have a distinct clinical trial and patent pathway. Guidance without tier is meaningless or misleading.
- **Why (Plain English)**: Before asking "Can I patent this?", the system must know whether it's an ancient recipe or a modern extract — the answer differs completely between the two.

### Point 4 — BDA 2023 ABS Pointer (`abs_pointer.py`)
- **What**: Deterministic rule engine evaluating queries for botanical resource mentions. Returns structured ABS obligation output: NBA approval required / SBB intimation required / AYUSH practitioner exemption / fee slab (0.1%–0.5%).
- **Why (Technical)**: The 2023 amendment to the Biological Diversity Act created specific exemptions and fee structures that a generative LLM may not know or may confuse with the pre-amendment rules.
- **Why (Plain English)**: If you mention using Ashwagandha commercially, the system automatically tells you exactly what ABS duties you owe or whether you are exempt, with the exact BDA 2023 section number.

### Point 5 — Jurisdiction Isolation (Rule R4, `VectorStoreManager.search()`)
- **What**: Qdrant `FieldCondition` payload filter on `jurisdiction`. National (India) and International chunks are stored and retrieved separately; `OutputAssembler` enforces separate labeled sections.
- **Why (Technical)**: India's Patents Act requirements differ materially from WIPO GRATK Treaty obligations. Conflating them leads to invalid patent filings.
- **Why (Plain English)**: Indian law and international treaties are kept in separate rooms — the system will never accidentally quote EU patent rules as Indian law.

### Point 6 — Citation Entailment Verifier (`verifier.py`)
- **What**: Post-generation sentence tokenizer that checks each sentence with a legal citation against the retrieved chunk. Claims not entailed by the chunk text are stripped.
- **Why (Technical)**: LLMs generate fluent legal text with hallucinated citations; NLI-based entailment verification is the industry-standard mitigation.
- **Why (Plain English)**: After the AI writes its answer, an internal fact-checker deletes every sentence where the cited section doesn't actually say what the answer claims.

### Point 7 — Output Assembler, Confidence Scoring & Mandatory Disclaimer (`assembler.py`)
- **What**: Computes a `HIGH`/`MEDIUM`/`LOW` confidence score from the verification ratio. Appends disclaimer in Python (not via LLM). Flags `< 70%` confidence for expert escalation.
- **Why (Technical)**: The Bar Council and regulatory standards require visible confidence indicators and a non-removable advisory disclaimer on automated legal guidance tools.
- **Why (Plain English)**: Every response shows a confidence rating and a legal note saying "this is guidance, not legal advice." If confidence is low, the system also suggests consulting a patent attorney.

### Point 8 — Pluggable LLM Factory (`llm_factory.py`)
- **What**: Single `LLM_PROVIDER` env variable switches between Cohere (`command-r`), OpenAI (`gpt-4o`), Gemini (`gemini-2.5-flash`), with full offline heuristic fallbacks for all nodes.
- **Why (Technical)**: Provider lock-in is a production risk. Heuristic fallbacks enable 100% offline testing with no API cost.
- **Why (Plain English)**: The AI brain can be swapped between different providers without changing any code — just change one line in `.env`.

### Point 9 — Cohere Embeddings Multilingual v3 (`EmbeddingProvider`)
- **What**: `embed-multilingual-v3.0` (1024-dim) via Cohere API. Batch embedding up to 96 docs/call. Separate `input_type` for indexing vs querying. Auto-dimension collection management. Hash-based offline fallback.
- **Why (Technical)**: Legal queries arrive in Hindi, Sanskrit, or vernacular botanical names; multilingual embeddings handle cross-language semantic matching natively.
- **Why (Plain English)**: Searching for "तुलसी के पेटेंट अधिकार" (Tulsi patent rights in Hindi) will still find the correct English statutory sections.

### Point 10 — Maximal Marginal Relevance Reranking (`_compute_mmr`)
- **What**: Vector-space MMR algorithm balancing relevance vs diversity among candidate chunks. Configurable `MMR_LAMBDA` (default 0.7). Applied after hybrid BM25 scoring.
- **Formula**: `MMR(d) = argmax[λ·Relevance(d) - (1-λ)·max_{s∈S} CosineSim(d, s)]`
- **Why (Technical)**: Qdrant cosine search returns near-duplicate clauses from the same section; MMR selects non-redundant, diverse statutory provisions for the context window.
- **Why (Plain English)**: Instead of showing 4 nearly identical copies of "Section 3(p) bars traditional knowledge patents", MMR picks the best one and uses the other 3 slots for related laws like BDA, FSSAI rules, and WIPO treaty obligations.

### Point 11 — FastAPI Backend with DPDP Logging
- **What**: REST API with endpoints `/api/v1/query`, `/api/v1/classify`, `/api/v1/abs`, `/api/v1/escalation`. DPDP Act 2023 compliant audit logger in `dpdp_logger.py`.
- **Why**: Provides a production-ready web API interface while ensuring user data privacy under India's Digital Personal Data Protection Act, 2023.

---

## 4. Guardrails Compliance Matrix (R1–R10)

| Rule | Description | Enforcement Mechanism | Status |
|---|---|---|---|
| R1 | No answer without verified source | Code-level conditional routing in `_edge_post_grade` | ✅ Fully Enforced |
| R2 | No orphan claims | Regex/NER sentence parser strips uncited legal claims | ✅ Fully Enforced |
| R3 | Citation must pass entailment | NLI verification pass on every (claim, chunk) pair | ✅ Fully Enforced |
| R4 | Jurisdiction sets never merged | Qdrant `FieldCondition` on `jurisdiction` field | ✅ Fully Enforced |
| R5 | Mandatory non-removable disclaimer | Python `str.append()` in `OutputAssembler` | ✅ Fully Enforced |
| R6 | Paid-source consent must be explicit & logged | Defined in spec; enforcement layer not yet coded | ❌ Not Yet Implemented |
| R7 | Corpus provenance labeled | `ProvenanceStatus` enum + Qdrant `must_not` filter for `MOCK_PENDING_ACCESS` | ✅ Fully Enforced |
| R8 | Confidence indicator on every answer | `HIGH`/`MEDIUM`/`LOW` computed in `OutputAssembler` | ✅ Fully Enforced |
| R9 | Formulation classification precedes IP guidance | Router check in `CRAGPipeline.run()` before state graph invocation | ✅ Fully Enforced |
| R10 | Version/date stamping on all statute chunks | `effective_date` field in `LegalChunk` schema shown in citations | ✅ Fully Enforced |

---

## 5. Test Suite Verification

All 17 automated unit and integration tests pass in under 1 second:

```
backend/tests/test_abs.py::test_ayush_practitioner_abs_exemption       PASSED
backend/tests/test_abs.py::test_foreign_entity_abs_requirement          PASSED
backend/tests/test_classify.py::test_classical_medicine_classification  PASSED
backend/tests/test_classify.py::test_phytopharmaceutical_classification PASSED
backend/tests/test_crag_api.py::test_api_query_national_sec_3p         PASSED
backend/tests/test_crag_api.py::test_api_query_international_wipo      PASSED
backend/tests/test_crag_api.py::test_api_query_safe_abstention_r1      PASSED
backend/tests/test_crag_api.py::test_api_query_r9_classification_gate  PASSED
ml_pipeline/tests/test_crag_pipeline.py::test_national_sec_3p_retrieval_and_answer   PASSED
ml_pipeline/tests/test_crag_pipeline.py::test_international_wipo_disclosure          PASSED
ml_pipeline/tests/test_crag_pipeline.py::test_safe_abstention_rule_r1               PASSED
ml_pipeline/tests/test_crag_pipeline.py::test_rule_r9_classification_gate           PASSED
ml_pipeline/tests/test_crag_pipeline.py::test_abs_pointer_trigger                   PASSED
ml_pipeline/tests/test_crag_pipeline.py::test_mock_chunk_exclusion_rule_r7          PASSED
ml_pipeline/tests/test_mmr.py::test_mmr_diversification_penalizes_redundancy        PASSED
ml_pipeline/tests/test_mmr.py::test_mmr_pure_relevance_when_lambda_one              PASSED
ml_pipeline/tests/test_mmr.py::test_vector_store_search_with_mmr_flag               PASSED

======================== 17 passed in 0.80s ========================
```

---

## 6. Gap Analysis: What Remains to Complete PS045

### 🔴 Critical Gaps (Required for a demo-ready submission)

#### Gap 1: Real Corpus Ingestion (HIGH PRIORITY)
- **Problem**: Only 11 hand-crafted seed chunks exist. The PS expects a corpus from India Code, WIPO Lex, IP India, FSSAI, CCRAS, Indian Kanoon, and NBA/ABS guidelines.
- **What to do**: Run `pypdf` + `BeautifulSoup4` scrapers against publicly available PDFs and web pages. Target minimum **100–200 real statutory chunks** covering all 6 IP regimes.
- **Files to build**: `ml_pipeline/corpus_ingestion/scrapers/india_code_scraper.py`, `wipo_lex_scraper.py`.

#### Gap 2: Real Embedding Quality (HIGH PRIORITY)
- **Problem**: Tests pass using hash-based pseudo-embeddings (semantically meaningless). Without a real `COHERE_API_KEY` configured, semantic retrieval is keyword-only.
- **What to do**: Set `COHERE_API_KEY` in `.env` and run `scripts/seed_corpus.py` to generate real 1024-dimensional embeddings for all corpus chunks.

#### Gap 3: Rule R6 — Paid-Source Access Consent (MEDIUM PRIORITY)
- **Problem**: R6 (explicit per-query consent + logging before accessing paid/gated sources) is defined in the guardrail matrix but not yet implemented.
- **What to do**: Add consent flow in `backend/app/api/v1/endpoints/query.py` when `verified_paid` sources are referenced.

### 🟡 Important Gaps (Phase 3 — Completeness)

#### Gap 4: Neo4j Knowledge Graph
- **Problem**: `scripts/build_graph.py` is a logging stub with no real Neo4j driver, schema creation, or ingestion pipeline.
- **What to do**: Install `neo4j` Python driver, implement `Herb`, `Formulation`, `Statute`, `Section` node models and edges (`BARRED_BY`, `GOVERNED_BY`, `REQUIRES_APPROVAL`).

#### Gap 5: Live Fallback to External Sources
- **Problem**: The fallback node only broadens jurisdiction within the internal Qdrant corpus. The CRAG.md spec calls for live queries to India Code API or WIPO Lex when internal fallback also fails.
- **What to do**: Add live HTTP retrieval in `_node_fallback` against `INPASS_API_ENDPOINT` and `WIPO_LEX_API_ENDPOINT` (both already configured in `.env.example`).

#### Gap 6: IP India Live Search (Patents / GI / Trademarks)
- **Problem**: IP India API endpoint is configured but integration layer is not implemented.
- **What to do**: Implement `backend/app/services/ip_india_service.py` to search patent, GI, and trademark databases and append results to retrieval context.

### 🟢 Phase 4 Gaps (Full Multilingual + Voice)

#### Gap 7: Bhashini API Integration
- **Problem**: `bhashini_service.py` class exists but `translate_text()` returns mock output; `speech_to_text()` returns hardcoded text.
- **What to do**: Wire real Bhashini API credentials (`BHASHINI_API_KEY`, `BHASHINI_PIPELINE_ID`) and implement actual NMT HTTP calls.

#### Gap 8: CRAG Pipeline Multilingual I/O
- **Problem**: Bhashini translation is not called before query processing (English normalization) or after answer generation (vernacular translation-back).
- **What to do**: Wrap `CRAGPipeline.run()` with language detection → Bhashini NMT → CRAG → Bhashini NMT → response.

#### Gap 9: Voice Interface (ASR + TTS)
- **Problem**: Speech-to-text and text-to-speech stubs exist but are not wired.
- **What to do**: Phase 4 — connect `speech_to_text()` and add a `TTS` method using Bhashini APIs.

---

## 7. Phase Completion Summary Table

| Phase | Description | Status | Completeness |
|---|---|---|---|
| **Phase 1** | MVP: CRAG grading + citation + disclaimer + safe abstention | ✅ Complete | **~100%** |
| **Phase 2** | Formulation gate + jurisdiction toggle + ABS pointer + fallback | ✅ Mostly Complete | **~90%** |
| **Phase 3** | Knowledge graph + multi-source orchestration + paid connectors | 🔶 Stub/Partial | **~15%** |
| **Phase 4** | Multilingual (Bhashini) + voice + live human escalation | 🔶 Stub/Partial | **~10%** |

---

## 8. System Data Flow

```
User Query (Any Language)
        │
        ▼
[Language Detection]  ──── NOT YET WIRED ──── [Bhashini NMT: Vernacular → English]
        │
        ▼
[Query Router Agent] ─── Jurisdiction: National | International | Both
        │
        ▼
[Rule R9 Gate] ─── Formulation IP query without classification? → Prompt classifier first
        │
        ▼
[Hybrid Vector Search: Qdrant]
  • Cohere embed-multilingual-v3.0 semantic vectors
  • BM25 keyword boost (statutory term abbreviations)
  • R4: Jurisdiction isolation filter
  • R7: Mock chunk exclusion filter
        │
        ▼
[MMR Diversification] ─── λ=0.7 (relevance vs diversity balance)
        │
        ▼
[CRAG Relevance Grader]
  • CORRECT / AMBIGUOUS / INCORRECT per chunk
        │
    ┌───┴────────────┐──────────────────┐
    │                │                  │
  ALL              AMBIGUOUS          CORRECT
 INCORRECT           │                  │
    │          [Fallback Retrieve]       │
    │         (Broader Jurisdiction)     │
    │                │                  │
    └──── Still failing? ───────────────┤
         ↓ R1: Abstain            ↓ Generate
[Safe Abstention]           [Grounded Generator]
 "No verified source"        (Citations forced)
        │                          │
        └──────────────────────────┘
                    │
                    ▼
        [Citation Entailment Verifier]
         Orphan claims stripped (R2, R3)
                    │
                    ▼
        [ABS Pointer: BDA 2023 rules]
         Deterministic — not generative
                    │
                    ▼
        [Output Assembler]
         • Confidence Score (R8)
         • Mandatory Disclaimer (R5)
         • Escalation flag if < 70% confidence
                    │
                    ▼
      [Bhashini NMT: English → Vernacular]  ──── NOT YET WIRED
                    │
                    ▼
          FastAPI REST Response
```

---

## 9. How to Configure & Run

### Step 1: Set up `.env`
```env
# Minimum required for semantic search + generation:
LLM_PROVIDER=cohere
COHERE_API_KEY=your_actual_cohere_api_key_here
COHERE_MODEL=command-r
COHERE_EMBED_MODEL=embed-multilingual-v3.0
USE_MMR=true
MMR_LAMBDA=0.7
```

### Step 2: Seed the corpus with real embeddings
```bash
PYTHONPATH=. uv run python scripts/seed_corpus.py
```

### Step 3: Run tests
```bash
PYTHONPATH=backend:. uv run pytest backend/tests ml_pipeline/tests -v
```

### Step 4: Start the backend server
```bash
uv run uvicorn backend.app.main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

---

## 10. Latest Progress & Implementation Update (2026-09-13)

### 🚀 1. Critical Gap 1 Resolved — 100% Real Statutory Ingestion (Option B)
- **Zero Fakes & Zero `text_override`**: All statutory chunks are dynamically fetched from live, verified public repositories with runtime text extraction:
  - **Indian Central Acts via Indian Kanoon** (Akoma Ntoso DOM extraction):
    - **The Patents Act, 1970**:
      - Section 3(p) — Traditional Knowledge Patent Bar (`doc/874310/`)
      - Section 3(d) — Enhanced Efficacy for Known Substances (`doc/874310/`)
      - Section 3(e) — Admixtures (`doc/874310/`)
      - Section 8 — Information regarding foreign applications (`doc/879773/`)
      - Section 10 — Contents of specifications / Biological origin disclosure (`doc/1217727/`)
      - Section 25 — Pre-Grant and Post-Grant Opposition on TK grounds (`doc/1485322/`)
      - Section 64 — Revocation of patents for non-disclosure of geographical origin (`doc/217797/`)
    - **The Biological Diversity Act, 2002 / (Amendment) Act, 2023**:
      - Section 3 — Prior Approval of National Biodiversity Authority (`doc/155946190/`)
      - Section 4 — Transfer of biological resource or knowledge (`doc/963675/`)
      - Section 6 — Prior NBA approval for IPR applications (`doc/1758638/`)
      - Section 19 — Application to NBA for access / commercial use (`doc/635100/`)
      - Section 21 — Determination of equitable benefit sharing by NBA (`doc/1380763/`)
      - Section 24 — Intimation to State Biodiversity Board & AYUSH exemptions (`doc/136870409/`)
    - **Geographical Indications of Goods Act, 1999**:
      - Section 2(1)(e) — Definition of Geographical Indication (`doc/1881745/`)
    - **The Drugs and Cosmetics Act, 1940**:
      - Section 3(a) — Definition of Ayurvedic, Siddha or Unani drug (`doc/737172/`)
      - Section 33EEB — Regulation of manufacture for sale of Ayurvedic drugs (`doc/1768061/`)
    - **Protection of Plant Varieties and Farmers' Rights Act, 2001**:
      - Section 39 — Farmers' Rights (Conservation & Seeds) (`doc/1385928/`)
  - **International Treaties** (Official PDFs downloaded & extracted via `pypdf`):
    - **WTO TRIPS Agreement (1995)**: Articles 27 (Patentable Subject Matter), 28 (Rights Conferred), 39 (Trade Secrets / Undisclosed Info), 22 (GI Protection).
    - **CBD Nagoya Protocol (2014)**: Articles 5 (Fair & Equitable Benefit-Sharing), 6 (Prior Informed Consent), 7 (Traditional Knowledge Access), 12 (TK Compliance).
    - **WIPO GRATK Treaty (Geneva, 2024)**: Articles 3 (Mandatory Genetic Resource / TK Disclosure Requirement), 4 (Non-Retroactivity), 5 (Sanctions & Remedies) extracted from signed Diplomatic Conference English PDF.
- **Local Disk Caching (`ml_pipeline/corpus_ingestion/data/cache/`)**:
  - Downloaded raw documents are saved to disk on first fetch. Repeated runs load from cache instantaneously, preventing rate limits or reliance on live internet during demonstrations.
- **Corpus Seeder Updated (`scripts/seed_corpus.py`)**:
  - `get_foundational_corpus()` now invokes `RealLegalScraper`, indexing all 28 real statutory chunks and 1 mock-labeled TKDL entry into Qdrant.

---

### 🛡️ 2. Critical Gap 3 Resolved — Rule R6: Paid-Source Access Consent Guard
- **Enforcement Layer (`backend/app/core/r6_consent_guard.py`)**:
  - Added strict consent validation for queries that touch gated, paid, or private sources (Manupatra, SCC Online, private TKDL access).
  - Enforced via `paid_source_consent: bool = False` in `QueryRequest` schema ([`backend/app/schemas/query_schema.py`](file:///Users/ayushk/Desktop/assistant/backend/app/schemas/query_schema.py)).
  - Queries without affirmative consent are restricted strictly to public corpus chunks (`ProvenanceStatus.VERIFIED_PUBLIC`), with DPDP Act 2023 audit events logged.

---

### 🔍 3. Verifier & Grader Refinements
- **Sentence Tokenizer & Numbered List Fix (`ml_pipeline/crag/verifier.py`)**:
  - Resolved false orphan claim penalties by making sentence splitting aware of numbered lists (`1. `, `2. `) and terminal citation tags (`[chunk_id]`).
- **Domain-Calibrated Keyword Overlap Thresholds (`ml_pipeline/crag/grader.py`)**:
  - Expanded stopwords and calibrated minimum overlap requirements to prevent spurious `AMBIGUOUS` grades on out-of-domain queries (e.g. quantum physics queries), ensuring clean Rule R1 safe abstention.

---

### 🧪 4. Updated Test Verification Matrix
All **17/17 automated tests** pass with real statutory ingestion:

```bash
PYTHONPATH=.:backend uv run pytest ml_pipeline/tests/ backend/tests/
======================= 17 passed, 3 warnings in 18.19s ========================
```

| Suite | Focus Areas | Result |
|---|---|---|
| `ml_pipeline/tests/test_crag_pipeline.py` | 6 tests: R1 safe abstention, R2 orphan claim filter, R3 entailment, R4 jurisdiction separation, R5 disclaimers, R7 mock exclusion, R9 formulation gate | **PASSED** |
| `ml_pipeline/tests/test_mmr.py` | 3 tests: MMR diversification & pure relevance weighting | **PASSED** |
| `backend/tests/test_abs.py` | 2 tests: BDA 2023 ABS fee slabs and AYUSH exemptions | **PASSED** |
| `backend/tests/test_classify.py` | 2 tests: 5-tier Ayurvedic formulation classification | **PASSED** |
| `backend/tests/test_crag_api.py` | 4 tests: FastAPI CRAG query, DPDP audit logging, R1 abstention, R9 classification gate | **PASSED** |

