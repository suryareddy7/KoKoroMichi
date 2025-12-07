import os
import asyncio
from typing import AsyncIterator, Dict, Any
from core.storage_adapter import StorageAdapter
import asyncpg

SUPABASE_URL = os.getenv("SUPABASE_URL", "postgresql://user:password@localhost:5432/kokoromichi")

class SupabaseAdapter(StorageAdapter):
    def __init__(self):
        self.dsn = SUPABASE_URL
        self.pool = None

    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(dsn=self.dsn)

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        await self.connect()
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT data FROM users WHERE user_id=$1", user_id)
            return dict(row["data"]) if row else {}

    async def save_user(self, user_id: str, data: Dict[str, Any]) -> bool:
        await self.connect()
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (user_id, data, last_modified)
                VALUES ($1, $2, NOW())
                ON CONFLICT (user_id) DO UPDATE SET data=$2, last_modified=NOW()
                """, user_id, data
            )
        return True

    async def get_game_data(self, section: str) -> Dict[str, Any]:
        await self.connect()
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT data FROM game_data WHERE section=$1", section)
            return dict(row["data"]) if row else {}

    async def save_game_data(self, section: str, data: Dict[str, Any]) -> bool:
        await self.connect()
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO game_data (section, data, last_modified)
                VALUES ($1, $2, NOW())
                ON CONFLICT (section) DO UPDATE SET data=$2, last_modified=NOW()
                """, section, data
            )
        return True

    async def list_users(self) -> AsyncIterator[str]:
        await self.connect()
        async with self.pool.acquire() as conn:
            async for row in conn.cursor("SELECT user_id FROM users"):
                yield row["user_id"]

    async def backup_collection(self, path_or_bucket: str) -> None:
        await self.connect()
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM users")
            import json
            with open(path_or_bucket, "w", encoding="utf-8") as f:
                json.dump([dict(r) for r in rows], f, default=str, indent=2)
