"""Data provider abstraction for KoKoroMichi.

This module defines the async DataProvider interface that all storage adapters
must implement (Local JSON, Mongo/Motor, Postgres/Supabase, Firebase, etc.).

All operations are async to avoid blocking the event loop.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class DataProvider(ABC):
    """Abstract async DataProvider interface.

    Implementations must be safe for concurrent use and perform non-blocking
    IO.
    """

    @abstractmethod
    async def get_user(self, user_id: str, /) -> Optional[Dict[str, Any]]:
        """Return the user data for `user_id` or None if not found."""

    @abstractmethod
    async def save_user(self, user_id: str, data: Dict[str, Any], /) -> None:
        """Persist `data` for `user_id`.

        Implementations should ensure atomicity where possible and provide
        backups for local adapters.
        """

    @abstractmethod
    async def get_game_data(self, section: str, /) -> Optional[Dict[str, Any]]:
        """Return a top-level game data section (e.g., 'items', 'store')."""

    @abstractmethod
    async def save_game_data(self, section: str, data: Dict[str, Any], /) -> None:
        """Persist a top-level game data section."""

    @abstractmethod
    async def sync_local_to_remote(self) -> Dict[str, Any]:
        """Synchronize local JSON files to the remote provider.

        Returns a summary dict with counts and any errors.
        """

    @abstractmethod
    async def sync_remote_to_local(self) -> Dict[str, Any]:
        """Synchronize remote provider data into local JSON files."""

    @abstractmethod
    async def migrate_local_to_remote(self, dry_run: bool = True) -> Dict[str, Any]:
        """Migrate local JSON data to remote storage.

        If `dry_run` is True, do not perform writes; instead return a report of
        planned actions.
        """
