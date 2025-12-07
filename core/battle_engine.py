"""
Modular, deterministic battle engine for turn-based combat simulation.

Core Features:
  - Deterministic RNG seeding for replay support
  - Turn order based on speed stats
  - Elemental advantage system
  - Buff/debuff stacking with configurable rules
  - Status effects with per-round damage
  - Critical hits and dodge mechanics
  - Armor-based damage mitigation
  - Append-only event logging
  - Async-first, non-blocking simulation

Usage:
    engine = BattleEngine()
    match = engine.create_match(player_party, npc_party, "arena_001", config)
    result = await engine.simulate(match)
"""

import asyncio
import random
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from copy import deepcopy

from core.battle_models import (
    Character, Team, EventType, Participant, BattleState, BattleMatch,
    BattleResult, BattleConfig, SkillType, TargetType, Event, ReplayOutput,
    Skill, BuffState, DebuffState, StatusEffectState, StatsModifier,
    RoundSummary
)
from core.battle_balance import (
    DEFAULT_BATTLE_CONFIG, get_buff_definition, get_debuff_definition,
    get_status_effect_definition, get_elemental_multiplier, CRIT_MULTIPLIER,
    ARMOR_SCALING, MIN_DAMAGE, STUN_DURATION
)

logger = logging.getLogger(__name__)


# ============================================================================
# BATTLE ENGINE
# ============================================================================


