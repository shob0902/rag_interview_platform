"""Generate the project technical documentation as a branded PDF.

    python scripts/make_docs.py

Writes ``Project_Documentation.pdf`` to the repository root. Pure-Python
(reportlab) so it needs no system dependencies.
"""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    ListFlowable,
    ListItem,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# --- Palette (matches the app's warm design system) ------------------------
ACCENT = HexColor("#C96E4B")
ACCENT_SOFT = HexColor("#F3E7E0")
INK = HexColor("#22201C")
MUTED = HexColor("#6F6A63")
BORDER = HexColor("#E6E0D8")
CODE_BG = HexColor("#F5F2EC")
SURFACE2 = HexColor("#F3F0EB")

OUT = Path(__file__).resolve().parent.parent.parent / "Project_Documentation.pdf"

styles = getSampleStyleSheet()


def S(name, **kw):
    return ParagraphStyle(name, **kw)


body = S("body", fontName="Helvetica", fontSize=10.2, leading=15.5,
         textColor=INK, spaceAfter=8, alignment=TA_LEFT)
muted = S("muted", parent=body, textColor=MUTED, fontSize=9.5, leading=14)
h1 = S("h1", fontName="Helvetica-Bold", fontSize=17, leading=21,
       textColor=INK, spaceBefore=6, spaceAfter=4)
h2 = S("h2", fontName="Helvetica-Bold", fontSize=12.5, leading=16,
       textColor=ACCENT, spaceBefore=12, spaceAfter=4)
h3 = S("h3", fontName="Helvetica-Bold", fontSize=10.8, leading=14,
       textColor=INK, spaceBefore=8, spaceAfter=2)
bullet = S("bullet", parent=body, spaceAfter=4, leading=14.5)
code = S("code", fontName="Courier", fontSize=8.4, leading=11.6, textColor=INK)
kicker = S("kicker", fontName="Helvetica-Bold", fontSize=9, leading=12,
           textColor=ACCENT, spaceAfter=3)
title = S("title", fontName="Helvetica-Bold", fontSize=30, leading=34,
          textColor=INK, alignment=TA_CENTER)
subtitle = S("subtitle", fontName="Helvetica", fontSize=13, leading=19,
             textColor=MUTED, alignment=TA_CENTER)
cover_meta = S("covermeta", fontName="Helvetica", fontSize=10, leading=16,
               textColor=MUTED, alignment=TA_CENTER)


def P(text, style=body):
    return Paragraph(text, style)


def bullets(items, style=bullet):
    return ListFlowable(
        [ListItem(P(t, style), leftIndent=6, value="•") for t in items],
        bulletType="bullet", start="•", leftIndent=14, bulletColor=ACCENT,
    )


def code_block(text):
    lines = [escape(l) for l in text.strip("\n").split("\n")]
    para = Paragraph("<br/>".join(lines) or "&nbsp;", code)
    t = Table([[para]], colWidths=[165 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def kv_table(rows, col0=48 * mm):
    data = [[P(f"<b>{escape(k)}</b>", muted), P(v, body)] for k, v in rows]
    t = Table(data, colWidths=[col0, 165 * mm - col0])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
    ]))
    return t


def rule():
    return HRFlowable(width="100%", thickness=0.8, color=BORDER,
                      spaceBefore=4, spaceAfter=10)


def section(num, name):
    return [Spacer(1, 6), P(f"{num}", kicker), P(name, h1), rule()]


# ===========================================================================
# Document assembly
# ===========================================================================
story = []

# ---- Cover ----
story += [Spacer(1, 55 * mm)]
story += [P("AI-Powered Role-Based", title), P("Candidate Screening System", title)]
story += [Spacer(1, 10)]
story += [P("A Retrieval-Augmented Generation (RAG) interview platform", subtitle)]
story += [Spacer(1, 26)]
story += [P("Technical Documentation", S("td", parent=subtitle, textColor=ACCENT,
            fontName="Helvetica-Bold", fontSize=12))]
