# Quest System Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List, Any
import random
from datetime import datetime, timedelta

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from core.config import FEATURES
from utils.helpers import format_number

class QuestCommands(commands.Cog):
    """Quest and mission system with story campaigns and daily tasks"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        
        # Quest templates
        self.quest_types = {
            "daily": {
                "Battle Victory": {
                    "description": "Win 3 battles in any mode",
                    "requirements": {"battles_won": 3},
                    "rewards": {"gold": 500, "xp": 200},
                    "emoji": "⚔️"
                },
                "Character Care": {
                    "description": "Increase any character's affection by 10",
                    "requirements": {"affection_gained": 10},
                    "rewards": {"gold": 300, "xp": 150},
                    "emoji": "💖"
                },
                "Treasure Hunter": {
                    "description": "Earn 2000 gold through any activities",
                    "requirements": {"gold_earned": 2000},
                    "rewards": {"gems": 10, "xp": 100},
                    "emoji": "💰"
                },
                "Social Butterfly": {
                    "description": "Use 5 different commands",
                    "requirements": {"commands_used": 5},
                    "rewards": {"gold": 400, "xp": 175},
                    "emoji": "🦋"
                }
            },
            "weekly": {
                "Arena Champion": {
                    "description": "Win 15 arena battles this week",
                    "requirements": {"arena_wins": 15},
                    "rewards": {"gold": 3000, "gems": 25, "xp": 1000},
                    "emoji": "🏆"
                },
                "Collection Master": {
                    "description": "Summon 20 new characters",
                    "requirements": {"summons": 20},
                    "rewards": {"gold": 2500, "gems": 20, "summon_ticket": 1},
                    "emoji": "✨"
                },
                "Economy Expert": {
                    "description": "Spend 10,000 gold in the store",
                    "requirements": {"gold_spent": 10000},
                    "rewards": {"gems": 30, "vip_day": 1},
                    "emoji": "💎"
                }
            },
            "story": {
                "The First Summon": {
                    "description": "Begin your journey by summoning your first character",
                    "requirements": {"first_summon": 1},
                    "rewards": {"gold": 1000, "gems": 15, "xp": 300},
                    "emoji": "🌟",
                    "chapter": 1
                },
                "Building Power": {
                    "description": "Reach level 10 with any character",
                    "requirements": {"character_level_10": 1},
                    "rewards": {"gold": 2000, "gems": 25, "enhancement_item": 1},
                    "emoji": "💪",
                    "chapter": 2
                },
                "Arena Debut": {
                    "description": "Win your first arena battle",
                    "requirements": {"first_arena_win": 1},
                    "rewards": {"gold": 1500, "arena_pass": 1},
                    "emoji": "🗡️",
                    "chapter": 3
                }
            }
        }
    
    @commands.command(name="quests", aliases=["missions", "tasks"])
    async def view_quests(self, ctx, quest_type: str = "daily"):
        """View available quests and your progress"""
        try:
            if quest_type.lower() not in ["daily", "weekly", "story"]:
                quest_type = "daily"
            
            user_data = data_manager.get_user_data(str(ctx.author.id))
            quest_data = user_data.get("quests", {})
            
            embed = self.embed_builder.create_embed(
                title=f"📜 {quest_type.title()} Quests",
                description=f"Your {quest_type} missions and progress",
                color=0x4169E1
            )
            
            # Get quests for this type
            available_quests = self.quest_types[quest_type.lower()]
            user_quest_progress = quest_data.get(quest_type.lower(), {})
            
            for quest_name, quest_info in available_quests.items():
                progress = user_quest_progress.get(quest_name, {"progress": {}, "completed": False})
                
                if progress["completed"]:
                    status = "✅ Completed"
                    status_color = "```diff\n+ "
                else:
                    # Check progress
                    progress_text = self.calculate_quest_progress(quest_info["requirements"], progress["progress"])
                    if progress_text == "Ready to complete!":
                        status = "🎁 Ready to claim!"
                        status_color = "```yaml\n"
                    else:
                        status = f"📊 {progress_text}"
                        status_color = "```\n"
                
                embed.add_field(
                    name=f"{quest_info['emoji']} {quest_name}",
                    value=f"{status_color}{quest_info['description']}\n"
                          f"Status: {status}\n"
                          f"Rewards: {self.format_quest_rewards(quest_info['rewards'])}```",
                    inline=False
                )
            
            # Show quest statistics
            total_completed = sum(1 for q in user_quest_progress.values() if q.get("completed", False))
            embed.add_field(
                name="📊 Quest Statistics",
                value=f"**Completed {quest_type.title()}:** {total_completed}/{len(available_quests)}\n"
                      f"**Total Quest XP:** {format_number(quest_data.get('total_quest_xp', 0))}\n"
                      f"**Quest Master Level:** {self.calculate_quest_master_level(quest_data)}",
                inline=False
            )
            
            await ctx.send(embed=embed)
            await self.log_quest_activity(ctx, "view", quest_type)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Quest Error",
                "Unable to load quest information."
            )
            await ctx.send(embed=embed)
            print(f"Quests command error: {e}")
    
    @commands.command(name="complete_quest", aliases=["claim_quest"])
    async def complete_quest(self, ctx, quest_type: str, *, quest_name: str):
        """Complete a finished quest and claim rewards"""
        try:
            if quest_type.lower() not in ["daily", "weekly", "story"]:
                embed = self.embed_builder.error_embed(
                    "Invalid Quest Type",
                    "Quest type must be 'daily', 'weekly', or 'story'."
                )
                await ctx.send(embed=embed)
                return
            
            user_data = data_manager.get_user_data(str(ctx.author.id))
            quest_data = user_data.get("quests", {})
            user_quest_progress = quest_data.get(quest_type.lower(), {})
            
            # Find quest
            available_quests = self.quest_types[quest_type.lower()]
            if quest_name not in available_quests:
                embed = self.embed_builder.error_embed(
                    "Quest Not Found",
                    f"Quest '{quest_name}' not found in {quest_type} quests."
                )
                await ctx.send(embed=embed)
                return
            
            quest_info = available_quests[quest_name]
            progress = user_quest_progress.get(quest_name, {"progress": {}, "completed": False})
            
            if progress["completed"]:
                embed = self.embed_builder.warning_embed(
                    "Quest Already Completed",
                    f"You've already completed '{quest_name}' quest!"
                )
                await ctx.send(embed=embed)
                return
            
            # Check if quest is ready to complete
            if not self.is_quest_ready(quest_info["requirements"], progress["progress"]):
                progress_text = self.calculate_quest_progress(quest_info["requirements"], progress["progress"])
                embed = self.embed_builder.warning_embed(
                    "Quest Not Ready",
                    f"Quest requirements not met yet.\nProgress: {progress_text}"
                )
                await ctx.send(embed=embed)
                return
            
            # Apply rewards
            rewards = quest_info["rewards"]
            reward_text = ""
            
            if "gold" in rewards:
                user_data["gold"] = user_data.get("gold", 0) + rewards["gold"]
                reward_text += f"💰 Gold: +{format_number(rewards['gold'])}\n"
            
            if "xp" in rewards:
                user_data["xp"] = user_data.get("xp", 0) + rewards["xp"]
                reward_text += f"⭐ XP: +{format_number(rewards['xp'])}\n"
            
            if "gems" in rewards:
                user_data["gems"] = user_data.get("gems", 0) + rewards["gems"]
                reward_text += f"💎 Gems: +{rewards['gems']}\n"
            
            # Apply special rewards
            if "summon_ticket" in rewards:
                inventory = user_data.setdefault("inventory", {})
                inventory["summon_ticket"] = inventory.get("summon_ticket", 0) + rewards["summon_ticket"]
                reward_text += f"🎟️ Summon Tickets: +{rewards['summon_ticket']}\n"
            
            if "arena_pass" in rewards:
                inventory = user_data.setdefault("inventory", {})
                inventory["arena_pass"] = inventory.get("arena_pass", 0) + rewards["arena_pass"]
                reward_text += f"🎫 Arena Passes: +{rewards['arena_pass']}\n"
            
            # Mark quest as completed
            progress["completed"] = True
            progress["completed_at"] = datetime.now().isoformat()
            user_quest_progress[quest_name] = progress
            quest_data[quest_type.lower()] = user_quest_progress
            
            # Update quest statistics
            quest_data["total_quest_xp"] = quest_data.get("total_quest_xp", 0) + rewards.get("xp", 0)
            quest_data["total_quests_completed"] = quest_data.get("total_quests_completed", 0) + 1
            
            user_data["quests"] = quest_data
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Create completion embed
            embed = self.embed_builder.success_embed(
                "Quest Completed!",
                f"**{quest_name}** has been successfully completed!"
            )
            
            embed.add_field(
                name="📜 Quest Details",
                value=f"{quest_info['emoji']} **{quest_name}**\n*{quest_info['description']}*",
                inline=False
            )
            
            embed.add_field(
                name="🎁 Rewards Claimed",
                value=reward_text,
                inline=False
            )
            
            # Check for quest master level up
            new_level = self.calculate_quest_master_level(quest_data)
            old_level = quest_data.get("quest_master_level", 1)
            
            if new_level > old_level:
                quest_data["quest_master_level"] = new_level
                embed.add_field(
                    name="🌟 Quest Master Level Up!",
                    value=f"You've reached Quest Master Level {new_level}!\n"
                          f"Unlocked new quest bonuses!",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            await self.log_quest_activity(ctx, "complete", f"{quest_type} - {quest_name}")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Quest Completion Error",
                "Unable to complete quest. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Complete quest error: {e}")
    
    def calculate_quest_progress(self, requirements: Dict, progress: Dict) -> str:
        """Calculate quest completion progress"""
        total_requirements = len(requirements)
        completed_requirements = 0
        
        for req, required_value in requirements.items():
            current_value = progress.get(req, 0)
            if current_value >= required_value:
                completed_requirements += 1
        
        if completed_requirements == total_requirements:
            return "Ready to complete!"
        else:
            return f"{completed_requirements}/{total_requirements} objectives"
    
    def is_quest_ready(self, requirements: Dict, progress: Dict) -> bool:
        """Check if quest is ready to be completed"""
        for req, required_value in requirements.items():
            current_value = progress.get(req, 0)
            if current_value < required_value:
                return False
        return True
    
    def format_quest_rewards(self, rewards: Dict) -> str:
        """Format quest rewards for display"""
        reward_parts = []
        
        if "gold" in rewards:
            reward_parts.append(f"{format_number(rewards['gold'])} gold")
        if "xp" in rewards:
            reward_parts.append(f"{format_number(rewards['xp'])} XP")
        if "gems" in rewards:
            reward_parts.append(f"{rewards['gems']} gems")
        if "summon_ticket" in rewards:
            reward_parts.append(f"{rewards['summon_ticket']} summon ticket")
        
        return " • ".join(reward_parts)
    
    def calculate_quest_master_level(self, quest_data: Dict) -> int:
        """Calculate quest master level based on completed quests"""
        total_completed = quest_data.get("total_quests_completed", 0)
        return min(50, 1 + (total_completed // 5))  # Level up every 5 quests
    
    async def update_quest_progress(self, user_id: str, activity_type: str, amount: int = 1):
        """Update quest progress for various activities"""
        try:
            user_data = data_manager.get_user_data(user_id)
            quest_data = user_data.get("quests", {})
            
            # Update daily quest progress
            daily_quests = quest_data.get("daily", {})
            today = datetime.now().date().isoformat()
            
            for quest_name, quest_info in self.quest_types["daily"].items():
                quest_progress = daily_quests.get(quest_name, {"progress": {}, "completed": False, "date": today})
                
                # Reset if new day
                if quest_progress.get("date") != today:
                    quest_progress = {"progress": {}, "completed": False, "date": today}
                
                if not quest_progress["completed"]:
                    # Update relevant progress
                    requirements = quest_info["requirements"]
                    for req_type in requirements.keys():
                        if req_type == f"{activity_type}s" or req_type == activity_type:
                            quest_progress["progress"][req_type] = quest_progress["progress"].get(req_type, 0) + amount
                
                daily_quests[quest_name] = quest_progress
            
            quest_data["daily"] = daily_quests
            user_data["quests"] = quest_data
            data_manager.save_user_data(user_id, user_data)
            
        except Exception as e:
            print(f"Quest progress update error: {e}")
    
    async def log_quest_activity(self, ctx, activity_type: str, details: str = ""):
        """Log quest activity to history channel"""
        try:
            history_channel = discord.utils.get(ctx.guild.text_channels, name='history')
            if not history_channel:
                return
            
            emojis = ["📜", "🎯", "⭐", "🏆", "✨", "🌟"]
            emoji = random.choice(emojis)
            
            if activity_type == "view":
                message = f"{emoji} **{ctx.author.display_name}** reviewed their {details} quest objectives and heroic progress!"
            elif activity_type == "complete":
                message = f"{emoji} **{ctx.author.display_name}** triumphantly completed the {details} quest and claimed magnificent rewards!"
            else:
                message = f"{emoji} **{ctx.author.display_name}** embarked on their quest journey!"
            
            embed = self.embed_builder.create_embed(
                description=message,
                color=0x4169E1
            )
            
            await history_channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error logging quest activity: {e}")

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(QuestCommands(bot))