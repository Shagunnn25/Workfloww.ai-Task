from uuid import UUID

import asyncpg


async def list_employees(conn: asyncpg.Connection, company_id: UUID):
    return await conn.fetch(
        """
        select id, full_name, email
        from public.users
        where company_id = $1 and role = 'employee'
        order by full_name
        """,
        company_id,
    )


async def get_user_by_id_and_company(conn: asyncpg.Connection, user_id: UUID, company_id: UUID):
    return await conn.fetchrow(
        """
        select id, full_name, email, role
        from public.users
        where id = $1 and company_id = $2
        """,
        user_id,
        company_id,
    )
