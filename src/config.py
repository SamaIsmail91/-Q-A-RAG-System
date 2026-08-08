"""
Central configuration for the Course Q&A RAG System.
Defines the course registry (single source of truth for course metadata,
used by both the ingestion pipeline and the Streamlit UI), file paths,
chunking parameters, and model settings.
"""
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
VECTOR_DB_DIR = ROOT_DIR / "vector_db"
COLLECTION_NAME = "course_materials"

# ---------------------------------------------------------------------------
# Course registry - the single source of truth for the 3 demo courses.
# Add a new course by adding an entry here and dropping its files into a
# matching folder under data/.
# ---------------------------------------------------------------------------
COURSES = {
    "CS101": {
        "name": "Introduction to Python Programming",
        "folder": "course_python",
        "accent": "#3D5A80",       # deep indigo-blue
        "accent_soft": "#E7EDF5",
        "icon": "🐍",
        "instructor": "Dr. Karim El-Sayed",
    },
    "DS201": {
        "name": "Data Science Fundamentals",
        "folder": "course_datascience",
        "accent": "#5C7A5E",       # sage green
        "accent_soft": "#ECF1EA",
        "icon": "📊",
        "instructor": "Prof. Amina Farouk",
    },
    "MKT150": {
        "name": "Digital Marketing Essentials",
        "folder": "course_marketing",
        "accent": "#8E5572",       # dusty plum
        "accent_soft": "#F3EBF0",
        "icon": "📣",
        "instructor": "Ms. Farida Hassan",
    },
}

# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
CHUNK_SIZE = 900          # target characters per chunk
CHUNK_OVERLAP = 150       # overlap between consecutive chunks
MIN_CHUNK_SIZE = 40       # discard chunks shorter than this after cleaning

# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"   # sentence-transformers, local & free

# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------
DEFAULT_TOP_K = 5
MAX_TOP_K = 10

# ---------------------------------------------------------------------------
# LLM (answer generation)
# ---------------------------------------------------------------------------
ANTHROPIC_MODEL = "claude-sonnet-4-6"
LLM_MAX_TOKENS = 1200
LLM_TEMPERATURE = 0.2

SYSTEM_PROMPT = """You are a helpful course teaching assistant. You answer student \
questions using ONLY the information in the "Retrieved course materials" \
provided in the user message.

Rules you must follow:
1. Base your answer strictly on the retrieved materials. Do not use outside \
knowledge, even if you happen to know the answer.
2. If the retrieved materials do not contain enough information to answer the \
question, say so clearly and suggest the student ask their instructor or check \
the course portal. Do not guess or make anything up.
3. When you state a fact, mention which source it came from by its short label \
(e.g. "[Source 2]"), so the student can verify it.
4. Be concise, clear, and friendly, as a teaching assistant would be. Use short \
paragraphs or bullet points where helpful.
5. If the question spans multiple courses and materials from more than one \
course were retrieved, make clear which course each part of the answer applies to.
"""

APP_TITLE = "Course Compass"
APP_TAGLINE = "Ask your course materials anything."
