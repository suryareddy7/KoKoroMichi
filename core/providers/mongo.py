"""MongoDB DataProvider implementation using Motor (async pymongo).

Requires: pip install motor
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from core.data_provider import DataProvider


class MongoDBProvider(DataProvider):
    """Async MongoDB adapter using Motor.

    Expects MONGO_URI environment variable:
      MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/kokoromichi
    """

    def __init__(self, mongo_uri: Optional[str] = None, db_name: str = "kokoromichi"):
        """Initialize MongoDB provider.

        Args:
            mongo_uri: MongoDB connection URI (defaults to MONGO_URI env var)
            db_name: Database name
        """
        self.mongo_uri = mongo_uri or os.getenv("MONGO_URI")
        if not self.mongo_uri:
            raise ValueError(
                "MONGO_URI environment variable not set. "
                "Required for MongoDBProvider."
            )

        self.db_name = db_name
        self.client = None
        self.db = None

    async def _connect(self) -> None:
        """Lazy connection to MongoDB."""
        if self.client is None:
            try:
                from motor.motor_asyncio import AsyncMongoClient

                self.client = AsyncMongoClient(self.mongo_uri)
                self.db = self.client[self.db_name]
                # Verify connection
                await self.db.admin.command("ping")
            except Exception as e:
                raise RuntimeError(f"Failed to connect to MongoDB: {e}")

    async def _ensure_connected(self) -> None:
        """Ensure connection is established."""
        if self.db is None:
            await self._connect()

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user document by ID."""
        await self._ensure_connected()
        try:
            doc = await self.db.users.find_one({"_id": user_id})
            if doc:
                doc.pop("_id", None)  # Remove internal ID
            return doc
        except Exception as e:
            raise RuntimeError(f"get_user failed: {e}")

    async def save_user(self, user_id: str, data: Dict[str, Any]) -> None:
        """Save user document (insert or update)."""
        await self._ensure_connected()
        try:
            data_copy = data.copy()
            data_copy["_id"] = user_id
            await self.db.users.replace_one(
                {"_id": user_id}, data_copy, upsert=True
            )
        except Exception as e:
            raise RuntimeError(f"save_user failed: {e}")

    async def get_game_data(self, section: str) -> Optional[Dict[str, Any]]:
        """Retrieve game data section (e.g., 'items', 'store')."""
        await self._ensure_connected()
        try:
            doc = await self.db.game_data.find_one({"_id": section})
            if doc:
                doc.pop("_id", None)
            return doc
        except Exception as e:
            raise RuntimeError(f"get_game_data failed: {e}")

    async def save_game_data(self, section: str, data: Dict[str, Any]) -> None:
        """Save a game data section."""
        await self._ensure_connected()
        try:
            data_copy = data.copy()
            data_copy["_id"] = section
            await self.db.game_data.replace_one(
                {"_id": section}, data_copy, upsert=True
            )
        except Exception as e:
            raise RuntimeError(f"save_game_data failed: {e}")

    async def sync_local_to_remote(self) -> Dict[str, Any]:
        """Placeholder: migrate local JSON to MongoDB."""
        return {
            "status": "not_implemented",
            "message": "Use migration scripts to migrate from local JSON",
        }

    async def sync_remote_to_local(self) -> Dict[str, Any]:
        """Placeholder: download MongoDB to local JSON."""
        return {"status": "not_implemented"}

    async def migrate_local_to_remote(self, dry_run: bool = True) -> Dict[str, Any]:
        """Placeholder: migrate local JSON to MongoDB with optional dry-run."""
        return {
            "status": "not_implemented",
            "dry_run": dry_run,
            "message": "Use migration scripts",
        }

    async def append_ledger(self, ledger_name: str, entry: Dict[str, Any]) -> None:
        """Append an entry to an append-only ledger collection."""
        await self._ensure_connected()
        try:
            collection_name = f"ledger_{ledger_name}"
            await self.db[collection_name].insert_one(entry)
        except Exception as e:
            raise RuntimeError(f"append_ledger failed: {e}")

    async def close(self) -> None:
        """Close MongoDB connection."""
        if self.client is not None:
            self.client.close()
