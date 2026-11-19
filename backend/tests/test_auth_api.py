def test_login_success_returns_role_and_token(client):
    resp = client.post("/auth/login", json={"email": "manager@acme-demo.io", "password": "Password123!"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["role"] == "manager"
    assert body["access_token"]


def test_login_wrong_password_is_401_with_consistent_shape(client):
    resp = client.post("/auth/login", json={"email": "manager@acme-demo.io", "password": "wrong"})
    assert resp.status_code == 401
    assert resp.json() == {"error": "unauthorized", "message": "Invalid email or password"}


def test_login_invalid_email_format_is_422(client):
    resp = client.post("/auth/login", json={"email": "not-an-email", "password": "x"})
    assert resp.status_code == 422
    assert resp.json()["error"] == "validation_error"


def test_tasks_requires_auth(client):
    resp = client.get("/tasks")
    assert resp.status_code == 401
