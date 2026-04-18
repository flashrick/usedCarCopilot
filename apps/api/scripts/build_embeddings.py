#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.embedding.builder import build_chunk_embeddings


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate embeddings for document_chunks.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of chunks to embed.")
    args = parser.parse_args()

    result = build_chunk_embeddings(limit=args.limit)
    print("Chunk embedding generation completed")
    for key, value in result.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
