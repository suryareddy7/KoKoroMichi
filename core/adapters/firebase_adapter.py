import os
import asyncio
from typing import AsyncIterator, Dict, Any
from core.storage_adapter import StorageAdapter
import firebase_admin
from firebase_admin import credentials, firestore_async

FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase.json")

class FirebaseAdapter(StorageAdapter):
    def __init__(self):
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
        self.db = firestore_async.client()

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        doc = await self.db.collection("users").document(user_id).get()
        return doc.to_dict() if doc.exists else {}

    async def save_user(self, user_id: str, data: Dict[str, Any]) -> bool:
        await self.db.collection("users").document(user_id).set(data)
        return True

    async def get_game_data(self, section: str) -> Dict[str, Any]:
        doc = await self.db.collection("game_data").document(section).get()
        return doc.to_dict() if doc.exists else {}

    async def save_game_data(self, section: str, data: Dict[str, Any]) -> bool:
        await self.db.collection("game_data").document(section).set(data)
        return True

    async def list_users(self) -> AsyncIterator[str]:
        users = self.db.collection("users").stream()
        async for doc in users:
            yield doc.id

    async def backup_collection(self, path_or_bucket: str) -> None:
        users = []
        async for doc in self.db.collection("users").stream():
            users.append(doc.to_dict())
        import json
        with open(path_or_bucket, "w", encoding="utf-8") as f:
            json.dump(users, f, default=str, indent=2)
