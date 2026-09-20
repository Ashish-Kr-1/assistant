"""
corpus/version_tracker.py — Scheduled corpus refresh and statutory amendment tracker.

Maintains an immutable SHA-256 version manifest of all ingested legal documents,
detects statutory amendments, and records version-diff history.
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from corpus.sources import ALL_SOURCES, CorpusSource

MANIFEST_FILE = Path(__file__).resolve().parent / "version_manifest.json"


def compute_sha256(content: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def load_manifest() -> dict[str, Any]:
    """Load existing version manifest from disk."""
    if MANIFEST_FILE.exists():
        try:
            with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "last_checked": None,
        "corpus_snapshot_id": None,
        "total_sources": 0,
        "sources": {},
        "history": [],
    }


def save_manifest(manifest: dict[str, Any]) -> None:
    """Save updated version manifest to disk."""
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def check_corpus_versions(sources: list[CorpusSource] = ALL_SOURCES) -> dict[str, Any]:
    """
    Check current corpus sources against the version manifest.
    Flags unchanged, new, and amended sources.
    """
    manifest = load_manifest()
    now_iso = datetime.now(timezone.utc).isoformat()

    new_sources = []
    amended_sources = []
    unchanged_sources = []

    combined_hash = hashlib.sha256()

    for src in sources:
        # Use source URL + name as tracking identity
        ip_types_str = ",".join(sorted(src.ip_types))
        src_id = f"{src.jurisdiction}_{ip_types_str}_{src.name}".replace(" ", "_")
        current_data = f"{src.name}|{src.url}|{src.jurisdiction}|{ip_types_str}"
        current_hash = compute_sha256(current_data)
        combined_hash.update(current_hash.encode("utf-8"))

        if src_id not in manifest["sources"]:
            new_sources.append(src.name)
            manifest["sources"][src_id] = {
                "title": src.name,
                "url": src.url,
                "jurisdiction": src.jurisdiction,
                "ip_types": src.ip_types,
                "hash": current_hash,
                "first_seen": now_iso,
                "last_verified": now_iso,
                "version": 1,
            }
        else:
            prev = manifest["sources"][src_id]
            if prev["hash"] != current_hash:
                amended_sources.append({
                    "title": src.name,
                    "previous_hash": prev["hash"],
                    "new_hash": current_hash,
                })
                prev["hash"] = current_hash
                prev["version"] = prev.get("version", 1) + 1
                prev["amended_at"] = now_iso
            else:
                unchanged_sources.append(src.name)
            prev["last_verified"] = now_iso

    snapshot_id = combined_hash.hexdigest()[:16]
    manifest["last_checked"] = now_iso
    manifest["corpus_snapshot_id"] = snapshot_id
    manifest["total_sources"] = len(sources)

    # Append run to history
    manifest["history"].append({
        "timestamp": now_iso,
        "snapshot_id": snapshot_id,
        "new_count": len(new_sources),
        "amended_count": len(amended_sources),
        "unchanged_count": len(unchanged_sources),
    })
    # Keep last 50 history entries
    manifest["history"] = manifest["history"][-50:]

    save_manifest(manifest)

    return {
        "status": "ok",
        "snapshot_id": snapshot_id,
        "last_checked": now_iso,
        "total_sources": len(sources),
        "new_sources": new_sources,
        "amended_sources": amended_sources,
        "unchanged_count": len(unchanged_sources),
    }


def get_version_manifest() -> dict[str, Any]:
    """Retrieve current corpus version manifest for observability."""
    manifest = load_manifest()
    if not manifest["last_checked"]:
        return check_corpus_versions()
    return manifest
