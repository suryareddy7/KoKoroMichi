# KoKoroMichi Module Reference

## Core Data Layer

### `core/data_provider.py`
**Abstract async interface for all storage backends.**
- `get_user(user_id)` — Retrieve user document
- `save_user(user_id, data)` — Persist user document
- `get_game_data(section)` — Get global game data section
- `save_game_data(section, data)` — Save global section
- `sync_local_to_remote()` — Sync local to remote DB
- `sync_remote_to_local()` — Sync remote DB to local
- `migrate_local_to_remote(dry_run)` — Migrate with optional dry-run

### `core/models.py`
**Pydantic models for domain objects.**
- `Item` — Purchasable item definition
- `Waifu` — Character/waifu model
- `UserProfile` — User data schema
- `Transaction` — Ledger transaction entry

### `core/logging_config.py`
**Centralized logging setup.**
- `configure_logging()` — Init logging with LOG_LEVEL from env

### `core/provider_manager.py`
**Provider factory and singleton management.**
- `get_provider()` — Get active provider (selects based on PROVIDER env var)
- `get_user_async(user_id)` — Async user fetch
- `save_user_async(user_id, data)` — Async user save
- `get_game_data_async(section)` — Async game data fetch
- `save_game_data_async(section, data)` — Async game data save

### `core/transactions.py`
**Transactional API for safe multi-step operations.**
- `Transaction` class — Begin/commit/rollback context manager
  - `await begin()` — Load user data snapshot
  - `set(key, value)` — Update pending state
  - `get(key)` — Read pending state
  - `incr/decr(key, amount)` — Numeric updates
  - `add_ledger_entry(entry)` — Queue ledger append
  - `await commit()` — Write all changes atomically
  - `await rollback()` — Discard changes
- `begin_transaction(user_id)` — Convenience factory

---

## Data Providers

### `core/providers/local_json.py`
**Default local file storage with advanced features.**

**Features:**
- Async file I/O via `asyncio.to_thread`
- Debounced writes (batches multiple writes, configurable interval)
- In-memory TTL cache (configurable expiry)
- Automatic timestamped backups before writes
- Append-only ledger support for audit trails

**Tuning:**
- `debounce_seconds=0.5` — Delay before disk write
- `cache_ttl=5.0` — Cache expiry time

**Usage:**
```python
from core.providers.local_json import LocalJSONProvider
provider = LocalJSONProvider(data_dir="data")
user_data = await provider.get_user("user_id")
```

### `core/providers/mongo.py`
**MongoDB async adapter using Motor.**

**Requirements:** `pip install motor`

**Environment:** `MONGO_URI=mongodb+srv://...`

**Features:**
- Lazy connection (connects on first use)
- Collections: `users`, `game_data`, `ledger_*`
- Automatic connection verification

**Usage:**
```python
from core.providers.mongo import MongoDBProvider
provider = MongoDBProvider()
user_data = await provider.get_user("user_id")
```

### `core/providers/postgres.py`
**PostgreSQL async adapter using asyncpg.**

**Requirements:** `pip install asyncpg`

**Environment:** `DATABASE_URL=postgresql://user:pass@host/db`

**Features:**
- Connection pooling (5-20 connections)
- Auto-schema initialization on startup
- Tables: `users`, `game_data`, `ledger_purchases`, `ledger_battles`
- JSONB support for flexible schemas

**Usage:**
```python
from core.providers.postgres import PostgresProvider
provider = PostgresProvider()
user_data = await provider.get_user("user_id")
```

---

## Services Layer

### `services/store.py`
**Transactional purchase system.**

**Class:** `StoreService`
- `__init__(provider)` — Initialize with data provider
- `async purchase_item(user_id, item_id, quantity)` — Buy item with transaction
  - Returns: `(success: bool, message: str, gold_balance: int)`
  - Checks: Gold balance, quantity limits
  - Actions: Deduct gold, add inventory, log purchase
  - Rollback on failure (insufficient funds, etc.)
- `async view_store()` — Get formatted store listing
- `async get_user_inventory(user_id)` — Get user's items

**Usage:**
```python
from services.store import StoreService
store = StoreService()
success, msg, balance = await store.purchase_item("user_id", "health_potion", 1)
```

---

## Commands Integration

### Modified Commands
- `commands/profile.py` — Uses async provider with fallback
- `commands/daily.py` — Uses async provider with fallback
- `commands/economy.py` — Uses async provider with fallback

**Pattern:** Try async provider first, fall back to `data_manager` on error:
```python
try:
    data = await get_user_async(user_id)
except:
    data = data_manager.get_user_data(user_id)
```

---

## Configuration & Deployment

### `bot.py`
**Main entrypoint.**
- Initializes Discord bot with intents
- Loads logging configuration
- Dynamically loads all command cogs from `commands/`
- Handles global error events
- Initializes provider on ready

