-- Companies: the tenant boundary. Every user and task belongs to exactly one.
create table if not exists public.companies (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    created_at timestamptz not null default now()
);
