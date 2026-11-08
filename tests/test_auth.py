from app.config import settings
from tests.conftest import auth_headers, register


def test_register_returns_user_without_password(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "Alice@Example.com", "username": "alice", "password": "correct-horse-1"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"
    assert "password" not in str(body)


def test_register_rejects_duplicate_username_and_email(client):
    register(client, "alice")
    taken_name = client.post(
        "/api/auth/register", json={"email": "other@example.com", "username": "alice", "password": "password-123"}
    )
    assert taken_name.status_code == 409
    taken_email = client.post(
        "/api/auth/register", json={"email": "ALICE@example.com", "username": "alice2", "password": "password-123"}
    )
    assert taken_email.status_code == 409


def test_register_validates_input(client):
    short_password = client.post(
        "/api/auth/register", json={"email": "a@example.com", "username": "alice", "password": "short"}
    )
    assert short_password.status_code == 422
    bad_username = client.post(
        "/api/auth/register", json={"email": "a@example.com", "username": "no spaces!", "password": "password-123"}
    )
    assert bad_username.status_code == 422


def test_login_with_username_or_email(client):
    register(client, "alice")
    for login in ("alice", "alice@example.com", "ALICE@example.com"):
        response = client.post("/api/auth/token", data={"username": login, "password": "correct-horse-1"})
        assert response.status_code == 200, login
        assert response.json()["token_type"] == "bearer"


def test_login_rejects_wrong_password(client):
    register(client, "alice")
    response = client.post("/api/auth/token", data={"username": "alice", "password": "wrong-password"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password."


def test_me_requires_a_valid_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-token"}).status_code == 401
    headers = auth_headers(client, "alice")
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "alice"


def test_login_is_rate_limited_per_ip(client, monkeypatch):
    monkeypatch.setattr(settings, "login_attempts_per_minute", 3)
    register(client, "alice")
    codes = [
        client.post("/api/auth/token", data={"username": "alice", "password": "wrong"}).status_code for _ in range(4)
    ]
    assert codes == [401, 401, 401, 429]
    blocked = client.post("/api/auth/token", data={"username": "alice", "password": "correct-horse-1"})
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) > 0
