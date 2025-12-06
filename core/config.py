# Configuration for KoKoroMichi Advanced Bot
import os
from pathlib import Path

# Bot Information
BOT_NAME = "KoKoroMichi"
BOT_VERSION = "3.0.0 Advanced"
BOT_DESCRIPTION = "Advanced Discord RPG Bot with comprehensive waifu collection and battle system"

# File paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
CHARACTERS_DIR = ASSETS_DIR / "characters"
RELICS_DIR = DATA_DIR / "relics"

# Default values
DEFAULT_GOLD = 10000
DEFAULT_GEMS = 100
MAX_LEVEL = 100
DEFAULT_HP = 100
DEFAULT_ATK = 50
DEFAULT_DEF = 30

# Discord Configuration
COMMAND_PREFIX = "!"
EMBED_COLOR = 0xFF69B4  # Hot pink

# Admin Configuration
ADMIN_USER_ID = "1344603209829974016"  # Your Discord user ID

# Feature Flags
FEATURES = {
    "investment_system_enabled": True,
    "pvp_enabled": True,
    "guild_system_enabled": True,
    "crafting_enabled": True,
    "dream_events_enabled": True,
    "seasonal_events_enabled": True,
    "achievement_system_enabled": True,
    "auction_system_enabled": True,
    "pet_system_enabled": True
}

# Game Mechanics
RARITY_TIERS = {
    "Mythic": {"threshold": 7000, "emoji": "🌈✨✨", "chance": 0.1, "multiplier": 7},
    "LR": {"threshold": 6000, "emoji": "⚡", "chance": 0.5, "multiplier": 6},
    "UR": {"threshold": 5500, "emoji": "🌟", "chance": 1.0, "multiplier": 5},
    "SSR": {"threshold": 5000, "emoji": "🌈✨", "chance": 3.0, "multiplier": 4},
    "SR": {"threshold": 4000, "emoji": "🔥", "chance": 10.0, "multiplier": 3},
    "R": {"threshold": 3000, "emoji": "🔧", "chance": 25.0, "multiplier": 2},
    "N": {"threshold": 0, "emoji": "🌿", "chance": 60.4, "multiplier": 1}
}

# Economy Settings
SUMMON_COST = 50  # Gems cost per summon
BULK_SUMMON_DISCOUNT = 0.1  # 10% discount for 10+ summons
INVESTMENT_MULTIPLIER = 1.2  # Investment return rate

# Battle Settings
BATTLE_XP_BASE = 50
BATTLE_GOLD_BASE = 100
LEVEL_UP_MULTIPLIER = 100
BATTLE_ROUNDS_MAX = 20
CRIT_BASE_MULTIPLIER = 1.5
LEVEL_STAT_GROWTH = {"hp": 10, "atk": 3, "def": 2, "speed": 1}

# Rarity Weights for random generation
RARITY_WEIGHTS = {
    "Mythic": 1,
    "LR": 5,
    "UR": 10,
    "SSR": 30,
    "SR": 100,
    "R": 250,
    "N": 604
}

# Error messages
ERROR_MESSAGES = {
    "user_not_found": "Profile not found. Use `!profile` to create one.",
    "insufficient_funds": "You don't have enough gold or gems for this action.",
    "command_cooldown": "This command is on cooldown. Please wait before using it again.",
    "permission_denied": "You don't have permission to use this command.",
    "waifu_not_found": "Character not found in your collection.",
    "invalid_amount": "Please provide a valid amount.",
    "data_error": "Error accessing game data. Please try again later."
}

# Success messages
SUCCESS_MESSAGES = {
    "profile_created": "Welcome to KoKoroMichi! Your adventure begins now!",
    "summon_success": "Summoning successful! Check your new character!",
    "battle_victory": "Victory! You've earned rewards!",
    "level_up": "Congratulations! You've leveled up!",
    "investment_success": "Investment completed successfully!"
}

# Emoji sets
ENCOURAGING_EMOJIS = ["✨", "🌟", "💖", "🔥", "🎉", "🌈", "⭐", "💫"]
RARITY_EMOJIS = {
    "Mythic": "🌈✨✨",
    "LR": "⚡",
    "UR": "🌟", 
    "SSR": "🌈✨",
    "SR": "🔥",
    "R": "🔧",
    "N": "🌿"
}