story += [Spacer(1, 40)]
story += [P("PG-AGI &mdash; AI/ML &amp; Backend Intern Assignment", cover_meta)]
story += [P("Author: Shourya Shobhit", cover_meta)]
story += [PageBreak()]

# ---- 1. Overview ----
story += section("SECTION 1", "Executive Overview")
story += [P(
    "This project is an <b>AI-powered, role-based candidate screening system</b>. "
    "A candidate uploads a resume and selects a target role; the system then "
    "conducts a structured technical interview in which the questions are "
    "<b>not predefined</b> &mdash; they are generated dynamically from three "
    "inputs: the candidate&rsquo;s resume, the selected role, and a role-specific "
    "knowledge base (an authoritative textbook).")]
story += [P(
    "The intelligence at its core is a <b>Retrieval-Augmented Generation (RAG)</b> "
    "pipeline. Rather than asking a language model to invent questions from memory, "
    "the system first <i>retrieves</i> the most relevant passages from the textbook "
    "and then <i>generates</i> questions grounded in those passages. Every question "
    "is traceable back to the exact source material that produced it, and the "
    "interview adapts to the candidate&rsquo;s answers as it progresses.")]
story += [P("The full lifecycle handled by the system:", h3)]
story += [bullets([
    "<b>Candidate entry</b> &mdash; upload a resume (PDF or text) and pick a role.",
    "<b>Resume processing</b> &mdash; parse the resume and extract skills, technologies, domains and seniority.",
    "<b>Context construction</b> &mdash; turn resume + role into targeted retrieval queries.",
    "<b>Knowledge retrieval (RAG)</b> &mdash; fetch the most relevant, grounded chunks from the role&rsquo;s knowledge base.",
    "<b>Question generation</b> &mdash; produce interview questions grounded in the retrieved context and tailored to the candidate.",
    "<b>Interactive interview</b> &mdash; the candidate answers in the UI; each next question adapts to previous answers.",
    "<b>Response handling &amp; storage</b> &mdash; persist every question, answer, and its grounding trace.",
    "<b>Final output</b> &mdash; a structured summary with strengths, gaps, a score and a recommendation.",
])]

# ---- 2. What it does (flow) ----
story += section("SECTION 2", "How the System Works &mdash; End-to-End Flow")
story += [P(
    "The pipeline is a single directed flow. The guiding principle is "
    "<b>Context -&gt; Question -&gt; Answer -&gt; Storage</b>: nothing is "
    "generated without grounding context, and nothing is discarded without being "
    "stored.")]
story += [code_block(
    "[1] Candidate Entry       upload resume (PDF/text) + select a role\n"
    "[2] Resume Processing     parse -> extract skills / technologies / domains\n"
    "[3] Context Construction  build resume + role driven retrieval queries\n"
    "[4] Knowledge Retrieval   embed queries -> top-k chunks from the book (RAG)\n"
    "[5] Question Generation   grounded, resume-aware question (one at a time)\n"
    "[6] Interactive Interview candidate answers -> next question adapts\n"
    "[7] Response Storage      persist question + answer + grounding trace\n"
    "[8] Final Output          structured summary: strengths, gaps, score\n"
    "\n"
    "        (steps 4->7 repeat for each question until the interview ends)")]
story += [P(
    "A short worked example: a candidate whose resume emphasises <i>NLP</i> and "
    "<i>PyTorch</i> triggers retrieval of passages on neural networks, "
    "regularization and generalization; the generator then asks a question such as "
    "&ldquo;how would you reduce overfitting in a text-classification network?&rdquo; "
    "&mdash; grounded in the retrieved passages and matched to the candidate&rsquo;s "
    "stated seniority. A candidate strong in reinforcement learning would be routed "
    "to different chapters entirely.")]

