-- Helper functions used by the RLS policies in 0005.
--
-- SECURITY DEFINER + a fixed search_path: these run with the privileges of
-- their owner (the migration role), not the calling role, so they can read
-- public.users directly instead of going back through RLS. Without this, a
-- policy on `users` that calls one of these to find the caller's own
-- company/role would recurse into the `users` policy it's defining.
create or replace function public.current_user_company_id()
returns uuid
language sql
stable
security definer
set search_path = public
as $$
    select company_id from public.users where id = auth.uid();
$$;

create or replace function public.current_user_role()
returns text
language sql
stable
security definer
set search_path = public
as $$
    select role from public.users where id = auth.uid();
$$;
