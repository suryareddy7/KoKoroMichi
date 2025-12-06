# Battle System Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List, Tuple
import random
import asyncio
import logging
from datetime import datetime

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from core.config import BATTLE_XP_BASE, BATTLE_GOLD_BASE
from utils.helpers import (
    format_number, find_character_by_name, calculate_battle_power,
    check_elemental_advantage
)
from utils.advanced_combat import BattleEngine
from utils.guild_manager import GuildManager
from utils.affinity_manager import AffinityManager
from utils.pet_manager import PetManager
from utils.dream_manager import DreamManager
from utils.channel_restriction import check_channel_restriction

logger = logging.getLogger(__name__)

class BattleCommands(commands.Cog):
    """Combat system and battle management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        self.active_battles = set()  # Prevent concurrent battles
        
        # Initialize advanced combat systems
        self.battle_engine = BattleEngine()
        self.guild_manager = GuildManager()
        self.affinity_manager = AffinityManager()
        self.pet_manager = PetManager()
        self.dream_manager = DreamManager()
        
        # Load NPC names for battles
        self.npc_names = self.load_npc_names()
    
    def load_npc_names(self) -> List[str]:
        """Load NPC names for battles"""
        try:
            npc_data = data_manager.get_game_data("npc_names")
            if isinstance(npc_data, list):
                return npc_data
            elif isinstance(npc_data, dict) and "names" in npc_data:
                return npc_data["names"]
        except:
            pass
        
        # Fallback NPC names
        return [
            "Shadow Warrior", "Mystic Guardian", "Crystal Golem", "Fire Spirit",
            "Ice Queen", "Thunder Lord", "Wind Dancer", "Earth Shaker",
            "Void Hunter", "Light Bringer", "Dark Assassin", "Steel Knight"
        ]
    
    @commands.command(name="battle", aliases=["combat"])
    async def battle_command(self, ctx, character_name: str = None, target: Optional[discord.Member] = None):
        """Start a battle with your character against NPCs or other players"""
        # Enforce channel restrictions for battle commands
        restriction_result = await check_channel_restriction(
            ctx, ["combat-calls", "duel-zone", "battle-arena"], ctx.bot
        )
        if not restriction_result:
            await ctx.send("⚔️ Battle commands can only be used in combat channels!", delete_after=10)
            return
        try:
            # Check if user is already in battle
            if str(ctx.author.id) in self.active_battles:
                embed = self.embed_builder.warning_embed(
                    "Battle In Progress",
                    "You're already in a battle! Please wait for it to finish."
                )
                await ctx.send(embed=embed)
                return
            
            # Add user to active battles
            self.active_battles.add(str(ctx.author.id))
            
            try:
                # Get user data
                user_data = data_manager.get_user_data(str(ctx.author.id))
                user_waifus = user_data.get("claimed_waifus", [])
                
                if not user_waifus:
                    embed = self.embed_builder.info_embed(
                        "No Characters",
                        "You need characters to battle! Use `!summon` to get started."
                    )
                    await ctx.send(embed=embed)
                    return
                
                # Select player character
                if character_name:
                    player_character = find_character_by_name(user_waifus, character_name)
                    if not player_character:
                        embed = self.embed_builder.error_embed(
                            "Character Not Found",
                            f"'{character_name}' not found in your collection."
                        )
                        await ctx.send(embed=embed)
                        return
                else:
                    # Use strongest character
                    player_character = max(user_waifus, key=lambda c: c.get("potential", 0))
                
                # Determine opponent
                if target and not target.bot:
                    # PvP battle
                    opponent_data = data_manager.get_user_data(str(target.id))
                    opponent_waifus = opponent_data.get("claimed_waifus", [])
                    
                    if not opponent_waifus:
                        embed = self.embed_builder.error_embed(
                            "Invalid Opponent",
                            f"{target.mention} doesn't have any characters to battle with!"
                        )
                        await ctx.send(embed=embed)
                        return
                    
                    opponent_character = max(opponent_waifus, key=lambda c: c.get("potential", 0))
                    opponent_name = target.display_name
                    is_pvp = True
                else:
                    # PvE battle
                    opponent_character = self.generate_npc_opponent(player_character)
                    opponent_name = random.choice(self.npc_names)
                    is_pvp = False
                
                # Start battle sequence
                await self.conduct_battle(ctx, player_character, opponent_character, 
                                        opponent_name, is_pvp, target)
                
            finally:
                # Remove user from active battles
                self.active_battles.discard(str(ctx.author.id))
                
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Battle Error",
                "Something went wrong during battle. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Battle command error: {e}")
            self.active_battles.discard(str(ctx.author.id))
    
    @commands.command(name="quick_arena", aliases=["quick_battle"])
    async def arena_battle(self, ctx):
        """Quick arena battle against a random opponent"""
        # Enforce channel restrictions for battle commands
        restriction_result = await check_channel_restriction(
            ctx, ["combat-calls", "duel-zone", "battle-arena"], ctx.bot
        )
        if not restriction_result:
            await ctx.send("⚔️ Arena battles can only be used in combat channels!", delete_after=10)
            return
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            user_waifus = user_data.get("claimed_waifus", [])
            
            if not user_waifus:
                embed = self.embed_builder.info_embed(
                    "No Characters",
                    "You need characters for arena battles! Use `!summon` to get started."
                )
                await ctx.send(embed=embed)
                return
            
            # Use strongest character
            player_character = max(user_waifus, key=lambda c: c.get("potential", 0))
            
            # Generate arena opponent (slightly stronger than player)
            opponent_character = self.generate_arena_opponent(player_character)
            opponent_name = f"Arena {random.choice(['Champion', 'Challenger', 'Warrior', 'Fighter'])}"
            
            await self.conduct_battle(ctx, player_character, opponent_character, 
                                    opponent_name, False, None, is_arena=True)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Arena Error",
                "Unable to start arena battle. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Arena command error: {e}")
    
    async def conduct_battle(self, ctx, player_char: Dict, opponent_char: Dict, 
                           opponent_name: str, is_pvp: bool, target_user: Optional[discord.Member] = None, 
                           is_arena: bool = False):
        """Conduct the actual battle sequence"""
        
        # Create battle setup embed
        embed = self.create_battle_setup_embed(player_char, opponent_char, opponent_name, is_pvp)
        battle_msg = await ctx.send(embed=embed)
        
        # Battle preparation animation
        await asyncio.sleep(2)
        
        # Initialize battle stats
        player_hp = player_char.get("hp", 100)
        player_max_hp = player_hp
        opponent_hp = opponent_char.get("hp", 100)
        opponent_max_hp = opponent_hp
        
        battle_log = []
        round_num = 1
        
        # Battle loop
        while player_hp > 0 and opponent_hp > 0 and round_num <= 20:  # Max 20 rounds
            
            # Player turn - use enhanced damage calculation
            player_damage, player_combat_log = self.calculate_damage(
                player_char, opponent_char, str(ctx.author.id) if not is_pvp else None
            )
            opponent_hp -= player_damage
            opponent_hp = max(0, opponent_hp)
            
            # Add detailed combat log
            battle_log.append(f"Round {round_num}: {player_char['name']} deals {player_damage} damage!")
            for log_entry in player_combat_log:
                if log_entry:  # Only add non-empty log entries
                    battle_log.append(f"  {log_entry}")
            
            if opponent_hp <= 0:
                break
            
            # Opponent turn
            opponent_damage, opponent_combat_log = self.calculate_damage(
                opponent_char, player_char, str(target.id) if is_pvp and target else None
            )
            player_hp -= opponent_damage
            player_hp = max(0, player_hp)
            
            battle_log.append(f"Round {round_num}: {opponent_name} deals {opponent_damage} damage!")
            for log_entry in opponent_combat_log:
                if log_entry:
                    battle_log.append(f"  {log_entry}")
            
            # Update battle display every few rounds
            if round_num % 3 == 0:
                embed = self.create_battle_progress_embed(
                    player_char, opponent_char, opponent_name,
                    player_hp, player_max_hp, opponent_hp, opponent_max_hp,
                    round_num, battle_log[-2:]
                )
                await battle_msg.edit(embed=embed)
                await asyncio.sleep(1)
            
            round_num += 1
        
        # Determine winner and rewards
        if player_hp > 0:
            winner = "player"
            victory = True
        else:
            winner = "opponent" 
            victory = False
        
        # Calculate rewards
        rewards = self.calculate_battle_rewards(victory, opponent_char, is_arena)
        
        # Get final buff display for the battle result
        final_buffs = self.get_active_buffs_display(player_char, str(ctx.author.id) if not is_pvp else None)
        
        # Update user stats
        await self.update_battle_stats(ctx.author.id, victory, player_damage, opponent_damage, rewards)
        
        # Create final battle result
        embed = self.create_battle_result_embed(
            player_char, opponent_char, opponent_name, victory, 
            player_hp, opponent_hp, rewards, battle_log, round_num, final_buffs
        )
        
        await battle_msg.edit(embed=embed)
    
    def generate_npc_opponent(self, player_char: Dict) -> Dict:
        """Generate an NPC opponent based on player character"""
        player_level = player_char.get("level", 1)
        player_potential = player_char.get("potential", 1000)
        
        # Create opponent with similar but varied stats
        level_variance = random.randint(-1, 2)
        opponent_level = max(1, player_level + level_variance)
        
        # Base stats with some randomness
        base_hp = player_char.get("hp", 100)
        base_atk = player_char.get("atk", 50)
        base_def = player_char.get("def", 30)
        
        return {
            "name": random.choice(self.npc_names),
            "level": opponent_level,
            "hp": max(50, base_hp + random.randint(-20, 30)),
            "atk": max(30, base_atk + random.randint(-15, 25)),
            "def": max(20, base_def + random.randint(-10, 20)),
            "element": random.choice(["Fire", "Water", "Earth", "Air", "Light", "Dark", "Neutral"]),
            "potential": max(500, player_potential + random.randint(-500, 300))
        }
    
    def generate_arena_opponent(self, player_char: Dict) -> Dict:
        """Generate a stronger arena opponent"""
        npc = self.generate_npc_opponent(player_char)
        
        # Arena opponents are 10-20% stronger
        strength_boost = random.uniform(1.1, 1.2)
        
        npc["hp"] = int(npc["hp"] * strength_boost)
        npc["atk"] = int(npc["atk"] * strength_boost)
        npc["def"] = int(npc["def"] * strength_boost)
        npc["potential"] = int(npc["potential"] * strength_boost)
        
        return npc
    
    def calculate_damage(self, attacker: Dict, defender: Dict, user_id: str = None) -> Tuple[int, List[str]]:
        """Calculate damage using comprehensive buff system"""
        # Apply all buffs and bonuses to attacker
        enhanced_attacker = self.apply_all_buffs(attacker, user_id)
        enhanced_defender = self.apply_all_buffs(defender, user_id)
        
        # Use advanced combat engine
        damage, is_crit, combat_log = self.battle_engine.calculate_damage(
            enhanced_attacker, enhanced_defender
        )
        
        # Add buff information to combat log
        buff_log = self.get_active_buffs_display(enhanced_attacker, user_id)
        combat_log.extend(buff_log)
        
        return damage, combat_log
    
    def apply_all_buffs(self, character: Dict, user_id: str = None) -> Dict:
        """Apply all available buffs to character stats"""
        if not user_id:
            return character
            
        # Start with base character stats
        enhanced_stats = character.copy()
        
        # Apply guild bonuses
        enhanced_stats = self.apply_guild_buffs(enhanced_stats, user_id)
        
        # Apply pet bonuses
        enhanced_stats = self.apply_pet_buffs(enhanced_stats, user_id)
        
        # Apply dream buffs
        enhanced_stats = self.apply_dream_buffs(enhanced_stats, user_id)
        
        # Apply affinity buffs (if fighting with other characters)
        enhanced_stats = self.apply_affinity_buffs(enhanced_stats, user_id)
        
        # Apply relic and trait bonuses (using battle engine)
        enhanced_stats = self.battle_engine.calculate_battle_stats(enhanced_stats)
        
        return enhanced_stats
    
    def apply_guild_buffs(self, stats: Dict, user_id: str) -> Dict:
        """Apply guild membership bonuses"""
        try:
            if user_id in self.guild_manager.user_guilds.get("memberships", {}):
                guild_id = self.guild_manager.user_guilds["memberships"][user_id]
                guild = self.guild_manager.user_guilds["guilds"].get(guild_id, {})
                
                # Apply faction bonuses
                faction = guild.get("faction", "")
                faction_bonuses = {
                    "celestial": {"atk": 1.2, "crit": 5},
                    "shadow": {"atk": 1.3, "speed": 1.2},
                    "elemental": {"magic": 1.25, "hp": 1.15},
                    "arcane": {"magic": 1.3, "def": 1.2}
                }
                
                if faction in faction_bonuses:
                    bonuses = faction_bonuses[faction]
                    for stat, multiplier in bonuses.items():
                        if stat in stats:
                            if stat == "crit":
                                stats[stat] = stats.get(stat, 5) + multiplier
                            else:
                                stats[stat] = int(stats.get(stat, 50) * multiplier)
                                
        except Exception as e:
            logger.warning(f"Guild buff error: {e}")
            
        return stats
    
    def apply_pet_buffs(self, stats: Dict, user_id: str) -> Dict:
        """Apply active pet bonuses"""
        try:
            user_pets = self.pet_manager.get_user_pets(user_id)
            active_pets = self.pet_manager.user_pets.get("active_pets", {}).get(user_id, [])
            
            for pet in user_pets:
                if pet.get("pet_id") in active_pets:
                    abilities = pet.get("unlocked_abilities", [])
                    for ability_name in abilities:
                        # Find ability effects in pet species data
                        species_name = pet.get("species", "")
                        for species in self.pet_manager.pet_data.get("pet_species", []):
                            if species["name"] == species_name:
                                for ability in species.get("abilities", []):
                                    if ability["name"] == ability_name:
                                        effect = ability.get("effect", {})
                                        for effect_type, value in effect.items():
                                            if effect_type == "damage_bonus":
                                                stats["atk"] = int(stats.get("atk", 50) * (1 + value))
                                            elif effect_type == "damage_reduction":
                                                stats["def"] = int(stats.get("def", 30) * (1 + value))
                                            elif effect_type == "crit_chance_bonus":
                                                stats["crit"] = stats.get("crit", 5) + (value * 100)
                                            elif effect_type == "dodge_chance":
                                                stats["speed"] = int(stats.get("speed", 50) * (1 + value))
                                                
        except Exception as e:
            logger.warning(f"Pet buff error: {e}")
            
        return stats
    
    def apply_dream_buffs(self, stats: Dict, user_id: str) -> Dict:
        """Apply active dream event buffs"""
        try:
            dream_buffs = self.dream_manager.user_dreams.get("dream_buffs", {}).get(user_id, {})
            
            for buff_id, buff_data in dream_buffs.items():
                expires_at = buff_data.get("expires_at")
                if expires_at:
                    try:
                        expire_time = datetime.fromisoformat(expires_at)
                        if datetime.now() > expire_time:
                            continue  # Skip expired buff
                    except:
                        continue
                
                buff_effects = buff_data.get("effects", {})
                for effect, value in buff_effects.items():
                    if effect == "combat_power":
                        stats["atk"] = int(stats.get("atk", 50) * (1 + value))
                    elif effect == "defense_boost":
                        stats["def"] = int(stats.get("def", 30) * (1 + value))
                    elif effect == "hp_boost":
                        stats["hp"] = int(stats.get("hp", 100) * (1 + value))
                        
        except Exception as e:
            logger.warning(f"Dream buff error: {e}")
            
        return stats
    
    def apply_affinity_buffs(self, stats: Dict, user_id: str) -> Dict:
        """Apply bonuses from character relationships"""
        try:
            # For now, apply a general affinity bonus based on overall relationship levels
            # This could be expanded to specific character pairs
            user_data = data_manager.get_user_data(user_id)
            characters = user_data.get("claimed_waifus", [])
            
            if len(characters) >= 2:
                # Calculate average affinity among characters
                total_affinity = 0
                pairs = 0
                
                for i, char1 in enumerate(characters):
                    for char2 in characters[i+1:]:
                        affinity = self.affinity_manager.get_affinity(
                            user_id, char1.get("name", ""), char2.get("name", "")
                        )
                        total_affinity += affinity
                        pairs += 1
                
                if pairs > 0:
                    avg_affinity = total_affinity / pairs
                    if avg_affinity > 70:  # High team cohesion bonus
                        stats["atk"] = int(stats.get("atk", 50) * 1.15)
                        stats["def"] = int(stats.get("def", 30) * 1.1)
                        
        except Exception as e:
            logger.warning(f"Affinity buff error: {e}")
            
        return stats
    
    def get_active_buffs_display(self, character: Dict, user_id: str) -> List[str]:
        """Get display messages for active buffs"""
        buff_messages = []
        
        try:
            # Check for guild buffs
            if user_id and user_id in self.guild_manager.user_guilds.get("memberships", {}):
                guild_id = self.guild_manager.user_guilds["memberships"][user_id]
                guild = self.guild_manager.user_guilds["guilds"].get(guild_id, {})
                faction = guild.get("faction", "")
                if faction:
                    buff_messages.append(f"🏰 Guild ({faction.title()}) buffs active!")
            
            # Check for pet buffs
            active_pets = self.pet_manager.user_pets.get("active_pets", {}).get(user_id, [])
            if active_pets:
                buff_messages.append(f"🐾 Pet companion buffs active ({len(active_pets)} pets)!")
            
            # Check for dream buffs
            dream_buffs = self.dream_manager.user_dreams.get("dream_buffs", {}).get(user_id, {})
            active_dream_buffs = 0
            for buff_data in dream_buffs.values():
                expires_at = buff_data.get("expires_at")
                if expires_at:
                    try:
                        expire_time = datetime.fromisoformat(expires_at)
                        if datetime.now() <= expire_time:
                            active_dream_buffs += 1
                    except:
                        pass
            
            if active_dream_buffs > 0:
                buff_messages.append(f"🌙 Dream buffs active ({active_dream_buffs} effects)!")
                
            # Check for traits
            if character.get("traits"):
                buff_messages.append(f"✨ Character traits active ({len(character['traits'])} traits)!")
                
            # Check for equipped relic
            if character.get("relic") or character.get("equipped_relic"):
                buff_messages.append("🏺 Relic bonuses active!")
                
        except Exception as e:
            logger.warning(f"Buff display error: {e}")
            
        return buff_messages
    
    def calculate_battle_rewards(self, victory: bool, opponent: Dict, is_arena: bool = False) -> Dict:
        """Calculate battle rewards based on outcome"""
        if not victory:
            return {"gold": 0, "xp": 10, "items": []}
        
        # Base rewards
        base_gold = BATTLE_GOLD_BASE
        base_xp = BATTLE_XP_BASE
        
        # Scale with opponent strength
        opponent_level = opponent.get("level", 1)
        opponent_potential = opponent.get("potential", 1000)
        
        strength_multiplier = 1 + (opponent_level - 1) * 0.1 + (opponent_potential / 5000)
        
        gold_reward = int(base_gold * strength_multiplier)
        xp_reward = int(base_xp * strength_multiplier)
        
        # Arena bonus
        if is_arena:
            gold_reward = int(gold_reward * 1.5)
            xp_reward = int(xp_reward * 1.3)
        
        # Random item drops
        items = []
        drop_chance = 0.3 if victory else 0.1
        
        if random.random() < drop_chance:
            item_pool = [
                "Health Potion Small", "Experience Scroll", "Gold Pouch",
                "Iron Ore", "Cloth Scrap", "Small Gem"
            ]
            items.append(random.choice(item_pool))
        
        return {
            "gold": gold_reward,
            "xp": xp_reward,
            "items": items
        }
    
    async def update_battle_stats(self, user_id: str, victory: bool, damage_dealt: int, 
                                damage_taken: int, rewards: Dict):
        """Update user battle statistics and apply rewards"""
        user_data = data_manager.get_user_data(user_id)
        
        # Update battle stats
        battle_stats = user_data.setdefault("battle_stats", {})
        if victory:
            battle_stats["battles_won"] = battle_stats.get("battles_won", 0) + 1
        else:
            battle_stats["battles_lost"] = battle_stats.get("battles_lost", 0) + 1
        
        battle_stats["total_damage_dealt"] = battle_stats.get("total_damage_dealt", 0) + damage_dealt
        battle_stats["total_damage_taken"] = battle_stats.get("total_damage_taken", 0) + damage_taken
        
        # Apply rewards
        user_data["gold"] = user_data.get("gold", 0) + rewards["gold"]
        user_data["xp"] = user_data.get("xp", 0) + rewards["xp"]
        
        # Add items to inventory
        inventory = user_data.setdefault("inventory", {})
        for item in rewards["items"]:
            inventory[item] = inventory.get(item, 0) + 1
        
        # Check for level up
        from utils.helpers import calculate_level_from_xp
        old_level = user_data.get("level", 1)
        new_level = calculate_level_from_xp(user_data["xp"])
        if new_level > old_level:
            user_data["level"] = new_level
        
        data_manager.save_user_data(user_id, user_data)
    
    def create_battle_setup_embed(self, player_char: Dict, opponent_char: Dict, 
                                opponent_name: str, is_pvp: bool) -> discord.Embed:
        """Create battle setup embed"""
        embed = self.embed_builder.create_embed(
            title="⚔️ Battle Commencing!",
            description="Warriors prepare for combat...",
            color=0xFF4500
        )
        
        # Player character
        embed.add_field(
            name=f"🛡️ {player_char['name']}",
            value=f"Level {player_char.get('level', 1)}\n"
                  f"❤️ {player_char.get('hp', 100)} HP\n"
                  f"⚔️ {player_char.get('atk', 50)} ATK\n"
                  f"🌟 {player_char.get('element', 'Neutral')}",
            inline=True
        )
        
        embed.add_field(
            name="⚡ VS ⚡",
            value="💥\n🔥\n⚔️",
            inline=True
        )
        
        # Opponent character
        embed.add_field(
            name=f"👹 {opponent_name}",
            value=f"Level {opponent_char.get('level', 1)}\n"
                  f"❤️ {opponent_char.get('hp', 100)} HP\n"
                  f"⚔️ {opponent_char.get('atk', 50)} ATK\n"
                  f"🌟 {opponent_char.get('element', 'Neutral')}",
            inline=True
        )
        
        battle_type = "Player vs Player" if is_pvp else "Player vs Environment"
        embed.add_field(
            name="🎯 Battle Type",
            value=battle_type,
            inline=False
        )
        
        return embed
    
    def create_battle_progress_embed(self, player_char: Dict, opponent_char: Dict, 
                                   opponent_name: str, player_hp: int, player_max_hp: int,
                                   opponent_hp: int, opponent_max_hp: int, round_num: int,
                                   recent_log: List[str]) -> discord.Embed:
        """Create battle progress embed"""
        embed = self.embed_builder.create_embed(
            title=f"⚔️ Battle in Progress - Round {round_num}",
            color=0xFF6347
        )
        
        # Health bars
        player_hp_bar = self.create_hp_bar(player_hp, player_max_hp)
        opponent_hp_bar = self.create_hp_bar(opponent_hp, opponent_max_hp)
        
        embed.add_field(
            name=f"🛡️ {player_char['name']}",
            value=f"{player_hp_bar}\n{player_hp}/{player_max_hp} HP",
            inline=True
        )
        
        embed.add_field(
            name="⚔️",
            value="VS",
            inline=True
        )
        
        embed.add_field(
            name=f"👹 {opponent_name}",
            value=f"{opponent_hp_bar}\n{opponent_hp}/{opponent_max_hp} HP",
            inline=True
        )
        
        # Recent battle log
        if recent_log:
            embed.add_field(
                name="📜 Recent Actions",
                value="\n".join(recent_log[-3:]),
                inline=False
            )
        
        return embed
    
    def create_hp_bar(self, current_hp: int, max_hp: int, length: int = 10) -> str:
        """Create a text-based HP bar"""
        if max_hp <= 0:
            return "▱" * length
        
        percentage = current_hp / max_hp
        filled = int(percentage * length)
        empty = length - filled
        
        if percentage > 0.6:
            bar_char = "🟩"
        elif percentage > 0.3:
            bar_char = "🟨"
        else:
            bar_char = "🟥"
        
        return bar_char * filled + "⬜" * empty
    
    def create_battle_result_embed(self, player_char: Dict, opponent_char: Dict, 
                                 opponent_name: str, victory: bool, player_hp: int,
                                 opponent_hp: int, rewards: Dict, battle_log: List[str], 
                                 rounds: int, active_buffs: List[str] = None) -> discord.Embed:
        """Create final battle result embed"""
        
        if victory:
            title = "🎉 Victory!"
            description = f"{player_char['name']} emerges victorious!"
            color = 0x00FF00
        else:
            title = "💔 Defeat"
            description = f"{opponent_name} proved too strong..."
            color = 0xFF0000
        
        embed = self.embed_builder.create_embed(
            title=title,
            description=description,
            color=color
        )
        
        # Final health status
        embed.add_field(
            name="💖 Final Health",
            value=f"{player_char['name']}: {player_hp} HP\n{opponent_name}: {opponent_hp} HP",
            inline=True
        )
        
        # Battle duration
        embed.add_field(
            name="⏱️ Battle Info",
            value=f"Duration: {rounds} rounds\nIntensity: {'High' if rounds > 10 else 'Medium' if rounds > 5 else 'Quick'}",
            inline=True
        )
        
        # Rewards (if victory)
        if victory and rewards:
            reward_text = ""
            if rewards["gold"] > 0:
                reward_text += f"💰 {format_number(rewards['gold'])} gold\n"
            if rewards["xp"] > 0:
                reward_text += f"⭐ {format_number(rewards['xp'])} XP\n"
            if rewards["items"]:
                reward_text += f"🎁 {', '.join(rewards['items'])}"
            
            if reward_text:
                embed.add_field(
                    name="🎁 Rewards Earned",
                    value=reward_text,
                    inline=False
                )
        
        # Active buffs display
        if active_buffs:
            embed.add_field(
                name="⚡ Active Buffs",
                value="\n".join(active_buffs) if active_buffs else "None",
                inline=False
            )
        
        # Battle summary
        if len(battle_log) > 6:
            summary_log = battle_log[:3] + ["..."] + battle_log[-3:]
        else:
            summary_log = battle_log
        
        embed.add_field(
            name="📜 Battle Summary",
            value="\n".join(summary_log[-8:]),
            inline=False
        )
        
        return embed


async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(BattleCommands(bot))