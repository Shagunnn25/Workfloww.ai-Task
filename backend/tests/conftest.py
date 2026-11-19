import pytest
from fastapi.testclient import TestClient

from app.main import app

DEMO_PASSWORD = "Password123!"


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


def _login(client: TestClient, email: str) -> dict:
    resp = client.post("/auth/login", json={"email": email, "password": DEMO_PASSWORD})
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.fixture(scope="session")
def acme_manager_token(client):
    return _login(client, "manager@acme-demo.io")["access_token"]


@pytest.fixture(scope="session")
def acme_employee_token(client):
    return _login(client, "emp1@acme-demo.io")["access_token"]


@pytest.fixture(scope="session")
def globex_manager_token(client):
    return _login(client, "manager@globex-demo.io")["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
