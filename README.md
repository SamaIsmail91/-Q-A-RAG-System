# 📚 Course Compass — Standard Course Q&A RAG System

A full Retrieval-Augmented Generation (RAG) pipeline that answers student
questions using **only** the content of real course materials — PDFs, Word
docs, CSVs, and text files — across multiple courses, with every answer
traceable back to its source.

Built for the "Standard Course Q&A RAG System" project brief: prepare
materials for 3 courses → extract, clean, and chunk → embed and store in a
vector database → retrieve and generate with an LLM → attribute sources →
serve through a Streamlit UI.

---

## ✅ Requirements checklist

| Requirement | Where it's implemented |
|---|---|
| Materials for 3 courses (PDF, CSV, DOCX, TXT) | `data/course_python`, `data/course_datascience`, `data/course_marketing` — one file of each type per course |
| Extract, clean, chunk text | `src/document_loader.py` (extract) + `src/text_processor.py` (clean & recursive overlapping chunker) |
| Embeddings + vector database | `src/embeddings.py` (Sentence-Transformers, local & free) + `src/vector_store.py` (ChromaDB, persistent) |
| Retriever connected to an LLM | `src/rag_pipeline.py` (retriever) + `src/llm.py` (Claude via the Anthropic API) |
| Answers generated only from retrieved content, with source attribution | System prompt in `src/config.py` enforces "answer only from context"; every answer ships with clickable source cards (course, file, match %) |
| Deployed with Streamlit, polished UI | `app.py` + `src/ui_theme.py` — a light, coordinated "academic library" theme |

---

## 🏗️ Architecture

```
                 ┌───────────────────────────┐
                 │   data/<course>/*.pdf,     │
                 │   *.docx, *.csv, *.txt     │
                 └────────────┬──────────────┘
                              │  document_loader.py
                              ▼
                 ┌───────────────────────────┐
                 │   Raw text per file        │
                 └────────────┬──────────────┘
                              │  text_processor.py
                              │  (clean → recursive chunk w/ overlap)
                              ▼
                 ┌───────────────────────────┐
                 │   Chunks + metadata        │
                 │   (course, file, type)     │
                 └────────────┬──────────────┘
                              │  embeddings.py (Sentence-Transformers)
                              ▼
                 ┌───────────────────────────┐
                 │   ChromaDB (vector_store.py)│
                 └────────────┬──────────────┘
                              │  query (rag_pipeline.py)
      question ──────────────►│  retrieve top-k, optional course filter
                              ▼
                 ┌───────────────────────────┐
                 │   Retrieved chunks         │
                 └────────────┬──────────────┘
                              │  llm.py → Claude (Anthropic API)
                              │  "answer only from this context"
                              ▼
                 ┌───────────────────────────┐
                 │   Answer + cited sources   │──► Streamlit UI (app.py)
                 └───────────────────────────┘
```

---

## 📁 Project structure

```
course_rag_system/
├── app.py                     # Streamlit app (entry point)
├── requirements.txt
├── .env.example                # Copy to .env for local API key (optional)
├── .streamlit/
│   ├── config.toml             # Base theme (colors used across native widgets)
│   └── secrets.toml.example    # Template for Streamlit Cloud secrets
├── data/                       # Course materials (source of truth for ingestion)
│   ├── course_python/          # CS101 — Introduction to Python Programming
│   │   ├── syllabus.pdf
│   │   ├── lecture_notes.docx
│   │   ├── schedule.csv
│   │   └── faq.txt
│   ├── course_datascience/     # DS201 — Data Science Fundamentals
│   └── course_marketing/       # MKT150 — Digital Marketing Essentials
├── src/
│   ├── config.py                # Course registry, chunking/model settings, system prompt
│   ├── document_loader.py       # PDF / DOCX / CSV / TXT → plain text
│   ├── text_processor.py        # Clean + recursive overlapping chunker
│   ├── embeddings.py            # Sentence-Transformers wrapper
│   ├── vector_store.py          # ChromaDB wrapper (add / query / stats)
│   ├── ingest.py                # End-to-end ingestion pipeline w/ progress events
│   ├── llm.py                   # Anthropic API call + prompt construction
│   ├── rag_pipeline.py          # Retriever + generation orchestration
│   └── ui_theme.py              # CSS design system + HTML card renderers
└── vector_db/                   # Persisted ChromaDB data (created on first build)
```

---

## 🚀 Local setup

**1. Install dependencies** (Python 3.10+ recommended):

