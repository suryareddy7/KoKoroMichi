# Lore and Achievement System for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List, Any
import random
from datetime import datetime

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from core.config import FEATURES

class LoreCommands(commands.Cog):
    """Lore books and achievement system for deep RPG experience"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        
    @commands.command(name="lorebooks", aliases=["books", "library"])
    async def view_lore(self, ctx, book_id: str = None):
        """View available lore books and stories"""
        try:
            lore_data = data_manager._load_json(data_manager.data_dir / "lore_achievements.json")
            lore_books = lore_data.get("lore_books", [])
            
            if not book_id:
                # Show all available lore books
                embed = self.embed_builder.create_embed(
                    title="📚 Ancient Lore Library",
                    description="Discover the rich history and legends of the KoKoroMichi realm!",
                    color=0x8B4513
                )
                
                user_data = data_manager.get_user_data(str(ctx.author.id))
                user_level = user_data.get("level", 1)
                battles_won = user_data.get("battle_stats", {}).get("battles_won", 0)
                waifus_count = len(user_data.get("claimed_waifus", []))
                
                books_text = ""
                for book in lore_books:
                    # Check if user meets requirements
                    req = book.get("unlock_requirement")
                    unlocked = self.check_lore_requirement(req, user_level, battles_won, waifus_count)
                    
                    status = "🔓" if unlocked else "🔒"
                    books_text += f"{status} **{book['title']}** ({book['chapters']} chapters)\n{book['description']}\n\n"
                
                embed.add_field(
                    name="📖 Available Books",
                    value=books_text if books_text else "No lore books available.",
                    inline=False
                )
                
                embed.add_field(
                    name="💡 How to Read",
                    value="Use `!lore <book_id>` to read a specific book!\nExample: `!lore origins_of_kokoromichi`",
                    inline=False
                )
                
                await ctx.send(embed=embed)
                return
            
            # Find specific book
            target_book = None
            for book in lore_books:
                if book["id"] == book_id:
                    target_book = book
                    break
            
            if not target_book:
                embed = self.embed_builder.error_embed(
                    "Book Not Found",
                    f"Lore book '{book_id}' not found. Use `!lore` to see available books."
                )
                await ctx.send(embed=embed)
                return
            
            # Check if user can access this book
            user_data = data_manager.get_user_data(str(ctx.author.id))
            user_level = user_data.get("level", 1)
            battles_won = user_data.get("battle_stats", {}).get("battles_won", 0)
            waifus_count = len(user_data.get("claimed_waifus", []))
            
            req = target_book.get("unlock_requirement")
            if not self.check_lore_requirement(req, user_level, battles_won, waifus_count):
                embed = self.embed_builder.warning_embed(
                    "Book Locked",
                    f"You don't meet the requirements to read '{target_book['title']}' yet."
                )
                await ctx.send(embed=embed)
                return
            
            # Display the book
            embed = self.embed_builder.create_embed(
                title=f"📜 {target_book['title']}",
                description=target_book["content"],
                color=0x8B4513
            )
            
            embed.add_field(
                name="📊 Book Info",
                value=f"Chapters: {target_book['chapters']}\nRequirement: {req.replace('_', ' ').title()}",
                inline=True
            )
            
            # Show rewards
            rewards = target_book.get("rewards", {})
            reward_text = ""
            for reward_type, value in rewards.items():
                if reward_type == "xp":
                    reward_text += f"⭐ {value:,} XP\n"
                elif reward_type == "gold":
                    reward_text += f"💰 {value:,} Gold\n"
                elif reward_type == "title":
                    reward_text += f"🎭 Title: {value}\n"
                elif reward_type == "rare_relic":
                    reward_text += f"💎 Rare Relic: {value}\n"
                elif reward_type == "permanent_battle_bonus":
                    reward_text += f"⚔️ +{int(value*100)}% Battle Bonus\n"
            
            if reward_text:
                embed.add_field(
                    name="🎁 Reading Rewards",
                    value=reward_text,
                    inline=True
                )
            
            embed.add_field(
                name="📚 Complete Reading",
                value="React with 📖 to fully read this book and claim rewards!",
                inline=False
            )
            
            message = await ctx.send(embed=embed)
            await message.add_reaction("📖")
            
            # Wait for reaction
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) == "📖" and reaction.message.id == message.id
            
            try:
                await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                
                # Apply rewards
                for reward_type, value in rewards.items():
                    if reward_type == "xp":
                        user_data["xp"] = user_data.get("xp", 0) + value
                    elif reward_type == "gold":
                        user_data["gold"] = user_data.get("gold", 0) + value
                
                # Mark book as read
                read_books = user_data.get("lore_books_read", [])
                if book_id not in read_books:
                    read_books.append(book_id)
                    user_data["lore_books_read"] = read_books
                
                data_manager.save_user_data(str(ctx.author.id), user_data)
                
                complete_embed = self.embed_builder.success_embed(
                    "Book Completed!",
                    f"You've finished reading '{target_book['title']}' and received the rewards!"
                )
                await ctx.send(embed=complete_embed)
                
            except asyncio.TimeoutError:
                pass
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Lore Error",
                "Unable to access lore library. Please try again later."
            )
            await ctx.send(embed=embed)
    
    def check_lore_requirement(self, requirement: str, level: int, battles_won: int, waifus_count: int) -> bool:
        """Check if user meets lore book requirements"""
        if requirement == "basic_lore":
            return level >= 1
        elif requirement == "character_lore":
            return waifus_count >= 5  # Simplified affinity check
        elif requirement == "advanced_lore":
            return battles_won >= 100
        elif requirement == "legendary_lore":
            return waifus_count >= 20  # Simplified rare waifus check
        return True
    
    @commands.command(name="lore_achievements", aliases=["lore_achieve"])
    async def view_achievements(self, ctx, achievement_id: str = None):
        """View available achievements and progress"""
        try:
            lore_data = data_manager._load_json(data_manager.data_dir / "lore_achievements.json")
            achievements = lore_data.get("achievements", [])
            
            user_data = data_manager.get_user_data(str(ctx.author.id))
            user_achievements = user_data.get("achievements", [])
            
            if not achievement_id:
                # Show all achievements with progress
                embed = self.embed_builder.create_embed(
                    title="🏆 Achievement Gallery",
                    description="Track your progress and unlock special rewards!",
                    color=0xFFD700
                )
                
                # Group by rarity
                rarity_groups = {"common": [], "uncommon": [], "rare": [], "epic": [], "legendary": []}
                for achievement in achievements:
                    rarity = achievement.get("rarity", "common")
                    rarity_groups[rarity].append(achievement)
                
                # Display each rarity group
                rarity_emojis = {
                    "common": "🌿",
                    "uncommon": "🔧", 
                    "rare": "🔥",
                    "epic": "🌟",
                    "legendary": "⚡"
                }
                
                for rarity, group in rarity_groups.items():
                    if group:
                        rarity_text = ""
                        for achievement in group:
                            completed = achievement["id"] in user_achievements
                            status = "✅" if completed else "⏳"
                            rarity_text += f"{status} **{achievement['name']}** - {achievement['description']}\n"
                        
                        embed.add_field(
                            name=f"{rarity_emojis[rarity]} {rarity.title()} Achievements",
                            value=rarity_text[:1024],  # Discord field limit
                            inline=False
                        )
                
                completed_count = len(user_achievements)
                total_count = len(achievements)
                embed.add_field(
                    name="📊 Progress",
                    value=f"Completed: {completed_count}/{total_count} ({int(completed_count/total_count*100)}%)",
                    inline=True
                )
                
                await ctx.send(embed=embed)
                return
            
            # Find specific achievement
            target_achievement = None
            for achievement in achievements:
                if achievement["id"] == achievement_id:
                    target_achievement = achievement
                    break
            
            if not target_achievement:
                embed = self.embed_builder.error_embed(
                    "Achievement Not Found",
                    f"Achievement '{achievement_id}' not found."
                )
                await ctx.send(embed=embed)
                return
            
            # Display achievement details
            completed = target_achievement["id"] in user_achievements
            status_color = 0x00FF00 if completed else 0xFFA500
            
            embed = self.embed_builder.create_embed(
                title=f"🏆 {target_achievement['name']}",
                description=target_achievement["description"],
                color=status_color
            )
            
            embed.add_field(
                name="📊 Status",
                value="✅ Completed" if completed else "⏳ In Progress",
                inline=True
            )
            
            embed.add_field(
                name="🌟 Rarity",
                value=target_achievement.get("rarity", "common").title(),
                inline=True
            )
            
            # Show requirements and progress
            requirement = target_achievement.get("requirement", {})
            req_text = ""
            for req_type, req_value in requirement.items():
                current_value = self.get_user_stat(user_data, req_type)
                progress = min(current_value, req_value)
                req_text += f"**{req_type.replace('_', ' ').title()}**: {progress}/{req_value}\n"
            
            if req_text:
                embed.add_field(
                    name="📋 Requirements",
                    value=req_text,
                    inline=False
                )
            
            # Show rewards
            rewards = target_achievement.get("rewards", {})
            if rewards:
                reward_text = ""
                for reward_type, value in rewards.items():
                    if reward_type == "gold":
                        reward_text += f"💰 {value:,} Gold\n"
                    elif reward_type == "title":
                        reward_text += f"🎭 Title: {value}\n"
                    elif reward_type.endswith("_boost"):
                        reward_text += f"⚡ {reward_type.replace('_', ' ').title()}: +{int(value*100)}%\n"
                
                embed.add_field(
                    name="🎁 Rewards",
                    value=reward_text,
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Achievement Error",
                "Unable to access achievements. Please try again later."
            )
            await ctx.send(embed=embed)
    
    def get_user_stat(self, user_data: Dict, stat_type: str) -> int:
        """Get user's current stat value for achievement checking"""
        if stat_type == "waifus_summoned":
            return len(user_data.get("claimed_waifus", []))
        elif stat_type == "unique_waifus":
            return len(set(w.get("name", "") for w in user_data.get("claimed_waifus", [])))
        elif stat_type == "battles_won":
            return user_data.get("battle_stats", {}).get("battles_won", 0)
        elif stat_type == "max_affinity_waifus":
            # Simplified - count high-level waifus
            return len([w for w in user_data.get("claimed_waifus", []) if w.get("level", 1) >= 50])
        elif stat_type == "lore_books_completed":
            return len(user_data.get("lore_books_read", []))
        elif stat_type == "level":
            return user_data.get("level", 1)
        elif stat_type == "legendary_waifus":
            return len([w for w in user_data.get("claimed_waifus", []) if "LR" in w.get("rarity", "") or "Mythic" in w.get("rarity", "")])
        return 0

async def setup(bot):
    await bot.add_cog(LoreCommands(bot))