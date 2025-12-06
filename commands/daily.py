# Daily Rewards Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Dict, List
import random
from datetime import datetime, timedelta

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from utils.helpers import format_number, is_on_cooldown

class DailyCommands(commands.Cog):
    """Daily rewards and login bonus system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        
        # Daily reward tiers based on consecutive login days
        self.daily_rewards = {
            1: {"gold": 1000, "gems": 10, "items": ["Health Potion Small"]},
            2: {"gold": 1200, "gems": 12, "items": ["Experience Scroll"]},
            3: {"gold": 1500, "gems": 15, "items": ["Gold Pouch"]},
            4: {"gold": 2000, "gems": 20, "items": ["Health Potion", "Iron Ore"]},
            5: {"gold": 2500, "gems": 25, "items": ["Experience Tome"]},
            6: {"gold": 3000, "gems": 30, "items": ["Precious Gem", "Silver Ore"]},
            7: {"gold": 5000, "gems": 50, "items": ["Treasure Chest", "Star Fragment"]},  # Weekly bonus
            8: {"gold": 1500, "gems": 18, "items": ["Lucky Charm"]},
            9: {"gold": 1800, "gems": 22, "items": ["Health Potion Large"]},
            10: {"gold": 2200, "gems": 28, "items": ["Ancient Codex"]},
            # Continues cycling with bonuses every 7 days
        }
        
        # Bonus events that can randomly occur
        self.bonus_events = {
            "golden_hour": {
                "name": "Golden Hour",
                "description": "Double gold rewards!",
                "multipliers": {"gold": 2.0},
                "chance": 0.1  # 10% chance
            },
            "gem_shower": {
                "name": "Gem Shower",
                "description": "Extra gems rain from the sky!",
                "multipliers": {"gems": 1.5},
                "bonus_gems": 25,
                "chance": 0.08  # 8% chance
            },
            "treasure_day": {
                "name": "Treasure Day",
                "description": "Rare items are more common!",
                "bonus_items": ["Mystic Crystal", "Dragon Scale"],
                "chance": 0.05  # 5% chance
            }
        }
    
    @commands.command(name="daily", aliases=["claim", "login"])
    async def daily_reward(self, ctx):
        """Claim your daily login reward"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            
            # Check if already claimed today
            last_daily = user_data.get("last_daily_claim")
            if last_daily:
                is_cooldown, hours_remaining = is_on_cooldown(last_daily, 20)  # 20 hour cooldown
                if is_cooldown:
                    next_claim = datetime.fromisoformat(last_daily) + timedelta(hours=20)
                    embed = self.embed_builder.warning_embed(
                        "Daily Already Claimed",
                        f"You can claim your next daily reward <t:{int(next_claim.timestamp())}:R>"
                    )
                    await ctx.send(embed=embed)
                    return
            
            # Calculate consecutive days and current reward tier
            consecutive_days = self.calculate_consecutive_days(user_data)
            reward_tier = ((consecutive_days - 1) % 10) + 1  # Cycle through 1-10
            
            # Get base rewards
            base_rewards = self.daily_rewards[reward_tier].copy()
            
            # Check for bonus events
            active_event = self.check_bonus_events()
            
            # Apply bonuses
            final_rewards = self.apply_reward_bonuses(base_rewards, active_event, consecutive_days)
            
            # Apply rewards to user
            user_data["gold"] = user_data.get("gold", 0) + final_rewards["gold"]
            user_data["gems"] = user_data.get("gems", 0) + final_rewards["gems"]
            
            # Add items to inventory
            inventory = user_data.setdefault("inventory", {})
            for item in final_rewards["items"]:
                inventory[item] = inventory.get(item, 0) + 1
            
            # Update daily claim data
            user_data["last_daily_claim"] = datetime.now().isoformat()
            user_data["consecutive_daily_claims"] = consecutive_days
            user_data.setdefault("total_daily_claims", 0)
            user_data["total_daily_claims"] += 1
            
            # Save user data
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Create reward embed
            embed = self.create_daily_reward_embed(
                consecutive_days, reward_tier, final_rewards, active_event
            )
            await ctx.send(embed=embed)
            
            # Special milestone messages
            if consecutive_days in [7, 30, 100, 365]:
                milestone_embed = self.create_milestone_embed(consecutive_days)
                await ctx.send(embed=milestone_embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Daily Reward Error",
                "Unable to process daily reward. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Daily reward error: {e}")
    
    @commands.command(name="streak", aliases=["dailystreak"])
    async def view_streak(self, ctx):
        """View your current daily login streak and upcoming rewards"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            
            consecutive_days = user_data.get("consecutive_daily_claims", 0)
            total_claims = user_data.get("total_daily_claims", 0)
            last_claim = user_data.get("last_daily_claim")
            
            # Check if streak is broken
            if last_claim:
                last_time = datetime.fromisoformat(last_claim)
                hours_since = (datetime.now() - last_time).total_seconds() / 3600
                if hours_since > 48:  # Grace period of 48 hours
                    consecutive_days = 0
            
            embed = self.embed_builder.create_embed(
                title="🔥 Daily Login Streak",
                description=f"Your dedication to the realm is noted!",
                color=0xFF4500
            )
            
            # Current streak info
            embed.add_field(
                name="📊 Streak Stats",
                value=f"Current Streak: **{consecutive_days} days**\n"
                      f"Total Claims: **{total_claims}**\n"
                      f"Next Tier: Day {((consecutive_days % 10) + 1)}",
                inline=True
            )
            
            # Next reward preview
            next_tier = ((consecutive_days % 10) + 1)
            if next_tier > 10:
                next_tier = 1
            
            next_rewards = self.daily_rewards[next_tier]
            next_items = ", ".join(next_rewards["items"])
            
            embed.add_field(
                name="🎁 Next Reward",
                value=f"Gold: {format_number(next_rewards['gold'])}\n"
                      f"Gems: {format_number(next_rewards['gems'])}\n"
                      f"Items: {next_items}",
                inline=True
            )
            
            # Show upcoming weekly bonus
            days_to_weekly = 7 - (consecutive_days % 7)
            if days_to_weekly == 7:
                days_to_weekly = 0
            
            if days_to_weekly > 0:
                embed.add_field(
                    name="⭐ Weekly Bonus",
                    value=f"In {days_to_weekly} days you'll receive the special weekly bonus!",
                    inline=False
                )
            else:
                embed.add_field(
                    name="⭐ Weekly Bonus",
                    value="Your next claim includes the weekly bonus!",
                    inline=False
                )
            
            # Streak milestones
            next_milestone = None
            for milestone in [7, 30, 100, 365]:
                if consecutive_days < milestone:
                    next_milestone = milestone
                    break
            
            if next_milestone:
                days_to_milestone = next_milestone - consecutive_days
                embed.add_field(
                    name="🏆 Next Milestone",
                    value=f"{next_milestone} days ({days_to_milestone} days to go)",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Streak Error",
                "Unable to load streak information."
            )
            await ctx.send(embed=error_embed)
            print(f"Streak command error: {e}")
    
    @commands.command(name="rewards", aliases=["dailyrewards"])
    async def view_daily_rewards(self, ctx):
        """View the daily reward schedule"""
        embed = self.embed_builder.create_embed(
            title="📅 Daily Reward Schedule",
            description="Login daily to claim escalating rewards!",
            color=0x9370DB
        )
        
        # Show reward tiers 1-7 (first week)
        for day in range(1, 8):
            rewards = self.daily_rewards[day]
            items_text = ", ".join(rewards["items"])
            
            special = ""
            if day == 7:
                special = " 🌟 **WEEKLY BONUS**"
            
            embed.add_field(
                name=f"Day {day}{special}",
                value=f"💰 {format_number(rewards['gold'])} gold\n"
                      f"💎 {format_number(rewards['gems'])} gems\n"
                      f"🎁 {items_text}",
                inline=True
            )
        
        embed.add_field(
            name="🔄 Reward Cycle",
            value="Rewards cycle every 10 days with weekly bonuses every 7th day!\n"
                  "Keep your streak alive for consistent rewards!",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Bonus Events",
            value="• **Golden Hour**: Double gold rewards (10% chance)\n"
                  "• **Gem Shower**: Extra gems (8% chance)\n"
                  "• **Treasure Day**: Rare items (5% chance)",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    def calculate_consecutive_days(self, user_data: Dict) -> int:
        """Calculate consecutive daily claims"""
        last_claim = user_data.get("last_daily_claim")
        consecutive = user_data.get("consecutive_daily_claims", 0)
        
        if not last_claim:
            return 1  # First claim
        
        try:
            last_time = datetime.fromisoformat(last_claim)
            hours_since = (datetime.now() - last_time).total_seconds() / 3600
            
            if hours_since > 48:  # Streak broken (48 hour grace period)
                return 1
            else:
                return consecutive + 1
        except:
            return 1
    
    def check_bonus_events(self) -> Dict:
        """Check if any bonus events are active"""
        for event_id, event_data in self.bonus_events.items():
            if random.random() < event_data["chance"]:
                return event_data
        return None
    
    def apply_reward_bonuses(self, base_rewards: Dict, bonus_event: Dict, consecutive_days: int) -> Dict:
        """Apply bonuses to base rewards"""
        final_rewards = base_rewards.copy()
        
        # Weekly bonus (every 7th day)
        if consecutive_days % 7 == 0:
            final_rewards["gold"] = int(final_rewards["gold"] * 1.5)
            final_rewards["gems"] = int(final_rewards["gems"] * 1.3)
            final_rewards["items"].append("Weekly Bonus Chest")
        
        # Long streak bonuses
        if consecutive_days >= 30:
            final_rewards["gold"] = int(final_rewards["gold"] * 1.2)
        if consecutive_days >= 100:
            final_rewards["gems"] = int(final_rewards["gems"] * 1.2)
        
        # Apply bonus event effects
        if bonus_event:
            if "multipliers" in bonus_event:
                for resource, multiplier in bonus_event["multipliers"].items():
                    final_rewards[resource] = int(final_rewards[resource] * multiplier)
            
            if "bonus_gems" in bonus_event:
                final_rewards["gems"] += bonus_event["bonus_gems"]
            
            if "bonus_items" in bonus_event:
                final_rewards["items"].extend(bonus_event["bonus_items"])
        
        return final_rewards
    
    def create_daily_reward_embed(self, consecutive_days: int, reward_tier: int, 
                                rewards: Dict, bonus_event: Dict) -> discord.Embed:
        """Create daily reward claim embed"""
        embed = self.embed_builder.success_embed(
            "Daily Reward Claimed!",
            f"Day {consecutive_days} - Tier {reward_tier} rewards collected!"
        )
        
        # Show rewards received
        items_text = ", ".join(rewards["items"])
        embed.add_field(
            name="🎁 Rewards Received",
            value=f"💰 {format_number(rewards['gold'])} gold\n"
                  f"💎 {format_number(rewards['gems'])} gems\n"
                  f"🎁 {items_text}",
            inline=True
        )
        
        # Streak information
        streak_text = f"Current Streak: **{consecutive_days} days**"
        if consecutive_days % 7 == 0:
            streak_text += "\n🌟 **Weekly bonus applied!**"
        
        embed.add_field(
            name="🔥 Login Streak",
            value=streak_text,
            inline=True
        )
        
        # Bonus event notification
        if bonus_event:
            embed.add_field(
                name=f"🎊 {bonus_event['name']} Active!",
                value=bonus_event["description"],
                inline=False
            )
        
        # Next reward preview
        next_tier = ((consecutive_days % 10) + 1)
        if next_tier > 10:
            next_tier = 1
        
        next_rewards = self.daily_rewards[next_tier]
        embed.add_field(
            name="👀 Tomorrow's Reward",
            value=f"💰 {format_number(next_rewards['gold'])} gold, "
                  f"💎 {format_number(next_rewards['gems'])} gems + items",
            inline=False
        )
        
        return embed
    
    def create_milestone_embed(self, days: int) -> discord.Embed:
        """Create milestone achievement embed"""
        milestones = {
            7: {"title": "Weekly Warrior", "description": "One week of dedication!", "bonus": "Extra daily rewards"},
            30: {"title": "Monthly Master", "description": "A month of commitment!", "bonus": "20% gold bonus"},
            100: {"title": "Centurion", "description": "100 days of loyalty!", "bonus": "20% gem bonus"},
            365: {"title": "Annual Legend", "description": "A full year of adventure!", "bonus": "Legendary status"}
        }
        
        milestone = milestones.get(days, {})
        
        embed = self.embed_builder.create_embed(
            title=f"🏆 Milestone Achieved: {milestone.get('title', 'Achievement')}",
            description=milestone.get('description', f"{days} days of daily logins!"),
            color=0xFFD700
        )
        
        embed.add_field(
            name="🎁 Milestone Bonus",
            value=milestone.get('bonus', 'Special recognition'),
            inline=False
        )
        
        embed.add_field(
            name="🌟 Congratulations!",
            value="Your dedication to the realm has not gone unnoticed. Keep up the amazing work!",
            inline=False
        )
        
        return embed


async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(DailyCommands(bot))