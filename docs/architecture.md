# Architecture notes

## Request flow (authenticated endpoints)

1. Frontend sends `Authorization: Bearer <access_token>` (obtained from `POST /auth/login`, which itself proxies to Supabase Auth).
2. `app/core/security.py` verifies the token's signature against Supabase's public JWKS (`ES256`) and checks `aud == "authenticated"`. No shared secret is involved.
3. `app/core/deps.get_request_context` acquires one pooled DB connection, opens a transaction, and runs:
   ```sql
   SET LOCAL ROLE authenticated;
   SELECT set_config('request.jwt.claims', '{"sub": "<user-id>", "role": "authenticated"}', true);
   ```
   This makes `auth.uid()` resolve correctly for the rest of the transaction, and switches off the pool's own role (which owns the tables and therefore bypasses RLS).
4. The route calls a **service** (business rules: who's allowed to do what), which calls a **repository** (plain SQL, no business logic). The route itself stays thin — it only translates HTTP in and out.
5. Every row the repository returns has already been filtered by Postgres RLS policies, not just application code — see `docs/database.md`.
6. The transaction commits when the request finishes successfully, or rolls back if an exception (including an `HTTPException`) propagates out.

## Why not an ORM

Three tables, all read through two or three shapes of query (join tasks to the assignee's name, a couple of inserts/updates). Raw SQL via `asyncpg` keeps the RLS-related session setup (`SET LOCAL ROLE`, `set_config`) and the SQL itself in plain view, which matters more here than ORM convenience would.

## Why JWKS instead of the legacy JWT secret

This Supabase project signs session tokens asymmetrically (`ES256`); the legacy shared HS256 secret exists on the dashboard but isn't what's actually used to sign issued tokens. Verifying against the project's JWKS (`/auth/v1/.well-known/jwks.json`) works regardless of which signing mode a given Supabase project uses, and the backend never has to hold a key capable of minting tokens.

## Frontend

- No router: there are only three screens (login, manager, employee) and no deep-linking requirement, so `App.tsx` just branches on session state.
- Session (JWT + role + name) lives in `sessionStorage`, not `localStorage`, so it's cleared when the tab closes. The frontend's role branching is UX only — the backend and RLS are what actually enforce access, so a tampered client gains nothing.
- The API client (`src/api/client.ts`) is a single typed `fetch` wrapper; all `/api/*.ts` modules are thin typed functions over it, matching the backend's routes/services/repository split in spirit (one place that knows about HTTP, one place that knows about each resource).

## Folder structure

```
/backend
  app/
    api/          # FastAPI routers (thin)
    services/     # business rules, role checks
    repositories/ # raw SQL, no business logic
    models/       # Pydantic request/response schemas
    core/         # config, DB pool, JWT verification, per-request context
  scripts/        # check_db.py
  tests/          # pytest
/db
  migrations/     # versioned, applied in filename order
  queries/        # example queries (not run by the app)
  seed/           # demo data + Supabase Auth user creation
/frontend
  src/
    types/        # shared TS interfaces
    api/          # typed fetch wrapper + per-resource functions
    utils/        # pure functions (filtering, completion %) + their tests
    components/   # LoginView, ManagerView, EmployeeView, StatusFilter
    context/      # auth session state
/docs
```
