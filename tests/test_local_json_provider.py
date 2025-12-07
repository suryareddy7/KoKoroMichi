import asyncio
import json
import os
from pathlib import Path

import pytest

from core.providers.local_json import LocalJSONProvider


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_save_and_get_user_tmp(tmp_path):
    data_dir = tmp_path / "data"
    prov = LocalJSONProvider(data_dir=data_dir, debounce_seconds=0.1, cache_ttl=1.0)

    async def _test():
        await prov.save_user("u1", {"user_id": "u1", "name": "Alice", "gold": 10})
        # wait longer than debounce to allow write to complete
        await asyncio.sleep(0.25)
        u = await prov.get_user("u1")
        assert u is not None
        assert u["name"] == "Alice"

    run(_test())


def test_backup_and_ledger(tmp_path):
    data_dir = tmp_path / "data"
    prov = LocalJSONProvider(data_dir=data_dir, debounce_seconds=0.05)

    async def _test():
        # write twice to cause a backup on second write
        await prov.save_user("u2", {"user_id": "u2", "gold": 1})
        await asyncio.sleep(0.1)
        await prov.save_user_now("u2", {"user_id": "u2", "gold": 2})

        users_dir = Path(data_dir) / "users"
        f = users_dir / "u2.json"
        assert f.exists()

        backups = list((Path(data_dir) / "backups").glob("u2.json.*.bak.json"))
        assert len(backups) >= 1

        # append ledger
        await prov.append_ledger("purchases", {"user_id": "u2", "amt": 2})
        ledger_file = Path(data_dir) / "ledgers" / "purchases.log"
        assert ledger_file.exists()
        lines = ledger_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) >= 1
        entry = json.loads(lines[-1])
        assert entry["user_id"] == "u2"

    run(_test())


def test_cache_ttl(tmp_path):
    data_dir = tmp_path / "data"
    prov = LocalJSONProvider(data_dir=data_dir, debounce_seconds=0.05)

    async def _test():
        await prov.save_user_now("u3", {"user_id": "u3", "gold": 5})
        # prime cache
        u = await prov.get_user("u3")
        assert u is not None
        # simulate expiry by manipulating internal cache expiry
        key = "u3"
        # force expiry
        if key in prov._cache:
            data, expiry = prov._cache[key]
            prov._cache[key] = (data, 0.0)

        # next read should reload from disk
        u2 = await prov.get_user("u3")
        assert u2 is not None

    run(_test())
