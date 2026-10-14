# AI Smart Knowledge Management System

An AI-powered knowledge and learning assistant inspired by Google AI Studio and NotebookLM.
Create notebooks, upload learning resources (PDF / DOCX / TXT / images / YouTube links), chat
with your sources through **Google Gemini**, and generate summaries, quizzes, flashcards, FAQs
and study notes.

Built as a **B.Tech Minor Project** with an intentionally simple architecture — no RAG,
embeddings or vector DB. The AI pipeline is straightforward:

```
extract resource text → store in MongoDB → build a grounded prompt → Gemini → save conversation → render answer
```

---

## Features

| Area | What works |
|---|---|
| **Auth** | Register, login, logout, JWT sessions, bcrypt hashing, profile & password update |
| **Notebooks** | CRUD, pinning, search, per-user ownership |
| **Resources** | Upload PDF / DOCX / TXT / images, text extraction, YouTube URL + transcript fetch |
| **AI Chat** | Gemini chat grounded in the sources you select, saved conversation history |
| **Generators** | Summary, Quiz, Flashcards, FAQ, Study Notes |
| **Prompt Studio** | Experiment with model, temperature and token settings |
| **History** | Conversations and generated artefacts persisted in MongoDB |
| **Extras** | Global search, dashboard stats, activity log, settings |
| **UI** | Next.js App Router, light/dark theme, responsive, animated (Framer Motion) |

## Tech Stack

**Backend** — Python 3.11+, [FastAPI](https://fastapi.tiangolo.com/), Uvicorn, PyMongo (MongoDB),
PyJWT + bcrypt, `google-generativeai` (Gemini), PyMuPDF, python-docx, Pillow, httpx, pytest.

**Frontend** — Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS v4, Framer Motion,
Lucide icons, React Hook Form + Zod, Axios.

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, CORS, routers, health check
│   │   ├── core/              # config, database, indexes, security (JWT/bcrypt)
│   │   ├── schemas/           # Pydantic models
│   │   ├── routers/           # auth, users, notebooks, resources, chat,
│   │   │                      # conversations, ai, prompts, search, settings, dashboard
│   │   ├── services/          # gemini, file extraction, storage, youtube, activity
│   │   ├── dependencies/      # JWT auth dependency
│   │   └── utils/             # ObjectId helpers, responses, validators, text utils
│   ├── scripts/               # db health check, migrations, backfills
│   ├── tests/                 # pytest suite (Gemini mocked)
│   ├── uploads/               # uploaded files (gitignored)
│   ├── requirements.txt
│   └── .env.example           # copy to .env and fill in
├── frontend/
│   ├── src/app/               # landing, login, register, forgot-password
│   │   └── (app)/             # dashboard, notebooks, workspace, studio,
│   │                          # conversations, search, profile, settings
│   ├── src/components/        # UI primitives + layout (sidebar / app shell)
│   ├── src/context/           # AuthContext, ThemeContext
│   ├── src/lib/               # Axios client
│   ├── src/services/          # typed API layer → FastAPI
│   └── src/types/             # shared TypeScript types
├── All other document/        # paper, presentation, research notes
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ (npm)
- MongoDB — local install, [MongoDB Atlas](https://www.mongodb.com/atlas) (free tier), or Docker
- A free [Google Gemini API key](https://aistudio.google.com/apikey)

### 1. MongoDB

Any of these work — the app creates its database, collections and indexes on startup:

```bash
# Docker (easiest)
docker run -d -p 27017:27017 --name mongo mongo:7

# or a local MongoDB service on mongodb://localhost:27017
# or MongoDB Atlas: set MONGODB_URL=mongodb+srv://<user>:<pass>@<cluster>/...
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # then fill in your values (drop the [TEMPLATE] line)
uvicorn app.main:app --reload --port 8000
```

`backend/.env`:

```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=ai_smart_knowledge_db

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-flash-lite-latest

JWT_SECRET_KEY=change_me_to_a_long_random_string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

UPLOAD_DIR=uploads
FRONTEND_URL=http://localhost:3000
MAX_UPLOAD_SIZE_MB=25
```

- Swagger UI: **http://localhost:8000/docs**
- Health check: **http://localhost:8000/api/health** — reports MongoDB + Gemini status

> `gemini-flash-lite-latest` is the default because it answers in ~1–2s. The backend
> automatically falls back through alternate model aliases if one is retired or rate-limited.
> The API key lives **only** in the backend — the browser never sees it; every AI call goes
> through FastAPI.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:3000
```

`frontend/.env.local` is optional — the API URL defaults to `http://localhost:8000`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testing

The backend ships with a **50-test pytest suite** (`backend/tests/`) covering registration/login, JWT
protection, notebook & resource ownership, file extraction (TXT/DOCX), the chat workflow, all
five AI generators, the prompt studio, settings, search and the dashboard.

The Gemini service is **mocked** — no API calls, no cost:

```bash
cd backend
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pytest tests/ -v
```

Tests run against a throwaway database (`ai_smart_knowledge_test_db`) that is wiped before and
dropped after the run, so your real data is never touched.

## Trying the app

1. Open http://localhost:3000 → register / login
2. Create a notebook → upload a PDF/TXT or paste a YouTube URL
3. Open **AI Workspace** → sources are auto-selected → ask questions
4. Use **Summarize / Quiz / Flashcards / FAQ / Study Notes**
5. Open **AI Studio** to experiment with prompts and model settings

## API Overview

All routes are prefixed with `/api`. `/api/auth/register` and `/api/auth/login` are public;
every other route requires an `Authorization: Bearer <token>` header.

| Prefix | Purpose |
|---|---|
| `/api/auth` | register, login, logout, current user, change password |
| `/api/users` | user profile |
| `/api/notebooks` | notebook CRUD, pin, search |
| `/api/resources` | upload file, add YouTube URL, list, get, download, delete |
| `/api/chat` | Gemini chat (grounded in selected sources) |
| `/api/conversations` | message history |
| `/api/ai` | summary, quiz, flashcards, faq, notes |
| `/api/prompts` | Prompt Studio |
| `/api/search` | global search |
| `/api/settings` | user settings |
| `/api/dashboard` | stats & activity |

## Troubleshooting

| Symptom | Fix |
|---|---|
| Frontend says "Cannot reach the server" | Start the backend on port 8000 |
| `503 Could not connect to MongoDB` | Check `MONGODB_URL` in `backend/.env`; start Mongo or use Atlas |
| `Gemini API error: 404 model not available` | Set `GEMINI_MODEL=gemini-flash-lite-latest` |
| AI responses are slow or time out | Avoid `gemini-flash-latest` (a thinking model) on large documents |
| `GEMINI_API_KEY is not set` | Add the key to `backend/.env` and restart uvicorn |
| Upload rejected | Allowed: PDF, DOCX, TXT, PNG/JPG/WEBP, max 25 MB (`MAX_UPLOAD_SIZE_MB`) |
| YouTube shows "no transcript" | The video has no captions; chat still works without transcript grounding |

## Security Notes

- `.env` files, `uploads/`, virtualenvs, `node_modules/` and `.next/` are gitignored — never
  commit secrets.
- JWT auth protects every non-auth route; records are scoped to the authenticated user.
- Change `JWT_SECRET_KEY` and get your own `GEMINI_API_KEY` before deploying.

## License

No license has been chosen yet — add a `LICENSE` file (MIT is a common pick for project work)
before publishing if you want to make reuse terms explicit.
