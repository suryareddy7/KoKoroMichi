"""
Battle balance constants and configuration.

Defines all balancing parameters: elemental charts, buff/debuff definitions,
status effects, and scaling factors. Can be loaded from JSON for easy tweaking.
"""

from core.battle_models import (
    BuffDef, DebuffDef, StatusEffectDef, BattleConfig
)


# ============================================================================
# ELEMENTAL ADVANTAGE CHART
# ============================================================================

ELEMENTAL_CHART = {
    "fire": {"fire": 1.0, "water": 0.8, "grass": 1.2, "neutral": 1.0},
    "water": {"water": 1.0, "grass": 0.8, "fire": 1.2, "neutral": 1.0},
    "grass": {"grass": 1.0, "fire": 0.8, "water": 1.2, "neutral": 1.0},
    "neutral": {"fire": 1.0, "water": 1.0, "grass": 1.0, "neutral": 1.0},
    "light": {"dark": 1.3, "light": 1.0, "neutral": 1.0},
    "dark": {"light": 1.3, "dark": 1.0, "neutral": 1.0},
}

# ============================================================================
# BUFF DEFINITIONS
# ============================================================================

BUFF_DEFINITIONS = {
    "attack_up": BuffDef(
        id="attack_up",
        name="Attack Up",
        stat_multiplier={"atk": 1.3},
        duration=3,
        stackable=True,
        max_stacks=3,
        overwrite_rule="stack",
    ),
    "defense_up": BuffDef(
        id="defense_up",
        name="Defense Up",
        stat_multiplier={"def_": 1.3},
        duration=3,
        stackable=True,
        max_stacks=3,
        overwrite_rule="stack",
    ),
    "speed_up": BuffDef(
        id="speed_up",
        name="Speed Up",
        stat_multiplier={"spd": 1.2},
        duration=2,
        stackable=True,
        max_stacks=2,
        overwrite_rule="stack",
    ),
    "elemental_shield": BuffDef(
        id="elemental_shield",
        name="Elemental Shield",
        stat_multiplier={"elem_def": 1.4},
        duration=3,
        stackable=False,
        max_stacks=1,
        overwrite_rule="refresh",
    ),
    "focus": BuffDef(
        id="focus",
        name="Focus",
        stat_multiplier={"elem_atk": 1.2},
        duration=2,
        stackable=True,
        max_stacks=2,
        overwrite_rule="stack",
    ),
}

# ============================================================================
# DEBUFF DEFINITIONS
# ============================================================================

DEBUFF_DEFINITIONS = {
    "attack_down": DebuffDef(
        id="attack_down",
        name="Attack Down",
        stat_reduction={"atk": 0.7},
        duration=3,
        stackable=True,
        max_stacks=3,
        overwrite_rule="stack",
    ),
    "defense_down": DebuffDef(
        id="defense_down",
        name="Defense Down",
        stat_reduction={"def_": 0.7},
        duration=3,
        stackable=True,
        max_stacks=3,
        overwrite_rule="stack",
    ),
    "speed_down": DebuffDef(
        id="speed_down",
        name="Speed Down",
        stat_reduction={"spd": 0.6},
        duration=2,
        stackable=True,
        max_stacks=2,
        overwrite_rule="stack",
    ),
    "vulnerability": DebuffDef(
        id="vulnerability",
        name="Vulnerability",
        stat_reduction={"elem_def": 0.5},
        duration=3,
        stackable=False,
        max_stacks=1,
        overwrite_rule="refresh",
    ),
}

# ============================================================================
# STATUS EFFECT DEFINITIONS
# ============================================================================

STATUS_EFFECTS = {
    "poison": StatusEffectDef(
        id="poison",
        name="Poison",
        dmg_per_round=15,
        duration=5,
        stackable=True,
        max_stacks=3,
    ),
    "bleed": StatusEffectDef(
        id="bleed",
        name="Bleed",
        dmg_per_round=20,
        duration=4,
        stackable=True,
        max_stacks=2,
    ),
    "burn": StatusEffectDef(
        id="burn",
        name="Burn",
        dmg_per_round=25,
        duration=3,
        stackable=True,
        max_stacks=2,
    ),
    "freeze": StatusEffectDef(
        id="freeze",
        name="Freeze",
        dmg_per_round=0,  # damage from thaw, not per-turn
        duration=2,
        stackable=False,
        max_stacks=1,
    ),
}

# ============================================================================
# GLOBAL BALANCE CONSTANTS
# ============================================================================

# Critical hit mechanics
CRIT_CHANCE_BASE = 0.10  # 10% base crit chance
CRIT_MULTIPLIER = 1.5  # 50% damage increase on crit

# Accuracy and evasion
ACCURACY_BASE = 1.0
DODGE_SCALING = 0.01  # 1% dodge per AGI point

# Armor and mitigation
ARMOR_SCALING = 0.05  # 5% damage reduction per DEF point
MIN_DAMAGE = 1  # minimum damage always dealt

# Status effect scaling
POISON_DMG_PER_ROUND = 15
BLEED_DMG_PER_ROUND = 20
BURN_DMG_PER_ROUND = 25
STUN_DURATION = 1  # turns stunned

# Buff/debuff mechanics
MAX_BUFF_STACKS = 3
MAX_DEBUFF_STACKS = 3

# Turn order
SPEED_PRIORITY_SCALE = 1.0  # multiplier for speed in turn order

# ============================================================================
# DEFAULT BATTLE CONFIG
# ============================================================================

DEFAULT_BATTLE_CONFIG = BattleConfig(
    max_rounds=50,
    rng_seed=None,
    elemental_advantage=ELEMENTAL_CHART,
    crit_chance_base=CRIT_CHANCE_BASE,
    crit_multiplier=CRIT_MULTIPLIER,
    dodge_scaling=DODGE_SCALING,
    accuracy_base=ACCURACY_BASE,
    armor_scaling=ARMOR_SCALING,
    max_buff_stacks=MAX_BUFF_STACKS,
    poison_dmg_per_round=POISON_DMG_PER_ROUND,
    stun_duration=STUN_DURATION,
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_buff_definition(buff_id: str) -> BuffDef:
    """Get a buff definition by ID."""
    return BUFF_DEFINITIONS.get(buff_id)


def get_debuff_definition(debuff_id: str) -> DebuffDef:
    """Get a debuff definition by ID."""
    return DEBUFF_DEFINITIONS.get(debuff_id)


def get_status_effect_definition(status_id: str) -> StatusEffectDef:
    """Get a status effect definition by ID."""
    return STATUS_EFFECTS.get(status_id)


def get_elemental_multiplier(attacker_element: str, defender_element: str) -> float:
    """Get damage multiplier based on elemental advantage."""
    return ELEMENTAL_CHART.get(attacker_element, {}).get(
        defender_element, 1.0
    )