# ---- 3. Technology stack ----
story += section("SECTION 3", "Technology Stack &mdash; What It Uses")
story += [kv_table([
    ("Frontend", "React 18 + Vite. Inter typeface, warm minimal design system, light/dark theme."),
    ("Backend", "Python 3.11 + FastAPI (async web framework) with Uvicorn."),
    ("Text generation", "Groq &mdash; Llama 3.3 70B (fast, generous free tier). Routed via a provider abstraction."),
    ("Embeddings", "Google Gemini &mdash; gemini-embedding-001 (3072-dim vectors)."),
    ("Vector database", "ChromaDB &mdash; persistent, embedded, cosine similarity search."),
    ("Relational storage", "SQLite via SQLModel (SQLAlchemy + Pydantic). Swappable to PostgreSQL."),
    ("Resume parsing", "pypdf for PDF text extraction; LLM-based structured profiling."),
    ("Config", "pydantic-settings &mdash; all values from environment / .env, no hard-coded secrets."),
])]
story += [Spacer(1, 4)]
story += [P(
    "<b>Why a hybrid of two AI providers?</b> Groq serves open-weight LLMs with a "
    "fast, generous free tier and strong reasoning &mdash; ideal for question "
    "generation. Groq, however, has <i>no embeddings API</i>, so embeddings use "
    "Gemini, whose embedding free tier is ample. A one-line setting "
    "(<font face='Courier'>LLM_PROVIDER</font>) selects the generation provider; "
    "everything routes through a single module, so switching is trivial.", muted)]

# ---- 4. Architecture ----
story += section("SECTION 4", "System Architecture")
story += [P(
    "The system is a modular, layered application &mdash; not a single script. "
    "Each layer has one responsibility, which keeps the code testable and easy to "
    "extend.")]
story += [kv_table([
    ("routers/", "HTTP transport only: parse requests, map errors to status codes."),
    ("services/interview_service.py", "Orchestration: the single source of truth for how a session advances."),
    ("services/ (RAG)", "One module per stage: parsing, chunking, embeddings, vector store, retrieval, generation, summary."),
    ("services/llm.py", "Provider dispatcher for generation (Groq | Gemini)."),
    ("models.py + database.py", "Persistence with SQLModel over SQLite."),
    ("config.py + roles.py", "Environment-driven configuration and the role registry."),
])]
story += [P("Request &amp; data flow", h3)]
story += [code_block(
    "React (Vite)  --HTTP/JSON-->  FastAPI routers\n"
    "                                   |\n"
    "                                   v\n"
    "                   interview_service  (orchestrator)\n"
    "                                   |\n"
    "    +--------------+---------------+------------------+\n"
    "    |              |               |                  |\n"
    "resume_parser  retrieval    question_generator   summary_service\n"
    "                   |               |                  |\n"
    "              vector_store     llm (Groq)         llm (Groq)\n"
    "              (ChromaDB)\n"
    "                   |\n"
    "         gemini_client (embeddings)        SQLite  (SQLModel)")]

