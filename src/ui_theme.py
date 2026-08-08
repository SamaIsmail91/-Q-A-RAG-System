"""
ui_theme.py
-----------
Design system for the Streamlit UI: a light, warm "academic library" theme
(parchment background, deep indigo ink, muted sage/plum course accents,
gold highlight) plus small HTML renderers for the bits Streamlit's native
widgets can't style on their own (source "index cards", course cards).

Palette:
  --bg          #FAF7F1  warm parchment background
  --surface     #FFFFFF  card surface
  --surface-alt #F3EEE3  soft section background (sidebar, hero)
  --border      #E7E0D3  hairline dividers
  --ink         #24272B  primary text
  --muted       #6B6B6F  secondary text
  --primary     #2C3E63  deep indigo (headings, primary actions)
  --primary-lt  #4A5D8A  indigo hover state
  --gold        #C68A2E  warm highlight / active states
  --gold-soft   #F6E9D2  gold tint background

Type:
  Display -> "Fraunces" (serif, warm academic character)
  Body    -> "Inter" (clean, highly legible)
  Mono    -> "IBM Plex Mono" (source metadata, citations, code)
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
  --bg: #FAF7F1;
  --surface: #FFFFFF;
  --surface-alt: #F3EEE3;
  --border: #E7E0D3;
  --ink: #24272B;
  --muted: #6B6B6F;
  --primary: #2C3E63;
  --primary-lt: #4A5D8A;
  --gold: #C68A2E;
  --gold-soft: #F6E9D2;
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
  background: var(--bg) !important;
  color: var(--ink);
  font-family: 'Inter', sans-serif;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stToolbar"] { right: 1rem; }

/* ---------- Typography ---------- */
h1, h2, h3, .cc-display {
  font-family: 'Fraunces', serif !important;
  color: var(--primary) !important;
  letter-spacing: -0.01em;
}
p, li, span, label, div { font-family: 'Inter', sans-serif; }
code, .cc-mono { font-family: 'IBM Plex Mono', monospace !important; }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
  background: var(--surface-alt) !important;
  border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: var(--ink); }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
  color: var(--primary) !important;
}

/* ---------- Hero banner ---------- */
.cc-hero {
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-lt) 100%);
  border-radius: 18px;
  padding: 28px 32px;
  margin-bottom: 22px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 6px 24px rgba(44,62,99,0.18);
}
.cc-hero::after {
  content: "";
  position: absolute; top: 0; right: 0; bottom: 0; width: 8px;
  background: var(--gold);
}
.cc-hero-title {
  font-family: 'Fraunces', serif;
  font-weight: 700;
  font-size: 2.1rem;
  color: #FFFFFF !important;
  margin: 0;
}
.cc-hero-tagline {
  font-family: 'Inter', sans-serif;
  color: #E7EDF5;
  font-size: 1rem;
  margin-top: 4px;
}

/* ---------- Buttons ---------- */
.stButton > button, .stDownloadButton > button {
  background: var(--primary) !important;
  color: #FFFFFF !important;
  border-radius: 10px !important;
  border: none !important;
  font-weight: 600 !important;
  padding: 0.5rem 1.1rem !important;
  transition: all 0.15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  background: var(--primary-lt) !important;
  box-shadow: 0 4px 14px rgba(44,62,99,0.25);
  transform: translateY(-1px);
}
.stButton > button[kind="secondary"] {
  background: var(--surface) !important;
  color: var(--primary) !important;
  border: 1.5px solid var(--primary) !important;
}

/* ---------- Inputs ---------- */
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
[data-testid="stChatInput"] textarea {
  background: var(--surface) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 10px !important;
  color: var(--ink) !important;
}
[data-testid="stChatInput"] { border-top: 1px solid var(--border); }

/* ---------- Tabs ---------- */
button[data-baseweb="tab"] {
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  color: var(--muted) !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
  color: var(--primary) !important;
}
div[data-baseweb="tab-highlight"] { background-color: var(--gold) !important; }
div[data-baseweb="tab-border"] { background-color: var(--border) !important; }

/* ---------- Chat bubbles ---------- */
[data-testid="stChatMessage"] {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 4px 6px;
  margin-bottom: 10px;
}

/* ---------- Expander (Sources) ---------- */
[data-testid="stExpander"] {
  background: var(--surface);
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}

/* ---------- Metric-ish badges ---------- */
.cc-badge {
  display: inline-block;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: 999px;
  background: var(--gold-soft);
  color: #8A5E1E;
  letter-spacing: 0.02em;
}

/* ---------- Source "index card" ---------- */
.cc-source-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 5px solid var(--course-accent, var(--primary));
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 10px;
}
.cc-source-meta {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.74rem;
  color: var(--muted);
  margin-bottom: 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.cc-source-course {
  font-weight: 600;
  color: var(--course-accent, var(--primary));
}
.cc-source-text {
  font-size: 0.88rem;
  color: var(--ink);
  line-height: 1.5;
}
.cc-score {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.7rem;
  background: var(--surface-alt);
  padding: 1px 8px;
  border-radius: 999px;
  color: var(--muted);
}

/* ---------- Course catalog card ---------- */
.cc-course-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-top: 6px solid var(--course-accent, var(--primary));
  border-radius: 14px;
  padding: 18px 20px;
  height: 100%;
}
.cc-course-icon { font-size: 1.8rem; }
.cc-course-name {
  font-family: 'Fraunces', serif;
  font-weight: 600;
  font-size: 1.15rem;
  color: var(--ink);
  margin: 6px 0 0 0;
}
.cc-course-code {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.78rem;
  color: var(--course-accent, var(--primary));
  font-weight: 600;
}
.cc-course-instructor { font-size: 0.85rem; color: var(--muted); margin-top: 4px; }
.cc-file-row {
  display: flex; align-items: center; gap: 8px;
  font-size: 0.82rem; color: var(--ink);
  padding: 5px 0; border-top: 1px dashed var(--border);
}
.cc-file-row:first-of-type { border-top: 1px solid var(--border); margin-top: 10px; }
.cc-chunk-pill {
  margin-left: auto;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.68rem;
  color: var(--muted);
}

/* ---------- Pipeline step ("How it works") ---------- */
.cc-step {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 16px 18px;
  text-align: left;
  height: 100%;
}
.cc-step-num {
  font-family: 'Fraunces', serif;
  font-weight: 700;
  font-size: 1.6rem;
  color: var(--gold);
}
.cc-step-title {
  font-family: 'Fraunces', serif;
  font-weight: 600;
  font-size: 1.02rem;
  color: var(--primary);
  margin: 2px 0 6px 0;
}
.cc-step-desc { font-size: 0.85rem; color: var(--muted); line-height: 1.45; }

.cc-divider { border: none; border-top: 1px dashed var(--border); margin: 8px 0 18px 0; }
.cc-caption { color: var(--muted); font-size: 0.82rem; }
</style>
"""


