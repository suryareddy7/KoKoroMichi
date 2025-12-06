# Arena System Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List
import random
import asyncio
from datetime import datetime, timedelta

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from core.config import RARITY_TIERS, BATTLE_XP_BASE, BATTLE_GOLD_BASE
from utils.helpers import format_number, calculate_battle_power

class ArenaCommands(commands.Cog):
    """Competitive arena battles with rankings and rewards"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        self.active_battles = set()  # Prevent concurrent battles
        
        # Arena opponents with varied difficulty
        self.arena_opponents = [
            {"name": "Arena Rookie", "level": 5, "power_multiplier": 0.8},
            {"name": "Seasoned Fighter", "level": 15, "power_multiplier": 1.0},
            {"name": "Arena Veteran", "level": 25, "power_multiplier": 1.2},
            {"name": "Elite Gladiator", "level": 35, "power_multiplier": 1.5},
            {"name": "Arena Champion", "level": 50, "power_multiplier": 2.0},
            {"name": "Legendary Warrior", "level": 75, "power_multiplier": 3.0}
        ]
    
    @commands.command(name="arena", aliases=["fight", "duel"])
    async def arena_battle(self, ctx, *, character_name: str = None):
        """Enter the arena for competitive battles"""
        try:
            # Check if user is already in battle
            if str(ctx.author.id) in self.active_battles:
                embed = self.embed_builder.warning_embed(
                    "Battle In Progress",
                    "You're already engaged in combat! Finish your current battle first."
                )
                await ctx.send(embed=embed)
                return
            
            # Get user data
            user_data = data_manager.get_user_data(str(ctx.author.id))
            user_characters = user_data.get("claimed_waifus", [])
            
            if not user_characters:
                embed = self.embed_builder.error_embed(
                    "No Characters",
                    "You need to summon characters before entering the arena! Use `!summon` first."
                )
                await ctx.send(embed=embed)
                return
            
            # Select character for battle
            if character_name:
                character = self.find_character_by_name(user_characters, character_name)
                if not character:
                    embed = self.embed_builder.error_embed(
                        "Character Not Found",
                        f"'{character_name}' not found in your collection. Use `!gallery` to view your characters."
                    )
                    await ctx.send(embed=embed)
                    return
            else:
                # Use strongest character
                character = max(user_characters, key=lambda c: c.get("potential", 0))
            
            # Add to active battles
            self.active_battles.add(str(ctx.author.id))
            
            try:
                # Select arena opponent based on character level
                char_level = character.get("level", 1)
                opponent = self.select_arena_opponent(char_level)
                
                # Show battle preparation
                prep_embed = await self.create_battle_preparation_embed(character, opponent)
                battle_msg = await ctx.send(embed=prep_embed)
                
                # Battle countdown
                for i in range(3, 0, -1):
                    prep_embed.description = f"⚔️ **Battle starts in {i}...** ⚔️\n\n{prep_embed.description}"
                    await battle_msg.edit(embed=prep_embed)
                    await asyncio.sleep(1)
                
                # Execute battle using enhanced system 
                battle_result = await self.execute_arena_battle(character, opponent)
                
                # Update user data
                self.update_arena_stats(user_data, battle_result)
                data_manager.save_user_data(str(ctx.author.id), user_data)
                
                # Show battle result
                result_embed = self.create_arena_result_embed(character, opponent, battle_result)
                await battle_msg.edit(embed=result_embed)
                
                # Log to history channel
                await self.log_arena_activity(ctx, character, opponent, battle_result)
                
            finally:
                # Remove from active battles
                self.active_battles.discard(str(ctx.author.id))
                
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Arena Error",
                "Something went wrong in the arena. Please try again later."
            )
            await ctx.send(embed=embed)
            self.active_battles.discard(str(ctx.author.id))
            print(f"Arena command error: {e}")
    
    @commands.command(name="arenastats", aliases=["arenareport"])
    async def arena_stats(self, ctx):
        """View arena statistics and leaderboard"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            arena_stats = user_data.get("arena_stats", {})
            
            embed = self.embed_builder.create_embed(
                title="🏟️ Arena Statistics",
                description=f"**{ctx.author.display_name}'s** Arena Performance",
                color=0xFF4500
            )
            
            # Battle record
            wins = arena_stats.get("wins", 0)
            losses = arena_stats.get("losses", 0)
            total_battles = wins + losses
            win_rate = (wins / total_battles * 100) if total_battles > 0 else 0
            
            embed.add_field(
                name="⚔️ Battle Record",
                value=f"**Wins:** {wins}\n**Losses:** {losses}\n**Win Rate:** {win_rate:.1f}%",
                inline=True
            )
            
            # Ranking and points
            ranking_points = arena_stats.get("ranking_points", 1000)
            highest_rank = arena_stats.get("highest_rank", "Unranked")
            current_streak = arena_stats.get("current_streak", 0)
            
            embed.add_field(
                name="🏆 Rankings",
                value=f"**Points:** {ranking_points:,}\n**Best Rank:** {highest_rank}\n**Win Streak:** {current_streak}",
                inline=True
            )
            
            # Rewards earned
            total_gold = arena_stats.get("total_gold_earned", 0)
            total_xp = arena_stats.get("total_xp_earned", 0)
            
            embed.add_field(
                name="💰 Rewards Earned",
                value=f"**Gold:** {format_number(total_gold)}\n**XP:** {format_number(total_xp)}",
                inline=True
            )
            
            # Recent battles
            recent_battles = arena_stats.get("recent_battles", [])
            if recent_battles:
                recent_text = ""
                for battle in recent_battles[-3:]:  # Show last 3 battles
                    result_emoji = "🏆" if battle["result"] == "win" else "💔"
                    recent_text += f"{result_emoji} vs {battle['opponent']} ({battle['date']})\n"
                
                embed.add_field(
                    name="📊 Recent Battles",
                    value=recent_text,
                    inline=False
                )
            
            await ctx.send(embed=embed)
            await self.log_arena_activity(ctx, None, None, {"type": "stats_check"})
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Stats Error",
                "Unable to retrieve arena statistics. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Arena stats error: {e}")
    
    def find_character_by_name(self, characters: List[Dict], name: str) -> Optional[Dict]:
        """Find character by name (case insensitive)"""
        name_lower = name.lower()
        for char in characters:
            if char.get("name", "").lower() == name_lower:
                return char
        return None
    
    def select_arena_opponent(self, player_level: int) -> Dict:
        """Select appropriate arena opponent based on player level"""
        # Filter opponents within reasonable level range
        suitable_opponents = [
            opp for opp in self.arena_opponents 
            if abs(opp["level"] - player_level) <= 20
        ]
        
        if not suitable_opponents:
            # Fallback to closest level opponent
            suitable_opponents = [min(self.arena_opponents, key=lambda x: abs(x["level"] - player_level))]
        
        return random.choice(suitable_opponents)
    
    async def create_battle_preparation_embed(self, character: Dict, opponent: Dict) -> discord.Embed:
        """Create battle preparation embed"""
        embed = self.embed_builder.create_embed(
            title="🏟️ Arena Battle Preparation",
            description="⚔️ **The crowd roars as warriors prepare for battle!** ⚔️",
            color=0xFF4500
        )
        
        # Player character info
        char_name = character.get("name", "Unknown")
        char_level = character.get("level", 1)
        char_power = calculate_battle_power(character)
        
        embed.add_field(
            name="🛡️ Your Champion",
            value=f"**{char_name}**\n"
                  f"Level: {char_level}\n"
                  f"Power: {format_number(char_power)}\n"
                  f"Element: {character.get('element', 'Neutral')}",
            inline=True
        )
        
        # Opponent info
        opp_power = int(char_power * opponent["power_multiplier"])
        embed.add_field(
            name="⚔️ Arena Opponent",
            value=f"**{opponent['name']}**\n"
                  f"Level: {opponent['level']}\n"
                  f"Power: {format_number(opp_power)}\n"
                  f"Difficulty: {self.get_difficulty_text(opponent['power_multiplier'])}",
            inline=True
        )
        
        # Battle preview
        victory_chance = min(90, max(10, 50 + (char_power - opp_power) / char_power * 50))
        embed.add_field(
            name="📊 Battle Preview",
            value=f"🎯 Victory Chance: {victory_chance:.0f}%\n"
                  f"🏆 Estimated Rewards: {self.calculate_arena_rewards(char_level, opponent)['preview']}",
            inline=False
        )
        
        return embed
    
    async def execute_arena_battle(self, character: Dict, opponent: Dict) -> Dict:
        """Execute arena battle and return results"""
        char_power = calculate_battle_power(character)
        opp_power = int(char_power * opponent["power_multiplier"])
        
        # Battle simulation with some randomness
        char_total = char_power + random.randint(-100, 200)
        opp_total = opp_power + random.randint(-100, 200)
        
        victory = char_total > opp_total
        
        # Calculate battle details
        rounds = random.randint(3, 8)
        damage_dealt = max(50, char_total - random.randint(0, 100))
        damage_taken = max(20, opp_total - random.randint(0, 150))
        
        return {
            "victory": victory,
            "player_power": char_power,
            "opponent_power": opp_power,
            "rounds": rounds,
            "damage_dealt": damage_dealt,
            "damage_taken": damage_taken,
            "battle_duration": rounds * 0.3
        }
    
    def create_arena_result_embed(self, character: Dict, opponent: Dict, battle_result: Dict) -> discord.Embed:
        """Create arena battle result embed"""
        victory = battle_result["victory"]
        
        if victory:
            title = "🏆 Arena Victory!"
            description = f"**{character.get('name')}** triumphs in glorious combat!"
            color = 0x00FF00
        else:
            title = "⚔️ Valiant Effort"
            description = f"**{character.get('name')}** fought bravely but was defeated!"
            color = 0xFF6B6B
        
        embed = self.embed_builder.create_embed(title=title, description=description, color=color)
        
        # Battle summary
        rounds = battle_result["rounds"]
        damage_dealt = battle_result["damage_dealt"]
        damage_taken = battle_result["damage_taken"]
        
        embed.add_field(
            name="⚔️ Battle Summary",
            value=f"**Opponent:** {opponent['name']}\n"
                  f"**Rounds:** {rounds}\n"
                  f"**Damage Dealt:** {format_number(damage_dealt)}\n"
                  f"**Damage Taken:** {format_number(damage_taken)}",
            inline=True
        )
        
        # Rewards
        if victory:
            char_level = character.get("level", 1)
            rewards = self.calculate_arena_rewards(char_level, opponent)
            
            embed.add_field(
                name="🎁 Victory Rewards",
                value=f"💰 Gold: +{format_number(rewards['gold'])}\n"
                      f"⭐ XP: +{format_number(rewards['xp'])}\n"
                      f"🏆 Arena Points: +{rewards['arena_points']}",
                inline=True
            )
        else:
            # Consolation rewards
            consolation_gold = max(50, int(character.get("level", 1) * 20))
            embed.add_field(
                name="💙 Consolation",
                value=f"💰 Gold: +{format_number(consolation_gold)}\n"
                      f"⭐ XP: +25\n"
                      f"🎯 Experience gained from defeat!",
                inline=True
            )
        
        # Performance rating
        performance_score = (damage_dealt - damage_taken) / max(1, damage_dealt + damage_taken) * 100
        performance_text = self.get_performance_rating(performance_score)
        
        embed.add_field(
            name="📈 Performance",
            value=f"**Rating:** {performance_text}\n"
                  f"**Score:** {performance_score:.1f}%",
            inline=False
        )
        
        return embed
    
    def calculate_arena_rewards(self, char_level: int, opponent: Dict) -> Dict:
        """Calculate arena battle rewards"""
        base_gold = BATTLE_GOLD_BASE * (1 + char_level * 0.1)
        base_xp = BATTLE_XP_BASE * (1 + char_level * 0.05)
        
        # Multiply by opponent difficulty
        multiplier = opponent["power_multiplier"]
        
        rewards = {
            "gold": int(base_gold * multiplier),
            "xp": int(base_xp * multiplier),
            "arena_points": int(10 * multiplier),
            "preview": f"{format_number(int(base_gold * multiplier))} gold, {format_number(int(base_xp * multiplier))} XP"
        }
        
        return rewards
    
    def update_arena_stats(self, user_data: Dict, battle_result: Dict):
        """Update user's arena statistics"""
        arena_stats = user_data.setdefault("arena_stats", {
            "wins": 0, "losses": 0, "ranking_points": 1000,
            "total_gold_earned": 0, "total_xp_earned": 0,
            "current_streak": 0, "best_streak": 0,
            "recent_battles": []
        })
        
        victory = battle_result["victory"]
        
        if victory:
            arena_stats["wins"] += 1
            arena_stats["current_streak"] += 1
            arena_stats["ranking_points"] += 25
            arena_stats["best_streak"] = max(arena_stats["best_streak"], arena_stats["current_streak"])
        else:
            arena_stats["losses"] += 1
            arena_stats["current_streak"] = 0
            arena_stats["ranking_points"] = max(800, arena_stats["ranking_points"] - 10)
        
        # Add recent battle record
        recent_battle = {
            "result": "win" if victory else "loss",
            "opponent": "Arena Opponent",
            "date": datetime.now().strftime("%m/%d"),
            "points_change": 25 if victory else -10
        }
        
        arena_stats["recent_battles"].append(recent_battle)
        # Keep only last 10 battles
        arena_stats["recent_battles"] = arena_stats["recent_battles"][-10:]
    
    def get_difficulty_text(self, multiplier: float) -> str:
        """Get difficulty description"""
        if multiplier <= 0.8:
            return "🟢 Easy"
        elif multiplier <= 1.0:
            return "🟡 Normal"
        elif multiplier <= 1.5:
            return "🟠 Hard"
        elif multiplier <= 2.0:
            return "🔴 Expert"
        else:
            return "🟣 Legendary"
    
    def get_performance_rating(self, score: float) -> str:
        """Get performance rating based on score"""
        if score >= 80:
            return "🌟 Flawless Victory"
        elif score >= 60:
            return "🔥 Excellent"
        elif score >= 40:
            return "⚡ Good"
        elif score >= 20:
            return "💪 Decent"
        else:
            return "🛡️ Needs Improvement"
    
    async def log_arena_activity(self, ctx, character: Optional[Dict], opponent: Optional[Dict], battle_result: Dict):
        """Log arena activity to history channel"""
        try:
            history_channel = discord.utils.get(ctx.guild.text_channels, name='history')
            if not history_channel:
                return
            
            emojis = ["⚔️", "🏟️", "🏆", "⚡", "🔥", "💫"]
            emoji = random.choice(emojis)
            
            if battle_result.get("type") == "stats_check":
                message = f"{emoji} **{ctx.author.display_name}** reviewed their arena achievements and battle history!"
            elif battle_result.get("victory"):
                char_name = character.get("name", "Champion") if character else "Champion"
                opp_name = opponent.get("name", "Opponent") if opponent else "Opponent"
                message = f"{emoji} **{ctx.author.display_name}**'s {char_name} achieved glorious victory against {opp_name} in the arena!"
            else:
                char_name = character.get("name", "Warrior") if character else "Warrior"
                message = f"{emoji} **{ctx.author.display_name}**'s {char_name} fought valiantly in the arena and gained valuable experience!"
            
            embed = self.embed_builder.create_embed(
                description=message,
                color=0xFF4500
            )
            
            await history_channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error logging arena activity: {e}")

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(ArenaCommands(bot))