-- Fetch all tasks belonging to a given company (replace $1 with a company id).
select
    t.id,
    t.title,
    t.status,
    t.assigned_to,
    u.full_name as assignee_name,
    t.due_date,
    t.created_at
from public.tasks t
join public.users u on u.id = t.assigned_to
where t.company_id = $1
order by t.created_at desc;

-- Count completed vs pending tasks per company.
select
    company_id,
    count(*) filter (where status = 'completed') as completed_count,
    count(*) filter (where status = 'pending') as pending_count
from public.tasks
group by company_id;
