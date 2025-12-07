# Store System - Command Quick Reference

## User Commands

### Browse Store
```
!store                    # Browse all items, page 1
!store 2                  # Go to page 2
!store 1 consumable       # Browse consumables category, page 1
!store 1 loot gems        # Browse loot in gems currency
!store 2 special gold     # Browse special items with gold prices
```

**Features**:
- Pagination with ◀ Previous / Next ▶ buttons
- Shows item name, description, current price, stock
- Price shows 📈 inflation indicator if item's been purchased recently
- Category filtering (consumable, healing, loot, buff, special)
- Currency selection (gold, gems)

### Purchase Item
```
!buy health_potion_small 1 gold       # Buy 1 potion for gold
!buy treasure_chest 2 gems             # Buy 2 chests for gems
!buy lucky_charm 3 gold                # Buy 3 charms (supports quantity)
```

**Response**:
- Shows item name, quantity, unit price, total cost
- Shows new balance after purchase
- ⚠️ Offline mode notice if purchase was recorded locally (not yet synced)
- Transaction ID for reference

### View Inventory
```
!inventory                # See all items you own with quantities
```

**Shows**:
- Items grouped by category (consumable, buff, special, etc.)
- Quantity for each item
- Purchase statistics (total spent, number of purchases, VIP status)

### View Purchase History
```
!ledger                   # Last 10 transactions
!ledger 50               # Last 50 transactions
!ledger 100              # Last 100 transactions
```

**Shows**:
- Transaction status (✅ COMMITTED, ⏳ PENDING, 📡 PENDING_OFFLINE, ❌ FAILED)
- Item ID, quantity, currency, timestamp
- Use transaction ID for support inquiries

---

## Admin Commands

### Restock Item
```
!store_restock health_potion_small 100    # Add 100 to stock
!store_restock treasure_chest 50          # Restock treasure chests
!store_restock lucky_charm 10             # Restock lucky charms
```

**Effect**:
- Increases item's stock by specified amount
- Increments item version (optimistic lock)
- Logs change for audit trail

### Set Item Price
```
!store_setprice health_potion_small 500 5      # Gold: 500, Gems: 5
!store_setprice treasure_chest 2500 25         # Dual-currency pricing
!store_setprice lucky_charm 1500 10            # Support both currencies
```

**Effect**:
- Changes base_price for both currencies
- Increments item version
- Affects all future purchases (not retroactive)

### Sync Pending Transactions
```
!store_sync                          # Flush offline txs to provider
```

**Response**:
- Applied: # of txs successfully synced
- Retried: # of txs that need retry
- Failed: # of txs that failed (review needed)
- Errors: List of failure reasons (first 5)

**When to use**:
- After provider comes back online
- To unblock pending offline transactions
- To ensure data consistency across systems

---

## Pricing & Inflation

### Base Price
Each item has a base price in each currency:
```
{
  "base_price": {
    "gold": 500,
    "gems": 5
  }
}
```

### Inflation
Price increases by **1% per purchase** (configurable per item via `inflation_rate`):
```
inflation_multiplier = (1 + inflation_rate) ^ total_sold

Example: health_potion_small with inflation_rate=0.01
├─ 0 purchases:   500 * 1.00 = 500 gold
├─ 10 purchases:  500 * 1.105 = 552.5 gold
├─ 50 purchases:  500 * 1.645 = 822.5 gold
└─ 100 purchases: 500 * 2.705 = 1352.5 gold
```

... (omitted for brevity)