# ---- 5. Core concepts ----
story += section("SECTION 5", "Core Concepts Behind It")
concepts = [
    ("Retrieval-Augmented Generation (RAG)",
     "Instead of trusting an LLM&rsquo;s parametric memory, RAG supplies the model "
     "with relevant external text at inference time. This grounds outputs in a "
     "trusted source, reduces hallucination, and makes answers auditable. Here it "
     "ensures every interview question comes from the assigned textbook."),
    ("Embeddings &amp; semantic search",
     "An embedding maps a piece of text to a high-dimensional vector so that "
     "semantically similar texts sit close together. Retrieval embeds the query and "
     "finds the nearest chunk vectors by cosine similarity &mdash; matching on "
     "<i>meaning</i>, not keywords."),
    ("Chunking",
     "A 400-page book cannot be embedded as one vector. It is split into overlapping, "
     "boundary-aware chunks so each is a focused, self-contained retrieval unit. "
     "Overlap preserves ideas that straddle a boundary; chunk size trades retrieval "
     "precision against context completeness."),
    ("Vector database",
     "ChromaDB stores the chunk vectors and performs fast nearest-neighbour search. "
     "It runs embedded (no server) and persists to disk, so ingestion is a one-time "
     "step and retrieval is instant."),
    ("Resume-driven / dynamic retrieval",
     "Queries are synthesised from the candidate&rsquo;s own resume signals paired "
     "with the role, so retrieval &mdash; and therefore the whole interview &mdash; "
     "is personalised rather than generic."),
    ("Adaptive, grounded generation",
     "Questions are generated one at a time, each conditioned on the retrieved "
     "context, the questions already asked, and the candidate&rsquo;s most recent "
     "answer &mdash; enabling follow-ups and difficulty calibration."),
    ("Traceability",
     "Each question stores the exact chunks that grounded it (source + similarity + "
     "snippet). The chain Context -&gt; Question -&gt; Answer -&gt; Storage is "
     "fully reconstructable and surfaced in the UI."),
]
for name, desc in concepts:
    story += [P(name, h3), P(desc)]

# ---- 6. RAG pipeline in detail ----
story += section("SECTION 6", "The RAG Pipeline in Detail")

story += [P("6.1 &nbsp; Knowledge ingestion (offline)", h2)]
story += [P(
    "Run once via <font face='Courier'>scripts/ingest.py</font>. It reads each "
    "role&rsquo;s documents, chunks them, embeds the chunks with Gemini, and stores "
    "them in ChromaDB tagged with the role. Because Gemini&rsquo;s free embedding "
    "tier counts one request per document and caps at 100/min, ingestion uses a "
    "sliding-window rate limiter and larger chunks so a full textbook fits under the "
    "cap. The Tom Mitchell <i>Machine Learning</i> book produced <b>499 chunks</b>.")]
story += [code_block(
    "def chunk_text(text, *, chunk_size, chunk_overlap):\n"
    "    text = _normalise(text)\n"
    "    units = _split_units(text)        # paragraphs -> sentences -> words\n"
    "    chunks, current = [], ''\n"
    "    for unit in units:\n"
    "        candidate = f'{current}\\n\\n{unit}'.strip() if current else unit\n"
    "        if len(candidate) <= chunk_size:\n"
    "            current = candidate            # keep packing the chunk\n"
    "        else:\n"
    "            chunks.append(current)\n"
    "            tail = current[-chunk_overlap:]   # carry overlap forward\n"
    "            current = f'{tail}\\n\\n{unit}'.strip()\n"
    "    ...\n"
    "    return [Chunk(text=c, index=i) for i, c in enumerate(chunks)]")]

story += [P("6.2 &nbsp; Retrieval mechanism", h2)]
story += [P(
    "At interview time, the system builds several queries from the resume profile "
    "and role, embeds each, queries ChromaDB (filtered to the role), and fuses the "
    "results &mdash; de-duplicating chunks and keeping the best similarity score.")]
story += [code_block(
    "def build_queries(*, profile, role_id):\n"
    "    role = get_role(role_id)\n"
    "    signals = dedup(profile.domains + profile.skills + profile.technologies)\n"
    "    queries = [f'{role.label} concepts related to {s}' for s in signals[:5]]\n"
    "    queries.append(f'Core {role.label} fundamentals: {role.description}')\n"
    "    return dedup(queries)\n"
    "\n"
    "def retrieve_context(*, profile, role_id, top_k):\n"
    "    best = {}\n"
    "    for q in build_queries(profile=profile, role_id=role_id):\n"
    "        emb = gemini_client.embed_query(q)\n"
    "        for chunk in vector_store.query(query_embedding=emb,\n"
    "                                        role=role_id, top_k=top_k):\n"
    "            key = (chunk.source, chunk.chunk_index)\n"
    "            if key not in best or chunk.score > best[key].score:\n"
    "                best[key] = chunk           # fuse, keep highest score\n"
    "    return sorted(best.values(), key=lambda c: c.score, reverse=True)[:top_k]")]

