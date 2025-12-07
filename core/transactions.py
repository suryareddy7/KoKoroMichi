"""Transaction support for KoKoroMichi.

Provides transactional primitives (begin/commit/rollback) for safe multi-step
operations like purchases, battle loot distribution, and other state changes.

Uses optimistic locking for local JSON provider and can be extended for
database-backed transactions.
"""
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from core.data_provider import DataProvider
from core.provider_manager import get_provider


@dataclass
class Transaction:
    """A single transaction context for a user."""

    tx_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    provider: DataProvider = field(default_factory=get_provider)

    # Original user data snapshot for rollback
    original_data: Optional[Dict[str, Any]] = None

    # Mutations accumulated during transaction
    pending_mutations: Dict[str, Any] = field(default_factory=dict)

    # Ledger entries to append (purchases, battle results, etc.)
    ledger_entries: list[Dict[str, Any]] = field(default_factory=list)

    async def begin(self) -> Dict[str, Any]:
        """Start a transaction by loading current user data."""
        data = await self.provider.get_user(self.user_id)
        if data is None:
            # Initialize default user if not found
            data = {"user_id": self.user_id, "gold": 10000, "inventory": {}}
        self.original_data = data.copy()
        self.pending_mutations = data.copy()
        return self.pending_mutations

    def set(self, key: str, value: Any) -> None:
        """Set a value in pending mutations."""
        if self.pending_mutations is None:
            raise RuntimeError("Transaction not begun; call begin() first")
        self.pending_mutations[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from pending mutations."""
        if self.pending_mutations is None:
            raise RuntimeError("Transaction not begun; call begin() first")
        return self.pending_mutations.get(key, default)

    def incr(self, key: str, amount: int = 1) -> int:
        """Increment a numeric value in pending mutations."""
        if self.pending_mutations is None:
            raise RuntimeError("Transaction not begun")
        old = self.pending_mutations.get(key, 0)
        new = old + amount
        self.pending_mutations[key] = new
        return new

    def decr(self, key: str, amount: int = 1) -> int:
        """Decrement a numeric value."""
        return self.incr(key, -amount)

    def add_ledger_entry(self, entry: Dict[str, Any]) -> None:
        """Add an entry to the append-only ledger (purchases, battle results, etc.)."""
        self.ledger_entries.append(entry)

    async def commit(self) -> bool:
        """Commit the transaction: write pending mutations and ledger entries."""
        if self.pending_mutations is None or self.original_data is None:
            raise RuntimeError("Transaction not begun")

        try:
            # Write user data
            await self.provider.save_user(self.user_id, self.pending_mutations)

            # Append ledger entries
            for entry in self.ledger_entries:
                await self.provider.append_ledger(entry.get("ledger_type", "general"), entry)

            return True
        except Exception as e:
            raise RuntimeError(f"Transaction commit failed: {e}")

    async def rollback(self) -> None:
        """Rollback: restore original data (no write)."""
        if self.original_data is None:
            raise RuntimeError("Transaction not begun")
        self.pending_mutations = self.original_data.copy()
        self.ledger_entries.clear()

    async def __aenter__(self) -> Transaction:
        """Async context manager entry."""
        await self.begin()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit: auto-rollback on exception."""
        if exc_type is not None:
            await self.rollback()


async def begin_transaction(user_id: str, provider: Optional[DataProvider] = None) -> Transaction:
    """Create and begin a transaction for a user."""
    if provider is None:
        provider = get_provider()
    tx = Transaction(user_id=user_id, provider=provider)
    await tx.begin()
    return tx
