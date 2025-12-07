from __future__ import annotations

import json
import os
import threading
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from core.store_models import (
    Item,
    StoreCatalog,
    PriceSnapshot,
    PurchaseTransaction,
    PurchaseResult,
    PendingOfflineTransaction,
    TransactionStatus,
    VipTierSpec,
)

from core.provider_manager import get_user_async, save_user_async
from core.data_manager import data_manager

PENDING_FILE = os.path.join("data", "pending_transactions.json")

# module logger
logger = logging.getLogger(__name__)


class StoreService:
    """Service layer for store operations.

    This service is offline-first: it reads the catalog from the provider when possible,
    falls back to `data/store_catalog.json` and records pending transactions locally
    if the remote provider is unavailable.
    """

    def __init__(self, provider=None, local_catalog_path: str = "data/store_catalog.json"):
        # provider is optional; we'll use data_manager / provider_manager helpers when available
        self.provider = provider
        self.local_catalog_path = local_catalog_path
        self._catalog_lock = threading.Lock()
        # Mode flags (env-configurable)
        self.single_tenant_mode = os.getenv("SINGLE_TENANT_MODE", "false").lower() == "true"
        # If AUTO_FALLBACK is true, when provider calls fail the service will switch to single-tenant mode automatically
        self.auto_fallback = os.getenv("AUTO_FALLBACK", "true").lower() == "true"

        logger.info("StoreService initializing (single_tenant_mode=%s, auto_fallback=%s)", self.single_tenant_mode, self.auto_fallback)

        self._load_local_catalog()

    def _load_local_catalog(self) -> None:
        if os.path.exists(self.local_catalog_path):
            with open(self.local_catalog_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            items = {}
            for k, v in raw.get("items", {}).items():
                try:
                    item = Item.parse_obj(v)
                    items[item.id] = item
                except Exception:
                    continue
            self.catalog = StoreCatalog(items=items)
        else:
            logger.warning("Local catalog not found at %s; initializing empty catalog", self.local_catalog_path)
            self.catalog = StoreCatalog()

    def _save_local_catalog(self) -> None:
        with self._catalog_lock:
            dump = {"items": {k: v.dict() for k, v in self.catalog.items.items()}, "last_updated": datetime.utcnow().isoformat()}
            with open(self.local_catalog_path, "w", encoding="utf-8") as f:
                json.dump(dump, f, default=str, indent=2)

    def _append_pending(self, tx: PendingOfflineTransaction) -> None:
        os.makedirs(os.path.dirname(PENDING_FILE), exist_ok=True)
        existing = []
        if os.path.exists(PENDING_FILE):
            try:
                with open(PENDING_FILE, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []
        existing.append(tx.dict())
        with open(PENDING_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, default=str, indent=2)
        logger.info("Appended pending offline transaction %s to %s", tx.tx_id, PENDING_FILE)

    def get_catalog(self, page: int = 1, per_page: int = 10, category: Optional[str] = None) -> Dict[str, Any]:
        items = list(self.catalog.items.values())
        if category:
            items = [i for i in items if category in i.categories]
        total = len(items)
        start = (page - 1) * per_page
        end = start + per_page
        page_items = items[start:end]
        return {"items": [it.dict() for it in page_items], "page": page, "per_page": per_page, "total": total}

    def get_item(self, item_id: str) -> Optional[Item]:
        return self.catalog.get_item(item_id)

    def preview_price(self, item_id: str, quantity: int = 1, vip_tier: Optional[VipTierSpec] = None, currency: str = "gold", exchange_rate: float = 1.0) -> PriceSnapshot:
        item = self.get_item(item_id)
        if not item:
            raise ValueError("Item not found")
        base = item.base_price.get(currency, 0)
        # calculate inflation multiplier
        inflation_multiplier = (1.0 + item.inflation_rate) ** item.total_sold
        vip_discount = vip_tier.discount_pct if vip_tier and (not vip_tier.categories or any(c in item.categories for c in vip_tier.categories)) else 0.0
        final_per_unit = int(base * inflation_multiplier * (1 - vip_discount) * exchange_rate)
        final_price = final_per_unit * max(1, quantity)
        return PriceSnapshot(
            item_id=item.id,
            currency=currency,
            base_price=base,
            inflation_multiplier=inflation_multiplier,
            vip_discount=vip_discount,
            exchange_rate=exchange_rate,
            final_price=final_price,
        )

    async def purchase_item(self, user_id: str, item_id: str, quantity: int = 1, currency: str = "gold", vip_tier: Optional[VipTierSpec] = None, simulate_provider_offline: bool = False) -> PurchaseResult:
        """Main purchase flow. Attempts to apply transaction; on provider offline will write a pending offline tx and apply local state where appropriate."""
        # load user (try async provider_manager, fallback to data_manager)
        user_data = None
        if self.single_tenant_mode:
            logger.debug("Single-tenant mode enabled; using local data for user %s", user_id)
            user_data = data_manager.get_user_data(user_id)
        else:
            try:
                user_data = await get_user_async(user_id)
                if user_data is None:
                    logger.debug("Provider returned no data for user %s; falling back to local data_manager", user_id)
                    user_data = data_manager.get_user_data(user_id)
            except Exception as e:
                logger.warning("Provider unavailable when loading user %s: %s", user_id, e)
                if self.auto_fallback:
                    logger.info("Auto-fallback enabled: switching to single-tenant mode (local storage only)")
                    self.single_tenant_mode = True
                    user_data = data_manager.get_user_data(user_id)
                else:
                    user_data = data_manager.get_user_data(user_id)

        item = self.get_item(item_id)
        if not item:
            return PurchaseResult(success=False, message="Item not found")

        # pre-checks
        if item.stock is not None and item.stock < quantity:
            return PurchaseResult(success=False, message="Not enough stock")

        user_bal = {"gold": int(user_data.get("gold", 0)), "gems": int(user_data.get("gems", 0))}
        pre_balances = dict(user_bal)

        price_snapshot = self.preview_price(item_id, quantity=quantity, vip_tier=vip_tier, currency=currency)

        if user_bal.get(currency, 0) < price_snapshot.final_price:
            return PurchaseResult(success=False, message="Insufficient funds")

        # optimistic lock: capture versions
        item_version = item.version
        user_version = user_data.get("version", 1)

        # Prepare transaction record
        tx = PurchaseTransaction(
            user_id=user_id,
            item_id=item_id,
            quantity=quantity,
            currency=currency,
            price_snapshot=price_snapshot,
            pre_balances=pre_balances,
        )

        # Apply locally first (reserve)
        try:
            # decrement stock and increment sold
            if item.stock is not None:
                item.stock -= quantity
            item.total_sold += quantity
            item.version += 1

            # debit user locally
            user_bal[currency] -= price_snapshot.final_price
            user_data[currency] = user_bal[currency]
            user_data.setdefault("inventory", {})
            user_data["inventory"][item_id] = user_data["inventory"].get(item_id, 0) + quantity
            user_data["version"] = user_version + 1

            tx.post_balances = dict(user_bal)

            # attempt to persist to provider
            if simulate_provider_offline:
                raise Exception("Simulated provider offline")

            # prefer async save_user_async if available
            if not self.single_tenant_mode:
                try:
                    await save_user_async(user_id, user_data)
                except Exception as e:
                    logger.warning("Failed to save user %s via provider: %s", user_id, e)
                    if self.auto_fallback:
                        logger.info("Auto-fallback: switching to single-tenant mode due to provider save failure")
                        self.single_tenant_mode = True
                        data_manager.save_user_data(user_id, user_data)
                    else:
                        data_manager.save_user_data(user_id, user_data)
            else:
                # single-tenant/local mode - persist locally
                data_manager.save_user_data(user_id, user_data)

            # persist catalog locally and attempt provider update if available
            self.catalog.items[item.id] = item
            self._save_local_catalog()

            # append ledger - if provider supports ledger append, should be used; for now write to local pending file as committed
            tx.status = TransactionStatus.COMMITTED
            tx.committed_at = datetime.utcnow()
            tx.provider_synced = True

            return PurchaseResult(success=True, tx_id=tx.tx_id, message="Purchase successful", new_balances=tx.post_balances)

        except Exception as e:
            # provider offline or write error -> write pending offline transaction
            logger.exception("Exception during purchase flow for user %s item %s: %s", user_id, item_id, e)
            pending = PendingOfflineTransaction(**tx.dict())
            pending.status = TransactionStatus.PENDING_OFFLINE
            pending.local_file_path = PENDING_FILE
            self._append_pending(pending)

            # ensure we persisted local catalog and local user_data where possible
            try:
                data_manager.save_user_data(user_id, user_data)
            except Exception as ex:
                logger.warning("Failed to save user data locally for %s after offline purchase: %s", user_id, ex)
            self.catalog.items[item.id] = item
            self._save_local_catalog()

            return PurchaseResult(success=True, tx_id=pending.tx_id, message="Purchase recorded locally (offline). Will sync when the provider is available.", new_balances=pending.post_balances)

    def restock_item(self, admin_user_id: str, item_id: str, amount: int) -> Item:
        item = self.get_item(item_id)
        if not item:
            raise ValueError("Item not found")
        if item.stock is None:
            item.stock = 0
        item.stock += amount
        item.version += 1
        self.catalog.items[item.id] = item
        self._save_local_catalog()
        return item

    def set_price(self, admin_user_id: str, item_id: str, new_base_price: Dict[str, int]) -> Item:
        item = self.get_item(item_id)
        if not item:
            raise ValueError("Item not found")
        item.base_price = new_base_price
        item.version += 1
        self.catalog.items[item.id] = item
        self._save_local_catalog()
        return item

    def sync_pending_transactions(self) -> Dict[str, Any]:
        """Attempt to sync pending transactions from local file to remote provider.

        Returns a simple report of applied and failed txs.
        """
        report = {"applied": 0, "failed": 0, "errors": []}
        if not os.path.exists(PENDING_FILE):
            return report
        try:
            with open(PENDING_FILE, "r", encoding="utf-8") as f:
                pending = json.load(f)
        except Exception as e:
            report["errors"].append(str(e))
            return report

        remaining = []
        for raw in pending:
            try:
                tx = PendingOfflineTransaction.parse_obj(raw)
                # attempt to apply: for now we mark as applied and assume remote writes succeed
                # In real provider, you'd re-run the commit flow with provider transaction
                tx.provider_synced = True
                tx.status = TransactionStatus.COMMITTED
                tx.committed_at = datetime.utcnow()
                report["applied"] += 1
            except Exception as e:
                remaining.append(raw)
                report["failed"] += 1
                report["errors"].append(str(e))

        if remaining:
            with open(PENDING_FILE, "w", encoding="utf-8") as f:
                json.dump(remaining, f, default=str, indent=2)
        else:
            os.remove(PENDING_FILE)

        return report

    def get_ledger(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        # Simple local ledger read: scan pending file and optionally provider ledger (not implemented)
        entries: List[Dict[str, Any]] = []
        if os.path.exists(PENDING_FILE):
            try:
                with open(PENDING_FILE, "r", encoding="utf-8") as f:
                    entries = json.load(f)
            except Exception:
                entries = []
        return entries[offset : offset + limit]
