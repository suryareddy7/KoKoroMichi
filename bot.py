"""KoKoroMichi Discord Bot Entrypoint

Initializes logging, the data provider, and loads all command modules.
Run with: python bot.py

Requires DISCORD_TOKEN environment variable.
"""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

import discord
from discord.ext import commands

from core.logging_config import configure_logging
from core.provider_manager import get_provider

# Load environment variables from .env file
load_dotenv()

# Configure logging early
configure_logging()
logger = logging.getLogger(__name__)


def create_bot() -> commands.Bot:
    """Create and return a configured Bot instance."""
    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True
    intents.guild_messages = True
    intents.dm_messages = True

    bot = commands.Bot(
        command_prefix="!",
        intents=intents,
        description="Advanced Discord RPG Bot with comprehensive waifu collection and battle system"
    )

    return bot


async def load_cogs(bot: commands.Bot) -> None:
    """Load all command cogs from the commands/ folder."""
    commands_dir = Path(__file__).parent / "commands"
    
    cog_modules = [
        "achievements",
        "admin",
        "arena",
        "battle",
        "contests",
        "crafting",
        "daily",
        "dreams",
        "economy",
        "events",
        "fan_clubs",
        "gallery",
        "guild",
        "help",
        "inspect",
        "intimate",
        "inventory",
        "lore",
        "mini_games",
        "misc",
        "mishaps",
        "pets",
        "profile",
        "pvp_bosses",
        "quests",
        "relics",
        "seasonal_events",
        "server_config",
        "server_setup",
        "store",
        "summon",
        "traits",
        "upgrade",
    ]

    for module_name in cog_modules:
        try:
            await bot.load_extension(f"commands.{module_name}")
            logger.info(f"✓ Loaded cog: {module_name}")
        except Exception as e:
            logger.error(f"✗ Failed to load cog {module_name}: {e}")


async def setup_bot(bot: commands.Bot) -> None:
    """Initialize bot event handlers and other setup."""

    @bot.event
    async def on_ready():
        logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
        logger.info(f"Connected to {len(bot.guilds)} guilds")
        # Initialize data provider
        provider = get_provider()
        logger.info(f"Data provider initialized: {provider.__class__.__name__}")

    @bot.event
    async def on_command_error(ctx: commands.Context, error: Exception) -> None:
        """Global command error handler."""
        if isinstance(error, commands.CommandNotFound):
            return
        logger.error(f"Command error in {ctx.command}: {error}", exc_info=error)


async def main() -> None:
    """Main entrypoint: create bot, load cogs, and run."""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN environment variable not set. Exiting.")
        raise RuntimeError("DISCORD_TOKEN is required")

    bot = create_bot()

    async with bot:
        await load_cogs(bot)
        await setup_bot(bot)
        await bot.start(token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
