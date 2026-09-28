# AI-Powered Role-Based Candidate Screening System

A RAG-powered technical interview platform. A candidate uploads a resume and
picks a target role; the system parses the resume, retrieves role-specific
material from an authoritative knowledge base (e.g. Tom Mitchell's *Machine
Learning*), and **dynamically generates interview questions grounded in that
retrieved context and tailored to the candidate**. The interview is interactive
and adaptive, every question is fully traceable to its source, and the session
ends with a structured evaluation.

---

## 1. What it does (the flow)

```
Candidate Entry ─► Resume Processing ─► Context Construction ─► Knowledge Retrieval (RAG)
      │                    │                      │                        │
 upload PDF/text     parse + extract        build role+resume        top-k chunks from
 select a role       skills / tech /        driven queries           role knowledge base
                     domains / seniority                                    │
                                                                            ▼
 Final Output  ◄─  Response Handling  ◄─  Interactive Interview  ◄─  Question Generation
      │                    │                      │                        │
 structured         store Q + A +          answer in UI, adapt      grounded, resume-aware
 summary+insights   context trace          to previous answer       question (one at a time)
```

Every question stores the retrieved chunks that grounded it, so the pipeline is
auditable end to end: **Context → Question → Answer → Storage**.

---

## 2. Architecture

```
┌────────────────────────┐        HTTP/JSON        ┌─────────────────────────────────┐
│   Frontend (React+Vite)│  ───────────────────►   │        Backend (FastAPI)        │
│                        │                         │                                 │
│  • Setup (upload+role) │                         │  routers/  → thin HTTP layer    │
│  • Interview flow      │  ◄───────────────────   │  services/ → business logic     │
│  • Summary + insights  │                         │    ├─ resume_parser             │
│  • Context trace view  │                         │    ├─ retrieval  ┐              │
└────────────────────────┘                         │    ├─ question_generator │ RAG  │
                                                    │    ├─ vector_store (Chroma)│     │
                                                    │    ├─ llm (Groq | Gemini)  │     │
                                                    │    ├─ gemini_client (embed)┘     │
                                                    │    └─ interview_service (orch.) │
                                                    │  models/ → SQLModel (SQLite)    │
                                                    └──────────┬──────────────────────┘
                                                               │
                          ┌────────────────┬──────────────────┼────────────────┐
                          ▼                ▼                   ▼                ▼
                   ChromaDB (vectors)  SQLite (sessions,   Groq (LLM      Google Gemini
                   role-tagged chunks  Q&A, trace, summary) generation)   (embeddings)
```

**Separation of concerns** is deliberate and strict:

| Layer | Responsibility |
|-------|----------------|
| `routers/` | HTTP transport only — parse requests, map errors to status codes. |
| `services/interview_service.py` | Orchestrates the interview lifecycle; the single source of truth for how a session advances. |
| `services/*` (RAG) | Each stage is its own module: parsing, chunking, embeddings, vector store, retrieval, generation, summary. |
| `models.py` + `database.py` | Persistence (SQLModel / SQLite). |
| `config.py` | All configuration via environment variables — no hard-coded secrets. |

---

## 3. The RAG pipeline (core focus)

### 3.1 Knowledge ingestion (`scripts/ingest.py`)
- **Load**: reads role documents from `data/knowledge_base/<role_id>/` (PDF/txt/md).
- **Chunk** (`services/chunking.py`): a *recursive, structure-aware* splitter with
  a ~1200-char target and 200-char overlap. It prefers to break on paragraph →
  sentence → word boundaries so chunks stay semantically coherent, and the
  overlap preserves concepts that straddle a boundary. This balances **context
  preservation** against **retrieval efficiency** (small, focused units).
- **Embed**: Google `gemini-embedding-001`, batched with retry/back-off.
- **Store**: ChromaDB (persistent, embedded, cosine space). Every chunk is
  tagged with its `role`, so each role's knowledge base is logically isolated.

### 3.2 Retrieval (`services/retrieval.py`)
- **Dynamic query construction**: instead of one static query, we synthesize
  several queries by pairing the candidate's salient resume signals (domains,
  skills, technologies) with the role focus — plus one role-level query so a
  sparse resume still retrieves core material. This is what makes retrieval
  *resume-driven*.
- **Fusion**: results from all queries are de-duplicated (by source + chunk
  index), keeping the best similarity score, then ranked and truncated to
  `top_k`.

### 3.3 Question generation (`services/question_generator.py`)
- Generates **one question at a time**. Generating incrementally is what enables
  **adaptivity**: each question is conditioned on the questions already asked and
  the candidate's most recent answer, so the interview probes deeper or pivots.