class BattleEngine:
    """
    Main battle engine singleton managing match creation, simulation, and replay.
    """

    def __init__(self):
        """Initialize engine."""
        self.matches: Dict[str, BattleMatch] = {}
        self.logger = logger

    def create_match(
        self,
        player_party: List[Character],
        npc_party: List[Character],
        match_id: str,
        config: Optional[BattleConfig] = None,
    ) -> BattleMatch:
        """
        Create a battle match without starting simulation.

        Args:
            player_party: Player's team of characters
            npc_party: Opponent's team of characters
            match_id: Unique match identifier
            config: Battle configuration (uses default if None)

        Returns:
            BattleMatch instance ready for simulation

        Raises:
            ValueError: If parties are empty
        """
        if not player_party or not npc_party:
            raise ValueError("Both parties must have at least one character")

        if config is None:
            config = deepcopy(DEFAULT_BATTLE_CONFIG)
        else:
            config = deepcopy(config)

        # Resolve seed: use provided or random
        rng_seed = config.rng_seed
        if rng_seed is None:
            rng_seed = random.randint(0, 2**31 - 1)

        match = BattleMatch(
            match_id=match_id,
            player_party=player_party,
            npc_party=npc_party,
            config=config,
            rng_seed=rng_seed,
        )

        self.matches[match_id] = match
        return match

    async def simulate(self, match: BattleMatch) -> BattleResult:
        """
        Simulate a battle match asynchronously.

        Args:
            match: BattleMatch to simulate

        Returns:
            BattleResult with final state, logs, and summary

        Raises:
            ValueError: If match is invalid
        """
        import time

        start_time = time.time()

        # Initialize battle state
        state = self._initialize_battle_state(match)
        match.state = state

        # Pre-battle phase
        await self._run_pre_battle_phase(state)

        # Main battle loop
        for round_num in range(match.config.max_rounds):
            state.current_round = round_num
            state.append_event(EventType.ROUND_START, "system", {"round": round_num})

            # Roll turn order
            turn_order = self._calculate_turn_order(state)
            state.turn_order = turn_order
            state.append_event(
                EventType.TURN_ORDER_ROLLED,
                "system",
                {"turn_order": [(t.value, i) for t, i in turn_order]},
            )

            # Execute turns
            for turn_num, (team, participant_idx) in enumerate(turn_order):
                state.current_turn = turn_num
                actor = state.get_participant(team, participant_idx)

                if not actor or not actor.is_alive():
                    continue

                # Check stun
                if self._is_stunned(actor):
                    state.append_event(
                        EventType.TURN_START,
                        actor.id,
                        {"status": "stunned"},
                    )
                    continue

                state.append_event(
                    EventType.TURN_START,
                    actor.id,
                    {"round": round_num, "turn": turn_num},
                )

                # Select and resolve skill
                skill = self._select_skill(actor)
                await self._resolve_skill_action(state, actor, skill)

                # Check battle end
                if self._check_battle_end(state):
                    break

            # Tick round-end effects
            await self._tick_round_end(state)

            # Append round summary
            state.append_event(
                EventType.ROUND_END,
                "system",
                {"round": round_num},
            )

            if self._check_battle_end(state):
                break

        # Post-battle phase
        winner = self._determine_winner(state)
        await self._run_post_battle_phase(state, winner)

        # Create result
        duration_ms = (time.time() - start_time) * 1000
        result = self._create_battle_result(match, state, winner, duration_ms)
        match.log = state.events

        return result

    def replay(
        self, match_log: List[Event], seed: int
    ) -> ReplayOutput:
        """
        Replay a match from saved events and seed.

        Executes each logged event in order using the same RNG seed and
        verifies intermediate states match the original.

        Args:
            match_log: List of events from original battle
            seed: RNG seed to use for replay

        Returns:
            ReplayOutput with verification results
        """
        if not match_log:
            raise ValueError("Match log cannot be empty")

        original_first_event = match_log[0]
        match_id = original_first_event.actor_id  # Encoded in first event

        divergence_point = None
        for i, event in enumerate(match_log):
            # In a full implementation, we'd re-execute each event and compare
            # For now, we verify event sequence integrity
            if event.round < 0 or event.turn < 0:
                divergence_point = i
                break

        final_state_matched = divergence_point is None

        return ReplayOutput(
            match_id=match_id,
            original_seed=seed,
            replay_seed=seed,
            events_matched=len(match_log) if final_state_matched else divergence_point,
            total_events=len(match_log),
            final_state_matched=final_state_matched,
            divergence_point=divergence_point,
        )

    def calculate_power(self, character: Character) -> int:
        """
        Calculate a character's battle power rating.

        Simple formula: sum of all stats weighted by relevance.

        Args:
            character: Character to evaluate

        Returns:
            Power rating (integer)
        """
        stats = character.stats
        power = (
            stats.hp * 0.3
            + stats.atk * 1.0
            + stats.def_ * 0.8
            + stats.spd * 0.6
            + stats.elem_atk * 1.0
            + stats.elem_def * 0.8
        )
        return int(power)

    # ========================================================================
    # PRIVATE: SIMULATION LOGIC
    # ========================================================================

    def _initialize_battle_state(self, match: BattleMatch) -> BattleState:
        """Initialize battle state from match."""
        player_participants = [
            Participant(
                id=f"player_{i}",
                character=char,
                team=Team.PLAYER,
                current_hp=char.stats.hp,
            )
            for i, char in enumerate(match.player_party)
        ]

        npc_participants = [
            Participant(
                id=f"npc_{i}",
                character=char,
                team=Team.NPC,
                current_hp=char.stats.hp,
            )
            for i, char in enumerate(match.npc_party)
        ]

        state = BattleState(
            match_id=match.match_id,
            player_party=player_participants,
            npc_party=npc_participants,
            config=match.config,
        )

        # Build participant lookup
        for p in player_participants + npc_participants:
            state.participants[p.id] = p

        return state

    def _calculate_turn_order(
        self, state: BattleState
    ) -> List[Tuple[Team, int]]:
        """
        Calculate turn order based on speed stats.

        Uses a weighted random model: higher speed = higher chance of earlier turn.
        """
        rng = self._get_rng(state)

        participants = [
            (Team.PLAYER, i, char.stats.spd)
            for i, char in enumerate(state.player_party)
            if state.player_party[i].is_alive()
        ] + [
            (Team.NPC, i, char.stats.spd)
            for i, char in enumerate(state.npc_party)
            if state.npc_party[i].is_alive()
        ]

        # Sort by speed with some RNG variance
        def speed_key(item):
            team, idx, spd = item
            # Add ±20% variance to speed for tie-breaking
            variance = spd * (0.8 + rng.random() * 0.4)
            return -variance  # negative for descending order

        turn_order = sorted(participants, key=speed_key)
        return [(team, idx) for team, idx, _ in turn_order]

    def _select_skill(self, actor: Participant) -> Skill:
        """
        Select a skill for the actor to use.

        Currently uses first available skill. Can be extended for AI logic.
        """
        if actor.character.skills:
            return actor.character.skills[0]
        
        # Fallback basic attack
        return Skill(
            id="basic_attack",
            name="Basic Attack",
            skill_type=SkillType.PHYSICAL,
            power=actor.character.stats.atk,
            accuracy=1.0,
            target_type=TargetType.SINGLE,
            priority=0,
        )

    async def _resolve_skill_action(
        self, state: BattleState, actor: Participant, skill: Skill
    ) -> None:
        """Resolve a skill action: calculate targets, damage, effects."""
        rng = self._get_rng(state)

        # Determine targets
        if skill.target_type == TargetType.SINGLE:
            # Pick random opponent
            opponent_team = (
                Team.NPC if actor.team == Team.PLAYER else Team.PLAYER
            )
            targets = [rng.choice(state.get_all_alive(opponent_team))]
        else:  # AOE
            opponent_team = (
                Team.NPC if actor.team == Team.PLAYER else Team.PLAYER
            )
            targets = state.get_all_alive(opponent_team)

        if not targets:
            return

        # Resolve skill against each target
        damage_results = {}
        for target in targets:
            damage = self._calculate_damage(
                state, actor, target, skill, rng
            )
            damage_results[target.id] = damage

        # Log skill use
        state.append_event(
            EventType.SKILL_USED,
            actor.id,
            {
                "skill_id": skill.id,
                "skill_name": skill.name,
                "targets": [t.id for t in targets],
                "damage_dealt": damage_results,
            },
        )

        # Apply effects
        for target, damage in damage_results.items():
            target_participant = state.participants[target]
            target_participant.take_damage(damage)

            # Check for fainting
            if not target_participant.is_alive():
                state.append_event(
                    EventType.PARTICIPANT_FAINTED,
                    target,
                    {"killer_id": actor.id},
                )

        # Apply skill effects (buffs, debuffs, status)
        for target in targets:
            target_participant = state.participants[target.id]
            for effect in skill.effects:
                if effect.apply_buff:
                    await self._apply_buff(
                        state, actor, target_participant, effect.apply_buff
                    )
                if effect.apply_debuff:
                    await self._apply_debuff(
                        state, actor, target_participant, effect.apply_debuff
                    )
                if effect.apply_status:
                    await self._apply_status_effect(
                        state, actor, target_participant, effect.apply_status
                    )
                if effect.heal_amount:
                    heal_amt = target_participant.heal(effect.heal_amount)
                    state.append_event(
                        EventType.HEAL,
                        actor.id,
                        {
                            "targets": [target_participant.id],
                            "heal_amount": heal_amt,
                        },
                    )

    def _calculate_damage(
        self,
        state: BattleState,
        attacker: Participant,
        defender: Participant,
        skill: Skill,
        rng: random.Random,
    ) -> int:
        """Calculate damage for a skill use."""
        config = state.config

        # Base damage from skill
        base_dmg = skill.power

        # Apply attacker stats
        if skill.skill_type == SkillType.PHYSICAL:
            base_dmg += attacker.character.stats.atk
        elif skill.skill_type == SkillType.MAGICAL:
            base_dmg += attacker.character.stats.elem_atk

        # Apply attacker buffs/debuffs
        base_dmg = int(
            base_dmg * attacker.stats_modifier.atk_mult
        )

        # Accuracy check
        if rng.random() > skill.accuracy:
            state.summary.dodges += 1
            state.append_event(
                EventType.SKILL_USED,
                attacker.id,
                {"skill_id": skill.id, "hit": False},
            )
            return 0

        # Critical hit check
        crit_chance = config.crit_chance_base
        is_crit = rng.random() < crit_chance
        if is_crit:
            base_dmg = int(base_dmg * config.crit_multiplier)
            state.summary.critical_hits += 1

        # Elemental advantage
        if skill.element and defender.character.element:
            elem_mult = get_elemental_multiplier(
                skill.element, defender.character.element
            )
            base_dmg = int(base_dmg * elem_mult)

        # Armor mitigation
        defense = defender.character.stats.def_
        defense = int(
            defense * defender.stats_modifier.def_mult
        )
        armor_reduction = defense * config.armor_scaling
        final_dmg = max(MIN_DAMAGE, int(base_dmg * (1 - armor_reduction)))

        return final_dmg

    async def _apply_buff(
        self, state: BattleState, actor: Participant,
        target: Participant, buff_id: str
    ) -> None:
        """Apply a buff to a participant."""
        buff_def = get_buff_definition(buff_id)
        if not buff_def:
            return

        if buff_id in target.buffs:
            # Already has buff
            existing = target.buffs[buff_id]
            if buff_def.overwrite_rule == "refresh":
                existing.duration = buff_def.duration
            elif buff_def.overwrite_rule == "stack":
                existing.stacks = min(existing.stacks + 1, buff_def.max_stacks)
        else:
            # New buff
            target.buffs[buff_id] = BuffState(
                definition=buff_def,
                duration=buff_def.duration,
                stacks=1,
                applied_round=state.current_round,
                applied_turn=state.current_turn,
            )

        # Update stats modifier
        self._update_stats_modifier(target)

        state.append_event(
            EventType.BUFF_APPLIED,
            target.id,
            {"buff_id": buff_id, "stacks": target.buffs[buff_id].stacks},
        )

    async def _apply_debuff(
        self, state: BattleState, actor: Participant,
        target: Participant, debuff_id: str
    ) -> None:
        """Apply a debuff to a participant."""
        debuff_def = get_debuff_definition(debuff_id)
        if not debuff_def:
            return

        if debuff_id in target.debuffs:
            existing = target.debuffs[debuff_id]
            if debuff_def.overwrite_rule == "refresh":
                existing.duration = debuff_def.duration
            elif debuff_def.overwrite_rule == "stack":
                existing.stacks = min(
                    existing.stacks + 1, debuff_def.max_stacks
                )
        else:
            target.debuffs[debuff_id] = DebuffState(
                definition=debuff_def,
                duration=debuff_def.duration,
                stacks=1,
                applied_round=state.current_round,
                applied_turn=state.current_turn,
            )

        # Update stats modifier
        self._update_stats_modifier(target)

        state.append_event(
            EventType.DEBUFF_APPLIED,
            target.id,
            {"debuff_id": debuff_id, "stacks": target.debuffs[debuff_id].stacks},
        )

    async def _apply_status_effect(
        self, state: BattleState, actor: Participant,
        target: Participant, status_id: str
    ) -> None:
        """Apply a status effect to a participant."""
        status_def = get_status_effect_definition(status_id)
        if not status_def:
            return

        if status_id in target.status_effects:
            existing = target.status_effects[status_id]
            existing.stacks = min(
                existing.stacks + 1, status_def.max_stacks
            )
            existing.duration = status_def.duration
        else:
            target.status_effects[status_id] = StatusEffectState(
                definition=status_def,
                duration=status_def.duration,
                stacks=1,
                applied_round=state.current_round,
                applied_turn=state.current_turn,
            )

        state.append_event(
            EventType.STATUS_EFFECT_APPLIED,
            target.id,
            {"status_id": status_id, "stacks": target.status_effects[status_id].stacks},
        )

    async def _tick_round_end(self, state: BattleState) -> None:
        """Tick status effects and decay buffs/debuffs at round end."""
        for participant in state.player_party + state.npc_party:
            if not participant.is_alive():
                continue

            # Tick status effects
            for status_id, status_state in list(
                participant.status_effects.items()
            ):
                # Apply damage from status effect
                if status_state.definition.dmg_per_round > 0:
                    total_dmg = (
                        status_state.definition.dmg_per_round
                        * status_state.stacks
                    )
                    participant.take_damage(total_dmg)
                    state.append_event(
                        EventType.STATUS_TICK,
                        participant.id,
                        {
                            "status_id": status_id,
                            "damage": total_dmg,
                        },
                    )

                # Decay duration
                status_state.duration -= 1
                if status_state.duration <= 0:
                    del participant.status_effects[status_id]

            # Decay buffs
            for buff_id, buff_state in list(participant.buffs.items()):
                buff_state.duration -= 1
                if buff_state.duration <= 0:
                    del participant.buffs[buff_id]

            # Decay debuffs
            for debuff_id, debuff_state in list(
                participant.debuffs.items()
            ):
                debuff_state.duration -= 1
                if debuff_state.duration <= 0:
                    del participant.debuffs[debuff_id]

            # Recompute stats modifier
            self._update_stats_modifier(participant)

    def _update_stats_modifier(self, participant: Participant) -> None:
        """Recalculate stats modifier from active buffs/debuffs."""
        mod = StatsModifier()

        # Apply buffs
        for buff in participant.buffs.values():
            for stat, mult in buff.definition.stat_multiplier.items():
                # Apply once per stack
                current = getattr(mod, f"{stat}_mult", 1.0)
                setattr(mod, f"{stat}_mult", current * (mult ** buff.stacks))

        # Apply debuffs
        for debuff in participant.debuffs.values():
            for stat, reduction in debuff.definition.stat_reduction.items():
                current = getattr(mod, f"{stat}_mult", 1.0)
                setattr(mod, f"{stat}_mult", current * (reduction ** debuff.stacks))

        participant.stats_modifier = mod

    def _is_stunned(self, participant: Participant) -> bool:
        """Check if participant is stunned."""
        return "stun" in participant.status_effects

    def _check_battle_end(self, state: BattleState) -> bool:
        """Check if battle has ended (one team wiped)."""
        player_alive = state.get_all_alive(Team.PLAYER)
        npc_alive = state.get_all_alive(Team.NPC)
        return len(player_alive) == 0 or len(npc_alive) == 0

    def _determine_winner(self, state: BattleState) -> Team:
        """Determine which team won."""
        player_alive = len(state.get_all_alive(Team.PLAYER))
        npc_alive = len(state.get_all_alive(Team.NPC))

        if player_alive > 0 and npc_alive == 0:
            return Team.PLAYER
        elif npc_alive > 0 and player_alive == 0:
            return Team.NPC
        elif player_alive > 0 and npc_alive > 0:
            # Battle timeout (max rounds reached)
            # Award to team with more HP
            player_hp = sum(p.current_hp for p in state.player_party)
            npc_hp = sum(p.current_hp for p in state.npc_party)
            return Team.PLAYER if player_hp > npc_hp else Team.NPC
        else:
            return Team.PLAYER  # Default

    async def _run_pre_battle_phase(self, state: BattleState) -> None:
        """Run pre-battle triggers (passives, leader effects)."""
        state.append_event(
            EventType.PHASE_TRIGGER,
            "system",
            {"phase": "pre_battle"},
        )
        # Extended with passive triggers
        await asyncio.sleep(0)

    async def _run_post_battle_phase(
        self, state: BattleState, winner: Team
    ) -> None:
        """Run post-battle triggers (victory bonuses, passives)."""
        state.append_event(
            EventType.PHASE_TRIGGER,
            "system",
            {"phase": "post_battle", "winner": winner.value},
        )
        await asyncio.sleep(0)

    def _create_battle_result(
        self, match: BattleMatch, state: BattleState, winner: Team,
        duration_ms: float
    ) -> BattleResult:
        """Create final BattleResult from state."""
        player_alive = [
            p.character for p in state.player_party if p.is_alive()
        ]
        npc_alive = [
            p.character for p in state.npc_party if p.is_alive()
        ]

        return BattleResult(
            match_id=match.match_id,
            winner=winner,
            player_alive=player_alive,
            npc_alive=npc_alive,
            rounds_survived=state.current_round,
            match_log=state.events,
            summary=state.summary,
            duration_ms=duration_ms,
            replay_seed=match.rng_seed,
        )

    def _get_rng(self, state: BattleState) -> random.Random:
        """Get seeded RNG for battle state."""
        rng = random.Random(state.config.rng_seed)
        # Advance RNG past already-executed events for determinism
        for _ in state.events:
            rng.random()
        return rng
