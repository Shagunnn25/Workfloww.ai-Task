# Database notes

## Schema

- **companies** `(id, name, created_at)` — the tenant boundary.
- **users** `(id, company_id, email, full_name, role, created_at)` — `id` is a foreign key to `auth.users(id)`, not independently generated, so a caller's JWT `sub` claim (exposed as `auth.uid()`) joins straight to this row. `role` is `manager` or `employee`.
- **tasks** `(id, company_id, title, description, status, assigned_to, created_by, due_date, created_at, updated_at)` — `status` is `pending` / `in_progress` / `completed`. `updated_at` is maintained by a trigger, never set by callers. Indexed on `company_id` and `assigned_to`.

Migrations are plain numbered `.sql` files in `/db/migrations`, applied in order by `db/apply_migrations.py` (no `psql` dependency, no migration framework — just `CREATE TABLE IF NOT EXISTS` / `CREATE OR REPLACE` so re-running is safe).

## RLS policies (`0005_rls_policies.sql`)

Two SQL helper functions do the role/company lookup once, as `SECURITY DEFINER` so they bypass RLS themselves (otherwise a policy on `users` calling back into `users` to find the caller's own row would recurse into itself):

- `current_user_company_id()` — the caller's own `company_id`.
- `current_user_role()` — the caller's own `role`.

| Table | Policy | Rule |
|---|---|---|
| companies | select | own company only |
| users | select | same company (needed for the assignee dropdown and to show names) |
| tasks | select (manager) | `role = 'manager' AND company_id = own company` |
| tasks | select (employee) | `role = 'employee' AND assigned_to = auth.uid()` |
| tasks | insert | manager, own company only |
| tasks | update (manager) | manager, own company only |
| tasks | update (employee) | `assigned_to = auth.uid()` only |

No insert/update/delete policy exists for `users` or `companies` under the `authenticated` role, so those stay read-only from the API's perspective by default (RLS denies what has no matching policy).

The backend only ever sends `{"status": ...}` in an employee's `PATCH` body, so the row-level `assigned_to = auth.uid()` scope above is sufficient — there's no separate column that needs locking down with column-level grants.

## Example queries

`/db/queries/example_queries.sql` has the two queries the assessment asks for: fetch tasks by company, and a completed/pending count per company (via `FILTER`).

## Seed data

`db/seed/seed.py` creates 2 companies, each with 1 manager + 2 employees + 4 tasks, and is re-runnable (it deletes any previous run's rows by company name first). It creates real Supabase Auth users via the Admin API — the only place in this project the Supabase **secret key** is used, and it's kept in `db/.env`, separate from `backend/.env`, so it's never reachable from the running API.

Demo login (password is the same for all seeded accounts): see the README's "Demo accounts" section.
