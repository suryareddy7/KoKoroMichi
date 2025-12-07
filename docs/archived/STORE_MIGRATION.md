# Store System Rewrite - Migration Guide

## Overview

The store system has been completely rewritten to separate business logic from Discord command UI, implement transactional semantics with optimistic locking, and support offline-first operations.

### Old System Issues
- **Tight coupling**: Store items and pricing logic embedded in `commands/store.py`
- **No atomicity**: Purchases could fail midway, leaving inconsistent state
- **Race conditions**: Multiple purchases could cause stock/balance issues
- **No persistence**: Pending transactions lost if the bot crashed
- **No audit trail**: No complete ledger of purchase history

### New System Benefits
- **Separation of concerns**: `StoreService` handles all business logic, `commands/store.py` only UI/Discord integration
- **ACID transactions**: Optimistic locking with version CAS, rollback on conflict
- **Offline-first**: Pending transactions recorded locally if provider unavailable, synced later
- **Idempotent**: Re-applying same transaction is a no-op (using tx_id deduplication)
- **Deterministic pricing**: Inflation calculated from total_sold, not random events
- **Audit logs**: Every transaction appended to ledger with tx_id, status, pre/post balances

---

## Architecture

### Core Files

**`core/store_models.py`** - Type-safe models
- `Item`: Store item definition (name, price, stock, inflation_rate, etc.)
- `PriceSnapshot`: Computed price with inflation & VIP discount applied
- `PurchaseTransaction`: Ledger entry (tx_id, user_id, item_id, pre/post balances, status)
- `PendingOfflineTransaction`: Local pending tx (for offline mode)
- `VipTierSpec`: VIP tier definition (tier_name, discount_pct, categories)
- `TransactionStatus`: Enum (PENDING, COMMITTED, FAILED, PENDING_OFFLINE)

**`services/store_service.py`** - Business logic
- `StoreService`: Main service class
  - `get_catalog(page, per_page, category, currency)` - Browse items
  - `preview_price(item_id, quantity, vip_tier, currency)` - Calculate price without purchase
  - `purchase_item(user_id, item_id, quantity, currency, vip_tier)` - Main transaction flow
  - `restock_item(admin_user_id, item_id, amount)` - Admin restock
  - `set_price(admin_user_id, item_id, new_base_price)` - Admin price change
  - `sync_pending_transactions()` - Flush offline pending txs to provider
  - `get_ledger(user_id, limit, offset)` - Query purchase history
  - `get_transaction_by_id(tx_id)` - Retrieve specific tx

**`data/store_catalog.json`** - Offline-first item catalog
- Items stored as JSON for fast local access
- Synced to provider if available
- Fallback when provider offline

**`commands/store.py`** - Discord command wrapper (REFACTORED)
- `StorePaginationView`: Discord.UI pagination with prev/next buttons
- `StoreCommands` cog with commands:
  - `!store [page] [category] [currency]` - Browse items
  - `!buy <item_id> <quantity> [currency]` - Purchase item
  - `!inventory` - View purchased items
  - `!ledger [limit]` - Purchase history
  - `!store_restock <item_id> <amount>` [ADMIN]
  - `!store_setprice <item_id> <gold> <gems>` [ADMIN]
  - `!store_sync` [ADMIN] - Sync pending txs

... (omitted for brevity)