story += [P("6.3 &nbsp; Question generation", h2)]
story += [P(
    "The generator prompts the LLM with the role, the resume profile, the retrieved "
    "context, the questions already asked, and the last answer. It returns "
    "structured JSON: the question, a topic, a difficulty, a one-line rationale, and "
    "the indices of the context chunks it used &mdash; which are then persisted for "
    "traceability.")]
story += [code_block(
    "def generate_question(*, role_id, profile, context,\n"
    "                      asked_questions, last_question, last_answer):\n"
    "    prompt = SYSTEM_PROMPT.format(role=..., profile=..., context=context,\n"
    "                                  asked=asked_questions,\n"
    "                                  followup=(last_question, last_answer))\n"
    "    data = llm.generate_json(prompt, temperature=0.6)\n"
    "    return GeneratedQuestion(question=data['question'], topic=data['topic'],\n"
    "                             difficulty=data['difficulty'],\n"
    "                             rationale=data['rationale'],\n"
    "                             context_indices=data['context_indices'])")]

# ---- 7. Data model ----
story += section("SECTION 7", "Data Model &amp; Persistence")
story += [P(
    "Two SQLModel tables capture the full record. A session owns an ordered list of "
    "question/answer turns, and each turn keeps its own grounding trace &mdash; so "
    "the provenance of every question survives in the database, not just in memory.")]
story += [P("InterviewSession", h3)]
story += [bullets([
    "candidate name, role, full resume text, structured <font face='Courier'>resume_profile</font>",
    "status (in_progress / completed), and the final <font face='Courier'>summary</font> (insights JSON)",
])]
story += [P("QAPair (one per turn)", h3)]
story += [bullets([
    "<font face='Courier'>topic</font>, <font face='Courier'>difficulty</font>, <font face='Courier'>rationale</font> &mdash; why the question was asked",
    "<font face='Courier'>context_chunks</font> &mdash; the grounding trace (source, similarity, snippet)",
    "<font face='Courier'>question</font>, <font face='Courier'>answer</font>, timestamps",
])]

# ---- 8. Main functions ----
story += section("SECTION 8", "The Main Function That Ties Everything Together")
story += [P(
    "The orchestrator in <font face='Courier'>services/interview_service.py</font> "
    "is the heart of the backend. Two functions drive the entire lifecycle; the web "
    "layer only calls into them.")]
story += [P("Starting an interview", h3)]
story += [code_block(
    "def start_interview(db, *, role_id, candidate_name, resume_text):\n"
    "    profile = resume_parser.build_profile(resume_text, role_id)  # extract\n"
    "    session = InterviewSession(role=role_id, resume_profile=profile, ...)\n"
    "    db.add(session); db.commit()\n"
    "    _generate_and_store_question(db, session)   # first grounded question\n"
    "    return session")]
story += [P("Generating &amp; storing the next question (retrieval + generation + persistence)", h3)]
story += [code_block(
    "def _generate_and_store_question(db, session):\n"
    "    profile = ResumeProfile(**session.resume_profile)\n"
    "    context = retrieval.retrieve_context(profile=profile, role_id=session.role)\n"
    "    existing = _ordered_questions(db, session)\n"
    "    last = existing[-1] if existing else None\n"
    "    gen = question_generator.generate_question(\n"
    "        role_id=session.role, profile=profile, context=context,\n"
    "        asked_questions=[q.question for q in existing],\n"
    "        last_question=last.question if last else None,\n"
    "        last_answer=last.answer if last else None)\n"
    "    used = gen.context_indices or list(range(min(3, len(context))))\n"
    "    qa = QAPair(session_id=session.id, order_index=len(existing),\n"
    "                topic=gen.topic, difficulty=gen.difficulty,\n"
    "                rationale=gen.rationale, question=gen.question,\n"
    "                context_chunks=[trace(context[i]) for i in used])\n"
    "    db.add(qa); db.commit()")]
