import os
import motor.motor_asyncio
from datetime import datetime
from typing import AsyncIterator, Dict, Any
from core.storage_adapter import StorageAdapter

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/kokoromichi")
DB_NAME = os.getenv("MONGO_DB_NAME", "kokoromichi")

class MongoAdapter(StorageAdapter):
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.users = self.db["users"]
        self.game_data = self.db["game_data"]
        self.logs = self.db["logs"]
        # Indexes
        self.users.create_index("user_id", unique=True)
        self.users.create_index("last_modified")

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        doc = await self.users.find_one({"user_id": user_id})
        return doc or {}

    async def save_user(self, user_id: str, data: Dict[str, Any]) -> bool:
        data["user_id"] = user_id
        data["last_modified"] = datetime.utcnow().isoformat()
        result = await self.users.update_one({"user_id": user_id}, {"$set": data}, upsert=True)
        return result.acknowledged

    async def get_game_data(self, section: str) -> Dict[str, Any]:
        doc = await self.game_data.find_one({"section": section})
        return doc or {}

    async def save_game_data(self, section: str, data: Dict[str, Any]) -> bool:
        data["section"] = section
        data["last_modified"] = datetime.utcnow().isoformat()
        result = await self.game_data.update_one({"section": section}, {"$set": data}, upsert=True)
        return result.acknowledged

    async def list_users(self) -> AsyncIterator[str]:
        async for doc in self.users.find({}, {"user_id": 1}):
            yield doc["user_id"]

    async def backup_collection(self, path_or_bucket: str) -> None:
        # Simple backup: dump users collection to JSON file
        import json
        users = []
        async for doc in self.users.find({}):
            users.append(doc)
        with open(path_or_bucket, "w", encoding="utf-8") as f:
            json.dump(users, f, default=str, indent=2)
