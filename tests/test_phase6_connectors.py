"""
tests/test_phase6_connectors.py — Test suite for Phase 6 Connectors & Version Tracker.
"""

import pytest
from fastapi.testclient import TestClient

from main import app
from corpus.connectors import (
    WIPOLexConnector,
    IPIndiaLiveConnector,
    ManupatraConnector,
    SCCOnlineConnector,
)
from corpus.version_tracker import check_corpus_versions, get_version_manifest, compute_sha256


client = TestClient(app)


def test_wipo_lex_connector():
    wipo = WIPOLexConnector()
    
    # Test TRIPS search
    trips_res = wipo.search_treaties("patentable subject matter Article 27")
    assert len(trips_res) > 0
    assert any("TRIPS" in r["source_name"] for r in trips_res)
    assert trips_res[0]["jurisdiction"] == "INTL"
    assert "https://www.wipo.int" in trips_res[0]["source_url"]

    # Test PCT search
    pct_res = wipo.search_treaties("PCT international phase")
    assert len(pct_res) > 0
    assert any("Patent Cooperation Treaty" in r["source_name"] for r in pct_res)

    # Test Madrid & Lisbon
    madrid_res = wipo.search_treaties("Madrid trade mark")
    assert len(madrid_res) > 0
    assert any("Madrid" in r["source_name"] for r in madrid_res)


def test_ip_india_live_connector():
    ip = IPIndiaLiveConnector()

    # Test InPASS search
    inpass_curcuma = ip.search_inpass("Curcuma turmeric formulation")
    assert len(inpass_curcuma) > 0
    assert "IN201811024321" in inpass_curcuma[0]["text"]
    assert inpass_curcuma[0]["jurisdiction"] == "IN"

    inpass_ashwa = ip.search_inpass("Ashwagandha extraction process")
    assert len(inpass_ashwa) > 0
    assert "IN201941031122" in inpass_ashwa[0]["text"]

    # Test GI Registry search
    gi_res = ip.search_gi_registry("Navara rice Kerala")
    assert len(gi_res) > 0
    assert "Navara" in gi_res[0]["source_name"]
    assert gi_res[0]["ip_type"] == "gi"


def test_manupatra_connector():
    manu = ManupatraConnector()

    # Test landmark Section 3(d) case: Novartis
    novartis_res = manu.search_case_law("Novartis Section 3(d) efficacy evergreening")
    assert len(novartis_res) > 0
    assert any("Novartis" in r["source_name"] for r in novartis_res)
    assert "MANU/SC/0281/2013" in novartis_res[0]["text"]

    # Test TKDL landmark: Turmeric revocation
    turmeric_res = manu.search_case_law("turmeric haldi wound healing prior art")
    assert len(turmeric_res) > 0
    assert any("Turmeric" in r["source_name"] for r in turmeric_res)

    # Test Neem revocation
    neem_res = manu.search_case_law("neem antifungal traditional knowledge")
    assert len(neem_res) > 0
    assert any("Neem" in r["source_name"] for r in neem_res)

    # Test Bishwanath Prasad
    bish_res = manu.search_case_law("Bishwanath Prasad inventive step")
    assert len(bish_res) > 0
    assert any("Bishwanath" in r["source_name"] for r in bish_res)


def test_scc_online_connector():
    scc = SCCOnlineConnector()

    # Test Monsanto plant variety Section 3(j)
    monsanto_res = scc.search_headnotes("Monsanto Section 3(j) plant variety bt cotton")
    assert len(monsanto_res) > 0
    assert any("Monsanto" in r["source_name"] for r in monsanto_res)
    assert "(2019) 3 SCC 381" in monsanto_res[0]["text"]

    # Test Eastern Book Company copyright modicum of creativity
    ebc_res = scc.search_headnotes("Eastern Book Company copyright originality")
    assert len(ebc_res) > 0
    assert any("Eastern Book Company" in r["source_name"] for r in ebc_res)
    assert "(2008) 1 SCC 1" in ebc_res[0]["text"]


def test_version_tracker():
    # Test hash computation
    h1 = compute_sha256("test-content")
    h2 = compute_sha256("test-content")
    assert h1 == h2
    assert len(h1) == 64

    # Test check_corpus_versions
    report = check_corpus_versions()
    assert report["status"] == "ok"
    assert "snapshot_id" in report
    assert report["total_sources"] >= 20

    # Test get_version_manifest
    manifest = get_version_manifest()
    assert "sources" in manifest
    assert len(manifest["sources"]) >= 20
    assert "history" in manifest


def test_fastapi_corpus_versions_endpoints():
    # GET /corpus/versions
    resp = client.get("/corpus/versions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "snapshot_id" in data
    assert data["total_sources"] >= 20

    # POST /corpus/refresh
    resp_refresh = client.post("/corpus/refresh")
    assert resp_refresh.status_code == 200
    data_refresh = resp_refresh.json()
    assert data_refresh["status"] == "ok"
    assert "snapshot_id" in data_refresh


def test_fastapi_connector_search_endpoint():
    # Query all connectors for "turmeric"
    payload = {
        "query": "turmeric curcuma wound healing",
        "connector": "all",
        "jurisdiction": "BOTH"
    }
    resp = client.post("/api/connectors/search", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] > 0
    results = data["results"]
    assert any("InPASS" in r["source_name"] or "Turmeric" in r["source_name"] for r in results)

    # Query specifically WIPO for TRIPS
    wipo_payload = {
        "query": "TRIPS Article 27 patentable",
        "connector": "wipo",
        "jurisdiction": "INTL"
    }
    resp_wipo = client.post("/api/connectors/search", json=wipo_payload)
    assert resp_wipo.status_code == 200
    assert resp_wipo.json()["count"] > 0
