import aiosqlite
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
import os

DATABASE_PATH = os.getenv("DATABASE_PATH", "./database.sqlite")


async def init_database():
    """Initialize SQLite database with required schema."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id TEXT UNIQUE NOT NULL,
                username TEXT,
                role TEXT CHECK(role IN ('admin', 'user', 'pending')) DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_banned INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS vms (
                detector_id TEXT PRIMARY KEY,
                hypervisor_name TEXT NOT NULL UNIQUE,
                secret_key TEXT NOT NULL UNIQUE,
                assigned_user_id TEXT,
                status TEXT CHECK(status IN ('online', 'offline', 'pending_shutdown')) DEFAULT 'offline',
                last_heartbeat DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(assigned_user_id) REFERENCES users(telegram_id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS failed_auth (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detector_id TEXT,
                attempt_time DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_vm_status ON vms(status);
            CREATE INDEX IF NOT EXISTS idx_user_telegram_id ON users(telegram_id);
        """)
        await db.commit()


async def register_user(telegram_id: str, username: str) -> bool:
    """Register a new user (starts as pending)."""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                "INSERT INTO users (telegram_id, username, role) VALUES (?, ?, ?)",
                (telegram_id, username, "pending")
            )
            await db.commit()
        return True
    except sqlite3.IntegrityError:
        return False


async def get_user(telegram_id: str) -> Optional[Dict]:
    """Retrieve user info by Telegram ID."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, telegram_id, username, role, is_banned FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_all_users() -> List[Dict]:
    """Retrieve all users."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT telegram_id, username, role, is_banned FROM users ORDER BY id DESC"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def promote_to_admin(telegram_id: str) -> bool:
    """Promote a user to admin role."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "UPDATE users SET role = 'admin' WHERE telegram_id = ?",
            (telegram_id,)
        )
        await db.commit()
        return cursor.rowcount > 0


async def approve_to_user(telegram_id: str) -> bool:
    """Approve a pending user to regular user role."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "UPDATE users SET role = 'user' WHERE telegram_id = ? AND role = 'pending'",
            (telegram_id,)
        )
        await db.commit()
        return cursor.rowcount > 0


async def ban_user(telegram_id: str) -> bool:
    """Ban a user from using the bot."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE users SET is_banned = 1 WHERE telegram_id = ?",
            (telegram_id,)
        )
        await db.commit()
        return True


async def unban_user(telegram_id: str) -> bool:
    """Unban a user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE users SET is_banned = 0 WHERE telegram_id = ?",
            (telegram_id,)
        )
        await db.commit()
        return True


async def add_vm(detector_id: str, hypervisor_name: str, secret_key: str) -> bool:
    """Register a new VM in the system."""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                """INSERT INTO vms (detector_id, hypervisor_name, secret_key, status)
                   VALUES (?, ?, ?, 'offline')""",
                (detector_id, hypervisor_name, secret_key)
            )
            await db.commit()
        return True
    except sqlite3.IntegrityError:
        return False


async def get_vm(detector_id: str) -> Optional[Dict]:
    """Retrieve VM info by Detector ID."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM vms WHERE detector_id = ?",
            (detector_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_vms_by_user(telegram_id: str) -> List[Dict]:
    """Retrieve all VMs assigned to a user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM vms WHERE assigned_user_id = ? ORDER BY detector_id",
            (telegram_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_all_vms() -> List[Dict]:
    """Retrieve all VMs."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM vms ORDER BY detector_id")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def assign_vm(detector_id: str, telegram_id: str) -> bool:
    """Assign a VM to a user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "UPDATE vms SET assigned_user_id = ? WHERE detector_id = ?",
            (telegram_id, detector_id)
        )
        await db.commit()
        return cursor.rowcount > 0


async def update_vm_status(detector_id: str, status: str) -> bool:
    """Update VM status and heartbeat timestamp."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE vms SET status = ?, last_heartbeat = ? WHERE detector_id = ?",
            (status, datetime.utcnow().isoformat(), detector_id)
        )
        await db.commit()
        return True


async def set_vm_pending_shutdown(detector_id: str) -> bool:
    """Mark a VM for graceful shutdown."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE vms SET status = 'pending_shutdown' WHERE detector_id = ?",
            (detector_id,)
        )
        await db.commit()
        return True


async def record_failed_auth(detector_id: str) -> bool:
    """Record a failed authentication attempt."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO failed_auth (detector_id) VALUES (?)",
            (detector_id,)
        )
        await db.commit()
        return True


async def get_failed_auth_count(detector_id: str) -> int:
    """Get recent failed auth attempts in the last hour."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """SELECT COUNT(*) as count FROM failed_auth 
               WHERE detector_id = ? AND attempt_time > datetime('now', '-1 hour')""",
            (detector_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def clear_failed_auth(detector_id: str) -> bool:
    """Clear failed auth records for a detector."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM failed_auth WHERE detector_id = ?", (detector_id,))
        await db.commit()
        return True


async def delete_vm(detector_id: str) -> bool:
    """Delete a VM from the database."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("DELETE FROM vms WHERE detector_id = ?", (detector_id,))
        await db.commit()
        return cursor.rowcount > 0


async def delete_user(telegram_id: str) -> bool:
    """Delete a user from the database completely."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # First, unassign all VMs from this user
        await db.execute(
            "UPDATE vms SET assigned_user_id = NULL WHERE assigned_user_id = ?",
            (telegram_id,)
        )
        # Then delete the user
        cursor = await db.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
        await db.commit()
        return cursor.rowcount > 0
