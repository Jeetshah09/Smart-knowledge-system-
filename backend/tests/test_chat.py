"""Tests for the chat workflow (Gemini mocked)."""


def _first_resource_id(client, headers, notebook_id):
    resources = client.get(
        f"/api/notebooks/{notebook_id}/resources", headers=headers
    ).json()["data"]["resources"]
    return resources[0]["id"]


def test_chat_success_creates_conversation(client, auth_headers, notebook_id):
    resource_id = _first_resource_id(client, auth_headers, notebook_id)
    response = client.post(
        "/api/chat",
        json={
            "notebook_id": notebook_id,
            "message": "What is photosynthesis?",
            "resource_ids": [resource_id],
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["response"]  # mocked answer
    assert data["resources_used"] == 1
    assert data["conversation_id"]


def test_chat_reuses_conversation(client, auth_headers, notebook_id):
    resource_id = _first_resource_id(client, auth_headers, notebook_id)
    first = client.post(
        "/api/chat",
        json={"notebook_id": notebook_id, "message": "Hi", "resource_ids": [resource_id]},
        headers=auth_headers,
    ).json()["data"]
    second = client.post(
        "/api/chat",
        json={
            "notebook_id": notebook_id,
            "message": "Continue",
            "resource_ids": [resource_id],
            "conversation_id": first["conversation_id"],
        },
        headers=auth_headers,
    ).json()["data"]
    assert second["conversation_id"] == first["conversation_id"]

    messages = client.get(
        f"/api/conversations/{first['conversation_id']}/messages", headers=auth_headers
    ).json()["data"]["messages"]
    assert len(messages) == 4  # 2 exchanges persisted in order
    assert [m["role"] for m in messages] == ["user", "assistant", "user", "assistant"]


def test_chat_stores_prompt_in_prompts_collection(client, auth_headers, notebook_id):
    """Every AI Workspace prompt must be persisted in `prompts`, not just Studio ones."""
    resource_id = _first_resource_id(client, auth_headers, notebook_id)
    message = "Store this workspace prompt in the prompts collection"
    response = client.post(
        "/api/chat",
        json={
            "notebook_id": notebook_id,
            "message": message,
            "resource_ids": [resource_id],
        },
        headers=auth_headers,
    )
    assert response.status_code == 200

    prompts = client.get("/api/prompts", headers=auth_headers).json()["data"]["prompts"]
    stored = [p for p in prompts if p["prompt"] == message]
    assert stored, "workspace prompt was not stored in the prompts collection"
    assert stored[0]["source"] == "workspace"
    assert stored[0]["response"]  # AI answer attached after generation


def test_chat_empty_resource_ids_uses_all_sources(client, auth_headers, notebook_id):
    """Empty resource_ids means 'use every source in the notebook' by design."""
    response = client.post(
        "/api/chat",
        json={"notebook_id": notebook_id, "message": "Hello?", "resource_ids": []},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["resources_used"] >= 1


def test_chat_with_bogus_resource_ids_rejected(client, auth_headers, notebook_id):
    response = client.post(
        "/api/chat",
        json={
            "notebook_id": notebook_id,
            "message": "Hello?",
            "resource_ids": ["000000000000000000000000"],
        },
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_chat_other_users_notebook_404(client, notebook_id, bob_headers):
    response = client.post(
        "/api/chat",
        json={"notebook_id": notebook_id, "message": "Hi", "resource_ids": []},
        headers=bob_headers,
    )
    assert response.status_code in (400, 404)


def test_chat_requires_auth(client, notebook_id):
    response = client.post(
        "/api/chat",
        json={"notebook_id": notebook_id, "message": "Hi", "resource_ids": []},
    )
    assert response.status_code == 401


def test_conversation_rename_and_delete(client, auth_headers, notebook_id):
    resource_id = _first_resource_id(client, auth_headers, notebook_id)
    conv = client.post(
        "/api/chat",
        json={"notebook_id": notebook_id, "message": "History test", "resource_ids": [resource_id]},
        headers=auth_headers,
    ).json()["data"]["conversation_id"]

    renamed = client.patch(
        f"/api/conversations/{conv}", json={"title": "Renamed"}, headers=auth_headers
    )
    assert renamed.status_code == 200
    assert renamed.json()["data"]["conversation"]["title"] == "Renamed"

    assert client.delete(f"/api/conversations/{conv}", headers=auth_headers).status_code == 200
    assert client.get(f"/api/conversations/{conv}/messages", headers=auth_headers).status_code == 404
