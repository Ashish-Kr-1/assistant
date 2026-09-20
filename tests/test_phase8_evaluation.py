"""
tests/test_phase8_evaluation.py — Test suite for Phase 8 Evaluation Harness.
"""

import json
import pytest
from pathlib import Path


# ── Dataset loading tests ──────────────────────────────────────────────────────

_DATA_DIR = Path(__file__).resolve().parent.parent / "evaluation" / "datasets"


def test_golden_dataset_loads():
    path = _DATA_DIR / "golden_qa.json"
    assert path.exists(), "golden_qa.json not found"
    with open(path) as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) >= 50, f"Expected 50 golden questions, got {len(data)}"


def test_golden_dataset_schema():
    with open(_DATA_DIR / "golden_qa.json") as f:
        data = json.load(f)

    required_fields = {"id", "category", "question", "expected_ip_type",
                       "expected_jurisdiction", "must_cite_keywords"}
    for item in data:
        for field in required_fields:
            assert field in item, f"Missing '{field}' in item {item.get('id', '?')}"
        assert isinstance(item["must_cite_keywords"], list)
        assert len(item["question"]) > 5, f"Question too short: {item['id']}"


def test_out_of_scope_dataset_loads():
    path = _DATA_DIR / "out_of_scope_qa.json"
    assert path.exists(), "out_of_scope_qa.json not found"
    with open(path) as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) >= 20, f"Expected 20 out-of-scope questions, got {len(data)}"


def test_out_of_scope_dataset_schema():
    with open(_DATA_DIR / "out_of_scope_qa.json") as f:
        data = json.load(f)

    required_fields = {"id", "category", "question", "expected_action"}
    for item in data:
        for field in required_fields:
            assert field in item, f"Missing '{field}' in item {item.get('id', '?')}"
        assert item["expected_action"] in ("refusal", "blocked")


def test_golden_dataset_has_multilingual():
    with open(_DATA_DIR / "golden_qa.json") as f:
        data = json.load(f)
    # Should have at least 2 Hindi/Hinglish questions
    multilingual = [q for q in data if q.get("language") in ("hi", "hinglish")]
    assert len(multilingual) >= 2, "Expected at least 2 multilingual test questions"


def test_golden_dataset_covers_all_ip_types():
    with open(_DATA_DIR / "golden_qa.json") as f:
        data = json.load(f)
    ip_types = {q["expected_ip_type"] for q in data}
    required_types = {"patent", "trademark", "gi", "copyright", "ayush", "abs", "tkdl"}
    missing = required_types - ip_types
    assert not missing, f"Golden dataset missing IP types: {missing}"


def test_golden_dataset_covers_both_jurisdictions():
    with open(_DATA_DIR / "golden_qa.json") as f:
        data = json.load(f)
    jurisdictions = {q["expected_jurisdiction"] for q in data}
    assert "IN" in jurisdictions
    assert "INTL" in jurisdictions


# ── Offline benchmark runner tests ─────────────────────────────────────────────

from evaluation.benchmark import (
    run_benchmark,
    _offline_mock_ask,
    _offline_mock_ask_oos,
    _compute_keyword_recall,
    _compute_citation_precision,
    _is_disclaimer_present,
    _confidence_appropriate,
    _percentile,
)


def test_offline_mock_ask_patent():
    response = _offline_mock_ask("What is Section 3(p) of the Indian Patents Act?")
    assert response["ip_type"] == "patent"
    assert len(response["sources"]) > 0
    assert "disclaimer" in response["answer"].lower() or "information, not legal advice" in response["answer"].lower()


def test_offline_mock_ask_abs():
    response = _offline_mock_ask("What is the Nagoya Protocol on ABS?", jurisdiction="international")
    assert response["ip_type"] in ("abs", "general")
    assert response["jurisdiction"] in ("INTL", "BOTH")


def test_offline_mock_ask_oos_refusal():
    response = _offline_mock_ask_oos("How do I make mango pickle?")
    assert "out of scope" in response["answer"].lower()
    assert response["confidence"]["level"] == "LOW"


def test_keyword_recall_all_present():
    answer = "section 3(p) traditional knowledge exclusion patents act"
    keywords = ["section 3(p)", "traditional knowledge", "patents act"]
    assert _compute_keyword_recall(answer, keywords) == 1.0


def test_keyword_recall_partial():
    answer = "section 3(p) exclusion applies here"
    keywords = ["section 3(p)", "traditional knowledge", "patents act"]
    recall = _compute_keyword_recall(answer, keywords)
    assert recall == pytest.approx(1 / 3)


def test_keyword_recall_empty_keywords():
    assert _compute_keyword_recall("any text", []) == 1.0


def test_citation_precision_all_valid():
    sources = [
        {"url": "https://indiacode.nic.in"},
        {"url": "https://tkdl.res.in"},
    ]
    assert _compute_citation_precision(sources) == 1.0


def test_citation_precision_some_invalid():
    sources = [
        {"url": "https://indiacode.nic.in"},
        {"url": ""},
        {"url": None},
    ]
    prec = _compute_citation_precision(sources)
    assert prec == pytest.approx(1 / 3)


def test_citation_precision_empty():
    assert _compute_citation_precision([]) == 0.0


