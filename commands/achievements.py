# Achievements and Milestone System for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List, Tuple
import json
from datetime import datetime

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from utils.helpers import format_number

class AchievementsCommands(commands.Cog):
    """Achievement tracking, milestones, and lore collection system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        
        # Achievement definitions organized by category
        self.achievements = {
            # Collection achievements
            "first_summon": {
                "name": "First Steps",
                "description": "Summon your first character",
                "category": "collection",
                "requirements": {"characters_summoned": 1},
                "rewards": {"gold": 1000, "gems": 50},
                "points": 10,
                "icon": "🌟"
            },
            "collector": {
                "name": "Collector",
                "description": "Own 25 different characters",
                "category": "collection",
                "requirements": {"unique_characters": 25},
                "rewards": {"gold": 10000, "gems": 200, "Collector's Badge": 1},
                "points": 50,
                "icon": "📚"
            },
            "legendary_collector": {
                "name": "Legendary Collector", 
                "description": "Own 100 different characters",
                "category": "collection",
                "requirements": {"unique_characters": 100},
                "rewards": {"gold": 50000, "gems": 1000, "Legendary Crown": 1},
                "points": 200,
                "icon": "👑"
            },
            
            # Battle achievements
            "first_victory": {
                "name": "First Victory",
                "description": "Win your first battle",
                "category": "battle",
                "requirements": {"battles_won": 1},
                "rewards": {"gold": 500, "Experience Scroll": 1},
                "points": 10,
                "icon": "⚔️"
            },
            "warrior": {
                "name": "Seasoned Warrior",
                "description": "Win 100 battles",
                "category": "battle",
                "requirements": {"battles_won": 100},
                "rewards": {"gold": 15000, "Battle Banner": 1},
                "points": 75,
                "icon": "🛡️"
            },
            "champion": {
                "name": "Arena Champion",
                "description": "Achieve a 90% win rate with at least 50 battles",
                "category": "battle",
                "requirements": {"battles_won": 50, "win_rate": 0.9},
                "rewards": {"gold": 25000, "Champion's Trophy": 1},
                "points": 150,
                "icon": "🏆"
            },
            
            # Economic achievements  
            "entrepreneur": {
                "name": "Entrepreneur",
                "description": "Own 3 different businesses",
                "category": "economy",
                "requirements": {"businesses_owned": 3},
                "rewards": {"gold": 20000, "Business License": 1},
                "points": 60,
                "icon": "💼"
            },
            "millionaire": {
                "name": "Millionaire",
                "description": "Accumulate 1,000,000 gold",
                "category": "economy",
                "requirements": {"total_gold_earned": 1000000},
                "rewards": {"gems": 500, "Golden Crown": 1},
                "points": 100,
                "icon": "💰"
            },
            
            # Crafting achievements
            "apprentice_crafter": {
                "name": "Apprentice Crafter",
                "description": "Successfully craft 50 items",
                "category": "crafting",
                "requirements": {"items_crafted": 50},
                "rewards": {"gold": 5000, "Crafting Kit": 1},
                "points": 40,
                "icon": "🔨"
            },
            "master_crafter": {
                "name": "Master Crafter",
                "description": "Reach crafting level 15",
                "category": "crafting",
                "requirements": {"crafting_level": 15},
                "rewards": {"gold": 30000, "Master's Hammer": 1},
                "points": 120,
                "icon": "⚒️"
            },
            
            # Social achievements
            "guild_founder": {
                "name": "Guild Founder",
                "description": "Create a guild",
                "category": "social",
                "requirements": {"guilds_created": 1},
                "rewards": {"gold": 10000, "Founder's Seal": 1},
                "points": 50,
                "icon": "🏰"
            },
            "loyal_member": {
                "name": "Loyal Member",
                "description": "Stay in the same guild for 30 days",
                "category": "social",
                "requirements": {"guild_loyalty_days": 30},
                "rewards": {"gold": 15000, "Loyalty Badge": 1},
                "points": 80,
                "icon": "🤝"
            },
            
            # Special achievements
            "daily_devotee": {
                "name": "Daily Devotee",
                "description": "Claim daily rewards for 30 consecutive days",
                "category": "special",
                "requirements": {"consecutive_daily_claims": 30},
                "rewards": {"gold": 25000, "gems": 500, "Devotion Crown": 1},
                "points": 100,
                "icon": "🔥"
            },
            "dream_walker": {
                "name": "Dream Walker",
                "description": "Experience 50 dream events",
                "category": "special",
                "requirements": {"dreams_experienced": 50},
                "rewards": {"gold": 20000, "Dream Crystal": 1},
                "points": 90,
                "icon": "💤"
            },
            "completionist": {
                "name": "Completionist",
                "description": "Unlock all other achievements",
                "category": "special",
                "requirements": {"achievements_unlocked": "all_others"},
                "rewards": {"gold": 100000, "gems": 2000, "Completionist Crown": 1},
                "points": 500,
                "icon": "🌈"
            }
        }
        
        # Lore books that can be collected
        self.lore_books = {
            "ancient_history": {
                "name": "Chronicles of the Ancient Era",
                "chapters": 12,
                "unlock_requirement": {"level": 10},
                "description": "The history of the realm before the Great Convergence"
            },
            "character_legends": {
                "name": "Legends of Heroes",
                "chapters": 25,
                "unlock_requirement": {"unique_characters": 20},
                "description": "Stories of the legendary characters you can summon"
            },
            "guild_wars": {
                "name": "The Guild Wars Saga",
                "chapters": 8,
                "unlock_requirement": {"guild_level": 3},
                "description": "Epic tales of guild conflicts and alliances"
            },
            "crafting_mastery": {
                "name": "Secrets of the Master Craftsmen",
                "chapters": 15,
                "unlock_requirement": {"crafting_level": 10},
                "description": "Advanced techniques and forbidden recipes"
            }
        }
    
    @commands.group(name="achievements", aliases=["achieve"], invoke_without_command=True)
    async def achievements_group(self, ctx):
        """View your achievement progress and statistics"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            
            # Get achievement progress
            unlocked_achievements = user_data.get("achievements", [])
            total_points = sum(self.achievements[ach_id]["points"] for ach_id in unlocked_achievements if ach_id in self.achievements)
            
            # Create overview embed
            embed = self.create_achievements_overview_embed(unlocked_achievements, total_points)
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Achievements Error",
                "Unable to load achievement information."
            )
            await ctx.send(embed=error_embed)
            print(f"Achievements command error: {e}")
    
    @achievements_group.command(name="list")
    async def list_achievements(self, ctx, category: str = None):
        """List all achievements, optionally filtered by category"""
        try:
            if category:
                # Filter by category
                filtered_achievements = {k: v for k, v in self.achievements.items() if v["category"] == category.lower()}
                if not filtered_achievements:
                    categories = list(set(ach["category"] for ach in self.achievements.values()))
                    embed = self.embed_builder.error_embed(
                        "Invalid Category",
                        f"Available categories: {', '.join(categories)}"
                    )
                    await ctx.send(embed=embed)
                    return
                achievements_to_show = filtered_achievements
                title = f"🏆 {category.title()} Achievements"
            else:
                achievements_to_show = self.achievements
                title = "🏆 All Achievements"
            
            user_data = data_manager.get_user_data(str(ctx.author.id))
            unlocked = user_data.get("achievements", [])
            
            # Create achievements list embed
            embed = self.create_achievements_list_embed(achievements_to_show, unlocked, title)
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Achievement List Error",
                "Unable to load achievement list."
            )
            await ctx.send(embed=error_embed)
            print(f"Achievement list error: {e}")
    
    @achievements_group.command(name="check")
    async def check_achievements(self, ctx):
        """Check for any newly unlocked achievements"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            
            # Check all achievements
            newly_unlocked = await self.check_user_achievements(str(ctx.author.id), user_data)
            
            if newly_unlocked:
                # Create achievement unlock embed
                embed = self.create_achievement_unlock_embed(newly_unlocked)
                await ctx.send(embed=embed)
            else:
                embed = self.embed_builder.info_embed(
                    "No New Achievements",
                    "You haven't unlocked any new achievements. Keep playing to earn more!"
                )
                await ctx.send(embed=embed)
                
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Achievement Check Error",
                "Unable to check for new achievements."
            )
            await ctx.send(embed=error_embed)
            print(f"Achievement check error: {e}")
    
    @commands.group(name="lore", invoke_without_command=True)
    async def lore_group(self, ctx):
        """View your lore book collection"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            
            # Create lore overview embed
            embed = self.create_lore_overview_embed(user_data)
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Lore Error",
                "Unable to load lore collection."
            )
            await ctx.send(embed=error_embed)
            print(f"Lore command error: {e}")
    
    @lore_group.command(name="read")
    async def read_lore(self, ctx, book_name: str, chapter: int = 1):
        """Read a specific chapter from a lore book"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            
            # Find the lore book
            book_id = None
            for lore_id, lore_data in self.lore_books.items():
                if book_name.lower() in lore_id.lower() or book_name.lower() in lore_data["name"].lower():
                    book_id = lore_id
                    break
            
            if not book_id:
                available_books = [book["name"] for book in self.lore_books.values()]
                embed = self.embed_builder.error_embed(
                    "Book Not Found",
                    f"Available books: {', '.join(available_books)}"
                )
                await ctx.send(embed=embed)
                return
            
            book_data = self.lore_books[book_id]
            
            # Check if user has unlocked this book
            unlocked_books = user_data.get("unlocked_lore_books", [])
            if book_id not in unlocked_books:
                # Check if user meets requirements
                if self.check_lore_requirements(user_data, book_data["unlock_requirement"]):
                    # Unlock the book
                    unlocked_books.append(book_id)
                    user_data["unlocked_lore_books"] = unlocked_books
                    data_manager.save_user_data(str(ctx.author.id), user_data)
                    
                    unlock_embed = self.embed_builder.success_embed(
                        "Lore Book Unlocked!",
                        f"You've unlocked **{book_data['name']}**!"
                    )
                    await ctx.send(embed=unlock_embed)
                else:
                    embed = self.embed_builder.error_embed(
                        "Book Locked",
                        f"You haven't met the requirements to unlock **{book_data['name']}** yet."
                    )
                    await ctx.send(embed=embed)
                    return
            
            # Validate chapter number
            if chapter < 1 or chapter > book_data["chapters"]:
                embed = self.embed_builder.error_embed(
                    "Invalid Chapter",
                    f"**{book_data['name']}** has {book_data['chapters']} chapters. Please choose a chapter between 1 and {book_data['chapters']}."
                )
                await ctx.send(embed=embed)
                return
            
            # Create lore reading embed
            embed = self.create_lore_reading_embed(book_data, chapter)
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Lore Reading Error",
                "Unable to read lore chapter."
            )
            await ctx.send(embed=error_embed)
            print(f"Lore reading error: {e}")
    
    async def check_user_achievements(self, user_id: str, user_data: Dict) -> List[Dict]:
        """Check if user has unlocked any new achievements"""
        current_achievements = set(user_data.get("achievements", []))
        newly_unlocked = []
        
        for ach_id, ach_data in self.achievements.items():
            if ach_id in current_achievements:
                continue
            
            # Check if requirements are met
            if self.check_achievement_requirements(user_data, ach_data["requirements"]):
                # Unlock achievement
                current_achievements.add(ach_id)
                newly_unlocked.append(ach_data.copy())
                newly_unlocked[-1]["id"] = ach_id
                
                # Give rewards
                await self.give_achievement_rewards(user_id, ach_data["rewards"])
        
        # Save updated achievements
        if newly_unlocked:
            user_data["achievements"] = list(current_achievements)
            data_manager.save_user_data(user_id, user_data)
        
        return newly_unlocked
    
    def check_achievement_requirements(self, user_data: Dict, requirements: Dict) -> bool:
        """Check if user meets achievement requirements"""
        for req_type, req_value in requirements.items():
            if req_type == "characters_summoned":
                total_summoned = user_data.get("summon_stats", {}).get("total_summons", 0)
                if total_summoned < req_value:
                    return False
            
            elif req_type == "unique_characters":
                unique_count = len(user_data.get("claimed_waifus", []))
                if unique_count < req_value:
                    return False
            
            elif req_type == "battles_won":
                wins = user_data.get("battle_stats", {}).get("battles_won", 0)
                if wins < req_value:
                    return False
            
            elif req_type == "win_rate":
                battle_stats = user_data.get("battle_stats", {})
                wins = battle_stats.get("battles_won", 0)
                losses = battle_stats.get("battles_lost", 0)
                total = wins + losses
                if total == 0 or (wins / total) < req_value:
                    return False
            
            elif req_type == "businesses_owned":
                businesses = len(user_data.get("investments", {}))
                if businesses < req_value:
                    return False
            
            elif req_type == "total_gold_earned":
                total_earned = user_data.get("lifetime_gold_earned", 0)
                if total_earned < req_value:
                    return False
            
            elif req_type == "items_crafted":
                crafted = user_data.get("crafting_stats", {}).get("successful_crafts", 0)
                if crafted < req_value:
                    return False
            
            elif req_type == "crafting_level":
                level = user_data.get("crafting_level", 1)
                if level < req_value:
                    return False
            
            elif req_type == "consecutive_daily_claims":
                streak = user_data.get("consecutive_daily_claims", 0)
                if streak < req_value:
                    return False
            
            elif req_type == "dreams_experienced":
                dreams = len(user_data.get("dreams_experienced", []))
                if dreams < req_value:
                    return False
            
            elif req_type == "achievements_unlocked":
                if req_value == "all_others":
                    current_achievements = set(user_data.get("achievements", []))
                    total_others = len(self.achievements) - 1  # Exclude completionist
                    if len(current_achievements) < total_others:
                        return False
        
        return True
    
    def check_lore_requirements(self, user_data: Dict, requirements: Dict) -> bool:
        """Check if user meets lore book unlock requirements"""
        for req_type, req_value in requirements.items():
            if req_type == "level":
                if user_data.get("level", 1) < req_value:
                    return False
            elif req_type == "unique_characters":
                if len(user_data.get("claimed_waifus", [])) < req_value:
                    return False
            elif req_type == "guild_level":
                # This would need guild system integration
                guild_level = user_data.get("guild_level", 0)
                if guild_level < req_value:
                    return False
            elif req_type == "crafting_level":
                if user_data.get("crafting_level", 1) < req_value:
                    return False
        
        return True
    
    async def give_achievement_rewards(self, user_id: str, rewards: Dict):
        """Give achievement rewards to user"""
        user_data = data_manager.get_user_data(user_id)
        inventory = user_data.setdefault("inventory", {})
        
        for item, amount in rewards.items():
            if item == "gold":
                user_data["gold"] = user_data.get("gold", 0) + amount
            elif item == "gems":
                user_data["gems"] = user_data.get("gems", 0) + amount
            else:
                inventory[item] = inventory.get(item, 0) + amount
        
        data_manager.save_user_data(user_id, user_data)
    
    def create_achievements_overview_embed(self, unlocked: List[str], total_points: int) -> discord.Embed:
        """Create achievements overview embed"""
        total_achievements = len(self.achievements)
        unlocked_count = len(unlocked)
        completion_percentage = (unlocked_count / total_achievements * 100) if total_achievements > 0 else 0
        
        embed = self.embed_builder.create_embed(
            title="🏆 Achievement Progress",
            description=f"Your journey through the realm's challenges",
            color=0xFFD700
        )
        
        # Progress stats
        embed.add_field(
            name="📊 Progress Overview",
            value=f"Unlocked: **{unlocked_count}/{total_achievements}** ({completion_percentage:.1f}%)\n"
                  f"Achievement Points: **{format_number(total_points)}**\n"
                  f"Rank: {self.get_achievement_rank(total_points)}",
            inline=True
        )
        
        # Recent achievements
        if unlocked:
            recent = unlocked[-3:]  # Last 3 achievements
            recent_text = ""
            for ach_id in recent:
                if ach_id in self.achievements:
                    ach = self.achievements[ach_id]
                    recent_text += f"{ach['icon']} {ach['name']}\n"
            
            embed.add_field(
                name="🌟 Recent Achievements",
                value=recent_text or "None yet",
                inline=True
            )
        
        # Categories progress
        categories = {}
        for ach_id, ach_data in self.achievements.items():
            category = ach_data["category"]
            if category not in categories:
                categories[category] = {"total": 0, "unlocked": 0}
            categories[category]["total"] += 1
            if ach_id in unlocked:
                categories[category]["unlocked"] += 1
        
        category_text = ""
        for category, data in categories.items():
            percentage = (data["unlocked"] / data["total"] * 100) if data["total"] > 0 else 0
            category_text += f"**{category.title()}**: {data['unlocked']}/{data['total']} ({percentage:.0f}%)\n"
        
        embed.add_field(
            name="📋 Category Progress",
            value=category_text,
            inline=False
        )
        
        embed.add_field(
            name="💡 Commands",
            value="• `!achievements list [category]` - View all achievements\n"
                  "• `!achievements check` - Check for new achievements\n"
                  "• `!lore` - View lore collection",
            inline=False
        )
        
        return embed
    
    def create_achievements_list_embed(self, achievements: Dict, unlocked: List[str], title: str) -> discord.Embed:
        """Create achievements list embed"""
        embed = self.embed_builder.create_embed(
            title=title,
            color=0xFFD700
        )
        
        # Group by category
        by_category = {}
        for ach_id, ach_data in achievements.items():
            category = ach_data["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append((ach_id, ach_data))
        
        # Add fields for each category
        for category, achievement_list in by_category.items():
            achievements_text = ""
            for ach_id, ach_data in achievement_list[:5]:  # Limit to 5 per category
                status = "✅" if ach_id in unlocked else "❌"
                achievements_text += f"{status} {ach_data['icon']} **{ach_data['name']}** ({ach_data['points']} pts)\n"
                achievements_text += f"   {ach_data['description']}\n\n"
            
            if len(achievement_list) > 5:
                achievements_text += f"... and {len(achievement_list) - 5} more"
            
            embed.add_field(
                name=f"🏆 {category.title()}",
                value=achievements_text or "No achievements",
                inline=True
            )
        
        return embed
    
    def create_achievement_unlock_embed(self, newly_unlocked: List[Dict]) -> discord.Embed:
        """Create achievement unlock notification embed"""
        if len(newly_unlocked) == 1:
            achievement = newly_unlocked[0]
            embed = self.embed_builder.success_embed(
                "🎉 Achievement Unlocked!",
                f"**{achievement['name']}**"
            )
            
            embed.add_field(
                name="📜 Description",
                value=achievement["description"],
                inline=False
            )
            
            # Show rewards
            rewards_text = ""
            for item, amount in achievement["rewards"].items():
                if item == "gold":
                    rewards_text += f"💰 {format_number(amount)} gold\n"
                elif item == "gems":
                    rewards_text += f"💎 {format_number(amount)} gems\n"
                else:
                    rewards_text += f"🎁 {item} x{amount}\n"
            
            embed.add_field(
                name="🎁 Rewards",
                value=rewards_text,
                inline=True
            )
            
            embed.add_field(
                name="⭐ Points",
                value=f"+{achievement['points']} achievement points",
                inline=True
            )
        else:
            embed = self.embed_builder.success_embed(
                f"🎊 {len(newly_unlocked)} Achievements Unlocked!",
                "Congratulations on your progress!"
            )
            
            achievements_text = ""
            total_points = 0
            for achievement in newly_unlocked:
                achievements_text += f"{achievement['icon']} **{achievement['name']}**\n"
                total_points += achievement["points"]
            
            embed.add_field(
                name="🏆 New Achievements",
                value=achievements_text,
                inline=False
            )
            
            embed.add_field(
                name="⭐ Total Points Earned",
                value=f"+{total_points} achievement points",
                inline=True
            )
        
        return embed
    
    def create_lore_overview_embed(self, user_data: Dict) -> discord.Embed:
        """Create lore collection overview embed"""
        embed = self.embed_builder.create_embed(
            title="📚 Lore Collection",
            description="Discover the rich history and legends of the realm",
            color=0x8B4513
        )
        
        unlocked_books = user_data.get("unlocked_lore_books", [])
        
        for book_id, book_data in self.lore_books.items():
            if book_id in unlocked_books:
                status = "✅ Unlocked"
                desc = book_data["description"]
            else:
                status = "🔒 Locked"
                req_text = ", ".join([f"{k}: {v}" for k, v in book_data["unlock_requirement"].items()])
                desc = f"Requirements: {req_text}"
            
            embed.add_field(
                name=f"📖 {book_data['name']}",
                value=f"{status}\n{desc}\nChapters: {book_data['chapters']}",
                inline=True
            )
        
        embed.add_field(
            name="💡 Reading",
            value="Use `!lore read <book_name> [chapter]` to read unlocked books",
            inline=False
        )
        
        return embed
    
    def create_lore_reading_embed(self, book_data: Dict, chapter: int) -> discord.Embed:
        """Create lore reading embed with generated content"""
        embed = self.embed_builder.create_embed(
            title=f"📖 {book_data['name']} - Chapter {chapter}",
            color=0x8B4513
        )
        
        # Generate chapter content based on book type
        content = self.generate_lore_content(book_data["name"], chapter)
        
        embed.add_field(
            name=f"📜 Chapter {chapter}",
            value=content,
            inline=False
        )
        
        # Navigation help
        nav_text = ""
        if chapter > 1:
            nav_text += f"Previous: `!lore read \"{book_data['name']}\" {chapter - 1}`\n"
        if chapter < book_data["chapters"]:
            nav_text += f"Next: `!lore read \"{book_data['name']}\" {chapter + 1}`"
        
        if nav_text:
            embed.add_field(
                name="📍 Navigation",
                value=nav_text,
                inline=False
            )
        
        return embed
    
    def generate_lore_content(self, book_name: str, chapter: int) -> str:
        """Generate lore content for a chapter"""
        # This is a simplified content generator
        # In a real implementation, you'd have actual lore content stored
        
        if "Ancient" in book_name:
            contents = [
                "In the beginning, there was only the Void...",
                "The first gods awakened from eternal slumber...",
                "The Great Convergence shattered reality itself...",
                "From the chaos, new worlds were born..."
            ]
        elif "Heroes" in book_name:
            contents = [
                "The legend speaks of a warrior who could not be defeated...",
                "In the darkest hour, heroes rise to meet destiny...",
                "Each character carries within them an ancient power...",
                "The bonds between heroes transcend time and space..."
            ]
        elif "Guild Wars" in book_name:
            contents = [
                "The first guild war began over a trivial dispute...",
                "Alliances formed and crumbled like sand...",
                "The great betrayal changed everything...",
                "From conflict came wisdom and unity..."
            ]
        else:
            contents = [
                "Knowledge is the greatest treasure of all...",
                "The masters guarded their secrets jealously...",
                "Innovation came from those who dared to experiment...",
                "The old ways are not always the best ways..."
            ]
        
        # Select content based on chapter
        content_index = (chapter - 1) % len(contents)
        base_content = contents[content_index]
        
        # Add chapter-specific flavor
        return f"{base_content}\n\n*[This is chapter {chapter} of {len(contents)} available chapters]*"
    
    def get_achievement_rank(self, points: int) -> str:
        """Get achievement rank based on points"""
        if points >= 1000:
            return "🌟 Legendary"
        elif points >= 500:
            return "👑 Master"
        elif points >= 250:
            return "⚔️ Expert"
        elif points >= 100:
            return "🛡️ Adept"
        elif points >= 50:
            return "🔰 Novice"
        else:
            return "📝 Beginner"


async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(AchievementsCommands(bot))