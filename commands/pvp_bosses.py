# PvP and Boss Battle Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List, Any
import random
import asyncio
from datetime import datetime, timedelta

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from core.config import FEATURES
from utils.helpers import format_number, calculate_battle_power

class PvPBossCommands(commands.Cog):
    """Player vs Player duels and epic boss battles"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        self.active_duels = {}  # Track active PvP duels
        
        # Boss templates
        self.world_bosses = {
            "shadow_dragon": {
                "name": "Ancient Shadow Dragon",
                "description": "A primordial dragon that devours light itself",
                "hp": 50000,
                "atk": 800,
                "def": 400,
                "special_abilities": ["Shadow Breath", "Dark Regeneration", "Eclipse Strike"],
                "emoji": "🐉",
                "required_players": 3,
                "rewards": {
                    "gold": (5000, 15000),
                    "xp": (2000, 8000),
                    "gems": (50, 150),
                    "special_drops": ["Dragon Scale", "Shadow Essence", "Ancient Relic"]
                },
                "spawn_chance": 0.02
            },
            "crystal_golem": {
                "name": "Crystalline Titan",
                "description": "Massive golem made of pure magical crystals",
                "hp": 35000,
                "atk": 600,
                "def": 600,
                "special_abilities": ["Crystal Barrage", "Healing Aura", "Diamond Armor"],
                "emoji": "💎",
                "required_players": 2,
                "rewards": {
                    "gold": (3000, 10000),
                    "xp": (1500, 6000),
                    "gems": (30, 100),
                    "special_drops": ["Crystal Core", "Gem Shard", "Titan's Heart"]
                },
                "spawn_chance": 0.03
            },
            "void_wraith": {
                "name": "Lord of the Void",
                "description": "Ethereal being from the space between dimensions",
                "hp": 25000,
                "atk": 1000,
                "def": 200,
                "special_abilities": ["Void Drain", "Phase Shift", "Reality Tear"],
                "emoji": "👻",
                "required_players": 2,
                "rewards": {
                    "gold": (2000, 8000),
                    "xp": (1000, 5000),
                    "gems": (25, 75),
                    "special_drops": ["Void Essence", "Wraith Cloak", "Dimensional Key"]
                },
                "spawn_chance": 0.04
            }
        }
    
    @commands.command(name="pvp_duel", aliases=["pvp", "challenge"])
    async def player_vs_player(self, ctx, opponent: discord.Member = None):
        """Challenge another player to a PvP duel"""
        try:
            if not opponent:
                embed = self.embed_builder.create_embed(
                    title="⚔️ PvP Dueling System",
                    description="Challenge other players to epic battles!",
                    color=0xFF4500
                )
                
                embed.add_field(
                    name="🎯 How to Duel",
                    value="• `!duel @player` - Challenge someone\n"
                          "• Accept duels by reacting ⚔️\n"
                          "• Winner takes glory and rewards\n"
                          "• No items or characters are lost",
                    inline=False
                )
                
                embed.add_field(
                    name="🏆 Duel Rewards",
                    value="• **Winner:** 1000-3000 gold + XP\n"
                          "• **Loser:** 200 gold + 100 XP (participation)\n"
                          "• **Both:** PvP ranking points\n"
                          "• Special achievements for win streaks",
                    inline=False
                )
                
                await ctx.send(embed=embed)
                return
            
            if opponent.id == ctx.author.id:
                embed = self.embed_builder.error_embed(
                    "Invalid Opponent",
                    "You can't duel yourself! Find another player to challenge."
                )
                await ctx.send(embed=embed)
                return
            
            if opponent.bot:
                embed = self.embed_builder.error_embed(
                    "Invalid Opponent", 
                    "You can't duel bots! Challenge a real player instead."
                )
                await ctx.send(embed=embed)
                return
            
            # Check if either player is already in a duel
            if str(ctx.author.id) in self.active_duels or str(opponent.id) in self.active_duels:
                embed = self.embed_builder.warning_embed(
                    "Duel In Progress",
                    "One of you is already in an active duel!"
                )
                await ctx.send(embed=embed)
                return
            
            # Get both players' data
            challenger_data = data_manager.get_user_data(str(ctx.author.id))
            opponent_data = data_manager.get_user_data(str(opponent.id))
            
            # Check if both players have characters
            challenger_chars = challenger_data.get("claimed_waifus", [])
            opponent_chars = opponent_data.get("claimed_waifus", [])
            
            if not challenger_chars:
                embed = self.embed_builder.error_embed(
                    "No Characters",
                    "You need characters to duel! Use `!summon` first."
                )
                await ctx.send(embed=embed)
                return
            
            if not opponent_chars:
                embed = self.embed_builder.error_embed(
                    "Opponent Has No Characters",
                    f"{opponent.display_name} doesn't have any characters to duel with!"
                )
                await ctx.send(embed=embed)
                return
            
            # Create duel challenge
            duel_id = f"duel_{ctx.author.id}_{opponent.id}_{int(datetime.now().timestamp())}"
            
            self.active_duels[str(ctx.author.id)] = {
                "type": "challenger",
                "duel_id": duel_id,
                "opponent_id": str(opponent.id)
            }
            
            self.active_duels[str(opponent.id)] = {
                "type": "challenged",
                "duel_id": duel_id,
                "challenger_id": str(ctx.author.id)
            }
            
            # Create challenge embed
            embed = self.embed_builder.create_embed(
                title="⚔️ Duel Challenge!",
                description=f"**{ctx.author.display_name}** challenges **{opponent.display_name}** to a duel!",
                color=0xFF4500
            )
            
            # Show challenger's strongest character
            challenger_strongest = max(challenger_chars, key=lambda c: c.get("potential", 0))
            challenger_power = calculate_battle_power(challenger_strongest)
            
            embed.add_field(
                name=f"🗡️ Challenger: {ctx.author.display_name}",
                value=f"**Champion:** {challenger_strongest['name']}\n"
                      f"**Level:** {challenger_strongest.get('level', 1)}\n"
                      f"**Power:** {format_number(challenger_power)}",
                inline=True
            )
            
            # Show opponent's strongest character  
            opponent_strongest = max(opponent_chars, key=lambda c: c.get("potential", 0))
            opponent_power = calculate_battle_power(opponent_strongest)
            
            embed.add_field(
                name=f"🛡️ Challenged: {opponent.display_name}",
                value=f"**Champion:** {opponent_strongest['name']}\n"
                      f"**Level:** {opponent_strongest.get('level', 1)}\n"
                      f"**Power:** {format_number(opponent_power)}",
                inline=True
            )
            
            embed.add_field(
                name="🏆 Duel Stakes",
                value="• Winner gets 2000-3000 gold + XP\n"
                      "• Loser gets 200 gold + 100 XP\n"
                      "• Both gain PvP ranking points\n"
                      "• Glory and bragging rights!",
                inline=False
            )
            
            embed.add_field(
                name="⏱️ Challenge Expires",
                value=f"{opponent.mention} has 2 minutes to accept!\n"
                      "React with ⚔️ to accept the challenge!",
                inline=False
            )
            
            # Send challenge
            challenge_msg = await ctx.send(embed=embed)
            await challenge_msg.add_reaction("⚔️")
            
            # Wait for acceptance
            def check(reaction, user):
                return (user.id == opponent.id and 
                       str(reaction.emoji) == "⚔️" and 
                       reaction.message.id == challenge_msg.id)
            
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=120.0, check=check)
                
                # Execute duel
                await self.execute_duel(ctx, challenge_msg, ctx.author, opponent, challenger_strongest, opponent_strongest)
                
            except asyncio.TimeoutError:
                # Challenge expired
                self.active_duels.pop(str(ctx.author.id), None)
                self.active_duels.pop(str(opponent.id), None)
                
                timeout_embed = self.embed_builder.warning_embed(
                    "Challenge Expired",
                    f"{opponent.display_name} didn't respond to the duel challenge in time."
                )
                await challenge_msg.edit(embed=timeout_embed)
            
        except Exception as e:
            # Clean up active duels on error
            self.active_duels.pop(str(ctx.author.id), None)
            if opponent:
                self.active_duels.pop(str(opponent.id), None)
            
            embed = self.embed_builder.error_embed(
                "Duel Error",
                "Unable to create duel challenge."
            )
            await ctx.send(embed=embed)
            print(f"Duel command error: {e}")
    
    @commands.command(name="bosses", aliases=["world_boss", "raid"])
    async def boss_battles(self, ctx):
        """View active world bosses and join raids"""
        try:
            game_data = data_manager.get_game_data()
            active_bosses = game_data.get("active_bosses", [])
            
            embed = self.embed_builder.create_embed(
                title="🐉 World Boss Raids",
                description="Epic battles against legendary creatures!",
                color=0x8B0000
            )
            
            if active_bosses:
                for boss_data in active_bosses:
                    boss_info = self.world_bosses.get(boss_data["boss_type"], {})
                    participants = len(boss_data.get("participants", []))
                    
                    time_left = self.calculate_boss_time_remaining(boss_data["end_time"])
                    hp_percentage = (boss_data["current_hp"] / boss_info["hp"]) * 100
                    
                    embed.add_field(
                        name=f"{boss_info['emoji']} {boss_info['name']}",
                        value=f"*{boss_info['description']}*\n"
                              f"**HP:** {hp_percentage:.1f}% remaining\n"
                              f"**Participants:** {participants}/{boss_info['required_players']}\n"
                              f"**Time Left:** {time_left}\n"
                              f"Use: `!join_raid {boss_data['boss_id'][:8]}`",
                        inline=True
                    )
            else:
                embed.add_field(
                    name="😴 No Active Bosses",
                    value="No world bosses are currently active.\n"
                          "Bosses spawn randomly throughout the day!\n"
                          "Higher activity increases spawn chances.",
                    inline=False
                )
            
            # Show boss spawn information
            embed.add_field(
                name="🌟 Boss Information",
                value="• Bosses require multiple players to defeat\n"
                      "• Participants share epic rewards\n"
                      "• Bosses have powerful special abilities\n"
                      "• Rare bosses drop legendary items",
                inline=False
            )
            
            # Show user's boss battle stats
            user_data = data_manager.get_user_data(str(ctx.author.id))
            boss_stats = user_data.get("boss_battle_stats", {})
            
            embed.add_field(
                name="🏆 Your Boss Stats",
                value=f"**Bosses Defeated:** {boss_stats.get('bosses_defeated', 0)}\n"
                      f"**Damage Dealt:** {format_number(boss_stats.get('total_damage', 0))}\n"
                      f"**Raids Joined:** {boss_stats.get('raids_joined', 0)}",
                inline=True
            )
            
            await ctx.send(embed=embed)
            await self.log_pvp_boss_activity(ctx, "boss_check")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Boss Error",
                "Unable to load boss information."
            )
            await ctx.send(embed=embed)
            print(f"Boss command error: {e}")
    
    @commands.command(name="join_raid", aliases=["attack_boss"])
    async def join_boss_raid(self, ctx, boss_id: str = None):
        """Join an active world boss raid"""
        try:
            if not boss_id:
                embed = self.embed_builder.error_embed(
                    "Boss ID Required",
                    "Please specify which boss to attack! Use `!bosses` to see active raids."
                )
                await ctx.send(embed=embed)
                return
            
            user_data = data_manager.get_user_data(str(ctx.author.id))
            user_characters = user_data.get("claimed_waifus", [])
            
            if not user_characters:
                embed = self.embed_builder.error_embed(
                    "No Characters",
                    "You need characters to fight bosses! Use `!summon` first."
                )
                await ctx.send(embed=embed)
                return
            
            # Find boss
            game_data = data_manager.get_game_data()
            active_bosses = game_data.get("active_bosses", [])
            
            target_boss = None
            for boss in active_bosses:
                if boss["boss_id"].startswith(boss_id):
                    target_boss = boss
                    break
            
            if not target_boss:
                embed = self.embed_builder.error_embed(
                    "Boss Not Found",
                    f"No active boss found with ID `{boss_id}`. Use `!bosses` to see active raids."
                )
                await ctx.send(embed=embed)
                return
            
            # Check if user already joined this raid
            participants = target_boss.get("participants", [])
            if str(ctx.author.id) in [p["user_id"] for p in participants]:
                embed = self.embed_builder.warning_embed(
                    "Already Joined",
                    "You're already participating in this boss raid!"
                )
                await ctx.send(embed=embed)
                return
            
            # Check if boss is still active
            if target_boss["current_hp"] <= 0:
                embed = self.embed_builder.warning_embed(
                    "Boss Defeated",
                    "This boss has already been defeated!"
                )
                await ctx.send(embed=embed)
                return
            
            # Select strongest character for raid
            strongest_char = max(user_characters, key=lambda c: c.get("potential", 0))
            char_power = calculate_battle_power(strongest_char)
            
            # Calculate damage dealt
            damage_dealt = int(char_power * random.uniform(0.8, 1.2))
            
            # Apply damage to boss
            target_boss["current_hp"] = max(0, target_boss["current_hp"] - damage_dealt)
            
            # Add participant
            participant_data = {
                "user_id": str(ctx.author.id),
                "username": ctx.author.display_name,
                "character_name": strongest_char["name"],
                "damage_dealt": damage_dealt,
                "joined_at": datetime.now().isoformat()
            }
            participants.append(participant_data)
            
            # Check if boss is defeated
            boss_info = self.world_bosses[target_boss["boss_type"]]
            boss_defeated = target_boss["current_hp"] <= 0
            
            if boss_defeated:
                # Distribute rewards to all participants
                await self.distribute_boss_rewards(ctx, target_boss, boss_info, participants)
                
                # Remove boss from active list
                active_bosses.remove(target_boss)
            
            # Save game data
            data_manager.save_game_data(game_data)
            
            # Create attack result embed
            embed = self.embed_builder.create_embed(
                title=f"⚔️ Boss Raid: {boss_info['name']}",
                description=f"**{strongest_char['name']}** unleashes a powerful attack!",
                color=0x8B0000
            )
            
            embed.add_field(
                name="💥 Attack Results",
                value=f"**Damage Dealt:** {format_number(damage_dealt)}\n"
                      f"**Boss HP:** {format_number(max(0, target_boss['current_hp']))}/{format_number(boss_info['hp'])}\n"
                      f"**HP Remaining:** {(max(0, target_boss['current_hp']) / boss_info['hp'] * 100):.1f}%",
                inline=True
            )
            
            embed.add_field(
                name="👥 Raid Progress",
                value=f"**Participants:** {len(participants)}\n"
                      f"**Required:** {boss_info['required_players']} minimum\n"
                      f"**Your Champion:** {strongest_char['name']}",
                inline=True
            )
            
            if boss_defeated:
                embed.add_field(
                    name="🎉 BOSS DEFEATED!",
                    value="The mighty foe has fallen! Rewards distributed to all participants!",
                    inline=False
                )
                embed.color = 0x32CD32
            else:
                embed.add_field(
                    name="⚡ Keep Fighting!",
                    value="The boss still stands! More warriors needed!",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            await self.log_pvp_boss_activity(ctx, "boss_attack", f"{boss_info['name']} - {format_number(damage_dealt)} damage")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Raid Error",
                "Unable to join boss raid."
            )
            await ctx.send(embed=embed)
            print(f"Join raid error: {e}")
    
    async def execute_duel(self, ctx, message, challenger, opponent, challenger_char, opponent_char):
        """Execute PvP duel between two players"""
        try:
            # Calculate battle powers
            challenger_power = calculate_battle_power(challenger_char)
            opponent_power = calculate_battle_power(opponent_char)
            
            # Add some randomness to battle
            challenger_final = challenger_power + random.randint(-200, 300)
            opponent_final = opponent_power + random.randint(-200, 300)
            
            winner = challenger if challenger_final > opponent_final else opponent
            loser = opponent if winner == challenger else challenger
            winner_char = challenger_char if winner == challenger else opponent_char
            loser_char = opponent_char if winner == challenger else challenger_char
            
            # Calculate rewards
            gold_reward = random.randint(1000, 3000)
            xp_reward = random.randint(300, 800)
            consolation_gold = 200
            consolation_xp = 100
            
            # Apply rewards
            winner_data = data_manager.get_user_data(str(winner.id))
            loser_data = data_manager.get_user_data(str(loser.id))
            
            winner_data["gold"] = winner_data.get("gold", 0) + gold_reward
            winner_data["xp"] = winner_data.get("xp", 0) + xp_reward
            loser_data["gold"] = loser_data.get("gold", 0) + consolation_gold
            loser_data["xp"] = loser_data.get("xp", 0) + consolation_xp
            
            # Update PvP stats
            self.update_pvp_stats(winner_data, True, gold_reward)
            self.update_pvp_stats(loser_data, False, consolation_gold)
            
            # Save data
            data_manager.save_user_data(str(winner.id), winner_data)
            data_manager.save_user_data(str(loser.id), loser_data)
            
            # Clean up active duels
            self.active_duels.pop(str(challenger.id), None)
            self.active_duels.pop(str(opponent.id), None)
            
            # Create result embed
            embed = self.embed_builder.create_embed(
                title="🏆 Duel Results",
                description=f"**{winner.display_name}** emerges victorious!",
                color=0x32CD32
            )
            
            embed.add_field(
                name="⚔️ Battle Summary",
                value=f"**Winner:** {winner.display_name} ({winner_char['name']})\n"
                      f"**Winner Power:** {format_number(challenger_final if winner == challenger else opponent_final)}\n"
                      f"**Loser:** {loser.display_name} ({loser_char['name']})\n"
                      f"**Loser Power:** {format_number(opponent_final if winner == challenger else challenger_final)}",
                inline=False
            )
            
            embed.add_field(
                name="🎁 Winner Rewards",
                value=f"💰 Gold: +{format_number(gold_reward)}\n"
                      f"⭐ XP: +{format_number(xp_reward)}\n"
                      f"🏆 PvP Points: +25",
                inline=True
            )
            
            embed.add_field(
                name="💙 Consolation Rewards",
                value=f"💰 Gold: +{format_number(consolation_gold)}\n"
                      f"⭐ XP: +{format_number(consolation_xp)}\n"
                      f"🏆 PvP Points: +10",
                inline=True
            )
            
            await message.edit(embed=embed)
            await self.log_pvp_boss_activity(ctx, "duel_complete", f"{winner.display_name} defeated {loser.display_name}")
            
        except Exception as e:
            print(f"Duel execution error: {e}")
    
    async def distribute_boss_rewards(self, ctx, boss_data: Dict, boss_info: Dict, participants: List[Dict]):
        """Distribute rewards to boss raid participants"""
        try:
            rewards = boss_info["rewards"]
            
            for participant in participants:
                user_id = participant["user_id"]
                user_data = data_manager.get_user_data(user_id)
                
                # Calculate individual rewards based on damage contribution
                damage_contribution = participant["damage_dealt"]
                total_damage = sum(p["damage_dealt"] for p in participants)
                contribution_percentage = damage_contribution / total_damage if total_damage > 0 else 0
                
                # Base rewards
                base_gold = random.randint(rewards["gold"][0], rewards["gold"][1])
                base_xp = random.randint(rewards["xp"][0], rewards["xp"][1])
                base_gems = random.randint(rewards["gems"][0], rewards["gems"][1])
                
                # Apply contribution bonus (top contributors get more)
                if contribution_percentage >= 0.3:  # Top contributor
                    gold_reward = int(base_gold * 1.5)
                    xp_reward = int(base_xp * 1.5)
                    gem_reward = int(base_gems * 1.3)
                    bonus_text = "🌟 Top Contributor Bonus!"
                elif contribution_percentage >= 0.15:  # High contributor
                    gold_reward = int(base_gold * 1.2)
                    xp_reward = int(base_xp * 1.2)
                    gem_reward = int(base_gems * 1.1)
                    bonus_text = "⭐ High Contributor Bonus!"
                else:  # Regular participant
                    gold_reward = base_gold
                    xp_reward = base_xp
                    gem_reward = base_gems
                    bonus_text = ""
                
                # Apply rewards
                user_data["gold"] = user_data.get("gold", 0) + gold_reward
                user_data["xp"] = user_data.get("xp", 0) + xp_reward
                user_data["gems"] = user_data.get("gems", 0) + gem_reward
                
                # Update boss battle stats
                boss_stats = user_data.setdefault("boss_battle_stats", {})
                boss_stats["bosses_defeated"] = boss_stats.get("bosses_defeated", 0) + 1
                boss_stats["total_damage"] = boss_stats.get("total_damage", 0) + damage_contribution
                boss_stats["raids_joined"] = boss_stats.get("raids_joined", 0) + 1
                
                # Save data
                data_manager.save_user_data(user_id, user_data)
                
                # Send individual reward notification
                try:
                    user = self.bot.get_user(int(user_id))
                    if user:
                        reward_embed = self.embed_builder.success_embed(
                            "🐉 Boss Defeated!",
                            f"**{boss_info['name']}** has been vanquished!"
                        )
                        
                        reward_embed.add_field(
                            name="🎁 Your Rewards",
                            value=f"💰 Gold: +{format_number(gold_reward)}\n"
                                  f"⭐ XP: +{format_number(xp_reward)}\n"
                                  f"💎 Gems: +{gem_reward}\n"
                                  f"{bonus_text}",
                            inline=False
                        )
                        
                        await user.send(embed=reward_embed)
                except:
                    pass  # Ignore if can't DM user
            
            # Announce boss defeat in the channel
            defeat_embed = self.embed_builder.create_embed(
                title=f"🏆 {boss_info['name']} Defeated!",
                description=f"The mighty **{boss_info['name']}** has fallen to the combined might of {len(participants)} heroes!",
                color=0x32CD32
            )
            
            # Show top contributors
            top_contributors = sorted(participants, key=lambda p: p["damage_dealt"], reverse=True)[:3]
            contributors_text = ""
            
            for i, contributor in enumerate(top_contributors):
                medal = ["🥇", "🥈", "🥉"][i]
                contributors_text += f"{medal} **{contributor['username']}** ({contributor['character_name']})\n"
                contributors_text += f"   Damage: {format_number(contributor['damage_dealt'])}\n"
            
            defeat_embed.add_field(
                name="🌟 Top Contributors",
                value=contributors_text,
                inline=False
            )
            
            await ctx.send(embed=defeat_embed)
            
        except Exception as e:
            print(f"Boss reward distribution error: {e}")
    
    def update_pvp_stats(self, user_data: Dict, won: bool, gold_earned: int):
        """Update user's PvP statistics"""
        pvp_stats = user_data.setdefault("pvp_stats", {})
        
        pvp_stats["total_duels"] = pvp_stats.get("total_duels", 0) + 1
        pvp_stats["total_gold_earned"] = pvp_stats.get("total_gold_earned", 0) + gold_earned
        
        if won:
            pvp_stats["duels_won"] = pvp_stats.get("duels_won", 0) + 1
            pvp_stats["current_win_streak"] = pvp_stats.get("current_win_streak", 0) + 1
            pvp_stats["best_win_streak"] = max(pvp_stats.get("best_win_streak", 0), pvp_stats["current_win_streak"])
            pvp_stats["ranking_points"] = pvp_stats.get("ranking_points", 1000) + 25
        else:
            pvp_stats["duels_lost"] = pvp_stats.get("duels_lost", 0) + 1
            pvp_stats["current_win_streak"] = 0
            pvp_stats["ranking_points"] = max(800, pvp_stats.get("ranking_points", 1000) - 10)
    
    def calculate_boss_time_remaining(self, end_time: str) -> str:
        """Calculate time remaining for boss"""
        try:
            end_datetime = datetime.fromisoformat(end_time)
            time_left = end_datetime - datetime.now()
            
            if time_left.total_seconds() <= 0:
                return "Expired"
            
            hours = int(time_left.total_seconds() / 3600)
            minutes = int((time_left.total_seconds() % 3600) / 60)
            
            if hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
                
        except:
            return "Unknown"
    
    async def log_pvp_boss_activity(self, ctx, activity_type: str, details: str = ""):
        """Log PvP and boss activity to history channel"""
        try:
            history_channel = discord.utils.get(ctx.guild.text_channels, name='history')
            if not history_channel:
                return
            
            emojis = ["⚔️", "🐉", "🏆", "⚡", "💥", "🛡️"]
            emoji = random.choice(emojis)
            
            if activity_type == "boss_check":
                message = f"{emoji} **{ctx.author.display_name}** scouted for legendary world bosses and epic raid opportunities!"
            elif activity_type == "boss_attack":
                message = f"{emoji} **{ctx.author.display_name}** bravely joined the raid against {details}!"
            elif activity_type == "duel_challenge":
                message = f"{emoji} **{ctx.author.display_name}** issued a honorable duel challenge: {details}!"
            elif activity_type == "duel_complete":
                message = f"{emoji} Epic duel concluded: {details}!"
            else:
                message = f"{emoji} **{ctx.author.display_name}** engaged in intense PvP battles!"
            
            embed = self.embed_builder.create_embed(
                description=message,
                color=0x8B0000
            )
            
            await history_channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error logging PvP boss activity: {e}")

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(PvPBossCommands(bot))