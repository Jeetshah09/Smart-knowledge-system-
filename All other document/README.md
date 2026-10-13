# AI Smart Knowledge Management System

An interactive AI knowledge and learning assistant inspired by Google AI Studio and NotebookLM.
Create notebooks, upload learning resources (PDF / DOCX / TXT / images / YouTube), chat with
your resources through **Google Gemini**, and generate summaries, quizzes, flashcards, FAQs
and study notes.

**B.Tech Minor Project** — intentionally simple architecture (no RAG / embeddings / vector DB).
The AI workflow is: extract resource text → store in MongoDB → build a prompt → Gemini → save
conversation → show answer.

---

## ✅ Status: fully working, frontend ↔ backend connected

Everything below has been verified end-to-end:

| Feature | Status |
|---|---|
| Register / Login / JWT auth | ✅ working |
| Notebooks CRUD + pin + search | ✅ working |
| Upload PDF / DOCX / TXT + text extraction | ✅ working |
| YouTube URL + transcript fetch | ✅ working |
| Chat with Gemini (grounded in selected sources) | ✅ verified live |
| Summary / Quiz / Flashcards / FAQ / Study Notes | ✅ verified live |
| Conversations & message history | ✅ persisted in MongoDB |
| Prompt Studio (model / temperature / tokens) | ✅ working |
| Global search, dashboard stats, activity log | ✅ working |
| Light / dark theme, responsive UI | ✅ working |

> A demo account already exists from testing: **test@example.com / password123**

---

## Technology Stack

**Backend** — Python 3.11, FastAPI, Uvicorn, PyMongo (MongoDB), JWT (PyJWT) + bcrypt,
`google-generativeai` (Gemini), PyMuPDF, python-docx, Pillow, httpx, pytest.

**Frontend** — Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS v4, Framer Motion,
Lucide icons, React Hook Form + Zod, Axios.

---

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, CORS, routers, health check
│   │   ├── core/                   # config, database, indexes, security (JWT/bcrypt)
│   │   ├── schemas/                # Pydantic models
│   │   ├── routers/                # auth, users, notebooks, resources, chat,
│   │   │                           # conversations, ai, prompts, search, settings, dashboard
│   │   ├── services/               # gemini_service, file extraction, storage, youtube, activity
│   │   ├── dependencies/           # JWT auth dependency
│   │   └── utils/                  # ObjectId helpers, responses, validators, text utils
│   ├── uploads/                    # uploaded files (gitignored)
│   ├── requirements.txt
│   └── .env                        # secrets (gitignored) — Gemini key lives here
├── frontend/
│   ├── src/app/                    # landing, login, register, forgot-password
│   │   └── (app)/                  # dashboard, notebooks, workspace, studio,
│   │                               # conversations, search, profile, settings
│   ├── src/components/             # ui primitives, layout (sidebar/app shell)
│   ├── src/context/                # AuthContext, ThemeContext
│   ├── src/services/               # Axios API layer → FastAPI
│   └── src/types/                  # shared TypeScript types
└── README.md
```

---

## Getting Started

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows  (source .venv/bin/activate on Mac/Linux)
pip install -r requirements.txt
```

Create `backend/.env` (see `.env.example`):

```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=ai_smart_knowledge_db
GEMINI_API_KEY=your_gemini_api_key        # get one free at aistudio.google.com/apikeyGEMINI_MODEL=gemini-flash-lite-latest   # fast alias (~1-2s answers)
JWT_SECRET_KEY=change_me_to_a_long_random_string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
UPLOAD_DIR=uploads
FRONTEND_URL=http://localhost:3000
MAX_UPLOAD_SIZE_MB=25
```

Run:

```bash
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

- API docs (Swagger): **http://localhost:8000/docs**
- Health check: **http://localhost:8000/api/health** — reports MongoDB + Gemini status

### 2. Frontend

```bash
cd frontend
npm install
npm run dev            # http://localhost:3000
```

The frontend reads the backend URL from `frontend/.env.local`
(`NEXT_PUBLIC_API_URL=http://localhost:8000`).

### 3. MongoDB

Any of these work — the app auto-creates its database, collections and indexes on startup:

- **Already installed locally** (this machine): runs as a Windows service on
  `mongodb://localhost:27017` — nothing to do.
- **MongoDB Atlas (free cloud)**: create a cluster, get your connection string and set
  `MONGODB_URL=mongodb+srv://<user>:<password>@<cluster>/...` in `backend/.env`.
- **Docker**: `docker run -d -p 27017:27017 --name mongo mongo:7`

### 4. Gemini API key

Free key: https://aistudio.google.com/apikey → put it in `backend/.env` as `GEMINI_API_KEY`.
The key **only** lives in the backend; the frontend never sees it — all AI calls go through
FastAPI. `gemini-flash-lite-latest` is used by default because it is fast (~1-2s per answer);
the backend automatically falls back through alternate model aliases if one is retired or
rate-limited, so model name churn no longer breaks the app.

---

## Testing

The backend has a **49-test pytest suite** (`backend/tests/`) covering registration/login,
JWT protection, notebook & resource ownership rules, file extraction (TXT/DOCX), the chat
workflow, all five AI generators, the prompt studio, settings, search and the dashboard.
The Gemini service is **mocked** — no API calls, no cost, runs in ~3 seconds:

```bash
cd backend
.venv\Scripts\python -m pytest tests/ -v
```

Tests use a throwaway database (`ai_smart_knowledge_test_db`) that is wiped before and
dropped after the run, so your real data is never touched.

To explore the API interactively, use the Swagger UI at `/docs`, or just use the app:

1. Open http://localhost:3000 → register/login
2. Create a notebook → upload a PDF/TXT or paste a YouTube URL
3. Open **AI Workspace** → sources are auto-selected → ask questions
4. Use **Summarize / Quiz / Flashcards / FAQ / Study Notes** action buttons
5. Explore **AI Studio** to experiment with prompts and settings

## Common errors

| Symptom | Fix |
|---|---|
| Frontend says "Cannot reach the server" | Start the backend on port 8000 |
| `503 Could not connect to MongoDB` | Check `MONGODB_URL` in `backend/.env`; start Mongo / use Atlas |
| `Gemini API error: 404 model not available` | Set `GEMINI_MODEL=gemini-flash-lite-latest` in `backend/.env` |
| AI responses are slow or time out | Use `gemini-flash-lite-latest` (the default) — `gemini-flash-latest` is a thinking model that can take minutes on large documents |
| `GEMINI_API_KEY is not set` | Add the key to `backend/.env` and restart uvicorn |
| Upload rejected | Allowed: PDF, DOCX, TXT, PNG/JPG/WEBP, max 25 MB (`MAX_UPLOAD_SIZE_MB`) |
| YouTube shows "no transcript" | The video has no captions; chat still works but without transcript grounding |
