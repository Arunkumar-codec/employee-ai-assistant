#!/usr/bin/env python3
"""
Document ingestion script.

WHAT: The one, explicit workflow that runs the full ingestion pipeline:
      load documents -> chunk -> embed -> upsert into ChromaDB.
WHY A SEPARATE SCRIPT (not run automatically at FastAPI startup): indexing
      is comparatively slow (loads a ~80MB embedding model, computes
      vectors for every chunk) and only needs to happen when the documents
      actually change — not on every server restart. Run this once after
      adding/editing documents, then start the API normally.

USAGE (from the project root):
    python scripts/ingest_documents.py
    python scripts/ingest_documents.py --rebuild   # full clean re-index

Run from the project root or from backend/ — settings.documents_directory
and settings.chroma_persist_directory are absolute paths computed from the
code's own location (see backend/app/core/config.py), so the working
directory does not matter.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.config import settings  # noqa: E402
from app.rag.chunker import chunk_documents  # noqa: E402
from app.rag.embedder import get_embedder  # noqa: E402
from app.rag.loader import DocumentLoadError, load_documents  # noqa: E402
from app.rag.vector_store import get_vector_store  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Index company documents into ChromaDB.")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Delete and recreate the collection before indexing (full clean re-index).",
    )
    args = parser.parse_args()

    print(f"Documents directory:       {settings.documents_directory}")
    print(f"Chroma persist directory:  {settings.chroma_persist_directory}")
    print(f"Chroma collection name:    {settings.chroma_collection_name}")
    print(f"Embedding model:           {settings.embedding_model}")
    print(f"Chunk size / overlap:      {settings.chunk_size} / {settings.chunk_overlap}")
    print()

    try:
        documents = load_documents(settings.documents_directory)
    except DocumentLoadError as exc:
        print(f"ERROR: could not load documents: {exc}", file=sys.stderr)
        return 1

    chunks = chunk_documents(documents, settings.chunk_size, settings.chunk_overlap)
    if not chunks:
        print("ERROR: chunking produced zero chunks — nothing to index.", file=sys.stderr)
        return 1

    print(f"Loaded {len(documents)} document(s), produced {len(chunks)} chunk(s).")
    print("Loading embedding model and generating embeddings (first run may take a while)...")

    start = time.time()
    embedder = get_embedder(settings.embedding_model)
    embeddings = embedder.embed_texts([chunk.content for chunk in chunks])
    elapsed = time.time() - start
    print(f"Generated {len(embeddings)} embeddings of dimension {embedder.dimension} in {elapsed:.1f}s.")

    store = get_vector_store(settings.chroma_persist_directory, settings.chroma_collection_name)
    if args.rebuild:
        print("Rebuilding collection from scratch (--rebuild)...")
        store.rebuild_collection()

    ids = [chunk.chunk_id for chunk in chunks]
    documents_text = [chunk.content for chunk in chunks]
    metadatas = [
        {
            "source": chunk.source,
            "document_type": chunk.document_type,
            "chunk_id": chunk.chunk_id,
            **({"page": chunk.page} if chunk.page is not None else {}),
        }
        for chunk in chunks
    ]

    store.upsert_chunks(ids=ids, embeddings=embeddings, documents=documents_text, metadatas=metadatas)

    print()
    print("Ingestion complete.")
    print(f"  Documents loaded:     {len(documents)}")
    print(f"  Chunks upserted:      {len(chunks)}")
    print(f"  Collection name:      {settings.chroma_collection_name}")
    print(f"  Total chunks in DB:   {store.count()}")
    print(f"  Persistence location: {settings.chroma_persist_directory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