- The prompt forces the model to ground the question in the retrieved context
  and to calibrate **difficulty to the resume** (seniority + demonstrated depth).
- Output is structured JSON: `question`, `topic`, `difficulty`, `rationale`, and
  the `context_indices` it used — persisted for traceability.

### 3.4 Why these choices
- **Hybrid LLM providers (Groq + Gemini)** — text *generation* runs on **Groq**
  (`llama-3.3-70b-versatile`) for its fast, generous free tier and strong
  question quality; *embeddings* run on **Gemini** (`gemini-embedding-001`)
  because Groq has no embeddings API and Gemini's embedding free tier is ample.
  The provider is chosen by `LLM_PROVIDER` in `.env` and everything routes
  through `services/llm.py`, so switching to all-Gemini is a one-line change.
- **ChromaDB** → a real, persistent vector DB that runs embedded (no server to
  provision) — the reviewer can run it in minutes.
- **We supply our own embeddings** to both ingestion and query so the embedding
  model is identical on both sides (a common source of silent retrieval bugs).

---

## 4. Data model (persistence)

- `InterviewSession`: candidate, role, resume text, structured `resume_profile`,
  status, and the final `summary` (insights).
- `QAPair`: `topic`, `difficulty`, `rationale`, `context_chunks` (the grounding
  trace), `question`, `answer`, timestamps — one row per turn, ordered.

This captures the full `Context → Question → Answer → Storage` chain per turn.

---

## 5. Setup & run

### Prerequisites
- Python 3.11+, Node 18+
- A **free** Groq API key (generation): https://console.groq.com/keys
- A **free** Google AI Studio API key (embeddings): https://aistudio.google.com/app/apikey

### 5.1 Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
.venv/Scripts/activate
pip install -r requirements.txt

cp .env.example .env          # then edit .env and set GOOGLE_API_KEY
```

**Ingest the knowledge base** (one-time). Put the role's PDF in
`backend/data/knowledge_base/ai_ml_engineer/` (e.g. Tom Mitchell's *Machine
Learning*), then:

```bash
python -m scripts.ingest --role ai_ml_engineer
```

**Run the API:**

```bash
uvicorn app.main:app --reload --port 8000
```

Docs at http://localhost:8000/docs, health at http://localhost:8000/api/health.

### 5.2 Frontend

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173  (proxies /api to :8000)
```

Open http://localhost:5173, upload a resume, type a role (or pick a preset), and start.

---

## 6. API surface

| Method | Path | Purpose |
|--------|------|---------|
| `GET`  | `/api/roles` | List roles + knowledge-base chunk counts. |
| `POST` | `/api/interviews/start` | Multipart (role, name, resume file/text) → session + first question. |
| `POST` | `/api/interviews/{id}/answer` | Submit an answer → next question or completion. |
| `GET`  | `/api/interviews/{id}` | Full session: transcript, context trace, insights. |
| `GET`  | `/api/health` | Service + model status. |

---

## 7. Configuration

All via environment (`backend/.env`; see `.env.example`). Key knobs:
`LLM_PROVIDER` (`groq` | `gemini`), `GROQ_API_KEY`, `GROQ_GENERATION_MODEL`,
`GOOGLE_API_KEY`, `GEMINI_GENERATION_MODEL`, `GEMINI_EMBEDDING_MODEL`,
`CHUNK_SIZE`, `CHUNK_OVERLAP`, `RETRIEVAL_TOP_K`, `QUESTIONS_PER_INTERVIEW`,
`DATABASE_URL` (swap SQLite → Postgres without code changes), `CORS_ORIGINS`.

---

## 8. Design decisions & trade-offs

- **Question-at-a-time generation** costs one LLM call per turn but unlocks
  adaptivity and keeps each question grounded in freshly-retrieved context.
- **Robustness over brittleness**: resume profiling and summary generation both
  have deterministic fallbacks, so a single model hiccup never breaks the flow.
  JSON responses use Gemini's JSON mode plus a salvage parser.
- **Traceability as a first-class feature**: the grounding chunks are stored and
  surfaced in the UI, not just used and discarded — reviewers can see exactly
  why each question was asked.
- **Roles are data, not code**: adding a preset role = one entry in `roles.py`
  + a folder of documents to ingest.
