"""
Battle engine data models using Pydantic v2 for type safety and validation.

Includes: Character stats, skills, buffs/debuffs, participants, events, battle state,
and final results. All models are immutable during battle execution unless explicitly
marked as mutable (e.g., BattleState).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
import time


# ============================================================================
# ENUMS & TYPES
# ============================================================================


class TargetType(str, Enum):
    """Skill target classification."""
    SINGLE = "single"
    AOE = "aoe"  # Area of effect


class SkillType(str, Enum):
    """Skill type classification."""
    PHYSICAL = "physical"
    MAGICAL = "magical"
    HEAL = "heal"
    STATUS = "status"  # applies status effects


class Team(str, Enum):
    """Battle team classification."""
    PLAYER = "player"
    NPC = "npc"


class EventType(str, Enum):
    """Battle event types for append-only logging."""
    ROUND_START = "round_start"
    TURN_ORDER_ROLLED = "turn_order_rolled"
    TURN_START = "turn_start"
    SKILL_USED = "skill_used"
    BUFF_APPLIED = "buff_applied"
    DEBUFF_APPLIED = "debuff_applied"
    STATUS_EFFECT_APPLIED = "status_effect_applied"
    HEAL = "heal"
    STATUS_TICK = "status_tick"
    TURN_END = "turn_end"
    PARTICIPANT_FAINTED = "participant_fainted"
    ROUND_END = "round_end"
    BATTLE_END = "battle_end"
    PHASE_TRIGGER = "phase_trigger"


# ============================================================================
# PYDANTIC MODELS (Immutable Game Domain)
# ============================================================================


class CharacterStats(BaseModel):
    """Base character stats."""
    model_config = ConfigDict(frozen=True)
    
    hp: int = Field(gt=0, description="Hit points")
    atk: int = Field(ge=0, description="Physical attack")
    def_: int = Field(ge=0, alias="def", description="Physical defense")
    spd: int = Field(ge=0, description="Speed (determines turn order)")
    elem_atk: int = Field(ge=0, description="Elemental attack")
    elem_def: int = Field(ge=0, description="Elemental defense")


class SkillEffect(BaseModel):
    """Effect applied by a skill."""
    model_config = ConfigDict(frozen=True)
    
    apply_buff: Optional[str] = None  # buff_id to apply
    apply_debuff: Optional[str] = None  # debuff_id to apply
    apply_status: Optional[str] = None  # status_id to apply
    heal_amount: Optional[int] = None  # direct heal


class Skill(BaseModel):
    """Character skill/action."""
    model_config = ConfigDict(frozen=True)
    
    id: str = Field(description="Unique skill identifier")
    name: str = Field(description="Display name")
    skill_type: SkillType = Field(description="Type of skill")
    element: Optional[str] = None  # fire, water, grass, etc.
    power: int = Field(ge=0, description="Base damage/heal power")
    accuracy: float = Field(ge=0, le=1, description="Hit chance (0-1)")
    target_type: TargetType = Field(description="Single or AoE")
    priority: int = Field(ge=-10, le=10, description="Turn priority")
    effects: List[SkillEffect] = Field(default_factory=list)
    cooldown: int = Field(ge=0, description="Turns between uses")


class PassiveAbility(BaseModel):
    """Character passive/trait ability."""
    model_config = ConfigDict(frozen=True)
    
    id: str = Field(description="Unique passive identifier")
    name: str = Field(description="Display name")
    trigger: str = Field(description="on_hit, on_damage_taken, on_death, start_of_battle")
    effect: str = Field(description="heal, buff, debuff, damage")
    params: Dict[str, Any] = Field(default_factory=dict)


class Character(BaseModel):
    """A character in the game (from JSON assets)."""
    model_config = ConfigDict(frozen=True)
    
    id: str = Field(description="Unique character ID")
    name: str = Field(description="Display name")
    element: str = Field(description="Primary element")
    rarity: str = Field(description="Rarity tier")
    stats: CharacterStats = Field(description="Base stats")
    skills: List[Skill] = Field(default_factory=list)
    passives: List[PassiveAbility] = Field(default_factory=list)


# ============================================================================
# BUFF/DEBUFF DEFINITIONS (Config-driven)
# ============================================================================


class BuffDef(BaseModel):
    """Buff definition from balance config."""
    model_config = ConfigDict(frozen=True)
    
    id: str
    name: str
    stat_multiplier: Dict[str, float] = Field(default_factory=dict)  # {"atk": 1.2}
    duration: int = Field(ge=1)
    stackable: bool = True
    max_stacks: int = 3
    overwrite_rule: str = "stack"  # "stack" | "refresh" | "max"


class DebuffDef(BaseModel):
    """Debuff definition from balance config."""
    model_config = ConfigDict(frozen=True)
    
    id: str
    name: str
    stat_reduction: Dict[str, float] = Field(default_factory=dict)  # {"def": 0.5}
    duration: int = Field(ge=1)
    stackable: bool = True
    max_stacks: int = 3
    overwrite_rule: str = "stack"


class StatusEffectDef(BaseModel):
    """Status effect definition from balance config."""
    model_config = ConfigDict(frozen=True)
    
    id: str
    name: str
    dmg_per_round: int = 0
    duration: int = Field(ge=1)
    stackable: bool = True
    max_stacks: int = 3


class BattleConfig(BaseModel):
    """Configurable battle parameters."""
    model_config = ConfigDict(frozen=True)
    
    max_rounds: int = Field(default=50, ge=10)
    rng_seed: Optional[int] = None  # None = random seed
    
    # Elemental advantage: {attacker_elem: {defender_elem: multiplier}}
    elemental_advantage: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    
    crit_chance_base: float = Field(default=0.10, ge=0, le=1)
    crit_multiplier: float = Field(default=1.5, gt=1)
    
    dodge_scaling: float = Field(default=0.01, description="% dodge per agility point")
    accuracy_base: float = Field(default=1.0, ge=0)
    
    armor_scaling: float = Field(default=0.05, description="% dmg reduction per def point")
    
    max_buff_stacks: int = Field(default=3, ge=1)
    buff_overwrite_rules: Dict[str, str] = Field(default_factory=dict)
    
    poison_dmg_per_round: int = Field(default=10, ge=0)
    stun_duration: int = Field(default=1, ge=1)


# ============================================================================
# MUTABLE STATE (during simulation)
# ============================================================================


@dataclass
class BuffState:
    """Active buff on a participant."""
    definition: BuffDef
    duration: int  # turns remaining
    stacks: int
    applied_round: int
    applied_turn: int


@dataclass
class DebuffState:
    """Active debuff on a participant."""
    definition: DebuffDef
    duration: int
    stacks: int
    applied_round: int
    applied_turn: int


@dataclass
class StatusEffectState:
    """Active status effect on a participant."""
    definition: StatusEffectDef
    duration: int
    stacks: int
    applied_round: int
    applied_turn: int


@dataclass
class StatsModifier:
    """Accumulated stat multipliers from buffs/debuffs."""
    atk_mult: float = 1.0
    def_mult: float = 1.0
    spd_mult: float = 1.0
    elem_atk_mult: float = 1.0
    elem_def_mult: float = 1.0
    
    def apply_stat(self, base_stat: int, stat_name: str) -> int:
        """Apply modifier to a stat value."""
        multiplier_name = f"{stat_name}_mult"
        if hasattr(self, multiplier_name):
            return max(1, int(base_stat * getattr(self, multiplier_name)))
        return base_stat


@dataclass
class Participant:
    """Character instance in battle with mutable state."""
    id: str
    character: Character
    team: Team
    current_hp: int
    buffs: Dict[str, BuffState] = field(default_factory=dict)
    debuffs: Dict[str, DebuffState] = field(default_factory=dict)
    status_effects: Dict[str, StatusEffectState] = field(default_factory=dict)
    stats_modifier: StatsModifier = field(default_factory=StatsModifier)
    
    def is_alive(self) -> bool:
        """Check if participant is still in battle."""
        return self.current_hp > 0
    
    def take_damage(self, amount: int) -> int:
        """Apply damage, return actual damage taken."""
        actual = min(self.current_hp, max(1, amount))
        self.current_hp -= actual
        return actual
    
    def heal(self, amount: int) -> int:
        """Apply healing, return actual healing done."""
        max_hp = self.character.stats.hp
        actual = min(max_hp - self.current_hp, amount)
        self.current_hp += actual
        return actual


# ============================================================================
# EVENTS (Immutable Log Entries)
# ============================================================================


@dataclass(frozen=True)
class Event:
    """Immutable battle event for append-only log."""
    round: int
    turn: int
    timestamp: float
    actor_id: str
    event_type: EventType
    details: Dict[str, Any] = field(default_factory=dict)
    seed_state: int = 0  # RNG state at event time (for replay)


@dataclass
class RoundSummary:
    """Summary of a single round."""
    round: int
    damage_dealt: Dict[str, int]  # {participant_id: total_damage}
    healing_done: Dict[str, int]
    participants_fainted: List[str]


@dataclass
class BattleSummary:
    """Summary statistics after battle."""
    total_damage_dealt: Dict[str, int]  # {participant_id: total}
    total_healing_done: Dict[str, int]
    critical_hits: int
    dodges: int
    buffs_applied: Dict[str, int]  # {buff_id: count}
    debuffs_applied: Dict[str, int]
    status_effects_applied: Dict[str, int]
    round_summaries: List[RoundSummary] = field(default_factory=list)


@dataclass
class BattleState:
    """Mutable battle state during simulation."""
    match_id: str
    player_party: List[Participant]
    npc_party: List[Participant]
    config: BattleConfig
    current_round: int = 0
    current_turn: int = 0
    turn_order: List[Tuple[Team, int]] = field(default_factory=list)
    participants: Dict[str, Participant] = field(default_factory=dict)
    events: List[Event] = field(default_factory=list)
    summary: BattleSummary = field(default_factory=lambda: BattleSummary(
        total_damage_dealt={},
        total_healing_done={},
        critical_hits=0,
        dodges=0,
        buffs_applied={},
        debuffs_applied={},
        status_effects_applied={}
    ))
    
    def get_participant(self, team: Team, idx: int) -> Optional[Participant]:
        """Get participant by team and index."""
        party = self.player_party if team == Team.PLAYER else self.npc_party
        return party[idx] if idx < len(party) else None
    
    def get_all_alive(self, team: Optional[Team] = None) -> List[Participant]:
        """Get all alive participants, optionally filtered by team."""
        if team is None:
            participants = self.player_party + self.npc_party
        else:
            participants = self.player_party if team == Team.PLAYER else self.npc_party
        
        return [p for p in participants if p.is_alive()]
    
    def get_all_fainted(self, team: Optional[Team] = None) -> List[Participant]:
        """Get all fainted participants."""
        if team is None:
            participants = self.player_party + self.npc_party
        else:
            participants = self.player_party if team == Team.PLAYER else self.npc_party
        
        return [p for p in participants if not p.is_alive()]
    
    def append_event(self, event_type: EventType, actor_id: str, 
                    details: Dict[str, Any], seed_state: int = 0) -> Event:
        """Create and append an event to the log."""
        event = Event(
            round=self.current_round,
            turn=self.current_turn,
            timestamp=time.time(),
            actor_id=actor_id,
            event_type=event_type,
            details=details,
            seed_state=seed_state
        )
        self.events.append(event)
        return event


# ============================================================================
# BATTLE MATCH & RESULT
# ============================================================================


@dataclass
class BattleMatch:
    """Complete battle specification and execution container."""
    match_id: str
    player_party: List[Character]
    npc_party: List[Character]
    config: BattleConfig
    rng_seed: int  # actual seed used (resolved if config had None)
    state: Optional[BattleState] = None
    log: List[Event] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class BattleResult:
    """Final battle outcome and statistics."""
    match_id: str
    winner: Team
    player_alive: List[Character]
    npc_alive: List[Character]
    rounds_survived: int
    match_log: List[Event]
    summary: BattleSummary
    duration_ms: float
    replay_seed: int  # seed for deterministic replay


@dataclass
class ReplayOutput:
    """Result of replaying a match from log."""
    match_id: str
    original_seed: int
    replay_seed: int
    events_matched: int
    total_events: int
    final_state_matched: bool
    divergence_point: Optional[int] = None  # event index where divergence occurred


# ============================================================================
# QUEUE TYPES
# ============================================================================


@dataclass
class QueuedMatch:
    """Match queued for arena processing."""
    match: BattleMatch
    priority: int
    queued_at: float = field(default_factory=time.time)
    
    def __lt__(self, other: "QueuedMatch") -> bool:
        """For PriorityQueue ordering (higher priority = lower value)."""
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.queued_at < other.queued_at
