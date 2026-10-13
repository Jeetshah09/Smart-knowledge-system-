"""Tests for authentication endpoints."""


def test_register_success(client):
    response = client.post(
        "/api/auth/register",
        json={"name": "Carol", "email": "carol@test.com", "password": "secret123"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["user"]["email"] == "carol@test.com"
    assert "access_token" in data
    assert "password_hash" not in data["user"]  # never leak hashes


def test_register_duplicate_email(client):
    payload = {"name": "Carol Two", "email": "carol@test.com", "password": "secret123"}
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 409


def test_register_invalid_email(client):
    response = client.post(
        "/api/auth/register",
        json={"name": "Bad Email", "email": "not-an-email", "password": "secret123"},
    )
    assert response.status_code == 422


def test_register_short_password(client):
    response = client.post(
        "/api/auth/register",
        json={"name": "Shorty", "email": "shorty@test.com", "password": "abc"},
    )
    assert response.status_code == 422


def test_login_success(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "carol@test.com", "password": "secret123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]


def test_login_wrong_password(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "carol@test.com", "password": "wrongpass"},
    )
    assert response.status_code == 401


def test_login_unknown_user(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "ghost@test.com", "password": "whatever1"},
    )
    assert response.status_code == 401


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_with_token(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["user"]["email"] == "alice@test.com"


def test_me_with_invalid_token(client):
    response = client.get(
        "/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401


def test_update_profile(client, auth_headers):
    response = client.put("/api/auth/me", json={"name": "Alice Updated"}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["user"]["name"] == "Alice Updated"


def test_change_password(client):
    login = client.post(
        "/api/auth/login", json={"email": "carol@test.com", "password": "secret123"}
    )
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}

    # wrong current password
    bad = client.post(
        "/api/auth/change-password",
        json={"current_password": "nope", "new_password": "newsecret1"},
        headers=headers,
    )
    assert bad.status_code == 400

    # correct change, then login with the new password
    good = client.post(
        "/api/auth/change-password",
        json={"current_password": "secret123", "new_password": "newsecret1"},
        headers=headers,
    )
    assert good.status_code == 200
    relogin = client.post(
        "/api/auth/login", json={"email": "carol@test.com", "password": "newsecret1"}
    )
    assert relogin.status_code == 200


def test_logout(client, auth_headers):
    response = client.post("/api/auth/logout", headers=auth_headers)
    assert response.status_code == 200
