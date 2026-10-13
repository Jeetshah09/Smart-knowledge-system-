"""Tests for AI generation endpoints (Gemini mocked)."""


def _resource_ids(client, headers, notebook_id):
    resources = client.get(
        f"/api/notebooks/{notebook_id}/resources", headers=headers
    ).json()["data"]["resources"]
    return [r["id"] for r in resources]


def test_summary_generation(client, auth_headers, notebook_id):
    response = client.post(
        "/api/ai/summary",
        json={"notebook_id": notebook_id, "resource_ids": _resource_ids(client, auth_headers, notebook_id)},
        headers=auth_headers,
    )
    assert response.status_code == 200
    content = response.json()["data"]["generated_content"]["content"]
    assert content["short_summary"]
    assert "key_points" in content


def test_quiz_generation(client, auth_headers, notebook_id):
    response = client.post(
        "/api/ai/quiz",
        json={
            "notebook_id": notebook_id,
            "resource_ids": _resource_ids(client, auth_headers, notebook_id),
            "number_of_questions": 5,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    questions = response.json()["data"]["generated_content"]["content"]["questions"]
    assert len(questions) == 1  # mock returns a single question
    q = questions[0]
    assert len(q["options"]) == 4
    assert q["correct_answer"] in q["options"]
    assert q["explanation"]


def test_flashcards_generation(client, auth_headers, notebook_id):
    response = client.post(
        "/api/ai/flashcards",
        json={
            "notebook_id": notebook_id,
            "resource_ids": _resource_ids(client, auth_headers, notebook_id),
            "number_of_cards": 5,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    cards = response.json()["data"]["generated_content"]["content"]["cards"]
    assert cards and cards[0]["question"] and cards[0]["answer"]


def test_faq_generation(client, auth_headers, notebook_id):
    response = client.post(
        "/api/ai/faq",
        json={"notebook_id": notebook_id, "resource_ids": _resource_ids(client, auth_headers, notebook_id)},
        headers=auth_headers,
    )
    assert response.status_code == 200
    faqs = response.json()["data"]["generated_content"]["content"]["faqs"]
    assert faqs and faqs[0]["question"] and faqs[0]["answer"]


def test_study_notes_generation(client, auth_headers, notebook_id):
    response = client.post(
        "/api/ai/study-notes",
        json={"notebook_id": notebook_id, "resource_ids": _resource_ids(client, auth_headers, notebook_id)},
        headers=auth_headers,
    )
    assert response.status_code == 200
    content = response.json()["data"]["generated_content"]["content"]
    assert content["overview"]
    assert content["important_concepts"]


def test_generated_content_listed_per_notebook(client, auth_headers, notebook_id):
    response = client.get(f"/api/ai/notebook/{notebook_id}", headers=auth_headers)
    assert response.status_code == 200
    types = {item["type"] for item in response.json()["data"]["items"]}
    assert {"summary", "quiz", "flashcards", "faq", "study_notes"} <= types


def test_ai_requires_resource_selection(client, auth_headers, notebook_id):
    response = client.post(
        "/api/ai/summary",
        json={"notebook_id": notebook_id, "resource_ids": []},
        headers=auth_headers,
    )
    assert response.status_code == 422  # min_length=1 on the schema


def test_ai_other_users_notebook_404(client, notebook_id, bob_headers):
    response = client.post(
        "/api/ai/summary",
        json={"notebook_id": notebook_id, "resource_ids": ["000000000000000000000000"]},
        headers=bob_headers,
    )
    assert response.status_code == 404


def test_prompt_studio_save_and_execute(client, auth_headers):
    created = client.post(
        "/api/prompts",
        json={
            "title": "Explain AI",
            "prompt": "Explain artificial intelligence simply.",
            "model": "balanced",
            "temperature": 0.5,
            "max_output_tokens": 512,
        },
        headers=auth_headers,
    )
    assert created.status_code == 200
    prompt = created.json()["data"]["prompt"]

    executed = client.post(
        f"/api/prompts/{prompt['id']}/execute", json={}, headers=auth_headers
    )
    assert executed.status_code == 200
    assert executed.json()["data"]["prompt"]["response"] == "Mock prompt response."

    listed = client.get("/api/prompts", headers=auth_headers).json()["data"]["prompts"]
    assert any(p["id"] == prompt["id"] for p in listed)

    assert client.delete(f"/api/prompts/{prompt['id']}", headers=auth_headers).status_code == 200


def test_settings_get_and_update(client, auth_headers):
    current = client.get("/api/settings", headers=auth_headers).json()["data"]["settings"]
    assert current["theme"] in ("light", "dark", "system")

    updated = client.put(
        "/api/settings",
        json={"theme": "dark", "response_style": "detailed"},
        headers=auth_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["settings"]["theme"] == "dark"

    invalid = client.put(
        "/api/settings", json={"theme": "neon"}, headers=auth_headers
    )
    assert invalid.status_code == 422


def test_search_and_dashboard(client, auth_headers):
    search = client.get("/api/search?q=photosynthesis", headers=auth_headers)
    assert search.status_code == 200
    data = search.json()["data"]
    assert len(data["resources"]) >= 1

    stats = client.get("/api/dashboard/stats", headers=auth_headers)
    assert stats.status_code == 200
    assert stats.json()["data"]["notebook_count"] >= 1
    assert isinstance(stats.json()["data"]["recent_activity"], list)
