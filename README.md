# Multi-Tenant Task Management App

A basic task management system for a multi-company environment. Managers assign tasks to employees within their own company; employees update the status of their own tasks. Users can never access another company's data, even by tampering with request parameters — enforcement happens at both the API layer and the database layer (Postgres Row Level Security).

## Tech stack

- **Backend:** FastAPI (Python), Pydantic, `asyncpg`
- **Database:** Supabase Postgres, accessed via the transaction pooler, with Row Level Security
- **Auth:** Supabase Auth (email/password), tokens verified against Supabase's JWKS
- **Frontend:** React + TypeScript (Vite), strict mode, no UI framework
- **Tests:** pytest (backend), Vitest (frontend)

## Folder structure

```
/backend   FastAPI app (routes -> services -> repositories), pytest tests
/db        SQL migrations, example queries, seed script
/frontend  React + TypeScript app, Vitest tests
/docs      Per-stage build notes, architecture and database reference
```

See `docs/architecture.md` and `docs/database.md` for more detail than this README.

## Setup

### Prerequisites

- Python 3.11+ (tested on 3.13)
- Node.js 18+
- A Supabase project (Postgres + Auth)

### Backend

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # then fill in the values below
```

Fill in `backend/.env`:

| Variable | Where to find it |
|---|---|
| `DATABASE_URL` | Supabase dashboard → Project Settings → Database → Connection string → **Transaction** pooler mode, port `6543` |
| `SUPABASE_URL` | Project Settings → API Keys → Project URL (or `https://<project-ref>.supabase.co`, where `<project-ref>` is the user segment of `DATABASE_URL`) |
| `SUPABASE_ANON_KEY` | Project Settings → API Keys → `anon`/publishable key |
| `FRONTEND_ORIGIN` | Defaults to `http://localhost:5173`, only origin allowed by CORS |

Apply migrations, then run the connectivity check and the app:

```bash
# from the repo root
backend/.venv/bin/python db/apply_migrations.py
backend/.venv/bin/python -m scripts.check_db   # run from inside backend/
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000
```

`GET http://localhost:8000/health` should return `{"status":"ok","database":"connected"}`. Interactive API docs: `http://localhost:8000/docs`.

### Database: migrations and seed data

```bash
# from the repo root, after backend/.env is filled in
backend/.venv/bin/python db/apply_migrations.py
```

The seed script creates real Supabase Auth users (so the demo accounts can actually log in), which needs the Supabase **secret key** — kept separate from the backend's own `.env` since the running API must never hold it:

```bash
cp db/.env.example db/.env   # fill in SUPABASE_URL and SUPABASE_SECRET_KEY (Project Settings -> API Keys)
backend/.venv/bin/python db/seed/seed.py
```

It's safe to re-run — it deletes any previous seed data (matched by company name) before inserting fresh rows.

#### Demo accounts

Password for every seeded account: **`Password123!`**

| Email | Role | Company |
|---|---|---|
| `manager@acme-demo.io` | manager | Acme Corporation |
| `emp1@acme-demo.io` | employee | Acme Corporation |
| `emp2@acme-demo.io` | employee | Acme Corporation |
| `manager@globex-demo.io` | manager | Globex Inc |
| `emp1@globex-demo.io` | employee | Globex Inc |
| `emp2@globex-demo.io` | employee | Globex Inc |

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_BASE_URL, defaults to http://localhost:8000
npm run dev
```

Open the printed local URL (typically `http://localhost:5173`) and log in with any demo account above.

### Running tests

```bash
# backend (from /backend, with .env filled in -- tests run against the real seeded DB)
.venv/bin/python -m pytest -v

# frontend (from /frontend)
npm run test
```

## API reference

All endpoints except `/health` and `/auth/login` require `Authorization: Bearer <access_token>`. Errors are always `{"error": "<code>", "message": "<text>"}`.

| Method | Path | Who | Description |
|---|---|---|---|
| GET | `/health` | anyone | API status + a real `SELECT 1` round-trip |
| POST | `/auth/login` | anyone | `{email, password}` -> `{access_token, token_type, role, full_name}` |
| GET | `/tasks` | manager or employee | All tasks in the caller's company (manager), or only the caller's own assigned tasks (employee) |
| POST | `/tasks` | manager | `{title, description?, assigned_to, due_date?}` -> created task (201) |
| PATCH | `/tasks/{id}` | manager or employee | `{status}` -> updated task. 404 (not 403) if the task doesn't exist *or* isn't visible to the caller |
| GET | `/employees` | manager | Employees in the caller's own company, for the assign dropdown |

Status codes used: `200`, `201`, `400` (e.g. assigning to someone outside your company), `401` (missing/invalid token, bad login), `403` (wrong role), `404` (task not found or not visible), `422` (validation error).

## Assumptions

- Supabase Auth handles passwords and sessions; there's no separate custom-auth table.
- `PATCH /tasks/{id}` only ever changes `status` for both roles, matching the scope ("update task status") — there's no general task-edit endpoint.
- No pagination, given the tiny seed dataset.
- `due_date` is optional.
- Tests run against the real seeded Supabase database rather than a separate test database, given the project's scope and time constraints — `test_tasks_api.py` creates one extra task per run, which is fine for this scale but wouldn't be the right call long-term.

## Security & tenant isolation

Cross-company access is prevented at two independent layers, so a bug in one doesn't expose the other:

1. **Identity never comes from the client.** `company_id` and the caller's role are never accepted from the request body or query params. Every request carries a Supabase-issued JWT; the backend verifies its signature against Supabase's public JWKS and reads the user id from the `sub` claim. From there, the caller's `company_id` and `role` are looked up server-side from `public.users` — the one row that table's own RLS policy always allows the caller to read (their own).

2. **Row Level Security enforces isolation at the database itself**, not just in application code. Per request, inside one transaction, the backend runs `SET LOCAL ROLE authenticated` and sets `request.jwt.claims` to the verified user id — switching off the connection pool's own role, which owns the tables and would otherwise bypass RLS entirely. From that point, Postgres policies (not the FastAPI code) decide which rows a query can see or touch: a manager's queries are scoped to `company_id = their own company`, an employee's to `assigned_to = their own user id`. The service and repository layers add a second, redundant check on top (verifying an employee is in the manager's own company before allowing a task assignment, for example), but the authorization decision that actually matters for data access is made by the database.

3. **404, not 403, for inaccessible task ids.** `PATCH /tasks/{id}` runs an `UPDATE ... WHERE id = $1 RETURNING *` against a connection already scoped by RLS. If the row belongs to another company, or is assigned to a different employee, RLS simply makes it invisible — the `UPDATE` matches zero rows, and the service layer reports `404 Not Found`. A caller probing task ids can't distinguish "doesn't exist" from "exists but isn't yours," so it leaks nothing.

4. **The Supabase secret (service-role) key is never used for user-facing requests** — only by the one-off seed script (`db/seed/seed.py`), kept in a separate `db/.env` the running API never reads, to create demo Auth users.

5. **Frontend role checks are UX only.** `App.tsx` branches on the logged-in user's role to show the right screen, but that's convenience, not security — a tampered client still hits the same backend, which re-derives identity from the JWT and re-applies RLS regardless of what the UI tried to do.
