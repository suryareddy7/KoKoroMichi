"""Helper utilities for KoKoroMichi bot"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import time


def format_number(number: int | float) -> str:
    """Format numbers with K/M notation for large values.
    
    Examples:
        1000 -> "1.0K"
        1500000 -> "1.5M"
        500 -> "500"
    """
    if isinstance(number, float):
        number = int(number)
    
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M".rstrip('0').rstrip('.')
    elif number >= 1_000:
        return f"{number / 1_000:.1f}K".rstrip('0').rstrip('.')
    else:
        return str(number)


def calculate_level_from_xp(total_xp: int) -> int:
    """Calculate user level from total XP.
    
    Uses exponential scaling: each level requires 1000 * level XP.
    """
    level = 1
    xp_needed = 0
    
    while True:
        xp_needed += 1000 * level
        if total_xp < xp_needed:
            break
        level += 1
    
    return level


def create_progress_bar(current: int, maximum: int, length: int = 10) -> str:
    """Create a visual progress bar.
    
    Args:
        current: Current progress value
        maximum: Maximum progress value
        length: Length of progress bar (default 10)
    
    Returns:
        String representation of progress bar
    """
    if maximum == 0:
        return "▯" * length
    
    filled = int((current / maximum) * length)
    filled = min(filled, length)
    empty = length - filled
    
    return "▮" * filled + "▯" * empty


def find_character_by_name(characters: List[Dict], search_name: str) -> Optional[Dict]:
    """Find a character in a list by name (case-insensitive partial match).
    
    Args:
        characters: List of character dictionaries
        search_name: Name to search for
    
    Returns:
        Character dict if found, None otherwise
    """
    if not search_name or not characters:
        return None
    
    search_lower = search_name.lower().strip()
    
    # Exact match first
    for char in characters:
        if char.get("name", "").lower() == search_lower:
            return char
    
    # Partial match
    for char in characters:
        if search_lower in char.get("name", "").lower():
            return char
    
    return None


def calculate_battle_power(character: Dict) -> float:
    """Calculate a character's battle power score.
    
    Args:
        character: Character dictionary with stats
    
    Returns:
        Numeric battle power score
    """
    hp = character.get("hp", 100)
    atk = character.get("atk", 10)
    defense = character.get("def", 5)
    speed = character.get("speed", 5)
    level = character.get("level", 1)
    rarity_multipliers = {
        "N": 1.0, "R": 1.2, "SR": 1.5,
        "SSR": 2.0, "UR": 2.5, "LR": 3.0, "Mythic": 4.0
    }
    rarity = character.get("rarity", "N")
    multiplier = rarity_multipliers.get(rarity, 1.0)
    
    # Simple formula: base stats + level scaling
    power = (hp * 0.5 + atk * 2 + defense * 1.5 + speed * 0.8) * level * multiplier
    
    return max(1.0, power)


def validate_amount(amount: str | int | float) -> Optional[int]:
    """Validate and parse a currency/amount input.
    
    Supports:
        - Plain numbers: 100
        - K notation: 1.5K -> 1500
        - M notation: 2M -> 2000000
    
    Returns:
        Parsed integer or None if invalid
    """
    try:
        if isinstance(amount, (int, float)):
            return int(amount)
        
        amount_str = str(amount).upper().strip().replace(",", "")
        
        if not amount_str:
            return None
        
        if 'M' in amount_str:
            return int(float(amount_str.replace('M', '')) * 1_000_000)
        elif 'K' in amount_str:
            return int(float(amount_str.replace('K', '')) * 1_000)
        else:
            return int(float(amount_str))
    except (ValueError, AttributeError):
        return None


def is_on_cooldown(user_id: str, action: str, cooldown_seconds: int, cooldown_tracker: Dict = None) -> bool:
    """Check if a user is on cooldown for an action.
    
    Args:
        user_id: Discord user ID
        action: Action name (e.g., "daily", "hourly")
        cooldown_seconds: Cooldown duration in seconds
        cooldown_tracker: Shared cooldown dictionary (default: in-memory)
    
    Returns:
        True if on cooldown, False if ready
    """
    if cooldown_tracker is None:
        cooldown_tracker = {}
    
    key = f"{user_id}:{action}"
    now = time.time()
    
    if key in cooldown_tracker:
        elapsed = now - cooldown_tracker[key]
        if elapsed < cooldown_seconds:
            return True
    
    cooldown_tracker[key] = now
    return False


def get_cooldown_remaining(user_id: str, action: str, cooldown_seconds: int, cooldown_tracker: Dict = None) -> int:
    """Get remaining cooldown seconds for a user action.
    
    Args:
        user_id: Discord user ID
        action: Action name
        cooldown_seconds: Cooldown duration in seconds
        cooldown_tracker: Shared cooldown dictionary
    
    Returns:
        Remaining seconds (0 if no cooldown)
    """
    if cooldown_tracker is None:
        cooldown_tracker = {}
    
    key = f"{user_id}:{action}"
    now = time.time()
    
    if key not in cooldown_tracker:
        return 0
    
    elapsed = now - cooldown_tracker[key]
    remaining = cooldown_seconds - elapsed
    
    return max(0, int(remaining))


def generate_unique_id(prefix: str = "") -> str:
    """Generate a unique ID.
    
    Args:
        prefix: Optional prefix for the ID
    
    Returns:
        Unique identifier string
    """
    import uuid
    unique = str(uuid.uuid4())[:8]
    return f"{prefix}{unique}" if prefix else unique


def is_admin(ctx: Any) -> bool:
    """Check if user is a bot admin.
    
    Args:
        ctx: Discord context
    
    Returns:
        True if user is admin, False otherwise
    """
    # Admin if user is server owner or has admin role
    if ctx.author == ctx.guild.owner:
        return True
    
    # Check for admin permissions
    if ctx.author.guild_permissions.administrator:
        return True
    
    return False


def check_elemental_advantage(attacker_element: str, defender_element: str) -> float:
    """Calculate elemental advantage multiplier.
    
    Type advantages (2x damage):
        Fire > Grass, Bug, Steel
        Water > Fire, Ground, Rock
        Grass > Water, Ground, Rock
        Electric > Water, Flying
        Ice > Grass, Flying, Ground, Dragon
        Fighting > Normal, Ice, Rock, Dark, Steel
        Poison > Grass, Fairy
        Ground > Fire, Electric, Poison, Rock, Steel
        Flying > Grass, Fighting, Bug
        Psychic > Fighting, Poison
        Bug > Grass, Psychic, Dark
        Rock > Fire, Ice, Flying, Bug
        Ghost > Psychic, Ghost
        Dragon > Dragon
        Dark > Psychic, Ghost
        Steel > Ice, Rock, Fairy
        Fairy > Fighting, Dragon, Dark
    
    Args:
        attacker_element: Attacker's element type
        defender_element: Defender's element type
    
    Returns:
        Damage multiplier (1.0 = normal, 2.0 = super effective, 0.5 = not effective)
    """
    advantages = {
        "fire": ["grass", "bug", "steel"],
        "water": ["fire", "ground", "rock"],
        "grass": ["water", "ground", "rock"],
        "electric": ["water", "flying"],
        "ice": ["grass", "flying", "ground", "dragon"],
        "fighting": ["normal", "ice", "rock", "dark", "steel"],
        "poison": ["grass", "fairy"],
        "ground": ["fire", "electric", "poison", "rock", "steel"],
        "flying": ["grass", "fighting", "bug"],
        "psychic": ["fighting", "poison"],
        "bug": ["grass", "psychic", "dark"],
        "rock": ["fire", "ice", "flying", "bug"],
        "ghost": ["psychic", "ghost"],
        "dragon": ["dragon"],
        "dark": ["psychic", "ghost"],
        "steel": ["ice", "rock", "fairy"],
        "fairy": ["fighting", "dragon", "dark"],
        "normal": [],
        "neutral": []
    }
    
    attacker = attacker_element.lower()
    defender = defender_element.lower()
    
    if attacker in advantages and defender in advantages[attacker]:
        return 2.0  # Super effective
    
    return 1.0  # Normal effectiveness


def generate_random_stats(rarity: str) -> Dict[str, int]:
    """Generate random stats for a newly summoned character.
    
    Args:
        rarity: Rarity tier (N, R, SR, SSR, UR, LR, Mythic)
    
    Returns:
        Dictionary of stat values
    """
    import random
    
    stat_ranges = {
        "N": {"hp": (80, 100), "atk": (8, 12), "def": (4, 7), "speed": (3, 6)},
        "R": {"hp": (100, 130), "atk": (12, 18), "def": (7, 11), "speed": (6, 10)},
        "SR": {"hp": (130, 160), "atk": (18, 26), "def": (11, 15), "speed": (10, 14)},
        "SSR": {"hp": (160, 200), "atk": (26, 35), "def": (15, 20), "speed": (14, 18)},
        "UR": {"hp": (200, 250), "atk": (35, 50), "def": (20, 28), "speed": (18, 24)},
        "LR": {"hp": (250, 300), "atk": (50, 70), "def": (28, 35), "speed": (24, 30)},
        "Mythic": {"hp": (300, 350), "atk": (70, 100), "def": (35, 45), "speed": (30, 40)}
    }
    
    ranges = stat_ranges.get(rarity, stat_ranges["N"])
    
    return {
        "hp": random.randint(*ranges["hp"]),
        "atk": random.randint(*ranges["atk"]),
        "def": random.randint(*ranges["def"]),
        "speed": random.randint(*ranges["speed"])
    }


def get_random_element() -> str:
    """Get a random elemental type.
    
    Returns:
        Random element type string
    """
    import random
    elements = ["fire", "water", "grass", "electric", "ice", "fighting", 
                "poison", "ground", "flying", "psychic", "bug", "rock", 
                "ghost", "dragon", "dark", "steel", "fairy"]
    return random.choice(elements)
