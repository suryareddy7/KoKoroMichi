# Mishaps System Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List, Any
import random
from datetime import datetime, timedelta

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from core.config import FEATURES
from utils.helpers import format_number

class MishapsCommands(commands.Cog):
    """Random mishap events that add challenge and humor to the game"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        
        # Mishap event templates
        self.mishap_events = {
            "minor": [
                {
                    "name": "Clumsy Accident",
                    "description": "You tripped while carrying gold coins!",
                    "effect": {"type": "gold_loss", "percentage": 0.05},
                    "emoji": "🤕",
                    "humor": "At least you looked graceful falling!"
                },
                {
                    "name": "Sneaky Pickpocket",
                    "description": "A tiny creature snatched some coins!",
                    "effect": {"type": "gold_loss", "flat": 200},
                    "emoji": "🐭",
                    "humor": "It was actually kind of cute..."
                },
                {
                    "name": "Character Tantrum",
                    "description": "One of your characters had a mood swing!",
                    "effect": {"type": "affection_loss", "amount": 5},
                    "emoji": "😤",
                    "humor": "Even waifus have bad days!"
                },
                {
                    "name": "Training Mishap",
                    "description": "Training equipment broke during practice!",
                    "effect": {"type": "xp_loss", "amount": 100},
                    "emoji": "💥",
                    "humor": "No pain, no gain... right?"
                }
            ],
            "moderate": [
                {
                    "name": "Marketplace Scam",
                    "description": "You fell for a 'too good to be true' deal!",
                    "effect": {"type": "gold_loss", "percentage": 0.10},
                    "emoji": "🎭",
                    "humor": "Experience is the best teacher!"
                },
                {
                    "name": "Equipment Malfunction",
                    "description": "Your gear needs expensive repairs!",
                    "effect": {"type": "gold_loss", "flat": 1000},
                    "emoji": "⚙️",
                    "humor": "At least it didn't explode!"
                },
                {
                    "name": "Character Jealousy",
                    "description": "Your characters are jealous of each other!",
                    "effect": {"type": "all_affection_loss", "amount": 10},
                    "emoji": "💔",
                    "humor": "Love triangles are complicated..."
                },
                {
                    "name": "Magic Backfire",
                    "description": "A spell went wrong and drained your energy!",
                    "effect": {"type": "xp_loss", "amount": 500},
                    "emoji": "⚡",
                    "humor": "That's why we read instruction manuals!"
                }
            ],
            "major": [
                {
                    "name": "Dragon Attack",
                    "description": "A wild dragon demanded tribute!",
                    "effect": {"type": "gold_loss", "percentage": 0.20},
                    "emoji": "🐉",
                    "humor": "At least it didn't eat anyone!"
                },
                {
                    "name": "Time Paradox",
                    "description": "Magic gone wrong affected your progress!",
                    "effect": {"type": "xp_loss", "percentage": 0.15},
                    "emoji": "🌀",
                    "humor": "Temporal mechanics are tricky!"
                },
                {
                    "name": "Cursed Artifact",
                    "description": "You touched something you shouldn't have!",
                    "effect": {"type": "stat_drain", "amount": 20},
                    "emoji": "💀",
                    "humor": "Curiosity didn't kill the cat this time!"
                },
                {
                    "name": "Portal Storm",
                    "description": "Chaotic portals scattered your resources!",
                    "effect": {"type": "mixed_loss", "gold_percentage": 0.15, "xp_amount": 300},
                    "emoji": "🌪️",
                    "humor": "At least the light show was spectacular!"
                }
            ],
            "legendary": [
                {
                    "name": "Cosmic Mischief",
                    "description": "Trickster gods decided to 'help' you!",
                    "effect": {"type": "major_setback", "gold_percentage": 0.30, "xp_percentage": 0.20},
                    "emoji": "🎭",
                    "humor": "Divine comedy at your expense!"
                },
                {
                    "name": "Reality Glitch",
                    "description": "The fabric of reality hiccupped!",
                    "effect": {"type": "random_chaos"},
                    "emoji": "🌈",
                    "humor": "At least it's scientifically interesting!"
                }
            ]
        }
    
    @commands.command(name="mishaps", aliases=["bad_luck", "incidents"])
    async def view_mishaps(self, ctx):
        """View recent mishap events and statistics"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            mishap_data = user_data.get("mishap_history", {})
            
            embed = self.embed_builder.create_embed(
                title="💥 Mishap History",
                description="Your recent adventures in Murphy's Law!",
                color=0xFF6B6B
            )
            
            # Show recent mishaps
            recent_mishaps = mishap_data.get("recent_events", [])
            if recent_mishaps:
                mishaps_text = ""
                for mishap in recent_mishaps[-5:]:  # Show last 5
                    date = mishap.get("date", "")[:10]
                    mishaps_text += f"{mishap['emoji']} **{mishap['name']}** ({date})\n"
                    mishaps_text += f"   *{mishap['description']}*\n"
                    mishaps_text += f"   Impact: {mishap.get('impact_description', 'Unknown')}\n\n"
                
                embed.add_field(
                    name="📜 Recent Mishaps",
                    value=mishaps_text,
                    inline=False
                )
            else:
                embed.add_field(
                    name="🍀 Lucky Streak",
                    value="No recent mishaps! You've been fortunate lately!",
                    inline=False
                )
            
            # Show mishap statistics
            total_mishaps = mishap_data.get("total_count", 0)
            total_losses = mishap_data.get("total_losses", {"gold": 0, "xp": 0})
            luck_rating = self.calculate_luck_rating(total_mishaps, user_data)
            
            embed.add_field(
                name="📊 Mishap Statistics", 
                value=f"**Total Mishaps:** {total_mishaps}\n"
                      f"**Gold Lost:** {format_number(total_losses.get('gold', 0))}\n"
                      f"**XP Lost:** {format_number(total_losses.get('xp', 0))}\n"
                      f"**Luck Rating:** {luck_rating}",
                inline=True
            )
            
            # Protection items
            protection_items = user_data.get("inventory", {})
            luck_charms = protection_items.get("luck_charm", 0)
            insurance = protection_items.get("mishap_insurance", 0)
            
            embed.add_field(
                name="🛡️ Protection Items",
                value=f"**Luck Charms:** {luck_charms}\n"
                      f"**Mishap Insurance:** {insurance}\n"
                      f"*Buy protection items from the store!*",
                inline=True
            )
            
            embed.add_field(
                name="💡 Mishap Facts",
                value="• Mishaps occur randomly (2-5% chance)\n"
                      "• Higher activity increases mishap chances\n"
                      "• Protection items reduce mishap severity\n"
                      "• Legendary mishaps are extremely rare but dramatic!",
                inline=False
            )
            
            await ctx.send(embed=embed)
            await self.log_mishap_activity(ctx, "history_check")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Mishaps Error",
                "Unable to load mishap history."
            )
            await ctx.send(embed=embed)
            print(f"Mishaps command error: {e}")
    
    async def trigger_random_mishap(self, ctx, trigger_command: str = "unknown"):
        """Trigger a random mishap event (called by other commands)"""
        if not FEATURES.get("mishaps_enabled", True):
            return
        
        try:
            # Base 3% chance, increased by user activity
            user_data = data_manager.get_user_data(str(ctx.author.id))
            base_chance = 0.03
            
            # Increase chance based on recent activity
            recent_commands = user_data.get("recent_commands", [])
            activity_bonus = min(0.02, len(recent_commands) * 0.005)
            total_chance = base_chance + activity_bonus
            
            if random.random() > total_chance:
                return  # No mishap this time
            
            # Check protection items
            protection_items = user_data.get("inventory", {})
            luck_charms = protection_items.get("luck_charm", 0)
            mishap_insurance = protection_items.get("mishap_insurance", 0)
            
            # Reduce chance with protection
            if luck_charms > 0 and random.random() < 0.5:
                # Luck charm activated
                protection_items["luck_charm"] -= 1
                await self.send_protection_message(ctx, "luck_charm")
                return
            
            # Determine mishap severity
            severity_chances = {
                "minor": 70.0,
                "moderate": 25.0,
                "major": 4.5,
                "legendary": 0.5
            }
            
            rand = random.uniform(0, 100)
            cumulative = 0
            selected_severity = "minor"
            
            for severity, chance in severity_chances.items():
                cumulative += chance
                if rand <= cumulative:
                    selected_severity = severity
                    break
            
            # Select random mishap of chosen severity
            available_mishaps = self.mishap_events[selected_severity]
            mishap = random.choice(available_mishaps)
            
            # Apply mishap effects (with insurance protection)
            original_impact = self.apply_mishap_effects(user_data, mishap, mishap_insurance > 0)
            
            if mishap_insurance > 0:
                protection_items["mishap_insurance"] -= 1
                insurance_used = True
            else:
                insurance_used = False
            
            # Record mishap
            self.record_mishap_event(user_data, mishap, original_impact, trigger_command)
            
            # Save data
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Announce mishap
            await self.announce_mishap_event(ctx, mishap, original_impact, insurance_used)
            
        except Exception as e:
            print(f"Mishap trigger error: {e}")
    
    def apply_mishap_effects(self, user_data: Dict, mishap: Dict, has_insurance: bool) -> Dict:
        """Apply mishap effects to user data"""
        effect = mishap["effect"]
        impact = {"type": effect["type"], "original": {}, "actual": {}}
        
        if effect["type"] == "gold_loss":
            user_gold = user_data.get("gold", 0)
            if "percentage" in effect:
                loss = int(user_gold * effect["percentage"])
            else:
                loss = effect.get("flat", 0)
            
            # Insurance reduces loss by 50%
            if has_insurance:
                loss = int(loss * 0.5)
            
            impact["original"]["gold"] = loss
            impact["actual"]["gold"] = loss
            user_data["gold"] = max(0, user_gold - loss)
        
        elif effect["type"] == "xp_loss":
            user_xp = user_data.get("xp", 0)
            if "percentage" in effect:
                loss = int(user_xp * effect["percentage"])
            else:
                loss = effect.get("amount", 0)
            
            if has_insurance:
                loss = int(loss * 0.5)
            
            impact["original"]["xp"] = loss
            impact["actual"]["xp"] = loss
            user_data["xp"] = max(0, user_xp - loss)
        
        elif effect["type"] == "affection_loss":
            characters = user_data.get("claimed_waifus", [])
            if characters:
                target_char = random.choice(characters)
                loss = effect.get("amount", 5)
                
                if has_insurance:
                    loss = int(loss * 0.5)
                
                target_char["affection"] = max(0, target_char.get("affection", 0) - loss)
                impact["original"]["affection"] = loss
                impact["actual"]["affection"] = loss
                impact["character"] = target_char["name"]
        
        # Add more effect types as needed
        
        return impact
    
    def record_mishap_event(self, user_data: Dict, mishap: Dict, impact: Dict, trigger_command: str):
        """Record mishap event in user history"""
        mishap_data = user_data.setdefault("mishap_history", {})
        recent_events = mishap_data.setdefault("recent_events", [])
        
        # Create mishap record
        mishap_record = {
            "name": mishap["name"],
            "description": mishap["description"],
            "emoji": mishap["emoji"],
            "humor": mishap["humor"],
            "date": datetime.now().isoformat(),
            "trigger_command": trigger_command,
            "impact": impact,
            "impact_description": self.format_impact_description(impact)
        }
        
        recent_events.append(mishap_record)
        # Keep only last 20 mishaps
        mishap_data["recent_events"] = recent_events[-20:]
        
        # Update statistics
        mishap_data["total_count"] = mishap_data.get("total_count", 0) + 1
        total_losses = mishap_data.setdefault("total_losses", {"gold": 0, "xp": 0})
        
        if "gold" in impact["actual"]:
            total_losses["gold"] += impact["actual"]["gold"]
        if "xp" in impact["actual"]:
            total_losses["xp"] += impact["actual"]["xp"]
        
        user_data["mishap_history"] = mishap_data
    
    def format_impact_description(self, impact: Dict) -> str:
        """Format mishap impact for display"""
        impact_parts = []
        
        if "gold" in impact["actual"]:
            impact_parts.append(f"Lost {format_number(impact['actual']['gold'])} gold")
        if "xp" in impact["actual"]:
            impact_parts.append(f"Lost {format_number(impact['actual']['xp'])} XP")
        if "affection" in impact["actual"]:
            char_name = impact.get("character", "character")
            impact_parts.append(f"{char_name} lost {impact['actual']['affection']} affection")
        
        return " • ".join(impact_parts) if impact_parts else "No significant impact"
    
    def calculate_luck_rating(self, total_mishaps: int, user_data: Dict) -> str:
        """Calculate user's luck rating"""
        # Consider total commands used vs mishaps encountered
        total_commands = user_data.get("total_commands_used", 1)
        mishap_rate = total_mishaps / total_commands
        
        if mishap_rate <= 0.01:
            return "🍀 Extraordinarily Lucky"
        elif mishap_rate <= 0.03:
            return "✨ Very Lucky"
        elif mishap_rate <= 0.05:
            return "🌟 Lucky"
        elif mishap_rate <= 0.07:
            return "⚖️ Average"
        elif mishap_rate <= 0.10:
            return "😅 Unlucky"
        else:
            return "💥 Mishap Magnet"
    
    async def announce_mishap_event(self, ctx, mishap: Dict, impact: Dict, insurance_used: bool):
        """Announce a mishap event"""
        try:
            embed = self.embed_builder.create_embed(
                title=f"{mishap['emoji']} Mishap Event!",
                description=f"**{mishap['name']}**",
                color=0xFF6B6B
            )
            
            embed.add_field(
                name="📖 What Happened",
                value=mishap["description"],
                inline=False
            )
            
            # Show impact
            impact_desc = self.format_impact_description(impact)
            if insurance_used:
                impact_desc += "\n🛡️ *Mishap insurance reduced the damage by 50%!*"
            
            embed.add_field(
                name="💥 Impact",
                value=impact_desc,
                inline=True
            )
            
            embed.add_field(
                name="😄 Silver Lining",
                value=mishap["humor"],
                inline=True
            )
            
            # Show current resources after mishap
            user_data = data_manager.get_user_data(str(ctx.author.id))
            embed.add_field(
                name="💰 Current Resources",
                value=f"Gold: {format_number(user_data.get('gold', 0))}\n"
                      f"XP: {format_number(user_data.get('xp', 0))}",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"Mishap announcement error: {e}")
    
    async def send_protection_message(self, ctx, protection_type: str):
        """Send message when protection item activates"""
        try:
            if protection_type == "luck_charm":
                embed = self.embed_builder.create_embed(
                    title="🍀 Luck Charm Activated!",
                    description="Your luck charm glowed brightly and protected you from a mishap!",
                    color=0x32CD32
                )
                
                embed.add_field(
                    name="✨ Protection Effect",
                    value="A potential mishap was completely prevented!\n"
                          "Your luck charm dissolved after protecting you.",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"Protection message error: {e}")
    
    @commands.command(name="luck_shop", aliases=["protection_shop"])
    async def luck_shop(self, ctx):
        """Browse protection items to prevent mishaps"""
        try:
            embed = self.embed_builder.create_embed(
                title="🍀 Luck & Protection Shop",
                description="Protect yourself from mishaps with these magical items!",
                color=0x32CD32
            )
            
            protection_items = {
                "luck_charm": {
                    "name": "Luck Charm",
                    "description": "50% chance to completely prevent a mishap",
                    "cost": 1000,
                    "emoji": "🍀"
                },
                "mishap_insurance": {
                    "name": "Mishap Insurance",
                    "description": "Reduces mishap damage by 50%",
                    "cost": 2000,
                    "emoji": "🛡️"
                },
                "fortune_cookie": {
                    "name": "Fortune Cookie",
                    "description": "Grants temporary luck boost (24h)",
                    "cost": 500,
                    "emoji": "🥠"
                }
            }
            
            for item_id, item_data in protection_items.items():
                embed.add_field(
                    name=f"{item_data['emoji']} {item_data['name']}",
                    value=f"*{item_data['description']}*\n"
                          f"**Cost:** {format_number(item_data['cost'])} gold\n"
                          f"Use: `!buy {item_id}` (from main store)",
                    inline=True
                )
            
            embed.add_field(
                name="💡 Protection Tips",
                value="• Luck charms are single-use but completely prevent mishaps\n"
                      "• Insurance reduces damage but doesn't prevent mishaps\n"
                      "• Fortune cookies provide temporary protection\n"
                      "• Stack multiple protection types for maximum safety",
                inline=False
            )
            
            await ctx.send(embed=embed)
            await self.log_mishap_activity(ctx, "protection_shop")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Luck Shop Error",
                "Unable to load protection shop."
            )
            await ctx.send(embed=embed)
            print(f"Luck shop error: {e}")
    
    async def log_mishap_activity(self, ctx, activity_type: str, details: str = ""):
        """Log mishap activity to history channel"""
        try:
            history_channel = discord.utils.get(ctx.guild.text_channels, name='history')
            if not history_channel:
                return
            
            emojis = ["💥", "😅", "🎭", "🍀", "⚡", "🌪️"]
            emoji = random.choice(emojis)
            
            if activity_type == "history_check":
                message = f"{emoji} **{ctx.author.display_name}** bravely reviewed their collection of comedic mishaps and adventures!"
            elif activity_type == "protection_shop":
                message = f"{emoji} **{ctx.author.display_name}** wisely browsed protection items to guard against future mishaps!"
            elif activity_type == "mishap_occurred":
                message = f"{emoji} **{ctx.author.display_name}** experienced an unexpected mishap: {details}!"
            else:
                message = f"{emoji} **{ctx.author.display_name}** encountered the unpredictable side of adventure!"
            
            embed = self.embed_builder.create_embed(
                description=message,
                color=0xFF6B6B
            )
            
            await history_channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error logging mishap activity: {e}")

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(MishapsCommands(bot))