def _flatten(html: str) -> str:
    """Strip leading whitespace from every line of an HTML snippet.

    Streamlit renders st.markdown(..., unsafe_allow_html=True) through a
    Markdown parser, and Markdown treats any line indented 4+ spaces as a
    preformatted code block. Without this, the pretty-indented f-strings
    below get rendered as literal text instead of HTML.
    """
    return "\n".join(line.strip() for line in html.strip().splitlines())


def hero_html(title: str, tagline: str) -> str:
    return _flatten(f"""
    <div class="cc-hero">
      <p class="cc-hero-title">📚 {title}</p>
      <p class="cc-hero-tagline">{tagline}</p>
    </div>
    """)


def source_card_html(index: int, source: dict, accent: str) -> str:
    meta = source["metadata"]
    score_pct = round(source.get("score", 0) * 100)
    excerpt = source["text"].strip().replace("\n", " ")
    if len(excerpt) > 320:
        excerpt = excerpt[:320].rsplit(" ", 1)[0] + "…"
    return _flatten(f"""
    <div class="cc-source-card" style="--course-accent: {accent};">
      <div class="cc-source-meta">
        <span><span class="cc-source-course">Source {index}</span> ·
        {meta.get('course_code','')} · {meta.get('file_name','')}</span>
        <span class="cc-score">{score_pct}% match</span>
      </div>
      <div class="cc-source-text">{excerpt}</div>
    </div>
    """)


def course_card_html(code: str, meta: dict, files: list[dict]) -> str:
    rows = ""
    icons = {"pdf": "📕", "docx": "📘", "csv": "📊", "txt": "📄"}
    for f in files:
        icon = icons.get(f["type"], "📄")
        rows += f"""
        <div class="cc-file-row">
          <span>{icon}</span><span>{f['name']}</span>
          <span class="cc-chunk-pill">{f.get('chunks', '—')} chunks</span>
        </div>
        """
    return _flatten(f"""
    <div class="cc-course-card" style="--course-accent: {meta['accent']};">
      <div class="cc-course-icon">{meta['icon']}</div>
      <p class="cc-course-name">{meta['name']}</p>
      <div class="cc-course-code">{code}</div>
      <div class="cc-course-instructor">👤 {meta['instructor']}</div>
      {rows}
    </div>
    """)


def step_card_html(num: str, title: str, desc: str) -> str:
    return _flatten(f"""
    <div class="cc-step">
      <div class="cc-step-num">{num}</div>
      <p class="cc-step-title">{title}</p>
      <p class="cc-step-desc">{desc}</p>
    </div>
    """)