- **Any role can be typed in**: presets are shortcuts. For a custom role, one
  LLM call decides whether an existing knowledge base is core to it (e.g. "NLP
  Engineer" uses the ML textbook, "Frontend Developer" doesn't); the result is
  cached per role name. Similarity scores alone couldn't make this call, since
  unrelated roles score nearly as high as related ones. With no applicable
  knowledge base, questions are generated from the role's core concepts and
  carry no sources.
- **Ingestion under a free-tier constraint**: Gemini's embedding free tier counts
  one request per document and caps at 100/min. Ingestion is throttled with a
  sliding-window rate limiter (`EMBEDDING_REQUESTS_PER_MINUTE`) and uses larger
  chunks (`CHUNK_SIZE=2600`) so a full textbook fits comfortably under the cap —
  a concrete example of designing around real constraints.

## 9. Possible extensions
- Re-retrieve using the candidate's last answer to make *retrieval* itself
  adaptive (currently adaptivity lives in generation).
- Per-answer scoring with rubric-based grading.
- Streaming responses; auth + multi-tenant candidate history.

---

## 10. Project structure

```
pgagi_project/
├─ backend/
│  ├─ app/
│  │  ├─ main.py            # FastAPI app + CORS + startup
│  │  ├─ config.py          # env-driven settings
│  │  ├─ database.py        # SQLModel engine/session
│  │  ├─ models.py          # InterviewSession, QAPair
│  │  ├─ schemas.py         # API contract
│  │  ├─ roles.py           # role registry
│  │  ├─ serializers.py     # model → schema mappers
│  │  ├─ routers/interview.py
│  │  └─ services/          # RAG + orchestration
│  │     ├─ chunking.py  vector_store.py
│  │     ├─ llm.py  groq_client.py  gemini_client.py   # generation + embeddings
│  │     ├─ resume_parser.py  retrieval.py  question_generator.py
│  │     ├─ summary_service.py  interview_service.py
│  ├─ scripts/ingest.py     # knowledge ingestion CLI
│  ├─ data/knowledge_base/  # drop role PDFs here
│  ├─ requirements.txt      └─ .env.example
└─ frontend/                # React + Vite (Inter, light/dark theme)
   └─ src/
      ├─ App.jsx  api.js  useTheme.js  styles.css
      └─ components/         # LandingScreen, SetupScreen, InterviewScreen,
                            #  SummaryScreen, ProfilePanel, ContextTrace,
                            #  Stepper, ThemeToggle
```

The frontend opens on a **landing page** explaining the product, then flows
Setup → Interview → Summary. It ships a warm, minimal design system (Inter,
soft neutral palette) with a light/dark theme toggle.

---

## 11. Deploying the backend (Koyeb, free)

`backend/Dockerfile` builds the API as a container (multi-stage: compiles
`chroma-hnswlib` from source in a build stage with a C toolchain, then ships a
slim runtime image). Any Docker-based host works; these steps are for
[Koyeb](https://www.koyeb.com), which has a free web-service tier with no
credit card required.

1. Push this repo to GitHub (already done).
2. On Koyeb: **Create Service → GitHub → select this repo**. Set the
   **Dockerfile path** to `backend/Dockerfile` and the **build context** to
   `backend/`. Koyeb injects a `PORT` env var at runtime; the Dockerfile's
   `CMD` already binds to it.
3. Set environment variables on the service: `GOOGLE_API_KEY`, `GROQ_API_KEY`,
   `LLM_PROVIDER=groq`, and `CORS_ORIGINS=https://<your-netlify-site>.netlify.app`
   (comma-separate multiple origins, no spaces).
4. Deploy. Koyeb gives you a public URL like `https://<name>-<org>.koyeb.app`.
   Point the frontend's `VITE_API_BASE_URL` at `<that URL>/api` and redeploy
   Netlify.

**Storage caveat:** Koyeb's free instance can't attach a volume (that's a
paid-instance feature), so `backend/data/` — the SQLite session DB and the
Chroma vector store — is **ephemeral**: it resets on every redeploy or
instance restart. This matches Render's free tier, which has the same
limitation. For a demo/portfolio deployment that's usually acceptable
(interview history resetting is harmless); the app still runs fine with an
empty vector store, it just won't have retrieved context until re-ingested.
To re-ingest after a restart, get a shell on the running instance with the
[Koyeb CLI](https://www.koyeb.com/docs/build-and-deploy/cli/reference) and run
the same ingestion step as local dev:

```bash
koyeb instances exec <instance-id> -- python -m scripts.ingest --role ai_ml_engineer
```

(The source PDF still needs to reach the container somehow — e.g. `curl` it
from a URL you control inside that shell — since the copyrighted textbook
PDFs are intentionally not committed to the repo.) If persistent storage
matters more than staying on a free tier, the cleanest fix is a paid instance
+ volume, or pointing `DATABASE_URL` at a managed Postgres and swapping Chroma
for a small hosted vector DB — both are drop-in via env vars, no code changes.
