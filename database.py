import aiosqlite
from datetime import datetime

DB_PATH = "bot.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id    INTEGER PRIMARY KEY,
                username   TEXT,
                ref_by     INTEGER,
                ref_count  INTEGER DEFAULT 0,
                os         TEXT    DEFAULT 'ios',
                used_trial INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER,
                plan       TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER,
                label      TEXT UNIQUE,
                amount     REAL,
                plan       TEXT,
                status     TEXT DEFAULT 'pending',
                os         TEXT DEFAULT 'ios',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER,
                username   TEXT,
                rating     INTEGER,
                text       TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS promocodes (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                code       TEXT UNIQUE,
                type       TEXT,
                value      INTEGER,
                uses_left  INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Миграции
        for col, definition in [
            ("os",         "TEXT DEFAULT 'ios'"),
            ("used_trial", "INTEGER DEFAULT 0"),
        ]:
            try:
                await db.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
            except Exception:
                pass
        try:
            await db.execute("ALTER TABLE payments ADD COLUMN os TEXT DEFAULT 'ios'")
        except Exception:
            pass
        await db.commit()

# ── Пользователи ──────────────────────────────────────────────────────────

async def add_user(user_id: int, username: str, ref_by: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, ref_by) VALUES (?,?,?)",
            (user_id, username, ref_by)
        )
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as cur:
            return await cur.fetchone()

async def get_user_os(user_id: int) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT os FROM users WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else "ios"

async def set_user_os(user_id: int, os: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET os=? WHERE user_id=?", (os, user_id))
        await db.commit()

async def has_used_trial(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT used_trial FROM users WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return bool(row[0]) if row else False

async def activate_trial(user_id: int, os: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET used_trial=1, os=? WHERE user_id=?", (os, user_id))
        await db.execute("""
            INSERT INTO subscriptions (user_id, plan, expires_at)
            VALUES (?, 'trial', datetime('now', '3 days'))
        """, (user_id,))
        await db.commit()

async def increment_ref(ref_by: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET ref_count=ref_count+1 WHERE user_id=?", (ref_by,)
        )
        await db.commit()

async def get_ref_count(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT ref_count FROM users WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0

async def get_all_user_ids() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cur:
            return [r[0] for r in await cur.fetchall()]

# ── Подписки ──────────────────────────────────────────────────────────────

async def get_active_subscription(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT * FROM subscriptions
            WHERE user_id=? AND expires_at > CURRENT_TIMESTAMP
            ORDER BY expires_at DESC LIMIT 1
        """, (user_id,)) as cur:
            return await cur.fetchone()

async def activate_subscription(user_id: int, plan: str):
    plan_days = {"1m": 30, "3m": 90, "1y": 365}
    days = plan_days.get(plan, 30)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO subscriptions (user_id, plan, expires_at)
            VALUES (?, ?, datetime('now', ? || ' days'))
        """, (user_id, plan, str(days)))
        await db.commit()

async def activate_subscription_days(user_id: int, days: int, plan: str = "promo"):
    """Активация на произвольное количество дней (для промокодов)"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO subscriptions (user_id, plan, expires_at)
            VALUES (?, ?, datetime('now', ? || ' days'))
        """, (user_id, plan, str(days)))
        await db.commit()

async def get_expiring_soon() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT user_id, expires_at FROM subscriptions
            WHERE expires_at > CURRENT_TIMESTAMP
              AND expires_at <= datetime('now', '3 days')
            GROUP BY user_id
        """) as cur:
            return await cur.fetchall()

# ── Платежи ───────────────────────────────────────────────────────────────

async def create_payment(user_id: int, label: str, amount: float, plan: str, os: str = "ios"):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO payments (user_id, label, amount, plan, os) VALUES (?,?,?,?,?)",
            (user_id, label, amount, plan, os)
        )
        await db.commit()

async def get_payment_by_label(label: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM payments WHERE label=?", (label,)) as cur:
            return await cur.fetchone()

async def confirm_payment(label: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE payments SET status='paid' WHERE label=?", (label,))
        await db.commit()

async def reject_payment(label: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE payments SET status='rejected' WHERE label=?", (label,))
        await db.commit()

# ── Отзывы ────────────────────────────────────────────────────────────────

async def add_review(user_id: int, username: str, rating: int, text: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO reviews (user_id, username, rating, text) VALUES (?,?,?,?)",
            (user_id, username, rating, text)
        )
        await db.commit()

async def get_reviews(limit: int = 5) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT username, rating, text, created_at FROM reviews ORDER BY id DESC LIMIT ?",
            (limit,)
        ) as cur:
            return await cur.fetchall()

async def get_avg_rating() -> float:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT AVG(rating), COUNT(*) FROM reviews") as cur:
            row = await cur.fetchone()
            return round(row[0] or 0, 1), row[1]

async def user_has_reviewed(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id FROM reviews WHERE user_id=?", (user_id,)) as cur:
            return await cur.fetchone() is not None

# ── Промокоды ─────────────────────────────────────────────────────────────

async def create_promo(code: str, type_: str, value: int, uses: int = 1):
    """
    type_ = 'discount' (скидка в %) или 'days' (бесплатные дни)
    value = число (процент или дни)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO promocodes (code, type, value, uses_left) VALUES (?,?,?,?)",
            (code.upper(), type_, value, uses)
        )
        await db.commit()

async def get_promo(code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM promocodes WHERE code=? AND uses_left > 0",
            (code.upper(),)
        ) as cur:
            return await cur.fetchone()

async def use_promo(code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE promocodes SET uses_left=uses_left-1 WHERE code=?",
            (code.upper(),)
        )
        await db.commit()

async def list_promos() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT code, type, value, uses_left FROM promocodes") as cur:
            return await cur.fetchall()

# ── Статистика ────────────────────────────────────────────────────────────

async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total_users = (await cur.fetchone())[0]
        async with db.execute("""
            SELECT COUNT(*) FROM subscriptions WHERE expires_at > CURRENT_TIMESTAMP
        """) as cur:
            active_subs = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM payments WHERE status='paid'") as cur:
            paid_payments = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM payments WHERE status='pending_review'") as cur:
            pending_payments = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT COALESCE(SUM(amount),0) FROM payments WHERE status='paid'"
        ) as cur:
            total_revenue = int((await cur.fetchone())[0])
        async with db.execute("SELECT COUNT(*) FROM reviews") as cur:
            total_reviews = (await cur.fetchone())[0]
    return {
        "total_users":      total_users,
        "active_subs":      active_subs,
        "paid_payments":    paid_payments,
        "pending_payments": pending_payments,
        "total_revenue":    total_revenue,
        "total_reviews":    total_reviews,
    }
