"""Migration script: move data from local JSON to remote databases.

Usage:
  # Dry-run (no writes):
  python scripts/migrate_json_to_db.py --provider mongo --dry-run

  # Perform actual migration:
  python scripts/migrate_json_to_db.py --provider postgres

Requires MONGO_URI or DATABASE_URL env var (depending on provider).
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def migrate_json_to_db(
    provider_type: str, data_dir: Path, dry_run: bool = True
) -> Dict[str, Any]:
    """Migrate data from local JSON to remote database.

    Args:
        provider_type: 'mongo' or 'postgres'
        data_dir: Path to local data directory
        dry_run: If True, don't write to remote DB

    Returns:
        Migration report dict with counts and status
    """
    # Import the target provider
    if provider_type == "mongo":
        try:
            from core.providers.mongo import MongoDBProvider

            provider = MongoDBProvider()
        except ImportError:
            return {
                "status": "error",
                "message": "Motor not installed. Run: pip install motor",
            }
    elif provider_type == "postgres":
        try:
            from core.providers.postgres import PostgresProvider

            provider = PostgresProvider()
        except ImportError:
            return {
                "status": "error",
                "message": "asyncpg not installed. Run: pip install asyncpg",
            }
    else:
        return {"status": "error", "message": f"Unknown provider: {provider_type}"}

    # Read local JSON files
    users_file = data_dir / "users.json"
    if not users_file.exists():
        return {"status": "error", "message": f"users.json not found at {users_file}"}

    with users_file.open("r", encoding="utf-8") as f:
        users_data = json.load(f)

    report = {
        "provider": provider_type,
        "dry_run": dry_run,
        "users_migrated": 0,
        "errors": [],
    }

    # Migrate users
    logger.info(f"Starting migration of {len(users_data)} users to {provider_type}...")

    for user_id, user_data in users_data.items():
        try:
            if dry_run:
                logger.info(f"[DRY-RUN] Would migrate user {user_id}")
            else:
                await provider.save_user(user_id, user_data)
                logger.info(f"✓ Migrated user {user_id}")
            report["users_migrated"] += 1
        except Exception as e:
            error_msg = f"Failed to migrate user {user_id}: {str(e)}"
            logger.error(error_msg)
            report["errors"].append(error_msg)

    # Migrate game data sections
    for section_file in data_dir.glob("*.json"):
        if section_file.name == "users.json":
            continue

        section_name = section_file.stem
        try:
            with section_file.open("r", encoding="utf-8") as f:
                section_data = json.load(f)

            if dry_run:
                logger.info(f"[DRY-RUN] Would migrate section {section_name}")
            else:
                await provider.save_game_data(section_name, section_data)
                logger.info(f"✓ Migrated section {section_name}")
        except Exception as e:
            error_msg = f"Failed to migrate section {section_name}: {str(e)}"
            logger.error(error_msg)
            report["errors"].append(error_msg)

    report["status"] = "success" if not report["errors"] else "partial"
    logger.info(
        f"\nMigration complete: {report['users_migrated']} users migrated, "
        f"{len(report['errors'])} errors"
    )

    if provider_type in ("mongo", "postgres"):
        try:
            await provider.close()
        except:
            pass

    return report


async def main():
    parser = ArgumentParser(description="Migrate local JSON data to remote database")
    parser.add_argument(
        "--provider",
        choices=["mongo", "postgres"],
        required=True,
        help="Target database provider",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Path to local data directory (default: data)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform dry-run without writing to database",
    )

    args = parser.parse_args()

    if not args.data_dir.exists():
        logger.error(f"Data directory not found: {args.data_dir}")
        sys.exit(1)

    report = await migrate_json_to_db(args.provider, args.data_dir, args.dry_run)

    print("\n" + "=" * 60)
    print("MIGRATION REPORT")
    print("=" * 60)
    print(json.dumps(report, indent=2))

    if report["status"] == "error":
        sys.exit(1)
    elif report["status"] == "partial":
        sys.exit(1)  # Exit with error if there were failures


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nMigration cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
