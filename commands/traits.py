# Traits System Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List, Any
import random
from datetime import datetime

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from core.config import FEATURES
from utils.helpers import format_number

class TraitsCommands(commands.Cog):
    """Character trait system with personality and combat traits"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
    
    @commands.command(name="traits", aliases=["trait_list"])
    async def view_traits(self, ctx, *, character_name: str = None):
        """View character traits and their effects"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            
            if character_name:
                # Show specific character's traits
                character = self.find_character_by_name(user_data.get("claimed_waifus", []), character_name)
                if not character:
                    embed = self.embed_builder.error_embed(
                        "Character Not Found",
                        f"'{character_name}' not found in your collection."
                    )
                    await ctx.send(embed=embed)
                    return
                
                embed = self.create_character_traits_embed(character)
                await ctx.send(embed=embed)
            else:
                # Show available traits system
                embed = self.create_traits_overview_embed()
                await ctx.send(embed=embed)
            
            await self.log_traits_activity(ctx, "view", character_name)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Traits Error",
                "Unable to load trait information."
            )
            await ctx.send(embed=embed)
            print(f"Traits command error: {e}")
    
    @commands.command(name="develop_trait", aliases=["unlock_trait"])
    async def develop_trait(self, ctx, character_name: str, trait_name: str):
        """Develop a new trait for a character"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            character = self.find_character_by_name(user_data.get("claimed_waifus", []), character_name)
            
            if not character:
                embed = self.embed_builder.error_embed(
                    "Character Not Found",
                    f"'{character_name}' not found in your collection."
                )
                await ctx.send(embed=embed)
                return
            
            # Get available traits
            game_data = data_manager.get_game_data()
            available_traits = game_data.get("traits", {}).get("trait_categories", {})
            
            # Find the trait
            trait_data = self.find_trait_by_name(available_traits, trait_name)
            if not trait_data:
                embed = self.embed_builder.error_embed(
                    "Trait Not Found",
                    f"Trait '{trait_name}' not found. Use `!traits` to see available traits."
                )
                await ctx.send(embed=embed)
                return
            
            # Check if character already has this trait
            char_traits = character.get("traits", [])
            if any(t["name"] == trait_data["name"] for t in char_traits):
                embed = self.embed_builder.warning_embed(
                    "Trait Already Unlocked",
                    f"{character['name']} already has the {trait_data['name']} trait!"
                )
                await ctx.send(embed=embed)
                return
            
            # Check unlock conditions
            if not self.check_trait_conditions(character, trait_data):
                embed = self.create_trait_requirements_embed(trait_data)
                await ctx.send(embed=embed)
                return
            
            # Calculate development cost
            development_cost = self.calculate_trait_cost(character, trait_data)
            user_gold = user_data.get("gold", 0)
            
            if user_gold < development_cost:
                embed = self.embed_builder.error_embed(
                    "Insufficient Gold",
                    f"Developing this trait costs {format_number(development_cost)} gold.\n"
                    f"You have: {format_number(user_gold)} gold"
                )
                await ctx.send(embed=embed)
                return
            
            # Develop the trait
            user_data["gold"] -= development_cost
            char_traits.append({
                "name": trait_data["name"],
                "description": trait_data["description"],
                "effects": trait_data["effects"],
                "developed_at": datetime.now().isoformat(),
                "level": 1
            })
            character["traits"] = char_traits
            
            # Apply trait effects
            self.apply_trait_effects(character, trait_data["effects"])
            
            # Save data
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Create success embed
            embed = self.embed_builder.success_embed(
                "Trait Developed!",
                f"**{character['name']}** has developed the **{trait_data['name']}** trait!"
            )
            
            embed.add_field(
                name="✨ New Trait",
                value=f"**{trait_data['name']}**\n*{trait_data['description']}*",
                inline=False
            )
            
            effects_text = self.format_trait_effects(trait_data["effects"])
            embed.add_field(
                name="🎯 Effects",
                value=effects_text,
                inline=True
            )
            
            embed.add_field(
                name="💰 Cost",
                value=f"{format_number(development_cost)} gold",
                inline=True
            )
            
            await ctx.send(embed=embed)
            await self.log_traits_activity(ctx, "develop", f"{character_name} - {trait_data['name']}")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Trait Development Error",
                "Unable to develop trait. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Develop trait error: {e}")
    
    @commands.command(name="trait_info", aliases=["trait_details"])
    async def trait_info(self, ctx, *, trait_name: str):
        """Get detailed information about a specific trait"""
        try:
            game_data = data_manager.get_game_data()
            available_traits = game_data.get("traits", {}).get("trait_categories", {})
            
            trait_data = self.find_trait_by_name(available_traits, trait_name)
            if not trait_data:
                embed = self.embed_builder.error_embed(
                    "Trait Not Found",
                    f"Trait '{trait_name}' not found in the database."
                )
                await ctx.send(embed=embed)
                return
            
            embed = self.embed_builder.create_embed(
                title=f"📖 Trait Information: {trait_data['name']}",
                description=trait_data['description'],
                color=0x8A2BE2
            )
            
            # Effects
            effects_text = self.format_trait_effects(trait_data["effects"])
            embed.add_field(
                name="🎯 Effects",
                value=effects_text,
                inline=False
            )
            
            # Unlock conditions
            conditions = trait_data.get("unlock_conditions", {})
            if conditions:
                conditions_text = ""
                for condition, value in conditions.items():
                    condition_name = condition.replace("_", " ").title()
                    if isinstance(value, int):
                        conditions_text += f"• {condition_name}: {value:,}\n"
                    else:
                        conditions_text += f"• {condition_name}: {value}\n"
                
                embed.add_field(
                    name="🔓 Unlock Requirements",
                    value=conditions_text,
                    inline=False
                )
            
            await ctx.send(embed=embed)
            await self.log_traits_activity(ctx, "info", trait_name)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Trait Info Error",
                "Unable to load trait information."
            )
            await ctx.send(embed=embed)
            print(f"Trait info error: {e}")
    
    def find_character_by_name(self, characters: List[Dict], name: str) -> Optional[Dict]:
        """Find character by name (case insensitive)"""
        name_lower = name.lower()
        for char in characters:
            if char.get("name", "").lower() == name_lower:
                return char
        return None
    
    def find_trait_by_name(self, trait_categories: Dict, name: str) -> Optional[Dict]:
        """Find trait by name across all categories"""
        name_lower = name.lower()
        for category, traits in trait_categories.items():
            for trait in traits:
                if trait["name"].lower() == name_lower:
                    return trait
        return None
    
    def create_character_traits_embed(self, character: Dict) -> discord.Embed:
        """Create embed showing character's traits"""
        char_name = character.get("name", "Unknown")
        char_traits = character.get("traits", [])
        
        embed = self.embed_builder.create_embed(
            title=f"🌟 {char_name}'s Traits",
            description=f"Personality and combat traits of **{char_name}**",
            color=0x8A2BE2
        )
        
        if char_traits:
            for trait in char_traits:
                effects_text = self.format_trait_effects(trait["effects"])
                trait_level = trait.get("level", 1)
                
                embed.add_field(
                    name=f"✨ {trait['name']} (Lv.{trait_level})",
                    value=f"*{trait['description']}*\n**Effects:** {effects_text}",
                    inline=False
                )
        else:
            embed.add_field(
                name="🌱 No Traits Developed",
                value=f"{char_name} hasn't developed any traits yet.\n"
                      f"Use `!develop_trait {char_name} <trait_name>` to unlock traits!",
                inline=False
            )
        
        # Show development potential
        char_level = character.get("level", 1)
        battles_won = character.get("battles_won", 0)
        
        embed.add_field(
            name="📊 Development Potential",
            value=f"**Level:** {char_level}\n"
                  f"**Battles Won:** {battles_won}\n"
                  f"**Available Traits:** Use `!traits` to browse",
            inline=True
        )
        
        return embed
    
    def create_traits_overview_embed(self) -> discord.Embed:
        """Create overview of available traits"""
        embed = self.embed_builder.create_embed(
            title="🌟 Character Traits System",
            description="Develop unique traits to enhance your characters' abilities",
            color=0x8A2BE2
        )
        
        # Trait categories
        trait_info = """
        **Personality Traits** 🧠
        Shape your character's behavior and interactions
        
        **Combat Traits** ⚔️
        Enhance battle performance and strategic options
        
        **Special Traits** ✨
        Unique abilities unlocked through extraordinary achievements
        
        **Elemental Traits** 🌟
        Enhance elemental affinities and magical abilities
        """
        
        embed.add_field(
            name="📚 Trait Categories",
            value=trait_info,
            inline=False
        )
        
        # Development info
        embed.add_field(
            name="🔧 How to Develop",
            value="1. Meet trait unlock conditions\n"
                  "2. Use `!develop_trait <character> <trait>`\n"
                  "3. Pay the development cost\n"
                  "4. Enjoy enhanced abilities!",
            inline=True
        )
        
        embed.add_field(
            name="💡 Tips",
            value="• Higher level characters unlock better traits\n"
                  "• Some traits require specific achievements\n"
                  "• Traits can be upgraded over time\n"
                  "• Use `!trait_info <trait>` for details",
            inline=True
        )
        
        return embed
    
    def check_trait_conditions(self, character: Dict, trait_data: Dict) -> bool:
        """Check if character meets trait unlock conditions"""
        conditions = trait_data.get("unlock_conditions", {})
        
        for condition, required_value in conditions.items():
            if condition == "min_level":
                if character.get("level", 1) < required_value:
                    return False
            elif condition == "battles_won":
                if character.get("battles_won", 0) < required_value:
                    return False
            elif condition == "min_affinity":
                if character.get("affection", 0) < required_value:
                    return False
            # Add more condition checks as needed
        
        return True
    
    def calculate_trait_cost(self, character: Dict, trait_data: Dict) -> int:
        """Calculate cost to develop a trait"""
        base_cost = 2000
        char_level = character.get("level", 1)
        current_traits = len(character.get("traits", []))
        
        # Cost increases with character level and existing traits
        level_multiplier = 1 + (char_level * 0.1)
        trait_multiplier = 1 + (current_traits * 0.2)
        
        return int(base_cost * level_multiplier * trait_multiplier)
    
    def format_trait_effects(self, effects: Dict) -> str:
        """Format trait effects for display"""
        effects_text = ""
        for effect, value in effects.items():
            effect_name = effect.replace("_", " ").title()
            if isinstance(value, float):
                percentage = int(value * 100)
                effects_text += f"{effect_name}: +{percentage}%  "
            else:
                effects_text += f"{effect_name}: +{value}  "
        
        return effects_text.strip()
    
    def apply_trait_effects(self, character: Dict, effects: Dict):
        """Apply trait effects to character stats"""
        for effect, value in effects.items():
            if effect.endswith("_bonus"):
                # These are percentage bonuses applied during calculations
                continue
            elif effect == "status_resistance":
                character["status_resistance"] = character.get("status_resistance", 0) + value
            elif effect == "focus_bonus":
                character["focus"] = character.get("focus", 1.0) + value
            # Add more direct stat applications as needed
    
    def create_trait_requirements_embed(self, trait_data: Dict) -> discord.Embed:
        """Create embed showing trait unlock requirements"""
        embed = self.embed_builder.warning_embed(
            "Trait Requirements Not Met",
            f"**{trait_data['name']}** requires specific conditions to unlock."
        )
        
        embed.add_field(
            name="📖 Trait Description",
            value=trait_data["description"],
            inline=False
        )
        
        conditions = trait_data.get("unlock_conditions", {})
        if conditions:
            conditions_text = ""
            for condition, value in conditions.items():
                condition_name = condition.replace("_", " ").title()
                if isinstance(value, int):
                    conditions_text += f"• {condition_name}: {value:,}\n"
                else:
                    conditions_text += f"• {condition_name}: {value}\n"
            
            embed.add_field(
                name="🔓 Requirements",
                value=conditions_text,
                inline=False
            )
        
        return embed
    
    async def log_traits_activity(self, ctx, activity_type: str, details: str = ""):
        """Log traits activity to history channel"""
        try:
            history_channel = discord.utils.get(ctx.guild.text_channels, name='history')
            if not history_channel:
                return
            
            emojis = ["🌟", "✨", "🔮", "💫", "🌈", "⚡"]
            emoji = random.choice(emojis)
            
            if activity_type == "view":
                if details:
                    message = f"{emoji} **{ctx.author.display_name}** examined the unique traits of their beloved {details}!"
                else:
                    message = f"{emoji} **{ctx.author.display_name}** explored the mystical traits system!"
            elif activity_type == "develop":
                message = f"{emoji} **{ctx.author.display_name}** successfully developed a new trait: {details}!"
            elif activity_type == "info":
                message = f"{emoji} **{ctx.author.display_name}** studied the secrets of the {details} trait!"
            else:
                message = f"{emoji} **{ctx.author.display_name}** delved into the world of character traits!"
            
            embed = self.embed_builder.create_embed(
                description=message,
                color=0x8A2BE2
            )
            
            await history_channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error logging traits activity: {e}")

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(TraitsCommands(bot))