"""
rag_pipeline.py
----------------
The retriever + generation orchestration layer. This is what the UI calls:
given a question, a course filter, and top_k, it retrieves relevant chunks
from the vector store and asks the LLM to answer using only that context,
returning both the answer and the source list for attribution.
"""
from __future__ import annotations

from dataclasses import dataclass

from .vector_store import VectorStore
from .embeddings import EmbeddingModel
from .llm import generate_answer, LLMError
from .config import DEFAULT_TOP_K


@dataclass
class RAGResult:
    answer: str
    sources: list[dict]
    question: str
    error: str | None = None


def retrieve(
    question: str,
    vector_store: VectorStore,
    embedder: EmbeddingModel,
    course_codes: list[str] | None = None,
    top_k: int = DEFAULT_TOP_K,
) -> list[dict]:
    """Retriever step: return the top_k most relevant chunks for a question."""
    return vector_store.query(question, embedder, top_k=top_k, course_codes=course_codes)


def answer_question(
    question: str,
    vector_store: VectorStore,
    embedder: EmbeddingModel,
    api_key: str,
    course_codes: list[str] | None = None,
    top_k: int = DEFAULT_TOP_K,
) -> RAGResult:
    """Full RAG turn: retrieve -> generate -> package with sources."""
    question = question.strip()
    if not question:
        return RAGResult(answer="Please enter a question.", sources=[], question=question)

    retrieved = retrieve(question, vector_store, embedder, course_codes=course_codes, top_k=top_k)

    if not api_key:
        return RAGResult(
            answer=(
                "No Anthropic API key is set, so I can't generate an answer yet. "
                "Add your API key in the sidebar to enable answer generation. "
                "In the meantime, here are the most relevant passages I found:"
            ),
            sources=retrieved,
            question=question,
        )

    try:
        answer = generate_answer(question, retrieved, api_key)
        return RAGResult(answer=answer, sources=retrieved, question=question)
    except LLMError as exc:
        return RAGResult(
            answer="I ran into a problem contacting the language model.",
            sources=retrieved,
            question=question,
            error=str(exc),
        )
