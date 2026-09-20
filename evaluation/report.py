"""
evaluation/report.py — Metrics Reporter for Charaka IP Evaluation Harness.

Generates structured Markdown and JSON reports from BenchmarkResults.
Supports:
  - Console summary table (colorised via ANSI where supported)
  - Full Markdown report with per-question breakdown
  - JSON export for phase-over-phase comparison dashboards
  - Threshold-based pass/fail gates for CI/CD pipelines

Quality thresholds (configurable via env vars):
  EVAL_MIN_IP_TYPE_ACCURACY       default: 0.80
  EVAL_MIN_KEYWORD_RECALL         default: 0.70
  EVAL_MIN_ABSTENTION_RATE        default: 0.85
  EVAL_MIN_DISCLAIMER_RATE        default: 0.95
  EVAL_MAX_LATENCY_P95_MS         default: 15000
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from evaluation.benchmark import BenchmarkResults

# ── Quality gates ──────────────────────────────────────────────────────────────

THRESHOLDS = {
    "ip_type_accuracy":          float(os.getenv("EVAL_MIN_IP_TYPE_ACCURACY", "0.80")),
    "avg_keyword_recall":        float(os.getenv("EVAL_MIN_KEYWORD_RECALL", "0.70")),
    "abstention_rate":           float(os.getenv("EVAL_MIN_ABSTENTION_RATE", "0.85")),
    "disclaimer_present_rate":   float(os.getenv("EVAL_MIN_DISCLAIMER_RATE", "0.95")),
    "latency_p95_ms":            float(os.getenv("EVAL_MAX_LATENCY_P95_MS", "15000")),
}


# ── ANSI color helpers ─────────────────────────────────────────────────────────

_GREEN = "\033[92m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


def _pass_fail(value: float, threshold: float, invert: bool = False) -> tuple[str, str]:
    """Return (symbol, color) based on whether value passes the threshold."""
    passed = (value <= threshold) if invert else (value >= threshold)
    if passed:
        return ("✅ PASS", _GREEN)
    return ("❌ FAIL", _RED)


def _pct(v: float) -> str:
    return f"{v * 100:.1f}%"


# ── Console summary ────────────────────────────────────────────────────────────

def print_summary(results: "BenchmarkResults") -> None:
    """Print a formatted summary table to stdout."""
    r = results
    print(f"\n{_BOLD}{'='*68}{_RESET}")
    print(f"{_BOLD}  CHARAK IP — EVALUATION RESULTS{_RESET}")
    print(f"  Run: {r.run_timestamp}   Mode: {r.mode.upper()}")
    print(f"  Golden QA: {r.total_golden}   Out-of-Scope: {r.total_out_of_scope}   Errors: {r.errors_count}")
    print(f"{_BOLD}{'='*68}{_RESET}\n")

    metrics = [
        ("IP Type Accuracy",         r.ip_type_accuracy,           "ip_type_accuracy",        False),
        ("Jurisdiction Accuracy",     r.jurisdiction_accuracy,       None,                      False),
        ("Avg Keyword Recall",        r.avg_keyword_recall,          "avg_keyword_recall",       False),
        ("Avg Citation Precision",    r.avg_citation_precision,      None,                      False),
        ("Abstention Rate",           r.abstention_rate,             "abstention_rate",          False),
        ("Disclaimer Present Rate",   r.disclaimer_present_rate,     "disclaimer_present_rate",  False),
        ("Confidence Appropriate",    r.confidence_appropriate_rate, None,                      False),
    ]

    for label, value, threshold_key, invert in metrics:
        pct_str = _pct(value)
        if threshold_key and threshold_key in THRESHOLDS:
            sym, color = _pass_fail(value, THRESHOLDS[threshold_key], invert)
            print(f"  {label:<28} {pct_str:<10} {color}{sym}{_RESET}")
        else:
            print(f"  {label:<28} {pct_str}")

    # Latency
    lat_sym, lat_color = _pass_fail(
        r.latency_p95_ms, THRESHOLDS["latency_p95_ms"], invert=True
    )
    print(f"  {'Latency p50':<28} {r.latency_p50_ms:.1f} ms")
    print(f"  {'Latency p95':<28} {r.latency_p95_ms:.1f} ms   {lat_color}{lat_sym}{_RESET}")

    print(f"\n{_BOLD}{'='*68}{_RESET}")

    # Overall gate
    all_pass = _all_gates_pass(results)
    if all_pass:
        print(f"\n  {_GREEN}{_BOLD}🎉 QUALITY GATE: ALL PASS{_RESET}")
    else:
        print(f"\n  {_RED}{_BOLD}⚠️  QUALITY GATE: SOME METRICS BELOW THRESHOLD{_RESET}")
    print()


def _all_gates_pass(results: "BenchmarkResults") -> bool:
    r = results
    return (
        r.ip_type_accuracy >= THRESHOLDS["ip_type_accuracy"]
        and r.avg_keyword_recall >= THRESHOLDS["avg_keyword_recall"]
        and r.abstention_rate >= THRESHOLDS["abstention_rate"]
        and r.disclaimer_present_rate >= THRESHOLDS["disclaimer_present_rate"]
        and r.latency_p95_ms <= THRESHOLDS["latency_p95_ms"]
    )


# ── Markdown report ────────────────────────────────────────────────────────────

def generate_markdown_report(results: "BenchmarkResults") -> str:
    """Generate a full Markdown evaluation report."""
    r = results
    lines: list[str] = []

    lines.append("# Charaka IP — Evaluation Report\n")
    lines.append(f"**Run Timestamp**: {r.run_timestamp}  ")
    lines.append(f"**Mode**: {r.mode.upper()}  ")
    lines.append(f"**Golden QA Count**: {r.total_golden}  ")
    lines.append(f"**Out-of-Scope Count**: {r.total_out_of_scope}  ")
    lines.append(f"**Errors**: {r.errors_count}\n")

    # Quality gate summary
    all_pass = _all_gates_pass(results)
    gate_icon = "✅" if all_pass else "❌"
    lines.append(f"## Quality Gate: {gate_icon} {'PASS' if all_pass else 'FAIL'}\n")

    # Aggregate metrics table
    lines.append("## Aggregate Metrics\n")
    lines.append("| Metric | Value | Threshold | Status |")
    lines.append("|--------|-------|-----------|--------|")

    metrics_rows = [
        ("IP Type Accuracy",         _pct(r.ip_type_accuracy),           _pct(THRESHOLDS["ip_type_accuracy"]),       "ip_type_accuracy",        False),
        ("Jurisdiction Accuracy",     _pct(r.jurisdiction_accuracy),       "—",                                        None,                      False),
        ("Avg Keyword Recall",        _pct(r.avg_keyword_recall),          _pct(THRESHOLDS["avg_keyword_recall"]),     "avg_keyword_recall",       False),
        ("Avg Citation Precision",    _pct(r.avg_citation_precision),      "—",                                        None,                      False),
        ("Abstention Rate",           _pct(r.abstention_rate),             _pct(THRESHOLDS["abstention_rate"]),        "abstention_rate",          False),
        ("Disclaimer Present Rate",   _pct(r.disclaimer_present_rate),     _pct(THRESHOLDS["disclaimer_present_rate"]),"disclaimer_present_rate",  False),
        ("Confidence Appropriate",    _pct(r.confidence_appropriate_rate), "—",                                        None,                      False),
        ("Latency p50 (ms)",          f"{r.latency_p50_ms:.1f}",          "—",                                        None,                      False),
        ("Latency p95 (ms)",          f"{r.latency_p95_ms:.1f}",          f"{THRESHOLDS['latency_p95_ms']:.0f}",      "latency_p95_ms",          True),
    ]

    for label, value, threshold_str, key, invert in metrics_rows:
        if key and key in THRESHOLDS:
            # Determine pass/fail
            raw_val = getattr(r, key)
            passed = (raw_val <= THRESHOLDS[key]) if invert else (raw_val >= THRESHOLDS[key])
            status = "✅ Pass" if passed else "❌ Fail"
        else:
            status = "—"
        lines.append(f"| {label} | {value} | {threshold_str} | {status} |")

    lines.append("")

    # Per-category breakdown
    lines.append("## Per-Category Accuracy (Golden QA)\n")
    categories: dict[str, list] = {}
    for qr in r.golden_results:
        categories.setdefault(qr.category, []).append(qr)

    lines.append("| Category | Count | IP Type Acc | KW Recall | Disclaimer | Confidence OK |")
    lines.append("|----------|-------|-------------|-----------|------------|---------------|")
    for cat, qrs in sorted(categories.items()):
        n = len(qrs)
        ip_acc = _pct(sum(q.ip_type_correct for q in qrs) / n)
        kw_rec = _pct(sum(q.keyword_recall for q in qrs) / n)
        disc = _pct(sum(q.disclaimer_present for q in qrs) / n)
        conf = _pct(sum(q.confidence_appropriate for q in qrs) / n)
        lines.append(f"| {cat} | {n} | {ip_acc} | {kw_rec} | {disc} | {conf} |")

    lines.append("")

    # Abstention breakdown
    lines.append("## Abstention Results (Out-of-Scope)\n")
    lines.append("| ID | Category | Correctly Refused |")
    lines.append("|----|----------|-------------------|")
    for ar in r.abstention_results:
        icon = "✅" if ar.correctly_refused else "❌"
        lines.append(f"| {ar.question_id} | {ar.category} | {icon} |")

    lines.append("")

    # Failed golden questions
    failed = [qr for qr in r.golden_results if qr.error or not qr.ip_type_correct or qr.keyword_recall < 0.5]
    if failed:
        lines.append("## Questions Needing Attention\n")
        for qr in failed:
            lines.append(f"### {qr.question_id} — {qr.category}")
            lines.append(f"**Q**: {qr.question}")
            if qr.error:
                lines.append(f"**Error**: `{qr.error}`")
            else:
                lines.append(f"- Expected IP Type: `{qr.expected_ip_type}` | Got: `{qr.actual_ip_type}` {'✅' if qr.ip_type_correct else '❌'}")
                lines.append(f"- Keyword Recall: `{_pct(qr.keyword_recall)}`")
                lines.append(f"- Disclaimer: {'✅' if qr.disclaimer_present else '❌'}")
            lines.append("")

    # Thresholds used
    lines.append("## Quality Thresholds Used\n")
    lines.append("| Metric | Threshold |")
    lines.append("|--------|-----------|")
    for k, v in THRESHOLDS.items():
        lines.append(f"| {k} | {v} |")

    lines.append("\n---\n_Generated by Charaka IP Evaluation Harness (Phase 8)_\n")

    return "\n".join(lines)


# ── JSON export ────────────────────────────────────────────────────────────────

def save_results(results: "BenchmarkResults", output_path: str) -> None:
    """
    Saves full benchmark results as JSON for phase-over-phase comparison.
    Creates parent directories if needed.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Convert dataclasses to dicts
    raw = asdict(results)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2, ensure_ascii=False)


