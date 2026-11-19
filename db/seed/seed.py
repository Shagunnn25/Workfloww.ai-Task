"""Seeds 2 companies, each with 1 manager + 2 employees, plus sample tasks.

Creates real Supabase Auth users via the Admin API (needs the SECRET key --
never used by the running backend, only by this one-off setup script) so the
seeded accounts can actually log in. Re-runnable: it deletes any previous
seed data (by company name) before inserting fresh rows.

Usage (from repo root): backend/.venv/bin/python db/seed/seed.py
"""

import asyncio
import os
import pathlib
import sys
from datetime import date, timedelta

import asyncpg
import httpx
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT.parent / "backend" / ".env")
load_dotenv(ROOT / ".env")

SEED_PASSWORD = "Password123!"

COMPANIES = [
    {
        "name": "Acme Corporation",
        "manager": {"email": "manager@acme-demo.io", "full_name": "Alice Manager"},
        "employees": [
            {"email": "emp1@acme-demo.io", "full_name": "Evan Employee"},
            {"email": "emp2@acme-demo.io", "full_name": "Ella Employee"},
        ],
        "tasks": [
            {"title": "Draft Q3 report", "status": "completed", "assignee": 0, "due_in_days": -5},
            {"title": "Fix login bug", "status": "in_progress", "assignee": 0, "due_in_days": 2},
            {"title": "Update onboarding docs", "status": "pending", "assignee": 1, "due_in_days": 5},
            {"title": "Prepare client demo", "status": "completed", "assignee": 1, "due_in_days": -1},
        ],
    },
    {
        "name": "Globex Inc",
        "manager": {"email": "manager@globex-demo.io", "full_name": "Gary Manager"},
        "employees": [
            {"email": "emp1@globex-demo.io", "full_name": "Grace Employee"},
            {"email": "emp2@globex-demo.io", "full_name": "Greg Employee"},
        ],
        "tasks": [
            {"title": "Audit Q3 expenses", "status": "pending", "assignee": 0, "due_in_days": 7},
            {"title": "Migrate CI pipeline", "status": "in_progress", "assignee": 0, "due_in_days": 3},
            {"title": "Write release notes", "status": "completed", "assignee": 1, "due_in_days": -3},
            {"title": "Review vendor contract", "status": "pending", "assignee": 1, "due_in_days": 10},
        ],
    },
]


class AuthAdmin:
    def __init__(self, supabase_url: str, secret_key: str):
        self._client = httpx.Client(
            base_url=f"{supabase_url}/auth/v1/admin",
            headers={"apikey": secret_key, "Authorization": f"Bearer {secret_key}"},
            timeout=15.0,
        )

    def find_user_id_by_email(self, email: str) -> str | None:
        resp = self._client.get("/users", params={"per_page": 200})
        resp.raise_for_status()
        for user in resp.json().get("users", []):
            if user.get("email") == email:
                return user["id"]
        return None

    def delete_user(self, user_id: str) -> None:
        resp = self._client.delete(f"/users/{user_id}")
        if resp.status_code not in (200, 204, 404):
            resp.raise_for_status()

    def create_user(self, email: str, password: str, full_name: str) -> str:
        resp = self._client.post(
            "/users",
            json={
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {"full_name": full_name},
            },
        )
        resp.raise_for_status()
        return resp.json()["id"]

    def close(self) -> None:
        self._client.close()


async def reset_existing(conn: asyncpg.Connection, admin: AuthAdmin, company_names: list[str]) -> None:
    company_ids = await conn.fetch(
        "select id from public.companies where name = any($1::text[])", company_names
    )
    ids = [row["id"] for row in company_ids]
    if not ids:
        return

    user_ids = await conn.fetch("select id from public.users where company_id = any($1::uuid[])", ids)
    await conn.execute("delete from public.tasks where company_id = any($1::uuid[])", ids)
    await conn.execute("delete from public.users where company_id = any($1::uuid[])", ids)
    await conn.execute("delete from public.companies where id = any($1::uuid[])", ids)

    for row in user_ids:
        admin.delete_user(str(row["id"]))


def create_auth_user(admin: AuthAdmin, email: str, full_name: str) -> str:
    try:
        return admin.create_user(email, SEED_PASSWORD, full_name)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 422:
            existing_id = admin.find_user_id_by_email(email)
            if existing_id:
                admin.delete_user(existing_id)
                return admin.create_user(email, SEED_PASSWORD, full_name)
        raise


async def seed_company(conn: asyncpg.Connection, admin: AuthAdmin, company: dict) -> None:
    company_id = await conn.fetchval(
        "insert into public.companies (name) values ($1) returning id", company["name"]
    )

    manager_auth_id = create_auth_user(admin, company["manager"]["email"], company["manager"]["full_name"])
    manager_id = await conn.fetchval(
        """
        insert into public.users (id, company_id, email, full_name, role)
        values ($1, $2, $3, $4, 'manager')
        returning id
        """,
        manager_auth_id,
        company_id,
        company["manager"]["email"],
        company["manager"]["full_name"],
    )

    employee_ids = []
    for employee in company["employees"]:
        auth_id = create_auth_user(admin, employee["email"], employee["full_name"])
        emp_id = await conn.fetchval(
            """
            insert into public.users (id, company_id, email, full_name, role)
            values ($1, $2, $3, $4, 'employee')
            returning id
            """,
            auth_id,
            company_id,
            employee["email"],
            employee["full_name"],
        )
        employee_ids.append(emp_id)

    for task in company["tasks"]:
        await conn.execute(
            """
            insert into public.tasks
                (company_id, title, status, assigned_to, created_by, due_date)
            values ($1, $2, $3, $4, $5, $6)
            """,
            company_id,
            task["title"],
            task["status"],
            employee_ids[task["assignee"]],
            manager_id,
            date.today() + timedelta(days=task["due_in_days"]),
        )

    print(f"Seeded '{company['name']}': 1 manager, {len(employee_ids)} employees, {len(company['tasks'])} tasks.")


async def main() -> int:
    database_url = os.environ["DATABASE_URL"]
    supabase_url = os.environ["SUPABASE_URL"]
    secret_key = os.environ["SUPABASE_SECRET_KEY"]

    admin = AuthAdmin(supabase_url, secret_key)
    conn = await asyncpg.connect(dsn=database_url, statement_cache_size=0)
    try:
        await reset_existing(conn, admin, [c["name"] for c in COMPANIES])
        for company in COMPANIES:
            await seed_company(conn, admin, company)

        print("\nDemo login password for every seeded user:", SEED_PASSWORD)
        print("Emails:")
        for company in COMPANIES:
            print(f"  {company['manager']['email']} (manager, {company['name']})")
            for employee in company["employees"]:
                print(f"  {employee['email']} (employee, {company['name']})")
        return 0
    finally:
        await conn.close()
        admin.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
