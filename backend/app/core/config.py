import os
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Settings:
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "ai_smart_knowledge_db")

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))

    # flash-lite answers in ~1-2s; the "flash-latest" alias resolves to a
    # thinking model that can take minutes and often returns empty answers.
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")


settings = Settings()
