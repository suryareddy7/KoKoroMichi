# Character Upgrade Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List
import random

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from utils.helpers import format_number, find_character_by_name, validate_amount

class UpgradeCommands(commands.Cog):
    """Character upgrade and enhancement system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
    
    @commands.command(name="upgrade", aliases=["levelup", "enhance"])
    async def upgrade_character(self, ctx, *, character_name: str):
        """Upgrade a character's level using XP"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            waifus = user_data.get("claimed_waifus", [])
            
            if not waifus:
                embed = self.embed_builder.info_embed(
                    "No Characters",
                    "You don't have any characters to upgrade! Use `!summon` to get started."
                )
                await ctx.send(embed=embed)
                return
            
            # Find character
            character = find_character_by_name(waifus, character_name)
            if not character:
                embed = self.embed_builder.error_embed(
                    "Character Not Found",
                    f"'{character_name}' not found in your collection."
                )
                await ctx.send(embed=embed)
                return
            
            # Check if character can be upgraded
            current_level = character.get("level", 1)
            current_exp = character.get("exp", 0)
            max_exp = character.get("max_exp", 100)
            
            if current_level >= 100:
                embed = self.embed_builder.warning_embed(
                    "Max Level Reached",
                    f"{character['name']} is already at the maximum level (100)!"
                )
                await ctx.send(embed=embed)
                return
            
            if current_exp < max_exp:
                needed_exp = max_exp - current_exp
                embed = self.embed_builder.warning_embed(
                    "Insufficient Experience",
                    f"{character['name']} needs {format_number(needed_exp)} more XP to level up.\n"
                    f"Current XP: {format_number(current_exp)}/{format_number(max_exp)}"
                )
                await ctx.send(embed=embed)
                return
            
            # Perform upgrade
            old_stats = {
                "level": character.get("level", 1),
                "hp": character.get("hp", 100),
                "atk": character.get("atk", 50),
                "def": character.get("def", 30),
                "potential": character.get("potential", 1000)
            }
            
            # Level up character
            new_level = current_level + 1
            stat_gains = self.calculate_stat_gains(character, new_level)
            
            # Update character stats
            character["level"] = new_level
            character["exp"] = current_exp - max_exp  # Carry over excess XP
            character["max_exp"] = self.calculate_exp_requirement(new_level)
            character["hp"] += stat_gains["hp"]
            character["atk"] += stat_gains["atk"]
            character["def"] += stat_gains["def"]
            character["potential"] += stat_gains["potential"]
            
            # Save changes
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Create upgrade result embed
            embed = self.create_upgrade_embed(character["name"], old_stats, character, stat_gains)
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Upgrade Error",
                "Unable to upgrade character. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Upgrade command error: {e}")
    
    @commands.command(name="train")
    async def train_character(self, ctx, character_name: str, amount: str = "1"):
        """Train a character by spending gold to gain XP"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            waifus = user_data.get("claimed_waifus", [])
            
            if not waifus:
                embed = self.embed_builder.info_embed(
                    "No Characters",
                    "You don't have any characters to train!"
                )
                await ctx.send(embed=embed)
                return
            
            # Find character
            character = find_character_by_name(waifus, character_name)
            if not character:
                embed = self.embed_builder.error_embed(
                    "Character Not Found",
                    f"'{character_name}' not found in your collection."
                )
                await ctx.send(embed=embed)
                return
            
            # Validate training amount
            valid, training_amount, error_msg = validate_amount(amount, 50)  # Max 50 training sessions
            if not valid:
                embed = self.embed_builder.error_embed("Invalid Amount", error_msg)
                await ctx.send(embed=embed)
                return
            
            # Calculate cost
            base_cost = 100
            level_multiplier = 1 + (character.get("level", 1) - 1) * 0.1
            cost_per_session = int(base_cost * level_multiplier)
            total_cost = cost_per_session * training_amount
            
            # Check funds
            user_gold = user_data.get("gold", 0)
            if user_gold < total_cost:
                embed = self.embed_builder.error_embed(
                    "Insufficient Gold",
                    f"Training costs {format_number(total_cost)} gold.\n"
                    f"You have: {format_number(user_gold)} gold"
                )
                await ctx.send(embed=embed)
                return
            
            # Perform training
            base_xp_gain = 25
            total_xp_gained = base_xp_gain * training_amount
            
            # Apply training bonus for higher amounts
            if training_amount >= 10:
                total_xp_gained = int(total_xp_gained * 1.2)  # 20% bonus
            elif training_amount >= 5:
                total_xp_gained = int(total_xp_gained * 1.1)  # 10% bonus
            
            # Update character and user data
            character["exp"] = character.get("exp", 0) + total_xp_gained
            user_data["gold"] -= total_cost
            
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Create training result embed
            embed = self.create_training_embed(
                character["name"], training_amount, total_xp_gained, 
                total_cost, character.get("exp", 0), character.get("max_exp", 100)
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Training Error",
                "Unable to train character. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Training command error: {e}")
    
    @commands.command(name="potential", aliases=["awaken"])
    async def increase_potential(self, ctx, character_name: str, material: str = None):
        """Increase a character's potential using special materials"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            waifus = user_data.get("claimed_waifus", [])
            inventory = user_data.get("inventory", {})
            
            if not waifus:
                embed = self.embed_builder.info_embed(
                    "No Characters",
                    "You don't have any characters to awaken!"
                )
                await ctx.send(embed=embed)
                return
            
            # Find character
            character = find_character_by_name(waifus, character_name)
            if not character:
                embed = self.embed_builder.error_embed(
                    "Character Not Found",
                    f"'{character_name}' not found in your collection."
                )
                await ctx.send(embed=embed)
                return
            
            # Define awakening materials
            awakening_materials = {
                "Star Fragment": {"potential": 500, "rarity": "rare"},
                "Divine Essence": {"potential": 1000, "rarity": "legendary"},
                "Mystic Crystal": {"potential": 250, "rarity": "uncommon"},
                "Ancient Rune": {"potential": 750, "rarity": "epic"}
            }
            
            if not material:
                # Show available materials
                embed = self.create_awakening_materials_embed(inventory, awakening_materials)
                await ctx.send(embed=embed)
                return
            
            # Find material in inventory
            found_material = None
            for mat_name in inventory.keys():
                if material.lower() in mat_name.lower():
                    found_material = mat_name
                    break
            
            if not found_material or found_material not in awakening_materials:
                embed = self.embed_builder.error_embed(
                    "Invalid Material",
                    f"'{material}' is not a valid awakening material or you don't have it."
                )
                await ctx.send(embed=embed)
                return
            
            if inventory[found_material] <= 0:
                embed = self.embed_builder.error_embed(
                    "No Materials",
                    f"You don't have any {found_material} to use."
                )
                await ctx.send(embed=embed)
                return
            
            # Perform awakening
            material_data = awakening_materials[found_material]
            potential_gain = material_data["potential"]
            
            # Add randomness to potential gain (±20%)
            variance = random.uniform(0.8, 1.2)
            actual_gain = int(potential_gain * variance)
            
            old_potential = character.get("potential", 1000)
            character["potential"] = old_potential + actual_gain
            
            # Use material
            inventory[found_material] -= 1
            if inventory[found_material] <= 0:
                del inventory[found_material]
            
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Create awakening result embed
            embed = self.create_awakening_embed(
                character["name"], found_material, old_potential, 
                character["potential"], actual_gain
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Awakening Error",
                "Unable to awaken character. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Potential command error: {e}")
    
    def calculate_stat_gains(self, character: Dict, new_level: int) -> Dict[str, int]:
        """Calculate stat gains for leveling up"""
        rarity = character.get("rarity", "N").split()[0]
        
        # Base stat gains by rarity
        rarity_multipliers = {
            "Mythic": 2.5,
            "LR": 2.2,
            "UR": 2.0,
            "SSR": 1.8,
            "SR": 1.5,
            "R": 1.2,
            "N": 1.0
        }
        
        multiplier = rarity_multipliers.get(rarity, 1.0)
        
        # Base gains per level
        base_gains = {
            "hp": int(8 * multiplier),
            "atk": int(5 * multiplier),
            "def": int(3 * multiplier),
            "potential": int(50 * multiplier)
        }
        
        # Add slight randomness
        for stat in base_gains:
            variance = random.randint(-1, 2)
            base_gains[stat] += variance
        
        return base_gains
    
    def calculate_exp_requirement(self, level: int) -> int:
        """Calculate XP requirement for next level"""
        return 100 + (level - 1) * 50
    
    def create_upgrade_embed(self, name: str, old_stats: Dict, character: Dict, gains: Dict) -> discord.Embed:
        """Create upgrade result embed"""
        embed = self.embed_builder.success_embed(
            "Level Up Success!",
            f"**{name}** has reached level {character['level']}!"
        )
        
        # Show stat changes
        changes_text = ""
        for stat, gain in gains.items():
            if stat == "level":
                continue
            old_val = old_stats[stat]
            new_val = character[stat]
            changes_text += f"{stat.upper()}: {format_number(old_val)} → {format_number(new_val)} (+{gain})\n"
        
        embed.add_field(
            name="📈 Stat Improvements",
            value=changes_text,
            inline=False
        )
        
        # Show new XP requirement
        current_exp = character.get("exp", 0)
        max_exp = character.get("max_exp", 100)
        
        embed.add_field(
            name="⭐ Experience Progress",
            value=f"Current XP: {format_number(current_exp)}/{format_number(max_exp)}",
            inline=True
        )
        
        return embed
    
    def create_training_embed(self, name: str, sessions: int, xp_gained: int, 
                            cost: int, current_exp: int, max_exp: int) -> discord.Embed:
        """Create training result embed"""
        embed = self.embed_builder.success_embed(
            "Training Complete!",
            f"**{name}** completed {sessions} training session(s)!"
        )
        
        embed.add_field(
            name="📚 Training Results",
            value=f"Sessions: {sessions}\n"
                  f"XP Gained: {format_number(xp_gained)}\n"
                  f"Cost: {format_number(cost)} gold",
            inline=True
        )
        
        embed.add_field(
            name="⭐ Current Progress",
            value=f"XP: {format_number(current_exp)}/{format_number(max_exp)}",
            inline=True
        )
        
        # Check if ready to level up
        if current_exp >= max_exp:
            embed.add_field(
                name="🎉 Ready to Level Up!",
                value=f"Use `!upgrade {name}` to level up!",
                inline=False
            )
        
        return embed
    
    def create_awakening_materials_embed(self, inventory: Dict, materials: Dict) -> discord.Embed:
        """Create awakening materials information embed"""
        embed = self.embed_builder.create_embed(
            title="🌟 Awakening Materials",
            description="Use special materials to increase character potential",
            color=0x9370DB
        )
        
        available_text = ""
        all_materials_text = ""
        
        for material, data in materials.items():
            count = inventory.get(material, 0)
            potential_gain = data["potential"]
            rarity = data["rarity"]
            
            material_line = f"**{material}** (+{potential_gain} potential) - {rarity}\n"
            all_materials_text += material_line
            
            if count > 0:
                available_text += f"{material_line}   You have: {count}\n"
        
        if available_text:
            embed.add_field(
                name="✅ Available Materials",
                value=available_text,
                inline=False
            )
        
        embed.add_field(
            name="📋 All Awakening Materials",
            value=all_materials_text,
            inline=False
        )
        
        embed.add_field(
            name="💡 Usage",
            value="Use `!potential <character_name> <material>` to awaken",
            inline=False
        )
        
        return embed
    
    def create_awakening_embed(self, name: str, material: str, old_potential: int, 
                             new_potential: int, gain: int) -> discord.Embed:
        """Create awakening result embed"""
        embed = self.embed_builder.success_embed(
            "Awakening Successful!",
            f"**{name}** has been awakened with {material}!"
        )
        
        embed.add_field(
            name="🔮 Potential Increase",
            value=f"Before: {format_number(old_potential)}\n"
                  f"After: {format_number(new_potential)}\n"
                  f"Gain: +{format_number(gain)}",
            inline=True
        )
        
        # Check for rarity tier breakthrough
        from utils.helpers import get_rarity_tier
        old_tier = get_rarity_tier(old_potential)
        new_tier = get_rarity_tier(new_potential)
        
        if old_tier != new_tier:
            embed.add_field(
                name="⭐ Rarity Breakthrough!",
                value=f"Potential tier increased from {old_tier} to {new_tier}!",
                inline=False
            )
        
        return embed


async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(UpgradeCommands(bot))