"""Provider manager: create and expose the active DataProvider.

Supports switching between local JSON, MongoDB, and PostgreSQL via PROVIDER env var:
  PROVIDER=local (default) | mongo | postgres

Commands can use the async provider while keeping legacy data_manager as fallback
during migration.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any

from core.data_provider import DataProvider
from core.providers.local_json import LocalJSONProvider

logger = logging.getLogger(__name__)

# Default data directory or override via DATA_DIR env var
DEFAULT_DATA_DIR = Path(os.getenv("DATA_DIR", "data"))

# Singleton provider instance
_provider: Optional[DataProvider] = None


def get_provider() -> DataProvider:
    """Get or create the active DataProvider based on PROVIDER env var."""
    global _provider
    if _provider is None:
        provider_type = os.getenv("PROVIDER", "local").lower()

        if provider_type == "mongo":
            try:
                from core.providers.mongo import MongoDBProvider

                _provider = MongoDBProvider()
                logger.info("Using MongoDB provider")
            except ImportError:
                logger.error("Motor not installed. Install with: pip install motor")
                raise
        elif provider_type == "postgres":
            try:
                from core.providers.postgres import PostgresProvider

                _provider = PostgresProvider()
                logger.info("Using PostgreSQL provider")
            except ImportError:
                logger.error("asyncpg not installed. Install with: pip install asyncpg")
                raise
        else:
            # Default to local JSON
            _provider = LocalJSONProvider(data_dir=DEFAULT_DATA_DIR)
            logger.info(f"Using LocalJSON provider (data_dir={DEFAULT_DATA_DIR})")

    return _provider


async def get_user_async(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user data asynchronously."""
    p = get_provider()
    return await p.get_user(user_id)


async def save_user_async(user_id: str, data: Dict[str, Any]) -> None:
    """Save user data asynchronously."""
    p = get_provider()
    return await p.save_user(user_id, data)


async def get_game_data_async(section: str) -> Optional[Dict[str, Any]]:
    """Get game data section asynchronously."""
    p = get_provider()
    return await p.get_game_data(section)


async def save_game_data_async(section: str, data: Dict[str, Any]) -> None:
    """Save game data section asynchronously."""
    p = get_provider()
    return await p.save_game_data(section, data)
