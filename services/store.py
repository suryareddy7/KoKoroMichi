"""Store Service: handles purchases, inventory, and shop transactions.

This is a modular service that encapsulates store logic and uses the
Transaction API for safe multi-step operations with rollback support.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any

from core.data_provider import DataProvider
from core.provider_manager import get_provider
from core.transactions import begin_transaction, Transaction


@dataclass
class StoreItem:
    """Definition of a purchasable item."""

    item_id: str
    name: str
    description: str
    price: int  # Cost in gold
    quantity_limit: Optional[int] = None  # None = unlimited


class StoreService:
    """Encapsulates all store-related operations."""

    def __init__(self, provider: Optional[DataProvider] = None):
        self.provider = provider or get_provider()

        # Example store items
        self.items: Dict[str, StoreItem] = {
            "health_potion": StoreItem(
                item_id="health_potion",
                name="Health Potion",
                description="Restores 50 HP",
                price=100,
            ),
            "mana_potion": StoreItem(
                item_id="mana_potion",
                name="Mana Potion",
                description="Restores 30 Mana",
                price=150,
            ),
            "revive_scroll": StoreItem(
                item_id="revive_scroll",
                name="Revive Scroll",
                description="Revive a fallen character",
                price=500,
                quantity_limit=5,
            ),
        }

    async def purchase_item(
        self, user_id: str, item_id: str, quantity: int = 1
    ) -> tuple[bool, str, int]:
        """
        Attempt to purchase an item.

        Returns: (success: bool, message: str, new_gold_balance: int)

        Uses Transaction API for safe rollback on failure.
        """
        if item_id not in self.items:
            return False, "Item not found in store.", 0

        item = self.items[item_id]
        total_cost = item.price * quantity

        tx = await begin_transaction(user_id, self.provider)

        try:
            # Check player has enough gold
            current_gold = tx.get("gold", 0)
            if current_gold < total_cost:
                await tx.rollback()
                return False, f"Insufficient gold. Need {total_cost}, have {current_gold}.", current_gold

            # Check quantity limit
            if item.quantity_limit is not None:
                inventory = tx.get("inventory", {})
                current_qty = inventory.get(item_id, 0)
                if current_qty + quantity > item.quantity_limit:
                    await tx.rollback()
                    return False, f"Purchase exceeds limit of {item.quantity_limit}.", current_gold

            # Perform the transaction:
            # 1. Deduct gold
            new_gold = tx.decr("gold", total_cost)

            # 2. Add item to inventory
            inventory = tx.get("inventory", {})
            inventory[item_id] = inventory.get(item_id, 0) + quantity
            tx.set("inventory", inventory)

            # 3. Log the purchase
            tx.add_ledger_entry(
                {
                    "ledger_type": "purchases",
                    "user_id": user_id,
                    "item_id": item_id,
                    "quantity": quantity,
                    "cost": total_cost,
                }
            )

            # Commit all changes atomically
            await tx.commit()

            return True, f"Purchased {quantity}x {item.name} for {total_cost} gold.", new_gold

        except Exception as e:
            await tx.rollback()
            return False, f"Purchase failed: {str(e)}", 0

    async def view_store(self) -> str:
        """Return a formatted store listing."""
        listing = "**=== STORE ===**\n"
        for item_id, item in self.items.items():
            limit_str = (
                f" (Limit: {item.quantity_limit})" if item.quantity_limit else ""
            )
            listing += f"• {item.name}: {item.price} gold - {item.description}{limit_str}\n"
        return listing

    async def get_user_inventory(self, user_id: str) -> Dict[str, int]:
        """Get a user's current inventory."""
        data = await self.provider.get_user(user_id)
        if data is None:
            return {}
        return data.get("inventory", {})
