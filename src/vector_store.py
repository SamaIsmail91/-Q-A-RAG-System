"""
vector_store.py
----------------
Persistent vector database layer built on ChromaDB. Stores one collection
containing chunks from every course, tagged with course_code metadata so
retrieval can be filtered to one course, several, or all of them.
"""
from __future__ import annotations

from pathlib import Path

import chromadb
from chromadb.config import Settings

from .config import VECTOR_DB_DIR, COLLECTION_NAME
from .text_processor import Chunk
from .embeddings import EmbeddingModel


class VectorStore:
    def __init__(self, persist_dir: Path = VECTOR_DB_DIR, collection_name: str = COLLECTION_NAME):
        persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------
    def reset(self) -> None:
        """Drop and recreate the collection (used before a full re-ingest)."""
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: list[Chunk], embedder: EmbeddingModel, batch_size: int = 64) -> int:
        """Embed and upsert chunks in batches. Returns the number added."""
        added = 0
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start:start + batch_size]
            texts = [c.text for c in batch]
            vectors = embedder.encode(texts)
            self.collection.upsert(
                ids=[c.chunk_id for c in batch],
                embeddings=vectors,
                documents=texts,
                metadatas=[c.metadata for c in batch],
            )
            added += len(batch)
        return added

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------
    def count(self) -> int:
        return self.collection.count()

    def stats_by_course(self) -> dict[str, int]:
        """Return {course_code: chunk_count} for everything currently indexed."""
        if self.count() == 0:
            return {}
        result = self.collection.get(include=["metadatas"])
        counts: dict[str, int] = {}
        for meta in result.get("metadatas", []):
            code = meta.get("course_code", "unknown")
            counts[code] = counts.get(code, 0) + 1
        return counts

    def indexed_files(self) -> set[str]:
        """Return the set of 'course_code::file_name' already indexed, used
        to support incremental (skip-unchanged-file) ingestion."""
        if self.count() == 0:
            return set()
        result = self.collection.get(include=["metadatas"])
        return {
            f'{m.get("course_code")}::{m.get("file_name")}'
            for m in result.get("metadatas", [])
        }

    def query(
        self,
        query_text: str,
        embedder: EmbeddingModel,
        top_k: int = 5,
        course_codes: list[str] | None = None,
    ) -> list[dict]:
        """Return the top_k most relevant chunks, optionally filtered to a
        subset of course codes. Each result includes text, metadata, and a
        0-1 similarity score (higher is more relevant)."""
        if self.count() == 0:
            return []

        where = None
        if course_codes:
            if len(course_codes) == 1:
                where = {"course_code": course_codes[0]}
            else:
                where = {"course_code": {"$in": course_codes}}

        query_vector = embedder.encode_query(query_text)
        raw = self.collection.query(
            query_embeddings=[query_vector],
            n_results=min(top_k, max(self.count(), 1)),
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        results = []
        docs = raw.get("documents", [[]])[0]
        metas = raw.get("metadatas", [[]])[0]
        dists = raw.get("distances", [[]])[0]
        for text, meta, dist in zip(docs, metas, dists):
            # Cosine distance -> similarity score in [0, 1] (approx).
            similarity = max(0.0, 1 - dist / 2)
            results.append({"text": text, "metadata": meta, "score": similarity})
        return results
