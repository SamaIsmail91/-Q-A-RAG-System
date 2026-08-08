"""
text_processor.py
------------------
Cleans raw extracted text and splits it into overlapping chunks suitable
for embedding. Uses a recursive, separator-aware splitter (paragraph ->
sentence -> word) so chunks break at natural boundaries instead of
mid-sentence whenever possible, with a sliding overlap to preserve context
across chunk boundaries.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .config import CHUNK_SIZE, CHUNK_OVERLAP, MIN_CHUNK_SIZE
from .document_loader import RawDocument


@dataclass
class Chunk:
    """A single chunk of text ready to be embedded, with full provenance."""
    chunk_id: str
    text: str
    course_code: str
    course_name: str
    file_name: str
    file_type: str
    chunk_index: int
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """Normalize whitespace and strip artifacts left by extraction."""
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)              # collapse runs of spaces/tabs
    text = re.sub(r"\n{3,}", "\n\n", text)             # collapse excess blank lines
    text = re.sub(r"[ \t]+\n", "\n", text)             # trailing spaces before newline
    return text.strip()


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

_SEPARATORS = ["\n\n", "\n", ". ", " "]  # tried in order: paragraph, line, sentence, word


def _split_on_separator(text: str, sep: str) -> list[str]:
    if sep == "":
        return list(text)
    parts = text.split(sep)
    # Re-attach the separator (except to the last piece) so no text is lost
    # and re-joining reconstructs the original string.
    return [p + sep for p in parts[:-1]] + [parts[-1]]


def _recursive_split(text: str, chunk_size: int, separators: list[str]) -> list[str]:
    """Split text into pieces no larger than chunk_size, preferring to break
    on the earliest separator in the list that keeps pieces under the limit."""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    if not separators:
        # Fallback: hard-split by character count.
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    sep, rest_seps = separators[0], separators[1:]
    pieces = _split_on_separator(text, sep)

    chunks: list[str] = []
    buffer = ""
    for piece in pieces:
        if len(piece) > chunk_size:
            # Piece itself is too big; flush buffer then recurse on the piece
            # with the next, finer-grained separator.
            if buffer.strip():
                chunks.append(buffer)
                buffer = ""
            chunks.extend(_recursive_split(piece, chunk_size, rest_seps))
            continue

        if len(buffer) + len(piece) <= chunk_size:
            buffer += piece
        else:
            if buffer.strip():
                chunks.append(buffer)
            buffer = piece

    if buffer.strip():
        chunks.append(buffer)

    return chunks


def _add_overlap(chunks: list[str], overlap: int) -> list[str]:
    """Prepend a tail slice of the previous chunk to each chunk so context
    is preserved across chunk boundaries."""
    if overlap <= 0 or len(chunks) <= 1:
        return chunks
    overlapped = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_tail = chunks[i - 1][-overlap:]
        overlapped.append(prev_tail + chunks[i])
    return overlapped


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Clean and split text into overlapping chunks."""
    cleaned = clean_text(text)
    if not cleaned:
        return []
    raw_chunks = _recursive_split(cleaned, chunk_size, _SEPARATORS)
    raw_chunks = [c.strip() for c in raw_chunks if len(c.strip()) >= MIN_CHUNK_SIZE]
    return _add_overlap(raw_chunks, overlap)


# ---------------------------------------------------------------------------
# Document -> Chunk objects
# ---------------------------------------------------------------------------

def chunk_document(doc: RawDocument) -> list[Chunk]:
    """Turn one RawDocument into a list of provenance-tagged Chunk objects."""
    pieces = chunk_text(doc.text)
    chunks = []
    for idx, piece in enumerate(pieces):
        chunk_id = f"{doc.course_code}__{doc.file_name}__{idx}".replace(" ", "_")
        chunks.append(Chunk(
            chunk_id=chunk_id,
            text=piece,
            course_code=doc.course_code,
            course_name=doc.course_name,
            file_name=doc.file_name,
            file_type=doc.file_type,
            chunk_index=idx,
            metadata={
                "course_code": doc.course_code,
                "course_name": doc.course_name,
                "file_name": doc.file_name,
                "file_type": doc.file_type,
                "chunk_index": idx,
                "file_path": doc.file_path,
            },
        ))
    return chunks


def chunk_all_documents(docs: list[RawDocument]) -> list[Chunk]:
    all_chunks: list[Chunk] = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))
    return all_chunks