```bash
cd course_rag_system
pip install -r requirements.txt
```

**2. Provide your Anthropic API key** — any one of these works:
- Paste it into the sidebar text field once the app is running (session-only, never stored to disk), **or**
- Copy `.env.example` to `.env` and fill in `ANTHROPIC_API_KEY`, **or**
- Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill it in.

Get a key at [console.anthropic.com](https://console.anthropic.com).

**3. Run the app:**

```bash
streamlit run app.py
```

**4. Build the knowledge base:** in the sidebar, click **⚡ Build** (indexes
new/changed files) or **🔄 Rebuild** (wipes and re-indexes everything). The
first run downloads the embedding model (~90 MB, one-time, needs internet)
and then works fully offline for embeddings — only the final answer step
calls the Anthropic API.

**5. Ask questions** in the "💬 Ask a Question" tab, e.g.:
- *"What is the grading breakdown for the Python course?"*
- *"What is the difference between .loc and .iloc in Pandas?"*
- *"What's a good email open rate according to the marketing course?"*

---

## ☁️ Deploying to Streamlit Community Cloud

1. Push this project to a GitHub repo (the `.gitignore` already excludes
   secrets and the local vector database).
2. On [share.streamlit.io](https://share.streamlit.io), create a new app
   pointing at `app.py` in your repo.
3. In the app's **Settings → Secrets**, paste:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-your-key-here"
   ```
4. Deploy. On first load, open the sidebar and click **⚡ Build** to index
   the bundled course materials (this runs once; ChromaDB persists to the
   app's storage after that, until the next redeploy).

> Note: free-tier Streamlit Cloud instances have limited memory. The default
> `all-MiniLM-L6-v2` embedding model is small (~90 MB) and runs comfortably
> on CPU, but very large document sets may need a paid tier.

---

## ➕ Adding your own course materials

1. Create a new folder under `data/`, e.g. `data/course_biology/`.
2. Drop in any mix of `.pdf`, `.docx`, `.csv`, `.txt` files.
3. Register the course in `src/config.py`'s `COURSES` dict:
   ```python
   "BIO110": {
       "name": "Introduction to Biology",
       "folder": "course_biology",
       "accent": "#4B7B63",       # any hex — used for that course's UI accent
       "accent_soft": "#E9F1EC",
       "icon": "🧬",
       "instructor": "Dr. Jane Doe",
   },
   ```
4. Click **⚡ Build** in the sidebar — only the new files get embedded;
   already-indexed files are skipped automatically.

The 12 sample files under `data/` are realistic placeholder content
(syllabus, lecture notes, schedule, FAQ) so the system is fully demoable
out of the box — swap them for your real materials any time.

---

## ⚙️ Key configuration (`src/config.py`)

| Setting | Default | Purpose |
|---|---|---|
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | 900 / 150 chars | Chunking granularity |
| `EMBEDDING_MODEL_NAME` | `all-MiniLM-L6-v2` | Local, free Sentence-Transformers model |
| `DEFAULT_TOP_K` / `MAX_TOP_K` | 5 / 10 | How many chunks are retrieved per question |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-6` | Answer-generation model |
| `SYSTEM_PROMPT` | — | Enforces "answer only from retrieved context, cite sources, say when unsure" |

---

## 🧰 Tech stack

- **UI:** Streamlit, custom CSS (Fraunces / Inter / IBM Plex Mono, light coordinated palette)
- **Parsing:** pypdf, python-docx, pandas
- **Embeddings:** Sentence-Transformers (`all-MiniLM-L6-v2`) — local, no API key required
- **Vector database:** ChromaDB (persistent, local, cosine similarity)
- **LLM:** Claude (Anthropic API) via the official `anthropic` Python SDK

---

## 🔍 Design notes

- **Grounded answers:** the system prompt explicitly forbids the model from
  using outside knowledge — try asking something not covered by any course
  (e.g. *"What's the capital of France?"*) to see it decline gracefully.
- **Incremental ingestion:** `⚡ Build` skips files already indexed (tracked
  by `course_code::file_name`), so adding one new file doesn't re-embed
  everything. `🔄 Rebuild` forces a clean slate.
- **Course-scoped retrieval:** the sidebar course filter is passed straight
  into the ChromaDB `where` clause, so searches can be scoped to one course,
  several, or all of them.
- **No vendor lock-in on embeddings:** embeddings are local and free; only
  the final answer-generation step requires an API key, keeping the
  knowledge-base-building step reproducible and cost-free.
