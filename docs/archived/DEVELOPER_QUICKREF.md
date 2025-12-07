# KoKoroMichi Developer Quick Reference

## Start Bot Locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with DISCORD_TOKEN
python bot.py
```

## Docker Quickstart

```bash
docker-compose up -d          # Start bot + mongo + postgres
docker-compose logs -f bot    # Watch logs
docker-compose down           # Stop services
```

## Key Files

| File | Purpose |
|------|---------|
| `bot.py` | Bot entrypoint (logging, provider, cogs) |
| `core/data_provider.py` | Abstract storage interface |
| `core/providers/local_json.py` | Default local storage |
| `core/provider_manager.py` | Provider factory |
| `core/transactions.py` | Transaction primitives |
| `services/store.py` | Example transactional service |
| `.env.example` | Config template |
| `DEPLOY.md` | Deployment guide |

## Environment Variables

| Var | Values | Example |
|-----|--------|---------|
| `DISCORD_TOKEN` | string | `your_token_here` |
| `PROVIDER` | local, mongo, postgres | `mongo` |
| `DATA_DIR` | path | `data` |
| `LOG_LEVEL` | DEBUG, INFO, WARNING, ERROR | `INFO` |
| `MONGO_URI` | connection string | `mongodb+srv://...` |
| `DATABASE_URL` | PostgreSQL URL | `postgresql://user:pass@host/db` |

## Add Async Provider to Command

```python
from core.provider_manager import get_user_async, save_user_async

# In async command:
try:
    user_data = await get_user_async(user_id)
    if not user_data:
        user_data = data_manager.get_user_data(user_id)
except:
    user_data = data_manager.get_user_data(user_id)

# After modification:
try:
    await save_user_async(user_id, user_data)
except:
    data_manager.save_user_data(user_id, user_data)
```

## Use Transactions

```python
from core.transactions import begin_transaction

async def purchase_item(user_id, item_id, cost):
    async with await begin_transaction(user_id) as tx:
        if tx.get("gold", 0) < cost:
            # Rollback on error (automatic)
            raise ValueError("Insufficient gold")
        
        tx.decr("gold", cost)
        inventory = tx.get("inventory", {})
        inventory[item_id] = inventory.get(item_id, 0) + 1
        tx.set("inventory", inventory)
        
        tx.add_ledger_entry({
            "ledger_type": "purchases",
            "user_id": user_id,
            "item_id": item_id,
            "cost": cost,
        })
        
        await tx.commit()  # All-or-nothing write
```

## Migrate Data

```bash
# Dry-run (preview)
python scripts/migrate_json_to_db.py --provider mongo --dry-run

# Perform migration
python scripts/migrate_json_to_db.py --provider postgres

# With custom data dir
python scripts/migrate_json_to_db.py --provider mongo --data-dir /path/to/data
```

## Run Tests

```bash
pytest tests/ -v
pytest tests/test_local_json_provider.py::test_save_and_get_user_tmp -v
```

## Pre-commit Checks

```bash
pre-commit install          # One-time setup
pre-commit run --all-files  # Check all files
```

## Add New Service

```python
# services/battle.py
from core.data_provider import DataProvider
from core.provider_manager import get_provider

class BattleService:
    def __init__(self, provider: DataProvider = None):
        self.provider = provider or get_provider()
    
    async def simulate_battle(self, user_id, opponent_id):
        # Use provider to get/save data
        user = await self.provider.get_user(user_id)
        # ... battle logic
```

## Add New Provider

```python
# core/providers/custom.py
from core.data_provider import DataProvider

class CustomProvider(DataProvider):
    async def get_user(self, user_id): ...
    async def save_user(self, user_id, data): ...
    async def get_game_data(self, section): ...
    async def save_game_data(self, section, data): ...
    async def sync_local_to_remote(self): ...
    async def sync_remote_to_local(self): ...
    async def migrate_local_to_remote(self, dry_run=True): ...

# Update core/provider_manager.py:
# elif provider_type == "custom":
#     from core.providers.custom import CustomProvider
#     _provider = CustomProvider()
```

## Log Levels

```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Detailed info")
logger.info("General info")
logger.warning("Warning message")
logger.error("Error message", exc_info=True)
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Bot doesn't start | Check `DISCORD_TOKEN` in `.env` |
| Async error | Ensure command is `async def` |
| Provider not found | `PROVIDER=local` is default |
| MongoDB error | Verify `MONGO_URI` and MongoDB is running |
| Postgres error | Check `DATABASE_URL`, run `docker-compose up postgres` |

## Deployment

**Render.com**: Connect GitHub → set env vars → auto-deploy  
**Railway.app**: Connect GitHub → set env vars → auto-deploy  
**VPS**: See [DEPLOY.md](DEPLOY.md) for systemd setup  

---

See full docs: [DEPLOY.md](DEPLOY.md), [README_REFACTOR.md](README_REFACTOR.md)
