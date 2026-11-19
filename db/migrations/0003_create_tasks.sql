create table if not exists public.tasks (
    id uuid primary key default gen_random_uuid(),
    company_id uuid not null references public.companies(id),
    title text not null,
    description text,
    status text not null default 'pending' check (status in ('pending', 'in_progress', 'completed')),
    assigned_to uuid not null references public.users(id),
    created_by uuid not null references public.users(id),
    due_date date,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_tasks_company_id on public.tasks(company_id);
create index if not exists idx_tasks_assigned_to on public.tasks(assigned_to);

-- Keep updated_at accurate on every UPDATE without relying on callers to set it.
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists trg_tasks_updated_at on public.tasks;
create trigger trg_tasks_updated_at
    before update on public.tasks
    for each row
    execute function public.set_updated_at();