def load_results(path: str) -> dict:
    """Load previously saved benchmark results for comparison."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_runs(baseline: dict, current: dict) -> str:
    """
    Generate a Markdown comparison table between two benchmark runs.
    Useful for tracking phase-over-phase improvements.
    """
    metrics = [
        ("ip_type_accuracy", "IP Type Accuracy", True, False),
        ("jurisdiction_accuracy", "Jurisdiction Accuracy", True, False),
        ("avg_keyword_recall", "Avg Keyword Recall", True, False),
        ("avg_citation_precision", "Avg Citation Precision", True, False),
        ("abstention_rate", "Abstention Rate", True, False),
        ("disclaimer_present_rate", "Disclaimer Present Rate", True, False),
        ("confidence_appropriate_rate", "Confidence Appropriate", True, False),
        ("latency_p50_ms", "Latency p50 (ms)", False, True),
        ("latency_p95_ms", "Latency p95 (ms)", False, True),
    ]

    lines = ["# Charaka IP — Phase Comparison Report\n"]
    lines.append(f"| Metric | Baseline | Current | Δ | Trend |")
    lines.append(f"|--------|----------|---------|---|-------|")

    for key, label, is_pct, lower_is_better in metrics:
        base_val = baseline.get(key, 0.0)
        curr_val = current.get(key, 0.0)
        delta = curr_val - base_val

        if is_pct:
            base_str = _pct(base_val)
            curr_str = _pct(curr_val)
            delta_str = f"{'+' if delta >= 0 else ''}{delta * 100:.1f}%"
        else:
            base_str = f"{base_val:.1f}"
            curr_str = f"{curr_val:.1f}"
            delta_str = f"{'+' if delta >= 0 else ''}{delta:.1f}"

        # Trend: improvement = green
        improved = (delta < 0) if lower_is_better else (delta > 0)
        trend = "🔺 Better" if improved else ("🔻 Worse" if delta != 0 else "➡️ Same")

        lines.append(f"| {label} | {base_str} | {curr_str} | {delta_str} | {trend} |")

    return "\n".join(lines)


def save_markdown_report(results: "BenchmarkResults", output_path: str) -> None:
    """Generate and save a Markdown evaluation report."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    md = generate_markdown_report(results)
    with open(path, "w", encoding="utf-8") as f:
        f.write(md)
