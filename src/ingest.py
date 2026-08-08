"""
ingest.py
---------
End-to-end ingestion pipeline: load course files -> clean & chunk ->
embed -> store in the vector database. Exposes a generator-based
`run_ingestion` so the Streamlit UI can show live progress.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

from .config import COURSES, DATA_DIR
from .document_loader import load_course_materials, RawDocument
from .text_processor import chunk_document, Chunk
from .embeddings import EmbeddingModel
from .vector_store import VectorStore


def run_ingestion(
    vector_store: VectorStore,
    embedder: EmbeddingModel,
    course_registry: dict = COURSES,
    data_dir: Path = DATA_DIR,
    full_rebuild: bool = False,
) -> Iterator[dict]:
    """Run ingestion for every course, yielding progress events so a caller
    (e.g. a Streamlit progress bar) can render live status.

    Each yielded dict has a "stage" key: "start" | "course" | "file" | "done".
    """
    if full_rebuild:
        vector_store.reset()

    already_indexed = vector_store.indexed_files() if not full_rebuild else set()

    total_chunks = 0
    total_files = 0

    yield {"stage": "start", "courses": list(course_registry.keys())}

    for code, meta in course_registry.items():
        folder = data_dir / meta["folder"]
        raw_docs: list[RawDocument] = load_course_materials(code, meta["name"], folder)
        yield {"stage": "course", "course_code": code, "course_name": meta["name"], "file_count": len(raw_docs)}

        for doc in raw_docs:
            key = f"{doc.course_code}::{doc.file_name}"
            if key in already_indexed:
                yield {"stage": "file", "course_code": code, "file_name": doc.file_name, "chunks": 0, "skipped": True}
                continue

            chunks: list[Chunk] = chunk_document(doc)
            if chunks:
                vector_store.add_chunks(chunks, embedder)
            total_chunks += len(chunks)
            total_files += 1
            yield {
                "stage": "file",
                "course_code": code,
                "file_name": doc.file_name,
                "chunks": len(chunks),
                "skipped": False,
            }

    yield {"stage": "done", "total_files": total_files, "total_chunks": total_chunks, "total_indexed": vector_store.count()}


def ingest_sync(full_rebuild: bool = False) -> dict:
    """Convenience non-generator entry point (e.g. for a CLI or a first-run
    script). Returns the final 'done' event."""
    embedder = EmbeddingModel()
    store = VectorStore()
    last_event = {}
    for event in run_ingestion(store, embedder, full_rebuild=full_rebuild):
        last_event = event
    return last_event


if __name__ == "__main__":
    import sys
    rebuild = "--rebuild" in sys.argv
    print("Starting ingestion" + (" (full rebuild)" if rebuild else "") + "...")
    result = ingest_sync(full_rebuild=rebuild)
    print(f"Done. Files processed: {result.get('total_files')}, "
          f"chunks added: {result.get('total_chunks')}, "
          f"total chunks in DB: {result.get('total_indexed')}")
