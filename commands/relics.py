# Relics System Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List, Any
import random
from datetime import datetime

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from core.config import FEATURES
from utils.helpers import format_number

class RelicsCommands(commands.Cog):
    """Ancient relics system with powerful equipment and buffs"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        
        # Relic templates
        self.relic_types = {
            "weapon": {
                "Celestial Blade": {
                    "description": "A sword blessed by the heavens",
                    "stats": {"atk": 50, "crit": 10},
                    "rarity": "SR",
                    "emoji": "⚔️",
                    "special_effect": "Divine Strike"
                },
                "Shadow Dagger": {
                    "description": "Blade forged in darkness",
                    "stats": {"atk": 35, "agility": 15},
                    "rarity": "R", 
                    "emoji": "🗡️",
                    "special_effect": "Shadow Step"
                },
                "Dragon Fang Spear": {
                    "description": "Weapon crafted from ancient dragon remains",
                    "stats": {"atk": 60, "penetration": 20},
                    "rarity": "SSR",
                    "emoji": "🔱",
                    "special_effect": "Dragon's Fury"
                }
            },
            "armor": {
                "Guardian's Plate": {
                    "description": "Heavy armor of legendary protectors",
                    "stats": {"def": 40, "hp": 100},
                    "rarity": "SR",
                    "emoji": "🛡️",
                    "special_effect": "Guardian's Will"
                },
                "Mystic Robes": {
                    "description": "Robes woven with ancient magic",
                    "stats": {"def": 25, "magic_resist": 30},
                    "rarity": "R",
                    "emoji": "👘",
                    "special_effect": "Spell Ward"
                },
                "Phoenix Feather Cloak": {
                    "description": "Cloak that grants rebirth powers",
                    "stats": {"def": 50, "hp": 150, "fire_resist": 50},
                    "rarity": "UR",
                    "emoji": "🧥",
                    "special_effect": "Phoenix Rebirth"
                }
            },
            "accessory": {
                "Ring of Power": {
                    "description": "Ancient ring that amplifies all abilities",
                    "stats": {"atk": 20, "def": 20, "hp": 50},
                    "rarity": "SSR",
                    "emoji": "💍",
                    "special_effect": "Power Amplification"
                },
                "Pendant of Wisdom": {
                    "description": "Necklace that enhances learning",
                    "stats": {"xp_bonus": 0.2, "skill_cooldown": -0.1},
                    "rarity": "SR",
                    "emoji": "📿",
                    "special_effect": "Rapid Learning"
                },
                "Lucky Charm": {
                    "description": "Trinket that brings good fortune",
                    "stats": {"crit": 15, "luck": 25},
                    "rarity": "R",
                    "emoji": "🍀",
                    "special_effect": "Fortune's Favor"
                }
            }
        }
    
    @commands.command(name="relics", aliases=["equipment", "gear"])
    async def view_relics(self, ctx, *, character_name: str = None):
        """View character equipment and relics"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            
            if character_name:
                # Show specific character's relics
                character = self.find_character_by_name(user_data.get("claimed_waifus", []), character_name)
                if not character:
                    embed = self.embed_builder.error_embed(
                        "Character Not Found",
                        f"'{character_name}' not found in your collection."
                    )
                    await ctx.send(embed=embed)
                    return
                
                embed = self.create_character_relics_embed(character)
                await ctx.send(embed=embed)
            else:
                # Show relic collection
                embed = self.create_relic_collection_embed(user_data)
                await ctx.send(embed=embed)
            
            await self.log_relic_activity(ctx, "view", character_name)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Relics Error",
                "Unable to load relic information."
            )
            await ctx.send(embed=embed)
            print(f"Relics command error: {e}")
    
    @commands.command(name="equip_relic", aliases=["equip"])
    async def equip_relic(self, ctx, character_name: str, *, relic_name: str):
        """Equip a relic to a character"""
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
            
            # Find relic in inventory
            relic_inventory = user_data.get("relic_inventory", [])
            relic_to_equip = None
            
            for i, relic in enumerate(relic_inventory):
                if relic["name"].lower() == relic_name.lower() and not relic.get("equipped_to"):
                    relic_to_equip = (i, relic)
                    break
            
            if not relic_to_equip:
                embed = self.embed_builder.error_embed(
                    "Relic Not Available",
                    f"'{relic_name}' not found in your unequipped relics."
                )
                await ctx.send(embed=embed)
                return
            
            relic_index, relic = relic_to_equip
            relic_type = relic["type"]
            
            # Check if character already has this type equipped
            current_relics = character.get("equipped_relics", {})
            if relic_type in current_relics:
                # Unequip current relic first
                old_relic = current_relics[relic_type]
                # Return old relic to inventory
                for inv_relic in relic_inventory:
                    if inv_relic["name"] == old_relic["name"] and inv_relic.get("equipped_to") == character["name"]:
                        inv_relic.pop("equipped_to", None)
                        break
            
            # Equip new relic
            relic["equipped_to"] = character["name"]
            current_relics[relic_type] = relic
            character["equipped_relics"] = current_relics
            
            # Apply stat bonuses
            self.apply_relic_stats(character, relic)
            
            # Save data
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Create equip success embed
            embed = self.embed_builder.success_embed(
                "Relic Equipped!",
                f"**{relic['name']}** equipped to **{character['name']}**!"
            )
            
            embed.add_field(
                name=f"{relic['emoji']} {relic['name']}",
                value=f"*{relic['description']}*\n"
                      f"**Type:** {relic_type.title()}\n"
                      f"**Rarity:** {relic['rarity']}",
                inline=False
            )
            
            # Show stat bonuses
            stats_text = ""
            for stat, bonus in relic["stats"].items():
                if isinstance(bonus, float):
                    stats_text += f"{stat.replace('_', ' ').title()}: +{int(bonus*100)}%\n"
                else:
                    stats_text += f"{stat.replace('_', ' ').title()}: +{bonus}\n"
            
            embed.add_field(
                name="📊 Stat Bonuses",
                value=stats_text,
                inline=True
            )
            
            embed.add_field(
                name="✨ Special Effect",
                value=relic.get("special_effect", "None"),
                inline=True
            )
            
            await ctx.send(embed=embed)
            await self.log_relic_activity(ctx, "equip", f"{character_name} - {relic['name']}")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Equip Error",
                "Unable to equip relic. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Equip relic error: {e}")
    
    @commands.command(name="forge_relic", aliases=["forge"])
    async def forge_relic(self, ctx, *, relic_name: str):
        """Forge a new relic using materials"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            
            # Find relic template
            relic_template = self.find_relic_template(relic_name)
            if not relic_template:
                embed = self.embed_builder.error_embed(
                    "Unknown Relic",
                    f"Relic '{relic_name}' not found in forging recipes."
                )
                await ctx.send(embed=embed)
                return
            
            relic_data, relic_type = relic_template
            
            # Calculate forging cost
            forging_cost = self.calculate_forging_cost(relic_data["rarity"])
            user_gold = user_data.get("gold", 0)
            
            if user_gold < forging_cost:
                embed = self.embed_builder.error_embed(
                    "Insufficient Resources",
                    f"Forging this relic costs {format_number(forging_cost)} gold."
                )
                await ctx.send(embed=embed)
                return
            
            # Create new relic
            new_relic = {
                "name": relic_data["name"],
                "description": relic_data["description"],
                "type": relic_type,
                "rarity": relic_data["rarity"],
                "emoji": relic_data["emoji"],
                "stats": relic_data["stats"].copy(),
                "special_effect": relic_data["special_effect"],
                "forged_at": datetime.now().isoformat(),
                "forge_quality": random.choice(["Normal", "High", "Perfect"])
            }
            
            # Quality bonuses
            if new_relic["forge_quality"] == "High":
                for stat in new_relic["stats"]:
                    new_relic["stats"][stat] = int(new_relic["stats"][stat] * 1.1)
            elif new_relic["forge_quality"] == "Perfect":
                for stat in new_relic["stats"]:
                    new_relic["stats"][stat] = int(new_relic["stats"][stat] * 1.2)
            
            # Add to inventory
            user_data["gold"] -= forging_cost
            relic_inventory = user_data.setdefault("relic_inventory", [])
            relic_inventory.append(new_relic)
            
            # Save data
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Create forging success embed
            embed = self.embed_builder.success_embed(
                "Relic Forged!",
                f"You've successfully forged a **{new_relic['forge_quality']}** quality relic!"
            )
            
            embed.add_field(
                name=f"{new_relic['emoji']} {new_relic['name']}",
                value=f"*{new_relic['description']}*\n"
                      f"**Quality:** {new_relic['forge_quality']}\n"
                      f"**Rarity:** {new_relic['rarity']}",
                inline=False
            )
            
            # Show enhanced stats
            stats_text = ""
            for stat, value in new_relic["stats"].items():
                if isinstance(value, float):
                    stats_text += f"{stat.replace('_', ' ').title()}: +{int(value*100)}%\n"
                else:
                    stats_text += f"{stat.replace('_', ' ').title()}: +{value}\n"
            
            embed.add_field(
                name="📊 Enhanced Stats",
                value=stats_text,
                inline=True
            )
            
            embed.add_field(
                name="💰 Forging Cost",
                value=f"Materials Used: {format_number(forging_cost)} gold\n"
                      f"Remaining Gold: {format_number(user_data['gold'])}",
                inline=True
            )
            
            await ctx.send(embed=embed)
            await self.log_relic_activity(ctx, "forge", f"{new_relic['name']} - {new_relic['forge_quality']}")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Forging Error",
                "Unable to forge relic. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Forge relic error: {e}")
    
    def find_character_by_name(self, characters: List[Dict], name: str) -> Optional[Dict]:
        """Find character by name (case insensitive)"""
        name_lower = name.lower()
        for char in characters:
            if char.get("name", "").lower() == name_lower:
                return char
        return None
    
    def find_relic_template(self, name: str) -> Optional[tuple]:
        """Find relic template by name"""
        name_lower = name.lower()
        for relic_type, relics in self.relic_types.items():
            for relic_name, relic_data in relics.items():
                if relic_name.lower() == name_lower:
                    return (relic_data, relic_type)
        return None
    
    def calculate_forging_cost(self, rarity: str) -> int:
        """Calculate cost to forge a relic"""
        base_costs = {
            "N": 1000,
            "R": 2500,
            "SR": 5000,
            "SSR": 10000,
            "UR": 20000,
            "LR": 50000,
            "Mythic": 100000
        }
        return base_costs.get(rarity, 1000)
    
    def apply_relic_stats(self, character: Dict, relic: Dict):
        """Apply relic stat bonuses to character"""
        for stat, bonus in relic["stats"].items():
            if stat in ["atk", "def", "hp", "crit"]:
                character[stat] = character.get(stat, 0) + bonus
            elif stat.endswith("_bonus"):
                # Store percentage bonuses separately
                bonuses = character.setdefault("relic_bonuses", {})
                bonuses[stat] = bonuses.get(stat, 0) + bonus
    
    def create_character_relics_embed(self, character: Dict) -> discord.Embed:
        """Create embed showing character's equipped relics"""
        char_name = character.get("name", "Unknown")
        equipped_relics = character.get("equipped_relics", {})
        
        embed = self.embed_builder.create_embed(
            title=f"⚔️ {char_name}'s Equipment",
            description=f"Ancient relics equipped by **{char_name}**",
            color=0x8B4513
        )
        
        if equipped_relics:
            for slot_type, relic in equipped_relics.items():
                stats_text = ""
                for stat, value in relic["stats"].items():
                    if isinstance(value, float):
                        stats_text += f"{stat.replace('_', ' ').title()}: +{int(value*100)}%\n"
                    else:
                        stats_text += f"{stat.replace('_', ' ').title()}: +{value}\n"
                
                embed.add_field(
                    name=f"{relic['emoji']} {relic['name']} ({slot_type.title()})",
                    value=f"*{relic['description']}*\n"
                          f"**Rarity:** {relic['rarity']}\n"
                          f"**Stats:** {stats_text}"
                          f"**Special:** {relic['special_effect']}",
                    inline=False
                )
        else:
            embed.add_field(
                name="⚡ No Equipment",
                value=f"{char_name} has no relics equipped.\n"
                      f"Use `!equip_relic {char_name} <relic_name>` to equip items!",
                inline=False
            )
        
        # Show total power bonus
        total_power = sum(character.get(stat, 0) for stat in ["atk", "def", "hp"])
        embed.add_field(
            name="💪 Equipment Power",
            value=f"**Total Combat Power:** {format_number(total_power)}\n"
                  f"**Equipment Slots:** {len(equipped_relics)}/3",
            inline=True
        )
        
        return embed
    
    def create_relic_collection_embed(self, user_data: Dict) -> discord.Embed:
        """Create relic collection overview embed"""
        relic_inventory = user_data.get("relic_inventory", [])
        
        embed = self.embed_builder.create_embed(
            title="🗡️ Relic Collection",
            description="Your collection of ancient artifacts and equipment",
            color=0x8B4513
        )
        
        if relic_inventory:
            # Group by type
            types = {}
            for relic in relic_inventory:
                relic_type = relic.get("type", "other")
                if relic_type not in types:
                    types[relic_type] = []
                types[relic_type].append(relic)
            
            for relic_type, relics in types.items():
                type_text = ""
                for relic in relics[:5]:  # Show first 5 of each type
                    equipped_to = relic.get("equipped_to", "")
                    status = f"(Equipped to {equipped_to})" if equipped_to else "(Available)"
                    type_text += f"{relic['emoji']} **{relic['name']}** {status}\n"
                
                if len(relics) > 5:
                    type_text += f"*... and {len(relics) - 5} more*"
                
                embed.add_field(
                    name=f"⚔️ {relic_type.title()} ({len(relics)})",
                    value=type_text,
                    inline=True
                )
        else:
            embed.add_field(
                name="📦 Empty Arsenal",
                value="You don't have any relics yet!\n"
                      "Use `!forge_relic <name>` to create powerful equipment!",
                inline=False
            )
        
        # Show forging recipes
        embed.add_field(
            name="🔨 Available Relics to Forge",
            value="Use `!relic_recipes` to see all available relics you can forge!",
            inline=False
        )
        
        return embed
    
    @commands.command(name="relic_recipes", aliases=["forge_list"])
    async def relic_recipes(self, ctx, relic_type: str = "all"):
        """View available relic forging recipes"""
        try:
            embed = self.embed_builder.create_embed(
                title="🔨 Relic Forging Recipes",
                description="Ancient blueprints for crafting powerful relics",
                color=0x8B4513
            )
            
            if relic_type.lower() == "all":
                # Show all categories
                for category, relics in self.relic_types.items():
                    category_text = ""
                    for relic_name, relic_data in list(relics.items())[:3]:  # Show first 3
                        cost = self.calculate_forging_cost(relic_data["rarity"])
                        category_text += f"{relic_data['emoji']} **{relic_name}** - {format_number(cost)} gold\n"
                    
                    embed.add_field(
                        name=f"⚔️ {category.title()} ({len(relics)} recipes)",
                        value=category_text,
                        inline=True
                    )
            else:
                # Show specific category
                if relic_type.lower() in self.relic_types:
                    relics = self.relic_types[relic_type.lower()]
                    
                    for relic_name, relic_data in relics.items():
                        cost = self.calculate_forging_cost(relic_data["rarity"])
                        
                        embed.add_field(
                            name=f"{relic_data['emoji']} {relic_name}",
                            value=f"*{relic_data['description']}*\n"
                                  f"**Rarity:** {relic_data['rarity']}\n"
                                  f"**Cost:** {format_number(cost)} gold\n"
                                  f"**Special:** {relic_data['special_effect']}",
                            inline=True
                        )
            
            embed.add_field(
                name="💡 Forging Tips",
                value="• Higher rarity relics provide better stat bonuses\n"
                      "• Each character can equip weapon, armor, and accessory\n"
                      "• Perfect quality increases all stats by 20%\n"
                      "• Use `!forge_relic <name>` to craft",
                inline=False
            )
            
            await ctx.send(embed=embed)
            await self.log_relic_activity(ctx, "recipes", relic_type)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Recipes Error",
                "Unable to load forging recipes."
            )
            await ctx.send(embed=embed)
            print(f"Relic recipes error: {e}")
    
    async def log_relic_activity(self, ctx, activity_type: str, details: str = ""):
        """Log relic activity to history channel"""
        try:
            history_channel = discord.utils.get(ctx.guild.text_channels, name='history')
            if not history_channel:
                return
            
            emojis = ["⚔️", "🛡️", "🔨", "⚡", "✨", "🏺"]
            emoji = random.choice(emojis)
            
            if activity_type == "view":
                if details:
                    message = f"{emoji} **{ctx.author.display_name}** examined the powerful relics equipped by their {details}!"
                else:
                    message = f"{emoji} **{ctx.author.display_name}** inspected their vast collection of ancient relics!"
            elif activity_type == "equip":
                message = f"{emoji} **{ctx.author.display_name}** equipped the legendary {details}!"
            elif activity_type == "forge":
                message = f"{emoji} **{ctx.author.display_name}** forged a magnificent {details} with masterful craftsmanship!"
            elif activity_type == "recipes":
                message = f"{emoji} **{ctx.author.display_name}** studied ancient forging recipes for {details} relics!"
            else:
                message = f"{emoji} **{ctx.author.display_name}** delved into the mysteries of ancient relics!"
            
            embed = self.embed_builder.create_embed(
                description=message,
                color=0x8B4513
            )
            
            await history_channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error logging relic activity: {e}")

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(RelicsCommands(bot))