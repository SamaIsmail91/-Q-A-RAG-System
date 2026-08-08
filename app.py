"""
app.py
------
Course Compass - a Retrieval-Augmented Generation Q&A system for course
materials. Students pick which course(s) to search, ask a question in
plain language, and get an answer generated strictly from the retrieved
course materials, with every claim traceable back to its source file.

Run locally:
    streamlit run app.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import COURSES, DATA_DIR, APP_TITLE, APP_TAGLINE, DEFAULT_TOP_K, MAX_TOP_K
from src.document_loader import load_course_materials
from src.embeddings import EmbeddingModel
from src.vector_store import VectorStore
from src.ingest import run_ingestion
from src.rag_pipeline import answer_question
from src.ui_theme import CSS, hero_html, source_card_html, course_card_html, step_card_html

st.set_page_config(page_title=APP_TITLE, page_icon="📚", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Cached resources
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_vector_store() -> VectorStore:
    return VectorStore()


@st.cache_resource(show_spinner=False)
def get_embedder() -> EmbeddingModel:
    return EmbeddingModel()


def resolve_api_key() -> str:
    """Priority: sidebar override in session_state > st.secrets > env var."""
    if st.session_state.get("api_key_override"):
        return st.session_state["api_key_override"]
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY", "")


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # list[{question, result}]
if "api_key_override" not in st.session_state:
    st.session_state.api_key_override = ""
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📚 Course Compass")
    st.caption("Standard RAG Q&A over your course materials")
    st.markdown("---")

    st.markdown("**🔑 Anthropic API key**")
    st.text_input(
        "Anthropic API key",
        type="password",
        placeholder="sk-ant-...",
        key="api_key_override",
        label_visibility="collapsed",
        help="Used only for this session to call Claude. Never stored or logged. "
             "You can also set it as an ANTHROPIC_API_KEY environment variable "
             "or Streamlit secret instead of pasting it here.",
    )
    api_key = resolve_api_key()
    if api_key:
        st.markdown('<span class="cc-badge">✓ Key detected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="cc-badge">No key set</span>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**🎯 Search scope**")
    course_options = {f"{m['icon']} {code} — {m['name']}": code for code, m in COURSES.items()}
    selected_labels = st.multiselect(
        "Courses to search",
        options=list(course_options.keys()),
        default=list(course_options.keys()),
        label_visibility="collapsed",
    )
    selected_courses = [course_options[label] for label in selected_labels] or None

    top_k = st.slider("Number of sources to retrieve", min_value=2, max_value=MAX_TOP_K, value=DEFAULT_TOP_K)

    st.markdown("---")
    st.markdown("**🗂️ Knowledge base**")

    vector_store = get_vector_store()
    total_indexed = vector_store.count()
    stats = vector_store.stats_by_course()

    if total_indexed == 0:
        st.warning("Knowledge base is empty. Build it to start asking questions.", icon="⚠️")
    else:
        st.markdown(f'<span class="cc-badge">{total_indexed} chunks indexed</span>', unsafe_allow_html=True)
        for code, meta in COURSES.items():
            st.caption(f"{meta['icon']} {code}: {stats.get(code, 0)} chunks")

    build_col, rebuild_col = st.columns(2)
    build_clicked = build_col.button("⚡ Build", use_container_width=True,
                                      help="Index any new/changed files without touching what's already indexed.")
    rebuild_clicked = rebuild_col.button("🔄 Rebuild", use_container_width=True,
                                          help="Wipe and re-index everything from scratch.")

    if build_clicked or rebuild_clicked:
        with st.spinner("Loading embedding model (first run downloads ~90MB, needs internet)..."):
            embedder = get_embedder()
        progress = st.progress(0.0, text="Starting ingestion...")
        log_box = st.empty()
        logs = []
        events = list(run_ingestion(vector_store, embedder, full_rebuild=rebuild_clicked))
        n_events = max(len(events), 1)
        for i, event in enumerate(events):
            if event["stage"] == "file":
                status = "skipped (already indexed)" if event.get("skipped") else f"{event['chunks']} chunks"
                logs.append(f"[{event['course_code']}] {event['file_name']} → {status}")
                log_box.code("\n".join(logs[-8:]))
            progress.progress((i + 1) / n_events, text=f"Processing... ({i+1}/{n_events})")
        progress.empty()
        st.cache_resource.clear()
        st.success("Knowledge base updated.", icon="✅")
        st.rerun()

    st.markdown("---")
    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    st.markdown("---")
    st.caption("Built with Streamlit · ChromaDB · Sentence-Transformers · Claude")


# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.markdown(hero_html(APP_TITLE, APP_TAGLINE), unsafe_allow_html=True)

tab_ask, tab_catalog, tab_how = st.tabs(["💬  Ask a Question", "📖  Course Catalog", "🧭  How It Works"])

# ---------------------------------------------------------------------------
# Tab 1: Ask a Question
# ---------------------------------------------------------------------------
with tab_ask:
    if total_indexed == 0:
        st.info("👈 Build the knowledge base from the sidebar first, then come back and ask away.")
    else:
        st.markdown("###### Try one of these, or ask your own question below")
        examples = [
            "What is the grading breakdown for the Python course?",
            "What is the difference between .loc and .iloc in Pandas?",
            "What's a good email open rate according to the marketing course?",
            "When is the midterm exam for Data Science Fundamentals?",
        ]
        ex_cols = st.columns(len(examples))
        for col, ex in zip(ex_cols, examples):
            if col.button(ex, use_container_width=True, key=f"ex_{ex}"):
                st.session_state.pending_question = ex

        st.markdown('<hr class="cc-divider"/>', unsafe_allow_html=True)

        # Render chat history
        for turn in st.session_state.chat_history:
            with st.chat_message("user", avatar="🧑‍🎓"):
                st.markdown(turn["question"])
            with st.chat_message("assistant", avatar="📚"):
                result = turn["result"]
                st.markdown(result.answer)
                if result.error:
                    st.error(f"LLM error: {result.error}")
                if result.sources:
                    with st.expander(f"📎 {len(result.sources)} source(s) used"):
                        for i, src in enumerate(result.sources, start=1):
                            code = src["metadata"].get("course_code", "")
                            accent = COURSES.get(code, {}).get("accent", "#2C3E63")
                            st.markdown(source_card_html(i, src, accent), unsafe_allow_html=True)

        # Chat input
        typed_question = st.chat_input("Ask about any indexed course (e.g. \"What's due in week 5?\")")
        question_to_run = typed_question or st.session_state.pending_question
        st.session_state.pending_question = None

        if question_to_run:
            with st.chat_message("user", avatar="🧑‍🎓"):
                st.markdown(question_to_run)
            with st.chat_message("assistant", avatar="📚"):
                with st.spinner("Searching course materials and drafting an answer..."):
                    embedder = get_embedder()
                    result = answer_question(
                        question_to_run,
                        vector_store,
                        embedder,
                        api_key=api_key,
                        course_codes=selected_courses,
                        top_k=top_k,
                    )
                st.markdown(result.answer)
                if result.error:
                    st.error(f"LLM error: {result.error}")
                if result.sources:
                    with st.expander(f"📎 {len(result.sources)} source(s) used", expanded=False):
                        for i, src in enumerate(result.sources, start=1):
                            code = src["metadata"].get("course_code", "")
                            accent = COURSES.get(code, {}).get("accent", "#2C3E63")
                            st.markdown(source_card_html(i, src, accent), unsafe_allow_html=True)

            st.session_state.chat_history.append({"question": question_to_run, "result": result})

# ---------------------------------------------------------------------------
# Tab 2: Course Catalog
# ---------------------------------------------------------------------------
with tab_catalog:
    st.markdown("###### The knowledge base currently spans these courses")
    cols = st.columns(3)
    file_type_labels = {"pdf": "pdf", "docx": "docx", "csv": "csv", "txt": "txt"}

    # Per-file chunk counts (best-effort; falls back to '—' if not indexed yet)
    per_file_counts = {}
    if total_indexed > 0:
        raw = vector_store.collection.get(include=["metadatas"])
        for m in raw.get("metadatas", []):
            key = (m.get("course_code"), m.get("file_name"))
            per_file_counts[key] = per_file_counts.get(key, 0) + 1

    for col, (code, meta) in zip(cols, COURSES.items()):
        folder = DATA_DIR / meta["folder"]
        files = []
        if folder.exists():
            for fp in sorted(folder.iterdir()):
                if fp.suffix.lower().lstrip(".") in file_type_labels:
                    files.append({
                        "name": fp.name,
                        "type": fp.suffix.lower().lstrip("."),
                        "chunks": per_file_counts.get((code, fp.name), "—"),
                    })
        with col:
            st.markdown(course_card_html(code, meta, files), unsafe_allow_html=True)

    st.markdown('<hr class="cc-divider"/>', unsafe_allow_html=True)
    st.caption(
        "Each course folder holds one file of each supported type — PDF, DOCX, CSV, and TXT — "
        "demonstrating that the pipeline extracts and indexes all four formats side by side. "
        "Drop your own files into a matching folder under data/ and click Rebuild to add real content."
    )

# ---------------------------------------------------------------------------
# Tab 3: How It Works
# ---------------------------------------------------------------------------
with tab_how:
    st.markdown("###### The pipeline, end to end")
    steps = [
        ("01", "Load", "PDF, DOCX, CSV, and TXT files are parsed with pypdf, python-docx, and pandas into plain text, keeping headings and tables readable."),
        ("02", "Clean & Chunk", "Text is normalized and recursively split into ~900-character overlapping chunks that break on paragraph/sentence boundaries, not mid-word."),
        ("03", "Embed", "Each chunk is converted into a vector with a local Sentence-Transformers model (all-MiniLM-L6-v2) — no API key needed for this step."),
        ("04", "Store", "Vectors and metadata (course, file, type) are persisted in a local ChromaDB collection, filterable by course."),
        ("05", "Retrieve", "A question is embedded the same way, and the top-k most similar chunks are pulled back via cosine similarity, optionally scoped to selected courses."),
        ("06", "Generate", "Claude receives only the retrieved chunks plus the question, and is instructed to answer strictly from that context and cite sources."),
        ("07", "Attribute", "Every answer is paired with the exact source chunks used, shown as cards with course, file, and match strength — so a claim is always traceable."),
    ]
    row1 = st.columns(4)
    row2 = st.columns(4)
    for col, step in zip(row1 + row2, steps):
        with col:
            st.markdown(step_card_html(*step), unsafe_allow_html=True)

    st.markdown('<hr class="cc-divider"/>', unsafe_allow_html=True)
    st.markdown("###### Why answers stay grounded")
    st.markdown(
        "The system prompt instructs Claude to answer **only** from the retrieved passages, "
        "cite which source backs each claim, and say plainly when the course materials don't "
        "cover something — rather than filling gaps with outside knowledge. "
        "Try asking something outside any syllabus (e.g. *\"What's the capital of France?\"*) "
        "to see this in action."
    )
