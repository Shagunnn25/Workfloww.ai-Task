-- App-level user profile, 1:1 with a Supabase Auth user (auth.users).
-- id is NOT generated here: it must equal the matching auth.users.id so the
-- caller's JWT ("sub" claim, exposed as auth.uid()) joins straight to this row.
create table if not exists public.users (
    id uuid primary key references auth.users(id) on delete cascade,
    company_id uuid not null references public.companies(id),
    email text not null unique,
    full_name text not null,
    role text not null check (role in ('manager', 'employee')),
    created_at timestamptz not null default now()
);

create index if not exists idx_users_company_id on public.users(company_id);
