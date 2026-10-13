"""Shared pytest fixtures.

Tests run against the real local MongoDB but use a THROWAWAY database
(ai_smart_knowledge_test_db) that is wiped before the session and dropped
after. The Gemini service is mocked - no real API calls are ever made.
"""
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import get_client
from app.main import app

TEST_DB_NAME = "ai_smart_knowledge_test_db"


@pytest.fixture(scope="session", autouse=True)
def test_database():
    """Point the app at a throwaway database for the whole test session."""
    original_db = settings.DATABASE_NAME
    settings.DATABASE_NAME = TEST_DB_NAME
    client = get_client()
    client.drop_database(TEST_DB_NAME)

    # Trigger index creation on the fresh test db.
    from app.core.indexes import create_indexes

    try:
        create_indexes()
    except Exception:
        pass

    yield client[TEST_DB_NAME]

    client.drop_database(TEST_DB_NAME)
    settings.DATABASE_NAME = original_db


@pytest.fixture(scope="session")
def client(test_database) -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def user_tokens(client) -> dict:
    """Register two users; return {email: token} for ownership tests."""
    tokens = {}
    for i, (name, email) in enumerate(
        [("Alice Tester", "alice@test.com"), ("Bob Tester", "bob@test.com")]
    ):
        response = client.post(
            "/api/auth/register",
            json={"name": name, "email": email, "password": "secret123"},
        )
        assert response.status_code == 200, response.text
        tokens[email] = response.json()["data"]["access_token"]
    return tokens


@pytest.fixture(scope="session")
def auth_headers(user_tokens) -> dict:
    """Default Authorization headers for alice."""
    return {"Authorization": f"Bearer {user_tokens['alice@test.com']}"}


@pytest.fixture(scope="session")
def bob_headers(user_tokens) -> dict:
    return {"Authorization": f"Bearer {user_tokens['bob@test.com']}"}


@pytest.fixture(scope="session")
def notebook_id(client, auth_headers) -> str:
    """A notebook owned by alice, with one processed TXT resource."""
    response = client.post(
        "/api/notebooks",
        json={"title": "Test Notebook", "description": "For tests"},
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    nb_id = response.json()["data"]["notebook"]["id"]

    upload = client.post(
        f"/api/resources/upload?notebook_id={nb_id}",
        files={"file": ("notes.txt", b"Photosynthesis converts light energy into chemical energy in plants.", "text/plain")},
        headers=auth_headers,
    )
    assert upload.status_code == 200, upload.text
    assert upload.json()["data"]["resource"]["processing_status"] == "completed"
    return nb_id


# ------------------------------------------------------------------ mocks

MOCK_CHAT_ANSWER = "Photosynthesis is the process by which plants convert light into chemical energy."


@pytest.fixture(scope="session", autouse=True)
def mock_gemini():
    """Replace every Gemini call with deterministic fakes - no real API usage."""
    from app.services import gemini_service

    gemini_service.generate_chat_response = lambda *a, **kw: MOCK_CHAT_ANSWER
    gemini_service.generate_summary = lambda *a, **kw: {
        "short_summary": "Short summary.",
        "detailed_summary": "Detailed summary.",
        "key_points": ["Point one", "Point two"],
    }
    gemini_service.generate_quiz = lambda *a, **kw: {
        "questions": [
            {
                "question": "What does photosynthesis convert?",
                "options": ["Light to chemical energy", "Water to oxygen", "Sugar to CO2", "Heat to light"],
                "correct_answer": "Light to chemical energy",
                "explanation": "Because plants transform light energy into chemical energy.",
            }
        ]
    }
    gemini_service.generate_flashcards = lambda *a, **kw: {
        "cards": [{"question": "What is photosynthesis?", "answer": "Light to chemical energy conversion", "explanation": "Core plant process."}]
    }
    gemini_service.generate_faq = lambda *a, **kw: {
        "faqs": [{"question": "What is photosynthesis?", "answer": "The conversion of light into chemical energy."}]
    }
    gemini_service.generate_study_notes = lambda *a, **kw: {
        "title": "Photosynthesis Notes",
        "overview": "How plants convert energy.",
        "important_concepts": [{"name": "Chlorophyll", "explanation": "The pigment capturing light."}],
        "key_points": ["Happens in chloroplasts"],
        "conclusion": "Foundation of plant life.",
    }
    gemini_service.generate_prompt_response = lambda *a, **kw: "Mock prompt response."
    yield
