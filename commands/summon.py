# Summoning System Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List
import random
import asyncio
from datetime import datetime

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from core.config import RARITY_TIERS, SUMMON_COST, BULK_SUMMON_DISCOUNT
from utils.helpers import format_number, generate_random_stats, get_random_element
from utils.channel_restriction import check_channel_restriction

class SummonCommands(commands.Cog):
    """Character summoning and gacha system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        self.active_summons = set()  # Prevent concurrent summons
    
    @commands.command(name="summon", aliases=["pull", "gacha"])
    async def summon_character(self, ctx, amount: int = 1):
        """Summon new characters using the gacha system"""
        # Enforce channel restrictions for summon commands
        restriction_result = await check_channel_restriction(
            ctx, ["summon-shrine", "gacha-temple", "character-summoning"], ctx.bot
        )
        if not restriction_result:
            await ctx.send("🌟 Summon commands can only be used in summoning channels!", delete_after=10)
            return
        try:
            # Validate amount
            if amount < 1 or amount > 50:
                embed = self.embed_builder.error_embed(
                    "Invalid Amount",
                    "You can summon between 1 and 50 characters at once."
                )
                await ctx.send(embed=embed)
                return
            
            # Check if user is already summoning
            if str(ctx.author.id) in self.active_summons:
                embed = self.embed_builder.warning_embed(
                    "Summoning In Progress",
                    "Please wait for your current summon to complete!"
                )
                await ctx.send(embed=embed)
                return
            
            # Add user to active summons
            self.active_summons.add(str(ctx.author.id))
            
            try:
                # Get user data and check funds
                user_data = data_manager.get_user_data(str(ctx.author.id))
                
                # Calculate cost with bulk discount
                total_cost = self.calculate_summon_cost(amount)
                
                if user_data.get("gems", 0) < total_cost:
                    embed = self.embed_builder.error_embed(
                        "Insufficient Gems",
                        f"You need {format_number(total_cost)} gems to summon {amount} character(s).\n"
                        f"You have: {format_number(user_data.get('gems', 0))} gems"
                    )
                    await ctx.send(embed=embed)
                    return
                
                # Show summoning animation
                animation_msg = await ctx.send(embed=self.create_summoning_animation_embed(amount))
                
                # Perform summons
                summoned_characters = []
                for i in range(amount):
                    character = await self.perform_single_summon(user_data)
                    if character:
                        summoned_characters.append(character)
                    
                    # Update animation every few summons
                    if amount > 5 and i % 3 == 0:
                        await animation_msg.edit(embed=self.create_summoning_animation_embed(amount, i + 1))
                        await asyncio.sleep(0.5)
                
                # Deduct cost and update user data
                user_data["gems"] -= total_cost
                user_data["claimed_waifus"].extend(summoned_characters)
                
                # Update summoning statistics
                user_data.setdefault("summon_stats", {})
                user_data["summon_stats"]["total_summons"] = user_data["summon_stats"].get("total_summons", 0) + amount
                user_data["summon_stats"]["gems_spent"] = user_data["summon_stats"].get("gems_spent", 0) + total_cost
                
                data_manager.save_user_data(str(ctx.author.id), user_data)
                
                # Show results
                if amount == 1:
                    # Single summon - detailed view
                    embed = self.create_single_summon_embed(summoned_characters[0], total_cost)
                else:
                    # Multi summon - summary view
                    embed = self.create_multi_summon_embed(summoned_characters, amount, total_cost)
                
                await animation_msg.edit(embed=embed)
                
                # Check for rare summons notification and logging
                rare_summons = [c for c in summoned_characters if self.get_rarity_tier(c.get("rarity", "N")) in ["SSR", "UR", "LR", "Mythic"]]
                if rare_summons:
                    await self.send_rare_summon_notification(ctx, rare_summons)
                    # Log to lucky-summons channel
                    from utils.channel_manager import channel_manager
                    for rare_char in rare_summons:
                        await channel_manager.log_special_event(ctx, "rare_summon", {"character": rare_char})
                
            finally:
                # Remove user from active summons
                self.active_summons.discard(str(ctx.author.id))
                
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Summon Error",
                "Something went wrong during summoning. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Summon command error: {e}")
            self.active_summons.discard(str(ctx.author.id))
    
    @commands.command(name="rates", aliases=["summon_rates"])
    async def summon_rates(self, ctx):
        """Display current summoning rates and costs"""
        embed = self.embed_builder.create_embed(
            title="🎲 Summoning Rates & Costs",
            description="Current gacha rates and pricing information",
            color=0x9370DB
        )
        
        # Show rarity rates
        rates_text = ""
        for rarity, data in RARITY_TIERS.items():
            emoji = data["emoji"]
            chance = data["chance"]
            rates_text += f"{emoji} **{rarity}**: {chance}%\n"
        
        embed.add_field(
            name="🎯 Drop Rates",
            value=rates_text,
            inline=True
        )
        
        # Show costs
        single_cost = SUMMON_COST
        bulk_cost = int(SUMMON_COST * 10 * (1 - BULK_SUMMON_DISCOUNT))
        
        embed.add_field(
            name="💎 Costs",
            value=f"Single Summon: {format_number(single_cost)} gems\n"
                  f"10x Summon: {format_number(bulk_cost)} gems\n"
                  f"Bulk Discount: {int(BULK_SUMMON_DISCOUNT * 100)}%",
            inline=True
        )
        
        # Pity system info
        embed.add_field(
            name="🎁 Pity System",
            value="• Guaranteed SR+ every 20 summons\n"
                  "• Guaranteed SSR+ every 50 summons\n"
                  "• Rates increase with consecutive summons",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    def calculate_summon_cost(self, amount: int) -> int:
        """Calculate total summon cost with bulk discounts"""
        if amount >= 10:
            # Apply bulk discount for 10+ summons
            return int(SUMMON_COST * amount * (1 - BULK_SUMMON_DISCOUNT))
        else:
            return SUMMON_COST * amount
    
    async def perform_single_summon(self, user_data: dict) -> Optional[Dict]:
        """Perform a single character summon"""
        try:
            # Get all available characters
            all_characters = data_manager.get_all_characters()
            if not all_characters:
                return None
            
            # Determine rarity using pity system
            summon_count = user_data.get("summon_stats", {}).get("total_summons", 0)
            rarity_tier = self.determine_rarity_with_pity(summon_count)
            
            # Select random character
            base_character = random.choice(all_characters)
            
            # Generate stats based on rarity
            stats = generate_random_stats(rarity_tier)
            
            # Create summoned character
            summoned_character = {
                "name": base_character.get("name", "Unknown"),
                "rarity": f"{rarity_tier} {RARITY_TIERS[rarity_tier]['emoji']}",
                "level": 1,
                "exp": 0,
                "max_exp": 100,
                "hp": stats["hp"],
                "atk": stats["atk"],
                "def": stats["def"],
                "potential": sum(stats.values()) + random.randint(0, 500),
                "element": base_character.get("element", get_random_element()),
                "skills": base_character.get("skills", []),
                "fate": base_character.get("fate", []),
                "affection": 0,
                "summoned_at": datetime.now().isoformat(),
                "relic": None
            }
            
            return summoned_character
            
        except Exception as e:
            print(f"Single summon error: {e}")
            return None
    
    def determine_rarity_with_pity(self, summon_count: int) -> str:
        """Determine rarity tier with pity system"""
        # Pity boosts
        pity_boost = 0
        if summon_count >= 50:
            pity_boost += 5.0  # 5% boost after 50 summons
        elif summon_count >= 20:
            pity_boost += 2.0  # 2% boost after 20 summons
        
        # Generate random number
        rand = random.uniform(0, 100)
        cumulative = 0
        
        # Check each rarity tier
        for rarity, data in RARITY_TIERS.items():
            chance = data["chance"]
            
            # Apply pity boost to rare tiers
            if rarity in ["SSR", "UR", "LR", "Mythic"]:
                chance += pity_boost
            
            cumulative += chance
            if rand <= cumulative:
                return rarity
        
        return "N"  # Fallback
    
    def get_rarity_tier(self, rarity_string: str) -> str:
        """Extract rarity tier from rarity string"""
        if not rarity_string:
            return "N"
        return rarity_string.split()[0]
    
    def create_summoning_animation_embed(self, total: int, current: int = 0) -> discord.Embed:
        """Create summoning animation embed"""
        if current == 0:
            title = "✨ Summoning Magic Circles ✨"
            description = f"Preparing to summon {total} character(s)..."
        else:
            title = "🌟 Summoning in Progress 🌟"
            description = f"Summoned {current}/{total} characters..."
        
        embed = self.embed_builder.create_embed(
            title=title,
            description=description,
            color=0xFF1493
        )
        
        # Add mystical flavor text
        flavor_texts = [
            "The ancient magic circles glow with power...",
            "Ethereal energies swirl through dimensions...",
            "Legendary beings hear your call...",
            "The fabric of reality shimmers...",
            "Destiny weaves new threads..."
        ]
        
        embed.add_field(
            name="🔮 Mystical Forces",
            value=random.choice(flavor_texts),
            inline=False
        )
        
        return embed
    
    def create_single_summon_embed(self, character: Dict, cost: int) -> discord.Embed:
        """Create single summon result embed"""
        name = character.get("name", "Unknown")
        rarity = character.get("rarity", "N")
        rarity_tier = self.get_rarity_tier(rarity)
        
        # Choose color based on rarity
        rarity_colors = {
            "Mythic": 0xFF0080,
            "LR": 0xFF4500,
            "UR": 0xFFD700,
            "SSR": 0xFF69B4,
            "SR": 0x9370DB,
            "R": 0x00CED1,
            "N": 0x808080
        }
        color = rarity_colors.get(rarity_tier, 0xFF69B4)
        
        embed = self.embed_builder.create_embed(
            title="🎉 Summoning Success!",
            description=f"You summoned **{name}**!",
            color=color
        )
        
        # Character details
        embed.add_field(
            name="✨ Character Details",
            value=f"**{rarity}**\n"
                  f"❤️ HP: {character.get('hp', 0)}\n"
                  f"⚔️ ATK: {character.get('atk', 0)}\n"
                  f"🛡️ DEF: {character.get('def', 0)}\n"
                  f"🌟 Element: {character.get('element', 'Neutral')}",
            inline=True
        )
        
        # Potential and cost
        potential = character.get("potential", 0)
        embed.add_field(
            name="📊 Summary",
            value=f"🔮 Potential: {format_number(potential)}\n"
                  f"💎 Cost: {format_number(cost)} gems",
            inline=True
        )
        
        # Special message for rare summons
        if rarity_tier in ["UR", "LR", "Mythic"]:
            embed.add_field(
                name="🎊 Incredible Luck!",
                value="You've summoned an exceptionally rare character!",
                inline=False
            )
        
        return embed
    
    def create_multi_summon_embed(self, characters: List[Dict], total: int, cost: int) -> discord.Embed:
        """Create multi summon result embed"""
        embed = self.embed_builder.create_embed(
            title=f"🎉 {total}x Summon Results!",
            description=f"Successfully summoned {len(characters)} characters!",
            color=0xFF1493
        )
        
        # Count by rarity
        rarity_counts = {}
        total_potential = 0
        
        for char in characters:
            rarity_tier = self.get_rarity_tier(char.get("rarity", "N"))
            rarity_counts[rarity_tier] = rarity_counts.get(rarity_tier, 0) + 1
            potential = char.get("potential", 0)
            total_potential += int(potential) if isinstance(potential, (int, str)) else 0
        
        # Show rarity breakdown
        rarity_text = ""
        for rarity in ["Mythic", "LR", "UR", "SSR", "SR", "R", "N"]:
            count = rarity_counts.get(rarity, 0)
            if count > 0:
                emoji = RARITY_TIERS[rarity]["emoji"]
                rarity_text += f"{emoji} {rarity}: {count}\n"
        
        embed.add_field(
            name="🎯 Rarity Breakdown",
            value=rarity_text or "No characters summoned",
            inline=True
        )
        
        # Show best summons
        best_characters = sorted(characters, key=lambda c: int(c.get("potential", 0)) if isinstance(c.get("potential", 0), (int, str)) else 0, reverse=True)[:3]
        best_text = ""
        for i, char in enumerate(best_characters, 1):
            name = char.get("name", "Unknown")
            rarity_tier = self.get_rarity_tier(char.get("rarity", "N"))
            potential = char.get("potential", 0)
            best_text += f"{i}. **{name}** ({rarity_tier}) - {format_number(potential)}\n"
        
        embed.add_field(
            name="⭐ Top Summons",
            value=best_text or "None",
            inline=True
        )
        
        # Summary stats
        avg_potential = int(total_potential / len(characters)) if characters else 0
        embed.add_field(
            name="📊 Summary",
            value=f"Total Potential: {format_number(total_potential)}\n"
                  f"Average Potential: {format_number(avg_potential)}\n"
                  f"Cost: {format_number(cost)} gems",
            inline=False
        )
        
        # Check for rare summons
        rare_count = sum(1 for c in characters if self.get_rarity_tier(c.get("rarity", "N")) in ["UR", "LR", "Mythic"])
        if rare_count > 0:
            embed.add_field(
                name="🌟 Rare Summons",
                value=f"You got {rare_count} rare character(s)! Amazing luck!",
                inline=False
            )
        
        return embed
    
    async def send_rare_summon_notification(self, ctx, rare_characters: List[Dict]):
        """Send special notification for rare summons"""
        try:
            embed = self.embed_builder.create_embed(
                title="🌟 RARE SUMMON ALERT! 🌟",
                description="You've summoned extremely rare characters!",
                color=0xFF0080
            )
            
            rare_text = ""
            for char in rare_characters:
                name = char.get("name", "Unknown")
                rarity = char.get("rarity", "N")
                rare_text += f"• **{name}** ({rarity})\n"
            
            embed.add_field(
                name="✨ Legendary Summons",
                value=rare_text,
                inline=False
            )
            
            embed.add_field(
                name="🎊 Congratulations!",
                value="These characters are incredibly rare and powerful!\n"
                      "Take good care of them on your adventures!",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"Rare summon notification error: {e}")


async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(SummonCommands(bot))