def test_disclaimer_present():
    answer = "This is general information, not legal advice, and should not be taken as such."
    assert _is_disclaimer_present(answer)


def test_disclaimer_absent():
    answer = "A patent can be filed under Section 3(p)."
    assert not _is_disclaimer_present(answer)


def test_confidence_appropriate():
    assert _confidence_appropriate("HIGH")
    assert _confidence_appropriate("MEDIUM")
    assert not _confidence_appropriate("LOW")
    assert not _confidence_appropriate("UNCERTAIN")
    assert _confidence_appropriate("high")  # case-insensitive


def test_percentile_median():
    data = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert _percentile(data, 50) == 3.0


def test_percentile_p95():
    data = list(range(1, 101))  # 1 to 100
    p95 = _percentile(data, 95)
    assert 94 <= p95 <= 96


def test_percentile_empty():
    assert _percentile([], 50) == 0.0


# ── Full offline benchmark run ─────────────────────────────────────────────────

def test_offline_benchmark_smoke_run():
    """Run the benchmark on 5 golden + 5 OOS questions in offline mode."""
    results = run_benchmark(mode="offline", golden_limit=5, oos_limit=5)
    assert results.total_golden == 5
    assert results.total_out_of_scope == 5
    assert len(results.golden_results) == 5
    assert len(results.abstention_results) == 5
    assert results.errors_count == 0


def test_offline_benchmark_metrics_in_range():
    results = run_benchmark(mode="offline", golden_limit=10, oos_limit=5)

    # In offline mode, all answers have disclaimers and valid citations
    assert results.disclaimer_present_rate == 1.0, (
        f"Expected 100% disclaimer rate in offline mock, got {results.disclaimer_present_rate:.0%}"
    )
    assert results.avg_citation_precision == 1.0, (
        f"Expected 100% citation precision in offline mock (all URLs are http), got {results.avg_citation_precision:.0%}"
    )
    assert results.latency_p50_ms >= 0.0
    assert results.latency_p95_ms >= results.latency_p50_ms


def test_offline_benchmark_full_golden():
    """Run all 50 golden questions in offline mode — should complete with no errors."""
    results = run_benchmark(mode="offline")
    assert results.total_golden == 50
    assert results.total_out_of_scope == 20
    assert results.errors_count == 0
    # All mocked answers have disclaimers
    assert results.disclaimer_present_rate == 1.0
    # All citation URLs are valid http
    assert results.avg_citation_precision == 1.0
    # Abstention rate should be high in offline mode (mock always refuses OOS)
    assert results.abstention_rate >= 0.85


# ── Report generation tests ────────────────────────────────────────────────────

from evaluation.report import (
    generate_markdown_report,
    save_results,
    load_results,
    compare_runs,
    _all_gates_pass,
)


def test_markdown_report_generation():
    results = run_benchmark(mode="offline", golden_limit=5, oos_limit=5)
    md = generate_markdown_report(results)

    assert "# Charaka IP" in md
    assert "IP Type Accuracy" in md
    assert "Abstention Rate" in md
    assert "Quality Gate" in md
    assert "| Category |" in md     # per-category table
    assert "Charaka IP Evaluation Harness" in md


def test_markdown_report_contains_all_sections():
    results = run_benchmark(mode="offline", golden_limit=5, oos_limit=5)
    md = generate_markdown_report(results)
    assert "## Aggregate Metrics" in md
    assert "## Per-Category Accuracy" in md
    assert "## Abstention Results" in md
    assert "## Quality Thresholds Used" in md


def test_save_and_load_results(tmp_path):
    results = run_benchmark(mode="offline", golden_limit=5, oos_limit=5)
    output = str(tmp_path / "test_results.json")
    save_results(results, output)

    loaded = load_results(output)
    assert loaded["mode"] == "offline"
    assert loaded["total_golden"] == 5
    assert loaded["total_out_of_scope"] == 5
    assert "ip_type_accuracy" in loaded
    assert isinstance(loaded["golden_results"], list)


def test_compare_runs():
    baseline = {
        "ip_type_accuracy": 0.75,
        "jurisdiction_accuracy": 0.80,
        "avg_keyword_recall": 0.65,
        "avg_citation_precision": 0.90,
        "abstention_rate": 0.80,
        "disclaimer_present_rate": 0.95,
        "confidence_appropriate_rate": 0.88,
        "latency_p50_ms": 2000.0,
        "latency_p95_ms": 8000.0,
    }
    current = {
        "ip_type_accuracy": 0.85,
        "jurisdiction_accuracy": 0.85,
        "avg_keyword_recall": 0.78,
        "avg_citation_precision": 0.93,
        "abstention_rate": 0.90,
        "disclaimer_present_rate": 1.00,
        "confidence_appropriate_rate": 0.92,
        "latency_p50_ms": 1800.0,
        "latency_p95_ms": 7200.0,
    }
    md = compare_runs(baseline, current)
    assert "# Charaka IP — Phase Comparison Report" in md
    assert "Better" in md   # improvements should show
    assert "IP Type Accuracy" in md
    assert "Latency p95" in md


def test_quality_gate_pass():
    results = run_benchmark(mode="offline", golden_limit=10, oos_limit=5)
    # Offline mock always hits thresholds — should pass all gates
    assert _all_gates_pass(results)
