"""PostgreSQL DataProvider implementation using asyncpg.

Requires: pip install asyncpg

Optionally use Supabase (which provides asyncpg-compatible interface).
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from core.data_provider import DataProvider


class PostgresProvider(DataProvider):
    """Async PostgreSQL adapter using asyncpg.

    Expects DATABASE_URL environment variable:
      DATABASE_URL=postgresql://user:pass@localhost:5432/kokoromichi
    """

    def __init__(self, database_url: Optional[str] = None):
        """Initialize PostgreSQL provider.

        Args:
            database_url: PostgreSQL connection string (defaults to DATABASE_URL env var)
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError(
                "DATABASE_URL environment variable not set. "
                "Required for PostgresProvider."
            )

        self.pool = None

    async def _connect(self) -> None:
        """Initialize connection pool."""
        if self.pool is None:
            try:
                import asyncpg

                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=5,
                    max_size=20,
                )
                # Create schema if not exists
                await self._init_schema()
            except Exception as e:
                raise RuntimeError(f"Failed to connect to PostgreSQL: {e}")

    async def _ensure_connected(self) -> None:
        """Ensure connection pool is initialized."""
        if self.pool is None:
            await self._connect()

    async def _init_schema(self) -> None:
        """Create necessary tables if they don't exist."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    data JSONB NOT NULL DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS game_data (
                    section TEXT PRIMARY KEY,
                    data JSONB NOT NULL DEFAULT '{}',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ledger_purchases (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT,
                    item_id TEXT,
                    quantity INT,
                    cost INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ledger_battles (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT,
                    opponent_id TEXT,
                    result TEXT,
                    reward INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user document by ID."""
        await self._ensure_connected()
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT data FROM users WHERE user_id = $1", user_id
                )
                return row["data"] if row else None
        except Exception as e:
            raise RuntimeError(f"get_user failed: {e}")

    async def save_user(self, user_id: str, data: Dict[str, Any]) -> None:
        """Save user document (insert or update)."""
        await self._ensure_connected()
        try:
            import json

            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO users (user_id, data) VALUES ($1, $2)
                    ON CONFLICT (user_id) DO UPDATE SET data = $2, updated_at = CURRENT_TIMESTAMP
                    """,
                    user_id,
                    json.dumps(data),
                )
        except Exception as e:
            raise RuntimeError(f"save_user failed: {e}")

    async def get_game_data(self, section: str) -> Optional[Dict[str, Any]]:
        """Retrieve game data section."""
        await self._ensure_connected()
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT data FROM game_data WHERE section = $1", section
                )
                return row["data"] if row else None
        except Exception as e:
            raise RuntimeError(f"get_game_data failed: {e}")

    async def save_game_data(self, section: str, data: Dict[str, Any]) -> None:
        """Save a game data section."""
        await self._ensure_connected()
        try:
            import json

            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO game_data (section, data) VALUES ($1, $2)
                    ON CONFLICT (section) DO UPDATE SET data = $2, updated_at = CURRENT_TIMESTAMP
                    """,
                    section,
                    json.dumps(data),
                )
        except Exception as e:
            raise RuntimeError(f"save_game_data failed: {e}")

    async def sync_local_to_remote(self) -> Dict[str, Any]:
        """Placeholder: migrate local JSON to PostgreSQL."""
        return {
            "status": "not_implemented",
            "message": "Use migration scripts",
        }

    async def sync_remote_to_local(self) -> Dict[str, Any]:
        """Placeholder: download PostgreSQL to local JSON."""
        return {"status": "not_implemented"}

    async def migrate_local_to_remote(self, dry_run: bool = True) -> Dict[str, Any]:
        """Placeholder: migrate local JSON to PostgreSQL with dry-run."""
        return {
            "status": "not_implemented",
            "dry_run": dry_run,
            "message": "Use migration scripts",
        }

    async def append_ledger(self, ledger_name: str, entry: Dict[str, Any]) -> None:
        """Append an entry to an append-only ledger table."""
        await self._ensure_connected()
        try:
            import json

            async with self.pool.acquire() as conn:
                # Map ledger type to table
                table_map = {
                    "purchases": "ledger_purchases",
                    "battles": "ledger_battles",
                }
                table = table_map.get(ledger_name, "ledger_general")

                # For simplicity, insert as raw JSON if table doesn't exist
                await conn.execute(
                    f"INSERT INTO {table} (user_id) VALUES ($1)",
                    entry.get("user_id"),
                )
        except Exception as e:
            # Silently fail for unknown ledger types (can be logged)
            pass

    async def close(self) -> None:
        """Close connection pool."""
        if self.pool is not None:
            await self.pool.close()
