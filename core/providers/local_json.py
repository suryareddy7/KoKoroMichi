"""Local JSON DataProvider implementation.

This adapter performs non-blocking file IO via `asyncio.to_thread` so it can be
used safely from the event loop without adding new runtime dependencies.

It stores per-user files under `data/users/{user_id}.json` and top-level
sections under `data/{section}.json`. Backups are written to
`data/backups/` with timestamps before each write.
"""
from __future__ import annotations

import asyncio
import json
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from core.data_provider import DataProvider


class LocalJSONProvider(DataProvider):
    """Local JSON file-backed provider.

    Note: This is intentionally lightweight. Higher-level features like
    debounced writes and TTL caches will be added in subsequent commits.
    """

    def __init__(
        self, data_dir: str | Path = "data", debounce_seconds: float = 0.5, cache_ttl: float = 5.0
    ) -> None:
        self.data_dir = Path(data_dir)
        self.users_dir = self.data_dir / "users"
        self.backup_dir = self.data_dir / "backups"
        self.ledger_dir = self.data_dir / "ledgers"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.users_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_dir.mkdir(parents=True, exist_ok=True)

        # Debounce configuration for writes
        self.debounce_seconds = float(debounce_seconds)

        # In-memory TTL cache: key -> (data, expiry_ts)
        self._cache: Dict[str, Tuple[Dict[str, Any], float]] = {}

        # Pending write tasks per key
        self._pending_writes: Dict[str, asyncio.Task] = {}

        # Lock for serializing access to pending_writes structure
        self._pending_lock = asyncio.Lock()

    async def _read_json(self, path: Path) -> Optional[Dict[str, Any]]:
        if not path.exists():
            return None

        def _read() -> Dict[str, Any]:
            with path.open("r", encoding="utf-8") as fh:
                return json.load(fh)

        return await asyncio.to_thread(_read)

    async def _write_json(self, path: Path, data: Dict[str, Any]) -> None:
        # create backup if file exists
        if path.exists():
            ts = int(time.time())
            backup_path = self.backup_dir / f"{path.name}.{ts}.bak.json"
            await asyncio.to_thread(shutil.copy2, str(path), str(backup_path))

        def _write() -> None:
            tmp = path.with_suffix(".tmp")
            with tmp.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
            tmp.replace(path)

        await asyncio.to_thread(_write)

    # --- Cache and debounced writes ---
    async def _schedule_write(self, key: str, path: Path, data: Dict[str, Any]) -> None:
        async with self._pending_lock:
            # Cancel existing pending write for key
            existing = self._pending_writes.get(key)
            if existing and not existing.done():
                existing.cancel()

            async def _delayed_write() -> None:
                try:
                    await asyncio.sleep(self.debounce_seconds)
                    await self._write_json(path, data)
                except asyncio.CancelledError:
                    return

            task = asyncio.create_task(_delayed_write())
            self._pending_writes[key] = task

    def _set_cache(self, key: str, data: Dict[str, Any], ttl: float = 5.0) -> None:
        self._cache[key] = (data, time.time() + ttl)

    def _get_cache(self, key: str) -> Optional[Dict[str, Any]]:
        item = self._cache.get(key)
        if not item:
            return None
        data, expiry = item
        if time.time() > expiry:
            del self._cache[key]
            return None
        return data

    # --- Ledger ---
    async def append_ledger(self, ledger_name: str, entry: Dict[str, Any]) -> None:
        """Append an entry (JSON line) to an append-only ledger file."""
        path = self.ledger_dir / f"{ledger_name}.log"

        def _append():
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

        await asyncio.to_thread(_append)

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        # Attempt cache first
        cached = self._get_cache(user_id)
        if cached is not None:
            return cached

        path = self.users_dir / f"{user_id}.json"
        data = await self._read_json(path)
        if data is not None:
            self._set_cache(user_id, data, ttl=self.debounce_seconds * 10)
        return data

    async def save_user(self, user_id: str, data: Dict[str, Any]) -> None:
        path = self.users_dir / f"{user_id}.json"
        # update cache immediately
        self._set_cache(user_id, data, ttl=self.debounce_seconds * 10)
        await self._schedule_write(f"user:{user_id}", path, data)

    async def save_user_now(self, user_id: str, data: Dict[str, Any]) -> None:
        """Force immediate write (bypasses debounce)."""
        path = self.users_dir / f"{user_id}.json"
        # cancel pending
        async with self._pending_lock:
            pending = self._pending_writes.pop(f"user:{user_id}", None)
            if pending and not pending.done():
                pending.cancel()
        await self._write_json(path, data)

    async def get_game_data(self, section: str) -> Optional[Dict[str, Any]]:
        # Use a simple cache key scheme
        cache_key = f"section:{section}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached
        path = self.data_dir / f"{section}.json"
        data = await self._read_json(path)
        if data is not None:
            self._set_cache(cache_key, data, ttl=self.debounce_seconds * 10)
        return data

    async def save_game_data(self, section: str, data: Dict[str, Any]) -> None:
        path = self.data_dir / f"{section}.json"
        cache_key = f"section:{section}"
        self._set_cache(cache_key, data, ttl=self.debounce_seconds * 10)
        await self._schedule_write(cache_key, path, data)

    async def sync_local_to_remote(self) -> Dict[str, Any]:
        # Placeholder: remote adapters will implement synchronization logic.
        return {"status": "not_implemented", "action": "sync_local_to_remote"}

    async def sync_remote_to_local(self) -> Dict[str, Any]:
        return {"status": "not_implemented", "action": "sync_remote_to_local"}

    async def migrate_local_to_remote(self, dry_run: bool = True) -> Dict[str, Any]:
        return {"status": "not_implemented", "dry_run": dry_run}
