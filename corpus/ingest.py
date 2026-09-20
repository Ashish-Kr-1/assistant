"""
corpus/ingest.py — Corpus ingestion orchestrator.

Run this script to fetch, parse, chunk, embed, and store all authoritative legal
sources into the ChromaDB vector store.

Usage:
    uv run python -m corpus.ingest              # ingest all sources
    uv run python -m corpus.ingest --ip patent  # ingest only patent-related sources
    uv run python -m corpus.ingest --dry-run    # list sources that would be ingested
    uv run python -m corpus.ingest --source "Patents Act 1970"  # ingest one source

The ingester:
  1. Reads ALL_SOURCES from corpus/sources.py
  2. For each source: fetches (PDF or HTML), parses into TextChunks, upserts to store
  3. Tracks failures and prints a summary

Re-running is safe: upsert uses stable IDs (sha256 of content fingerprint), so
re-ingesting the same unchanged content is a no-op. Changed sections get new
version_hashes and are re-embedded.
"""

import argparse
import sys
import time

from corpus.parsers.html_parser import fetch_and_parse_html
from corpus.parsers.pdf_parser import fetch_and_parse_pdf
from corpus.sources import ALL_SOURCES, CorpusSource
from corpus.store import corpus_count, upsert_chunks


def ingest_source(source: CorpusSource, verbose: bool = True) -> tuple[int, str | None]:
    """
    Ingest a single CorpusSource. Returns (chunks_written, error_message_or_None).
    """
    try:
        if source.fetch_type == "pdf":
            chunks = fetch_and_parse_pdf(source.url, source_name=source.name)
        elif source.fetch_type == "html":
            chunks = fetch_and_parse_html(source.url, source_name=source.name)
        else:
            return 0, f"Unknown fetch_type: {source.fetch_type!r}"

        if not chunks:
            return 0, "Parsed 0 chunks — page may be empty or blocked"

        written = upsert_chunks(
            chunks=chunks,
            source_name=source.name,
            source_url=source.url,
            jurisdiction=source.jurisdiction,
            ip_types=source.ip_types,
        )

        if verbose:
            print(f"  ✓ {source.name}: {written} chunks upserted")
        return written, None

    except Exception as exc:
        msg = f"{type(exc).__name__}: {exc}"
        if verbose:
            print(f"  ✗ {source.name}: {msg}", file=sys.stderr)
        return 0, msg


def ingest_all(
    ip_type_filter: str | None = None,
    source_name_filter: str | None = None,
    dry_run: bool = False,
    verbose: bool = True,
) -> dict:
    """
    Ingest sources matching the optional filters.
    Returns a summary dict with counts and any errors.
    """
    sources = ALL_SOURCES

    if ip_type_filter:
        sources = [s for s in sources if ip_type_filter in s.ip_types]
    if source_name_filter:
        sources = [s for s in sources if source_name_filter.lower() in s.name.lower()]

    if not sources:
        print("No matching sources found.")
        return {"total": 0, "ingested": 0, "failed": 0, "errors": {}}

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Ingesting {len(sources)} source(s)...\n")

    total_chunks = 0
    failed = 0
    errors: dict[str, str] = {}

    for i, source in enumerate(sources, 1):
        print(f"[{i}/{len(sources)}] {source.name}")
        print(f"   URL: {source.url}")
        print(f"   Type: {source.fetch_type} | Jurisdiction: {source.jurisdiction} | IP: {source.ip_types}")

        if dry_run:
            print(f"   [skipped — dry run]")
            continue

        written, err = ingest_source(source, verbose=verbose)
        if err:
            failed += 1
            errors[source.name] = err
        else:
            total_chunks += written

        # Be polite to public servers
        time.sleep(1.5)

    total_in_store = corpus_count()
    print(f"\n{'─' * 60}")
    print(f"Ingestion complete.")
    print(f"  Sources processed : {len(sources)}")
    print(f"  Chunks written    : {total_chunks}")
    print(f"  Failures          : {failed}")
    print(f"  Total in store    : {total_in_store}")
    if errors:
        print(f"\nErrors:")
        for name, msg in errors.items():
            print(f"  • {name}: {msg}")

    return {
        "total": len(sources),
        "ingested": len(sources) - failed,
        "failed": failed,
        "chunks_written": total_chunks,
        "total_in_store": total_in_store,
        "errors": errors,
    }


# ── CLI entry point ─────────────────────────────────────────────────────────────

def _cli():
    parser = argparse.ArgumentParser(
        description="Charaka IP corpus ingestion — fetch, parse, embed, and store authoritative legal sources."
    )
    parser.add_argument("--ip", metavar="IP_TYPE", help="Filter by IP type (patent, trademark, gi, copyright, ayush, abs, tkdl)")
    parser.add_argument("--source", metavar="NAME", help="Filter by source name (substring match)")
    parser.add_argument("--dry-run", action="store_true", help="List sources without fetching")
    parser.add_argument("--count", action="store_true", help="Print current corpus chunk count and exit")
    args = parser.parse_args()

    if args.count:
        print(f"Corpus currently contains {corpus_count()} chunks.")
        return

    ingest_all(
        ip_type_filter=args.ip,
        source_name_filter=args.source,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    _cli()
