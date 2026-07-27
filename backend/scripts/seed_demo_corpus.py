#!/usr/bin/env python3
"""Uploads the demo corpus (seed_corpus/) to a running QAssist API.

Idempotent: skips any file whose filename already exists in the target
API's document list, so it's safe to re-run against the same deployment.

Usage:
    python scripts/seed_demo_corpus.py https://qassist-api.onrender.com
    python scripts/seed_demo_corpus.py http://localhost:8000
"""
import sys
from pathlib import Path

import httpx

CORPUS_DIR = Path(__file__).resolve().parent.parent / "seed_corpus"
CONTENT_TYPES = {".txt": "text/plain", ".md": "text/markdown", ".pdf": "application/pdf"}


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: seed_demo_corpus.py <api_base_url>", file=sys.stderr)
        raise SystemExit(1)

    base_url = sys.argv[1].rstrip("/")
    existing = {doc["filename"] for doc in httpx.get(f"{base_url}/documents", timeout=30).json()}

    for path in sorted(CORPUS_DIR.glob("*")):
        if path.name in existing:
            print(f"skip (already present): {path.name}")
            continue
        content_type = CONTENT_TYPES.get(path.suffix, "text/plain")
        with path.open("rb") as f:
            response = httpx.post(
                f"{base_url}/documents",
                files={"file": (path.name, f, content_type)},
                timeout=60,
            )
        response.raise_for_status()
        doc = response.json()
        print(f"uploaded: {doc['filename']} -> {doc['status']}")


if __name__ == "__main__":
    main()
