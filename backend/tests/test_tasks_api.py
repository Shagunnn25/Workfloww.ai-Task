from tests.conftest import auth_headers


def test_manager_sees_only_own_company_tasks(client, acme_manager_token):
    resp = client.get("/tasks", headers=auth_headers(acme_manager_token))
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) >= 4
    company_ids = {r["company_id"] for r in rows}
    assert len(company_ids) == 1  # every row belongs to the manager's own company


def test_employee_sees_only_own_assigned_tasks(client, acme_employee_token):
    resp = client.get("/tasks", headers=auth_headers(acme_employee_token))
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) >= 1
    assignees = {r["assigned_to"] for r in rows}
    assert len(assignees) == 1  # every row is assigned to this one employee


def test_employee_cannot_create_task(client, acme_employee_token, acme_manager_token):
    employees = client.get("/employees", headers=auth_headers(acme_manager_token)).json()
    resp = client.post(
        "/tasks",
        headers=auth_headers(acme_employee_token),
        json={"title": "Nope", "assigned_to": employees[0]["id"]},
    )
    assert resp.status_code == 403
    assert resp.json()["error"] == "forbidden"


def test_manager_create_then_assigned_employee_can_update_status(client, acme_manager_token):
    employees = client.get("/employees", headers=auth_headers(acme_manager_token)).json()
    emp1 = next(e for e in employees if e["email"] == "emp1@acme-demo.io")

    create_resp = client.post(
        "/tasks",
        headers=auth_headers(acme_manager_token),
        json={"title": "Service layer test task", "assigned_to": emp1["id"]},
    )
    assert create_resp.status_code == 201
    task = create_resp.json()
    assert task["status"] == "pending"

    login_resp = client.post("/auth/login", json={"email": "emp1@acme-demo.io", "password": "Password123!"})
    emp1_token = login_resp.json()["access_token"]

    patch_resp = client.patch(
        f"/tasks/{task['id']}",
        headers=auth_headers(emp1_token),
        json={"status": "completed"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "completed"


def test_cross_company_task_update_is_404_not_403(client, acme_manager_token, globex_manager_token):
    acme_tasks = client.get("/tasks", headers=auth_headers(acme_manager_token)).json()
    some_acme_task_id = acme_tasks[0]["id"]

    resp = client.patch(
        f"/tasks/{some_acme_task_id}",
        headers=auth_headers(globex_manager_token),
        json={"status": "completed"},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "not_found"


def test_invalid_status_value_is_422(client, acme_manager_token):
    tasks = client.get("/tasks", headers=auth_headers(acme_manager_token)).json()
    resp = client.patch(
        f"/tasks/{tasks[0]['id']}",
        headers=auth_headers(acme_manager_token),
        json={"status": "not-a-real-status"},
    )
    assert resp.status_code == 422


def test_employees_endpoint_is_manager_only(client, acme_manager_token, acme_employee_token):
    manager_resp = client.get("/employees", headers=auth_headers(acme_manager_token))
    assert manager_resp.status_code == 200
    assert len(manager_resp.json()) == 2

    employee_resp = client.get("/employees", headers=auth_headers(acme_employee_token))
    assert employee_resp.status_code == 403