**Run:** `python bot.py`

### `.env.example`
**Environment variables template.**
- `DISCORD_TOKEN` — Required, Discord bot token
- `PROVIDER` — local (default), mongo, postgres
- `DATA_DIR` — Path to data directory (local provider)
- `LOG_LEVEL` — DEBUG, INFO, WARNING, ERROR
- `MONGO_URI` — MongoDB connection string
- `DATABASE_URL` — PostgreSQL connection string
- `SAAS_MODE` — false (reserved for future multi-tenant support)

### `Dockerfile`
**Container image for bot.**
- Python 3.12 slim base
- Installs dependencies from `requirements.txt`
- Creates `data/` directory
- Sets `PYTHONUNBUFFERED=1` and `LOG_LEVEL=INFO`
- Runs: `python bot.py`

### `docker-compose.yml`
**Local development environment.**
- **bot** — KoKoroMichi bot service
- **mongo** — MongoDB (optional, commented out)
- **postgres** — PostgreSQL (optional, commented out)
- Shared network, volume for data persistence

**Usage:**
```bash
docker-compose up -d           # Start all services
docker-compose logs -f bot     # Watch bot logs
docker-compose stop mongo      # Stop MongoDB only
docker-compose down            # Stop and remove all
```

---

## Scripts

### `scripts/migrate_json_to_db.py`
**Migrate local JSON data to remote databases.**

**Usage:**
```bash
# Dry-run (preview without writing)
python scripts/migrate_json_to_db.py --provider mongo --dry-run

# Perform actual migration
python scripts/migrate_json_to_db.py --provider postgres

# Custom data directory
python scripts/migrate_json_to_db.py --provider mongo --data-dir /path/to/data
```

**Features:**
- Reads all JSON files from `data/` directory
- Iterates through users and game data sections
- Dry-run mode shows planned actions without writing
- Error reporting and rollback suggestions
- Returns JSON report with migration stats

---

## Testing

### `tests/test_data_provider.py`
**Tests for pydantic models.**
- `test_user_profile_model()` — UserProfile instantiation
- `test_item_model()` — Item instantiation

### `tests/test_local_json_provider.py`
**Tests for LocalJSONProvider.**
- `test_save_and_get_user_tmp()` — Write and read user data
- `test_backup_and_ledger()` — Verify backups and ledger append
- `test_cache_ttl()` — Test cache expiry

**Run:** `pytest tests/ -v`

---

## CI/CD

### `.github/workflows/ci.yml`
**Automated testing and linting.**
- Runs on: push to main/develop, pull requests
- Python versions: 3.10, 3.11, 3.12
- Jobs:
  - **lint** — black, isort, flake8, mypy
  - **test** — pytest suite
  - **security** — bandit security checks

### `.pre-commit-config.yaml`
**Local pre-commit hooks.**
- black — Code formatting
- isort — Import sorting
- flake8 — Linting
- Standard hooks — Trailing whitespace, file endings

**Setup:** `pre-commit install && pre-commit run --all-files`

---

## Documentation

| Document | Purpose |
|----------|---------|
| `REFACTOR_SUMMARY.md` | High-level overview of changes |
| `README_REFACTOR.md` | Architecture guide and quick start |
| `DEPLOY.md` | Production deployment guide |
| `DEVELOPER_QUICKREF.md` | Quick reference for developers |
| `DEVELOPER_MODULES.md` | This file — module reference |
| `.env.example` | Configuration template |

---

## Dependency Tree

```
bot.py
  ├── core/logging_config.py
  ├── core/provider_manager.py
  │   ├── core/data_provider.py
  │   ├── core/providers/local_json.py
  │   ├── core/providers/mongo.py
  │   └── core/providers/postgres.py
  └── commands/*.py
      ├── core/provider_manager.py
      ├── core/data_manager.py (legacy fallback)
      └── discord.py

services/store.py
  ├── core/data_provider.py
  ├── core/provider_manager.py
  └── core/transactions.py

core/transactions.py
  ├── core/data_provider.py
  └── core/provider_manager.py
```

---

## Quick Troubleshooting

| Problem | Check | Solution |
|---------|-------|----------|
| Bot won't start | `DISCORD_TOKEN` in `.env` | Add token from Discord Developer Portal |
| "Module not found" | `pip install -r requirements.txt` | Install all dependencies |
| MongoDB connection fails | `MONGO_URI` env var | Verify connection string and MongoDB is running |
| PostgreSQL connection fails | `DATABASE_URL` env var | Verify URL and PostgreSQL is running |
| Async errors in commands | `async def` declaration | Command methods must be `async def` |
| Cache not working | `cache_ttl` value | Check TTL hasn't expired (default 5s) |
| Tests fail | Python version | Use Python 3.10+ |

---

**For more details, see the full documentation in DEPLOY.md and README_REFACTOR.md.**