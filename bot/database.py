from __future__ import annotations

import asyncpg
from datetime import date
from bot.config import settings

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(settings.DATABASE_URL)
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# ── Habits ───────────────────────────────────────────────────────────────────

async def get_active_habits() -> list[dict]:
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT id, name, type FROM habits WHERE is_active = true ORDER BY created_at"
    )
    return [dict(r) for r in rows]


async def get_all_habits() -> list[dict]:
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT id, name, type, is_active, archived_at FROM habits ORDER BY created_at"
    )
    return [dict(r) for r in rows]


async def create_habit(name: str, habit_type: str) -> dict:
    pool = await get_pool()
    row = await pool.fetchrow(
        "INSERT INTO habits (name, type) VALUES ($1, $2) RETURNING id, name, type",
        name, habit_type,
    )
    return dict(row)


async def archive_habit(habit_id: str) -> bool:
    pool = await get_pool()
    result = await pool.execute(
        "UPDATE habits SET is_active = false, archived_at = CURRENT_DATE WHERE id = $1",
        habit_id,
    )
    return result == "UPDATE 1"


# ── Logs ─────────────────────────────────────────────────────────────────────

async def get_unfilled_habits(log_date: date) -> list[dict]:
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT h.id, h.name, h.type
        FROM habits h
        WHERE h.is_active = true
          AND h.id NOT IN (
              SELECT habit_id FROM habit_logs WHERE date = $1
          )
        ORDER BY h.created_at
        """,
        log_date,
    )
    return [dict(r) for r in rows]


async def upsert_log(habit_id: str, log_date: date, value: int) -> None:
    pool = await get_pool()
    await pool.execute(
        """
        INSERT INTO habit_logs (habit_id, date, value)
        VALUES ($1, $2, $3)
        ON CONFLICT (habit_id, date) DO UPDATE SET value = EXCLUDED.value
        """,
        habit_id, log_date, value,
    )


async def get_day_logs(log_date: date) -> list[dict]:
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT h.name, h.type, hl.value
        FROM habit_logs hl
        JOIN habits h ON h.id = hl.habit_id
        WHERE hl.date = $1
        ORDER BY h.created_at
        """,
        log_date,
    )
    return [dict(r) for r in rows]
