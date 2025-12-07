import typing
from typing import AsyncIterator, Dict, Any

class StorageAdapter:
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        raise NotImplementedError

    async def save_user(self, user_id: str, data: Dict[str, Any]) -> bool:
        raise NotImplementedError

    async def get_game_data(self, section: str) -> Dict[str, Any]:
        raise NotImplementedError

    async def save_game_data(self, section: str, data: Dict[str, Any]) -> bool:
        raise NotImplementedError

    async def list_users(self) -> AsyncIterator[str]:
        raise NotImplementedError

    async def backup_collection(self, path_or_bucket: str) -> None:
        raise NotImplementedError