story += [P("Advancing the interview", h3)]
story += [code_block(
    "def submit_answer(db, *, session_id, answer):\n"
    "    session = _get_session(db, session_id)\n"
    "    pending = _pending_question(db, session)      # the open question\n"
    "    pending.answer = answer; db.commit()\n"
    "    if _answered_count(db, session) >= QUESTIONS_PER_INTERVIEW:\n"
    "        _finalise(db, session)                    # generate summary/insights\n"
    "    else:\n"
    "        _generate_and_store_question(db, session) # adaptive next question\n"
    "    return session")]
story += [P(
    "This is where all the pieces meet: <b>resume parsing</b> feeds <b>retrieval</b>, "
    "which feeds <b>generation</b>, whose output (with its grounding trace) is "
    "<b>persisted</b>, and the answer loop repeats until the session is "
    "<b>summarised</b>.", muted)]

# ---- 9. Design decisions ----
story += section("SECTION 9", "Key Design Decisions &amp; Trade-offs")
story += [bullets([
    "<b>Question-at-a-time generation</b> costs one LLM call per turn but unlocks adaptivity and keeps each question grounded in freshly-retrieved context.",
    "<b>Hybrid providers (Groq + Gemini)</b> use each provider where it is strongest &mdash; Groq for fast, generous generation; Gemini for embeddings.",
    "<b>Robustness over brittleness</b>: resume profiling and summary generation have deterministic fallbacks, and JSON parsing has a salvage path, so one model hiccup never breaks the flow.",
    "<b>Traceability as a feature</b>: grounding chunks are stored and shown in the UI, not used and discarded.",
    "<b>Designing around real constraints</b>: ingestion is rate-limited and uses larger chunks to fit a whole textbook under the free embedding cap.",
    "<b>Roles are data, not code</b>: adding a role is one registry entry plus a folder of documents.",
    "<b>Config via environment</b>: no secrets in code; SQLite-&gt;PostgreSQL is a connection-string change.",
])]

# ---- 10. How to run ----
story += section("SECTION 10", "How to Run")
story += [P("Backend", h3)]
story += [code_block(
    "cd backend\n"
    "python -m venv .venv && .venv\\Scripts\\activate\n"
    "pip install -r requirements.txt\n"
    "copy .env.example .env      # set GROQ_API_KEY and GOOGLE_API_KEY\n"
    "python -m scripts.ingest --role ai_ml_engineer   # one-time ingestion\n"
    "uvicorn app.main:app --reload --port 8000")]
story += [P("Frontend", h3)]
story += [code_block(
    "cd frontend\n"
    "npm install\n"
    "npm run dev                 # http://localhost:5173")]
story += [Spacer(1, 10)]
story += [P(
    "Open the app, read the landing page, upload a resume, choose the AI/ML "
    "Engineer role, and the system runs a grounded, adaptive interview ending in a "
    "structured assessment.", muted)]


# ===========================================================================
# Page furniture (header rule + footer page number)
# ===========================================================================
def decorate(canvas, doc):
    canvas.saveState()
    w, h = A4
    if doc.page > 1:
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(20 * mm, 12 * mm,
                          "AI Candidate Screening — Technical Documentation")
        canvas.drawRightString(w - 20 * mm, 12 * mm, f"{doc.page}")
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(20 * mm, 15 * mm, w - 20 * mm, 15 * mm)
    canvas.restoreState()


def build():
    doc = BaseDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
        title="AI Candidate Screening — Technical Documentation",
        author="Shourya Shobhit",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin,
                  doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=decorate)])
    doc.build(story)
    print(f"Wrote {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build()
