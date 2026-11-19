-- Enable RLS everywhere. Once enabled, access defaults to deny for every
-- role except the table owner (e.g. the `postgres` role our migrations and
-- seed script run as), so every grant below is explicit and additive.
alter table public.companies enable row level security;
alter table public.users enable row level security;
alter table public.tasks enable row level security;

-- A satisfying policy is necessary but not sufficient: the role also needs
-- the underlying table privilege. Supabase grants these by default for new
-- tables, but we grant explicitly so the policy file is self-contained.
grant usage on schema public to authenticated;
grant select on public.companies to authenticated;
grant select on public.users to authenticated;
grant select, insert, update on public.tasks to authenticated;

-- companies: read-only, scoped to the caller's own company.
drop policy if exists companies_select_own on public.companies;
create policy companies_select_own on public.companies
    for select
    to authenticated
    using (id = public.current_user_company_id());

-- users: same-company directory (needed for the manager's assignee dropdown
-- and to show assignee names on the task list). No insert/update/delete
-- policy exists for `authenticated`, so writes stay denied by default.
drop policy if exists users_select_same_company on public.users;
create policy users_select_same_company on public.users
    for select
    to authenticated
    using (company_id = public.current_user_company_id());

-- tasks: managers see, create and update every task in their own company.
drop policy if exists tasks_select_manager on public.tasks;
create policy tasks_select_manager on public.tasks
    for select
    to authenticated
    using (
        public.current_user_role() = 'manager'
        and company_id = public.current_user_company_id()
    );

drop policy if exists tasks_insert_manager on public.tasks;
create policy tasks_insert_manager on public.tasks
    for insert
    to authenticated
    with check (
        public.current_user_role() = 'manager'
        and company_id = public.current_user_company_id()
    );

drop policy if exists tasks_update_manager on public.tasks;
create policy tasks_update_manager on public.tasks
    for update
    to authenticated
    using (
        public.current_user_role() = 'manager'
        and company_id = public.current_user_company_id()
    )
    with check (
        public.current_user_role() = 'manager'
        and company_id = public.current_user_company_id()
    );

-- tasks: employees see and update only tasks assigned to them. The API only
-- ever sends {"status": ...} in an employee's PATCH body, so this row-level
-- scope is sufficient -- there's no separate column that needs locking down.
drop policy if exists tasks_select_employee on public.tasks;
create policy tasks_select_employee on public.tasks
    for select
    to authenticated
    using (
        public.current_user_role() = 'employee'
        and assigned_to = auth.uid()
    );

drop policy if exists tasks_update_employee on public.tasks;
create policy tasks_update_employee on public.tasks
    for update
    to authenticated
    using (
        public.current_user_role() = 'employee'
        and assigned_to = auth.uid()
    )
    with check (
        public.current_user_role() = 'employee'
        and assigned_to = auth.uid()
    );
