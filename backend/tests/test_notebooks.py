"""Tests for notebook endpoints and ownership rules."""


def test_create_notebook(client, auth_headers):
    response = client.post(
        "/api/notebooks",
        json={"title": "Owned notebook", "description": "Alice's"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    notebook = response.json()["data"]["notebook"]
    assert notebook["title"] == "Owned notebook"
    assert notebook["resource_count"] == 0


def test_list_notebooks_only_mine(client, auth_headers, bob_headers):
    listed = client.get("/api/notebooks", headers=auth_headers).json()["data"]["notebooks"]
    assert all(nb["user_id"] not in ("", None) for nb in listed)
    # every returned notebook must be accessible via alice's token only -
    # fetch one as bob and expect 404 (bob cannot see alice's notebooks)
    target = listed[0]["id"]
    response = client.get(f"/api/notebooks/{target}", headers=bob_headers)
    assert response.status_code == 404


def test_get_notebook_requires_auth(client, notebook_id):
    assert client.get(f"/api/notebooks/{notebook_id}").status_code == 401


def test_get_other_users_notebook_404(client, notebook_id, bob_headers):
    response = client.get(f"/api/notebooks/{notebook_id}", headers=bob_headers)
    assert response.status_code == 404


def test_update_notebook(client, auth_headers):
    created = client.post(
        "/api/notebooks", json={"title": "Old title"}, headers=auth_headers
    ).json()["data"]["notebook"]
    response = client.put(
        f"/api/notebooks/{created['id']}",
        json={"title": "New title", "description": "Updated"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["notebook"]["title"] == "New title"


def test_pin_toggle(client, auth_headers):
    created = client.post(
        "/api/notebooks", json={"title": "Pin me"}, headers=auth_headers
    ).json()["data"]["notebook"]
    first = client.patch(f"/api/notebooks/{created['id']}/pin", headers=auth_headers).json()
    second = client.patch(f"/api/notebooks/{created['id']}/pin", headers=auth_headers).json()
    assert first["data"]["is_pinned"] is True
    assert second["data"]["is_pinned"] is False


def test_search_notebooks(client, auth_headers):
    client.post("/api/notebooks", json={"title": "Quantum Physics"}, headers=auth_headers)
    response = client.get("/api/notebooks/search?q=quantum", headers=auth_headers)
    assert response.status_code == 200
    titles = [nb["title"] for nb in response.json()["data"]["notebooks"]]
    assert "Quantum Physics" in titles


def test_invalid_notebook_id_format(client, auth_headers):
    response = client.get("/api/notebooks/not-a-valid-id", headers=auth_headers)
    assert response.status_code == 400


def test_delete_notebook(client, auth_headers):
    created = client.post(
        "/api/notebooks", json={"title": "Delete me"}, headers=auth_headers
    ).json()["data"]["notebook"]
    assert client.delete(f"/api/notebooks/{created['id']}", headers=auth_headers).status_code == 200
    assert client.get(f"/api/notebooks/{created['id']}", headers=auth_headers).status_code == 404
