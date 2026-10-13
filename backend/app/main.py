"""AI Smart Knowledge Management System - FastAPI application entry point."""
import logging

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import DatabaseNotConnected
from app.core.indexes import create_indexes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

app = FastAPI(
    title="AI Smart Knowledge Management System API",
    description="Backend for an AI knowledge and learning assistant (FastAPI + MongoDB + Gemini).",
    version="1.0.0",
)

# CORS - allow the Next.js frontend.
frontend_origins = [origin.strip() for origin in settings.FRONTEND_URL.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins + ["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from app.routers import ai, auth, chat, conversations, dashboard, notebooks, prompts, resources, search, settings as settings_router, users  # noqa: E402

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(notebooks.router)
app.include_router(resources.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(ai.router)
app.include_router(prompts.router)
app.include_router(search.router)
app.include_router(settings_router.router)
app.include_router(dashboard.router)


@app.on_event("startup")
def startup() -> None:
    try:
        create_indexes()
        logger.info("MongoDB connected and indexes ensured.")
    except DatabaseNotConnected as exc:
        logger.warning("MongoDB not available at startup: %s", exc)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Index creation failed: %s", exc)


@app.exception_handler(DatabaseNotConnected)
async def db_not_connected_handler(request: Request, exc: DatabaseNotConnected):
    return JSONResponse(
        status_code=503,
        content={"success": False, "message": str(exc), "data": None},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error.", "data": None},
    )


@app.get("/")
def root():
    return {"success": True, "message": "AI Smart Knowledge Management System API", "data": {"docs": "/docs"}}


@app.get("/api/health")
def health():
    """Health check that also reports MongoDB and Gemini configuration status."""
    db_ok = False
    db_message = "connected"
    try:
        from app.core.database import get_database

        get_database()
        db_ok = True
    except DatabaseNotConnected as exc:
        db_message = str(exc)

    return {
        "success": True,
        "message": "API is running",
        "data": {
            "database": {"connected": db_ok, "message": db_message},
            "gemini_configured": bool(settings.GEMINI_API_KEY),
            "gemini_model": settings.GEMINI_MODEL,
        },
    }
