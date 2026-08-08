"""
llm.py
------
Thin wrapper around the Anthropic API used to generate the final answer
from retrieved course-material chunks. Kept separate from rag_pipeline.py
so the prompt-building logic and the API call are easy to test/swap
independently (e.g. to point at a different provider later).
"""
from __future__ import annotations

from .config import ANTHROPIC_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE, SYSTEM_PROMPT


class LLMError(Exception):
    """Raised for any problem calling the LLM (bad key, network, etc.)."""


def get_client(api_key: str):
    import anthropic
    return anthropic.Anthropic(api_key=api_key)


def build_context_block(retrieved: list[dict]) -> str:
    """Render retrieved chunks into a numbered context block the LLM can
    cite back to (e.g. "[Source 2]")."""
    lines = []
    for i, item in enumerate(retrieved, start=1):
        meta = item["metadata"]
        header = f'[Source {i}] Course: {meta.get("course_name")} ({meta.get("course_code")}) | File: {meta.get("file_name")}'
        lines.append(f"{header}\n{item['text']}")
    return "\n\n---\n\n".join(lines)


def build_user_message(question: str, retrieved: list[dict]) -> str:
    context = build_context_block(retrieved)
    return (
        f"Retrieved course materials:\n\n{context}\n\n"
        f"---\n\nStudent question: {question}"
    )


def generate_answer(question: str, retrieved: list[dict], api_key: str) -> str:
    """Call Claude with the retrieved context and return the answer text."""
    if not retrieved:
        return (
            "I couldn't find anything relevant to that question in the indexed "
            "course materials. Try rephrasing, or check that the right course "
            "is selected in the sidebar."
        )

    client = get_client(api_key)
    user_message = build_user_message(question, retrieved)

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=LLM_MAX_TOKENS,
            temperature=LLM_TEMPERATURE,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
    except Exception as exc:
        raise LLMError(str(exc)) from exc

    text_parts = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    return "\n".join(text_parts).strip() or "The model returned an empty response. Please try again."
