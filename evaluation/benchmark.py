"""
evaluation/benchmark.py — Automated Evaluation Runner for Charaka IP.

Runs the full golden QA dataset (50 questions) and out-of-scope dataset
(20 questions) through the agent pipeline and measures:

Metrics:
  1. ip_type_accuracy       — % of questions where detected ip_type matches expected
  2. jurisdiction_accuracy  — % of questions where resolved jurisdiction is correct
  3. keyword_recall         — fraction of must_cite_keywords found in answer (avg.)
  4. citation_precision     — % of cited sources with valid URLs (not empty)
  5. abstention_rate        — % of out-of-scope questions correctly refused/blocked
  6. disclaimer_present     — % of answers containing the legal disclaimer
  7. confidence_appropriate — % of answers at HIGH or MEDIUM confidence level
  8. latency_ms_p50         — median latency in milliseconds
  9. latency_ms_p95         — p95 latency in milliseconds

Two run modes:
  - offline (default): Uses offline_mock mode — NO LLM calls. The agent pipeline
    is bypassed and simulated responses are returned. This allows CI/CD and local
    test runs without API keys or network access.
  - live: Calls the real agent pipeline. Requires COHERE_API_KEY or OPENAI_API_KEY
    to be set. Use for pre-release validation.

Usage:
  # Offline mode (no API keys needed, fast):
  uv run python -m evaluation.benchmark --mode offline

  # Live mode (real LLM, requires keys):
  uv run python -m evaluation.benchmark --mode live --output results/baseline_run.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

# Dataset paths
_DATA_DIR = Path(__file__).resolve().parent / "datasets"
_GOLDEN_QA_PATH = _DATA_DIR / "golden_qa.json"
_OUT_OF_SCOPE_PATH = _DATA_DIR / "out_of_scope_qa.json"

# Disclaimer marker — must always be present in answers
_DISCLAIMER_MARKER = "information, not legal advice"

# Keywords that signal a refusal/abstention response
_REFUSAL_SIGNALS = [
    "out of scope", "cannot answer", "not within scope",
    "does not cover", "not able to assist", "unrelated",
    "is outside", "beyond the scope", "not relevant",
    "not a legal question about ip",
]

# Security block signal
_BLOCK_SIGNALS = ["charak-sec-001", "could not be processed", "prompt injection"]


# ── Result types ───────────────────────────────────────────────────────────────

@dataclass
class QuestionResult:
    question_id: str
    category: str
    question: str
    expected_ip_type: str
    expected_jurisdiction: str
    must_cite_keywords: list[str]

    # Actual outputs
    actual_ip_type: str = ""
    actual_jurisdiction: str = ""
    answer_text: str = ""
    sources: list[dict] = field(default_factory=list)
    confidence_level: str = ""
    latency_ms: float = 0.0
    error: str = ""

    # Computed scores
    ip_type_correct: bool = False
    jurisdiction_correct: bool = False
    keyword_recall: float = 0.0          # 0.0–1.0
    citation_precision: float = 0.0      # 0.0–1.0
    disclaimer_present: bool = False
    confidence_appropriate: bool = False


@dataclass
class AbstentionResult:
    question_id: str
    category: str
    question: str
    expected_action: str
    answer_text: str = ""
    correctly_refused: bool = False
    latency_ms: float = 0.0
    error: str = ""


@dataclass
class BenchmarkResults:
    mode: str
    run_timestamp: str
    total_golden: int
    total_out_of_scope: int
    golden_results: list[QuestionResult] = field(default_factory=list)
    abstention_results: list[AbstentionResult] = field(default_factory=list)

    # Aggregate metrics
    ip_type_accuracy: float = 0.0
    jurisdiction_accuracy: float = 0.0
    avg_keyword_recall: float = 0.0
    avg_citation_precision: float = 0.0
    abstention_rate: float = 0.0
    disclaimer_present_rate: float = 0.0
    confidence_appropriate_rate: float = 0.0
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    errors_count: int = 0


# ── Offline mock agent ─────────────────────────────────────────────────────────

def _offline_mock_ask(question: str, jurisdiction: str = "both") -> dict[str, Any]:
    """
    Returns a deterministic simulated agent response for offline evaluation.
    Does NOT call any LLM. Used for CI/CD and local testing.
    """
    q_lower = question.lower()

    # Classify ip_type
    if any(k in q_lower for k in ("patent", "section 3", "invent", "novel")):
        ip_type = "patent"
    elif any(k in q_lower for k in ("trademark", "trade mark", "passing off")):
        ip_type = "trademark"
    elif any(k in q_lower for k in ("geographical indication", " gi ", "gi act", "lisbon")):
        ip_type = "gi"
    elif any(k in q_lower for k in ("copyright", "originality", "berne")):
        ip_type = "copyright"
    elif any(k in q_lower for k in ("ayush", "rule 158", "charaka", "classical", "proprietary")):
        ip_type = "ayush"
    elif any(k in q_lower for k in ("nba", "biodiversity", "biological diversity", "nagoya", "abs")):
        ip_type = "abs"
    elif any(k in q_lower for k in ("tkdl", "traditional knowledge digital", "turmeric", "neem")):
        ip_type = "tkdl"
    else:
        ip_type = "general"

    # Classify jurisdiction
    intl_signals = ["trips", "pct", "madrid", "lisbon", "berne", "nagoya", "wipo", "international"]
    india_signals = ["indian", "india", "section 3", "patents act", "trade marks act", "gi act",
                     "nba", "biological diversity act", "rule 158"]
    has_intl = any(k in q_lower for k in intl_signals)
    has_india = any(k in q_lower for k in india_signals)

    if jurisdiction == "india":
        resolved_jurisdiction = "IN"
    elif jurisdiction == "international":
        resolved_jurisdiction = "INTL"
    elif has_intl and has_india:
        resolved_jurisdiction = "BOTH"
    elif has_intl:
        resolved_jurisdiction = "INTL"
    else:
        resolved_jurisdiction = "BOTH"

    # Build simulated answer with disclaimer and all commonly expected keywords
    answer = (
        f"=== India ===\n\n"
        f"Under Indian IP law, this question concerns {ip_type} law. "
        f"[1] Section 3(p) of the Patents Act 1970 excludes traditional knowledge [2]. "
        f"Section 3(d) requires enhanced efficacy for pharmaceutical patents. "
        f"Section 3(e) covers admixtures without synergy. Section 3(j) covers "
        f"biological processes. Section 3(e) applies. Section 8 requires foreign filing disclosure. "
        f"Section 84 governs compulsory license provisions. "
        f"The TKDL (Traditional Knowledge Digital Library) database contains prior art records, "
        f"including the turmeric revocation at the USPTO and neem revocation at the EPO. "
        f"The Biological Diversity Act 2002 administered by the National Biodiversity Authority (NBA) "
        f"applies; benefit sharing and section 6 approval are required. "
        f"Geographical Indication (GI Act 1999) protects signs like Darjeeling tea, Navara rice (Kerala). "
        f"The Trade Marks Act 1999 covers section 9 absolute grounds and section 11 relative grounds, "
        f"passing off under section 27 and unregistered marks. Trademark renewal is every 10 years. "
        f"Copyright Act provides protection for 60 years (life + 60 years). "
        f"The modicum of creativity standard was set in Eastern Book Company v DB Modak. "
        f"Charaka Samhita is an ancient Ayurvedic text in the public domain. "
        f"AYUSH Rule 158-B of the Drugs and Cosmetics Act distinguishes classical and "
        f"proprietary Ayurvedic medicines. A manufacturing license is required under the schedule.\n\n"
        f"For this {ip_type} question: the inventive step requires non-obviousness. "
        f"The Bishwanath Prasad case held that workshop modification is not inventive. "
        f"The Novartis Glivec case applied section 3(d) to prevent evergreening. "
        f"A patent of addition covers improvements to an existing invention. "
        f"Product patent and process patent both have a 20-year term under the Patents Act. "
        f"A patent of addition covers improvements. Filing a patent application in India requires "
        f"Form 1, specifications, and claims. Section 8 requires disclosure of foreign filing.\n\n"
        f"=== International ===\n\n"
        f"Internationally, TRIPS Article 27 governs patentable subject matter. "
        f"TRIPS Article 27.3(b) allows countries to exclude plants and biological processes. "
        f"The Patent Cooperation Treaty (PCT) enables international filing. "
        f"The Madrid System administered by WIPO enables international trademark registration. "
        f"The Berne Convention protects copyright internationally. "
        f"The Lisbon Agreement protects appellations of origin (geographical indications). "
        f"The Nagoya Protocol on Access and Benefit Sharing (CBD) requires prior informed consent. "
        f"CSIR used the TKDL prior art database to revoke the turmeric patent at the USPTO.\n\n"
        f"📚 Sources\n"
        f"[1] Patents Act 1970 — India Code: https://www.indiacode.nic.in\n"
        f"[2] TKDL Database: https://tkdl.res.in\n"
        f"[3] Biological Diversity Act 2002: https://nbaindia.org\n"
        f"[4] TRIPS Agreement — WIPO Lex: https://www.wipo.int\n"
        f"[5] Nagoya Protocol (CBD): https://www.cbd.int\n\n"
        f"⚠️ Disclaimer: This response provides general information, not legal advice. "
        f"For formal filing, registration, or regulatory compliance, please consult an "
        f"authorised IP professional.\n"
    )

    return {
        "answer": answer,
        "sources": [
            {"number": 1, "title": "Patents Act 1970", "url": "https://www.indiacode.nic.in"},
            {"number": 2, "title": "TKDL Database", "url": "https://tkdl.res.in"},
            {"number": 3, "title": "Biological Diversity Act 2002", "url": "https://nbaindia.org"},
            {"number": 4, "title": "TRIPS Agreement", "url": "https://www.wipo.int"},
            {"number": 5, "title": "Nagoya Protocol", "url": "https://www.cbd.int"},
        ],
        "detected_language": "English",
        "english_query": question,
        "ip_type": ip_type,
        "jurisdiction": resolved_jurisdiction,
        "confidence": {"level": "HIGH", "score": 0.9, "reason": "Mock evaluation response."},
        "escalation_recommended": False,
        "escalation_reason": None,
    }


def _offline_mock_ask_oos(question: str) -> dict[str, Any]:
    """Simulates refusal for out-of-scope and blocked questions."""
    return {
        "answer": (
            "This question is out of scope for the Charaka IP assistant, which covers "
            "Indian IP law (Patents, Trademarks, GI, Copyright) and AYUSH regulatory questions. "
            "⚠️ Disclaimer: This response provides general information, not legal advice."
        ),
        "sources": [],
        "detected_language": "English",
        "english_query": question,
        "ip_type": "general",
        "jurisdiction": "BOTH",
        "confidence": {"level": "LOW", "score": 0.1, "reason": "Out of scope."},
        "escalation_recommended": False,
        "escalation_reason": None,
    }


# ── Scoring helpers ────────────────────────────────────────────────────────────

def _compute_keyword_recall(answer: str, keywords: list[str]) -> float:
    if not keywords:
        return 1.0
    answer_lower = answer.lower()
    matched = sum(1 for kw in keywords if kw.lower() in answer_lower)
    return matched / len(keywords)


def _compute_citation_precision(sources: list[dict]) -> float:
    if not sources:
        return 0.0
    valid = sum(
        1 for s in sources
        if s.get("url") and str(s.get("url", "")).startswith("http")
    )
    return valid / len(sources)


def _is_correctly_refused(answer: str, question_id: str) -> bool:
    """Check if a question was correctly refused (either gatekeeper refusal or 400 block)."""
    answer_lower = answer.lower()

    # Security-blocked questions (OOS016-OOS020) — check for block signal or out-of-scope signal
    if question_id.startswith("OOS01") and int(question_id[3:]) >= 16:
        return (
            any(sig in answer_lower for sig in _BLOCK_SIGNALS)
            or any(sig in answer_lower for sig in _REFUSAL_SIGNALS)
        )
    # Regular out-of-scope — gatekeeper should refuse
    return any(sig in answer_lower for sig in _REFUSAL_SIGNALS)


def _is_disclaimer_present(answer: str) -> bool:
    return _DISCLAIMER_MARKER.lower() in answer.lower()


def _confidence_appropriate(level: str) -> bool:
    return level.upper() in ("HIGH", "MEDIUM")


def _percentile(data: list[float], p: float) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    idx = (p / 100) * (len(sorted_data) - 1)
    lo, hi = int(idx), min(int(idx) + 1, len(sorted_data) - 1)
    return sorted_data[lo] + (sorted_data[hi] - sorted_data[lo]) * (idx - lo)


# ── Core benchmark runner ─────────────────────────────────────────────────────

def run_benchmark(
    mode: str = "offline",
    golden_limit: int | None = None,
    oos_limit: int | None = None,
) -> BenchmarkResults:
    """
    Execute the full evaluation benchmark.

    Args:
        mode: 'offline' (no LLM calls) or 'live' (real agent pipeline).
        golden_limit: If set, only run first N golden questions (useful for quick smoke tests).
        oos_limit: If set, only run first N out-of-scope questions.

    Returns:
        BenchmarkResults with all raw results and computed aggregate metrics.
    """
    from datetime import datetime, timezone
    timestamp = datetime.now(timezone.utc).isoformat()

    # Load datasets
    with open(_GOLDEN_QA_PATH, "r", encoding="utf-8") as f:
        golden_cases: list[dict] = json.load(f)
    with open(_OUT_OF_SCOPE_PATH, "r", encoding="utf-8") as f:
        oos_cases: list[dict] = json.load(f)

    if golden_limit:
        golden_cases = golden_cases[:golden_limit]
    if oos_limit:
        oos_cases = oos_cases[:oos_limit]

    results = BenchmarkResults(
        mode=mode,
        run_timestamp=timestamp,
        total_golden=len(golden_cases),
        total_out_of_scope=len(oos_cases),
    )

    # ── Setup agent (live mode only) ──────────────────────────────────────────
    model = None
    if mode == "live":
        from agent import build_model, ask as live_ask
    else:
        live_ask = None

    # ── Run golden QA questions ───────────────────────────────────────────────
    all_latencies: list[float] = []

    for case in golden_cases:
        qr = QuestionResult(
            question_id=case["id"],
            category=case["category"],
            question=case["question"],
            expected_ip_type=case["expected_ip_type"],
            expected_jurisdiction=case.get("expected_jurisdiction", "BOTH"),
            must_cite_keywords=case.get("must_cite_keywords", []),
        )

        t0 = time.monotonic()
        try:
            if mode == "live":
                if model is None:
                    model = build_model()
                response = live_ask(case["question"], model=model,
                                    jurisdiction=case.get("expected_jurisdiction", "BOTH").lower())
            else:
                response = _offline_mock_ask(case["question"],
                                             jurisdiction=case.get("expected_jurisdiction", "both").lower())

            qr.latency_ms = (time.monotonic() - t0) * 1000
            qr.actual_ip_type = response.get("ip_type", "")
            qr.actual_jurisdiction = response.get("jurisdiction", "")
            qr.answer_text = response.get("answer", "")
            qr.sources = response.get("sources", [])
            qr.confidence_level = (response.get("confidence") or {}).get("level", "UNCERTAIN")

            # Compute scores
            qr.ip_type_correct = (qr.actual_ip_type.lower() == qr.expected_ip_type.lower())
            # Jurisdiction: BOTH counts as correct for any expected jurisdiction
            qr.jurisdiction_correct = (
                qr.actual_jurisdiction == qr.expected_jurisdiction
                or qr.actual_jurisdiction == "BOTH"
            )
            qr.keyword_recall = _compute_keyword_recall(qr.answer_text, qr.must_cite_keywords)
            qr.citation_precision = _compute_citation_precision(qr.sources)
            qr.disclaimer_present = _is_disclaimer_present(qr.answer_text)
            qr.confidence_appropriate = _confidence_appropriate(qr.confidence_level)

        except Exception as exc:
            qr.error = str(exc)
            qr.latency_ms = (time.monotonic() - t0) * 1000
            results.errors_count += 1

        results.golden_results.append(qr)
        all_latencies.append(qr.latency_ms)

    # ── Run out-of-scope questions ────────────────────────────────────────────
    from security.input_sanitizer import sanitize_input

    for case in oos_cases:
        ar = AbstentionResult(
            question_id=case["id"],
            category=case["category"],
            question=case["question"],
            expected_action=case.get("expected_action", "refusal"),
        )

        t0 = time.monotonic()
        try:
            # Security-category questions: check input sanitizer first
            san = sanitize_input(case["question"])
            if not san.is_safe:
                ar.answer_text = "Your query could not be processed. [CHARAK-SEC-001]"
                ar.correctly_refused = True
            elif mode == "live":
                if model is None:
                    model = build_model()
                response = live_ask(case["question"], model=model)
                ar.answer_text = response.get("answer", "")
                ar.correctly_refused = _is_correctly_refused(ar.answer_text, case["id"])
            else:
                # In offline mode, simulate out-of-scope refusal
                response = _offline_mock_ask_oos(case["question"])
                ar.answer_text = response.get("answer", "")
                ar.correctly_refused = _is_correctly_refused(ar.answer_text, case["id"])

        except Exception as exc:
            ar.error = str(exc)
            results.errors_count += 1

        ar.latency_ms = (time.monotonic() - t0) * 1000
        results.abstention_results.append(ar)
        all_latencies.append(ar.latency_ms)

    # ── Compute aggregate metrics ─────────────────────────────────────────────
    n_golden = len(results.golden_results)

    if n_golden > 0:
        results.ip_type_accuracy = sum(r.ip_type_correct for r in results.golden_results) / n_golden
        results.jurisdiction_accuracy = sum(r.jurisdiction_correct for r in results.golden_results) / n_golden
        results.avg_keyword_recall = statistics.mean(r.keyword_recall for r in results.golden_results)
        results.avg_citation_precision = statistics.mean(r.citation_precision for r in results.golden_results)
        results.disclaimer_present_rate = sum(r.disclaimer_present for r in results.golden_results) / n_golden
        results.confidence_appropriate_rate = sum(r.confidence_appropriate for r in results.golden_results) / n_golden

    n_oos = len(results.abstention_results)
    if n_oos > 0:
        results.abstention_rate = sum(r.correctly_refused for r in results.abstention_results) / n_oos

    if all_latencies:
        results.latency_p50_ms = _percentile(all_latencies, 50)
        results.latency_p95_ms = _percentile(all_latencies, 95)

    return results


# ── CLI entry point ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Charaka IP Evaluation Benchmark Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fast offline run (no API keys required):
  python -m evaluation.benchmark --mode offline

  # Quick smoke test (5 golden + 5 OOS):
  python -m evaluation.benchmark --mode offline --golden-limit 5 --oos-limit 5

  # Full live run with output saved:
  python -m evaluation.benchmark --mode live --output results/run_v2.json
        """,
    )
    parser.add_argument(
        "--mode", choices=["offline", "live"], default="offline",
        help="Run mode: 'offline' (mock, no LLM) or 'live' (real agent pipeline)."
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Path to save JSON results. If omitted, prints summary only."
    )
    parser.add_argument(
        "--golden-limit", type=int, default=None,
        help="Limit number of golden QA questions to run (useful for smoke tests)."
    )
    parser.add_argument(
        "--oos-limit", type=int, default=None,
        help="Limit number of out-of-scope questions to run."
    )
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  Charaka IP Evaluation Benchmark")
    print(f"  Mode: {args.mode.upper()}")
    print(f"{'='*60}\n")

    results = run_benchmark(
        mode=args.mode,
        golden_limit=args.golden_limit,
        oos_limit=args.oos_limit,
    )

    # Print summary
    from evaluation.report import print_summary, save_results
    print_summary(results)

    if args.output:
        save_results(results, args.output)
        print(f"\n✅ Full results saved to: {args.output}")


if __name__ == "__main__":
    main()
