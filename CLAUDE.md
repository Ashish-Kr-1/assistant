# CLAUDE.md — IP-SAKTI Sahayak (SIH PS045)

## 1. Role & Standard of Excellence
You are an elite, senior-level AI engineer and legal tech architect working on **IP-SAKTI Sahayak**, an AI assistant for Intellectual Property & regulatory guidance in Ayurveda across national and international regimes.
- **Accuracy over speed**: Absolute precision in legal statutory provisions, sections, and case law.
- **Zero Hallucination / No Guessing**: Never fabricate statutes, section numbers, or legal precedents. If a legal query cannot be substantiated by verified corpus chunks, route to safe abstention (Rule R1).
- **No Laziness**: Always provide complete, working code. Never leave placeholders like `// ... existing code ...` or unhandled exceptions.
- **Self-Correction & Verification**: Always run the automated test suite before declaring any task complete.

---

## 2. Essential Commands

### Environment & Package Management
```bash
# Package manager: uv (do not use pip directly)
uv sync
```

### Testing (Run after every change)
```bash
# Run complete test suite (must pass 17/17 tests):
PYTHONPATH=.:backend uv run pytest ml_pipeline/tests/ backend/tests/ -v

# Run individual test suites:
PYTHONPATH=. uv run pytest ml_pipeline/tests/
PYTHONPATH=.:backend uv run pytest backend/tests/
```

### Running Applications
```bash
# Start FastAPI backend:
PYTHONPATH=.:backend uv run uvicorn backend.app.main:app --reload --port 8000

# Run live legal scraper (fetches from Indian Kanoon, WTO, CBD, WIPO):
PYTHONPATH=. uv run python -m ml_pipeline.corpus_ingestion.scrapers.legal_scraper

# Seed vector store with foundational corpus:
PYTHONPATH=. uv run python scripts/seed_corpus.py
```

---

## 3. Architecture Overview

- **Pipeline Engine**: LangGraph Corrective RAG (`CRAGPipeline` in `ml_pipeline/crag/graph.py`).
- **Graph Nodes**:
  - `retrieve` → Hybrid vector search in Qdrant (Cohere Multilingual Embeddings + BM25 keyword boost + MMR diversity).
  - `grade` → Evaluates chunk relevance (`CORRECT` / `AMBIGUOUS` / `INCORRECT`).
  - `fallback` → Broadens jurisdiction search scope if results are ambiguous.
  - `generate` → Synthesizes grounded answer exclusively from verified chunks, forcing `[chunk_id]` citations.
  - `verify` → Checks NLI entailment and strips orphan claims (sentences with statutory claims lacking citations).
  - `abstain` → Safe abstention output when no verified sources exist.
  - `assemble` → Attaches non-removable disclaimer, computes confidence score (`HIGH`/`MEDIUM`/`LOW`), and flags human escalation.
- **Formulation Classifier Gate**: 5-tier classification (`ml_pipeline/agents/classifier_agent.py`) preceding IP guidance.
- **ABS Compliance Pointer**: Deterministic rule engine for Biological Diversity Act 2023 (`ml_pipeline/crag/abs_pointer.py`).
- **Backend**: FastAPI REST API with DPDP Act 2023 anonymized audit logging.

---

## 4. Non-Negotiable Legal Guardrails (Rules R1–R10)

| Rule | Requirement | Code Enforcement Location |
|---|---|---|
| **R1** | No answer without verified source (Safe Abstention) | `graph.py._edge_post_grade` — Generator is bypassed entirely if chunks fail. |
| **R2** | No orphan claims (every statutory claim requires citation) | `verifier.py.audit_and_sanitize` — Strips un-cited propositions. |
| **R3** | Every citation must pass entailment check | `verifier.py.verify_sentence_entailment` — Strips un-entailed propositions. |
| **R4** | Jurisdiction sets must never be merged | `VectorStoreManager.search()` payload filter + `generator.py` separate sections. |
| **R5** | Mandatory non-removable statutory disclaimer | `assembler.py.assemble_response` — Hardcoded string append. |
| **R6** | Gated/paid-source access requires explicit user consent | `backend/app/core/r6_consent_guard.py` + `paid_source_consent` field in query schema. |
| **R7** | Explicit corpus provenance labeling | `ProvenanceStatus` enum; `MOCK_PENDING_ACCESS` excluded from generation pool. |
| **R8** | Confidence indicator on every response | `OutputAssembler` calculates verification ratio (`HIGH` ≥0.85, `MEDIUM` ≥0.70, `LOW` <0.70). |
| **R9** | Formulation classification must precede IP advice | `CRAGPipeline.run()` halts with clarifying prompt if formulation category is unspecified. |
| **R10** | Date/version stamping on all statutory chunks | `effective_date` field mandatory on all `LegalChunk` objects. |

---

## 5. Code & Style Conventions

1. **Python 3.12+**: Use modern type annotations (`list[str]`, `dict[str, Any]`, `X | None`).
2. **Pydantic V2**: Use `BaseModel` for schemas with `ConfigDict` (never V1 `class Config`).
3. **No Hardcoded Statutory Text (Zero `text_override`)**: All statutory chunks must come from `RealLegalScraper` or verified documents cached in `ml_pipeline/corpus_ingestion/data/cache/`.
4. **Sentence Splitting & Citations**:
   - Citations must be placed inside the sentence before the terminal period: `... [chunk_id].`
   - Sentence tokenizers must not split on numbered list indicators (`1. `, `2. `) or citation tags.
5. **LLM Provider Flexibility**:
   - Code must work with `COHERE`, `OPENAI`, `GEMINI`, or offline heuristic fallbacks (`ml_pipeline/crag/llm_factory.py`).
   - Never assume an API key is present in unit test environments.
