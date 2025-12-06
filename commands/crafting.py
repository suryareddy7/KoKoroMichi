# Crafting and Alchemy Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List, Tuple
import random
from datetime import datetime

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from utils.helpers import format_number, validate_amount

class CraftingCommands(commands.Cog):
    """Item crafting, alchemy, and material processing system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        
        # Crafting recipes organized by category
        self.recipes = {
            # Equipment recipes
            "iron_sword": {
                "name": "Iron Sword",
                "category": "equipment",
                "materials": {"Iron Ore": 3, "Cloth Scrap": 1},
                "result_count": 1,
                "success_rate": 0.8,
                "crafting_level": 1,
                "description": "A basic iron sword for combat"
            },
            "steel_armor": {
                "name": "Steel Armor",
                "category": "equipment", 
                "materials": {"Steel Ore": 5, "Dragon Scale": 2, "Mystic Thread": 1},
                "result_count": 1,
                "success_rate": 0.6,
                "crafting_level": 5,
                "description": "Protective steel armor with magical reinforcement"
            },
            
            # Consumable recipes
            "health_potion": {
                "name": "Health Potion",
                "category": "consumables",
                "materials": {"Healing Herb": 2, "Pure Water": 1},
                "result_count": 2,
                "success_rate": 0.9,
                "crafting_level": 1,
                "description": "Restores HP when consumed"
            },
            "mana_elixir": {
                "name": "Mana Elixir",
                "category": "consumables",
                "materials": {"Blue Crystal": 1, "Mystic Essence": 1, "Pure Water": 1},
                "result_count": 1,
                "success_rate": 0.7,
                "crafting_level": 3,
                "description": "Restores mana and increases spell power temporarily"
            },
            
            # Enhancement materials
            "star_fragment": {
                "name": "Star Fragment",
                "category": "enhancement",
                "materials": {"Stardust": 10, "Celestial Core": 1, "Divine Essence": 1},
                "result_count": 1,
                "success_rate": 0.4,
                "crafting_level": 8,
                "description": "Rare material used for character awakening"
            },
            "enchanted_gem": {
                "name": "Enchanted Gem",
                "category": "enhancement",
                "materials": {"Raw Gem": 3, "Magic Powder": 2},
                "result_count": 1,
                "success_rate": 0.75,
                "crafting_level": 4,
                "description": "Gem imbued with magical properties"
            },
            
            # Special items
            "philosopher_stone": {
                "name": "Philosopher's Stone",
                "category": "legendary",
                "materials": {"Gold Ore": 10, "Dragon Heart": 1, "Ancient Scroll": 3, "Divine Essence": 5},
                "result_count": 1,
                "success_rate": 0.1,
                "crafting_level": 15,
                "description": "Legendary item that transmutes materials"
            }
        }
        
        # Material gathering locations
        self.gathering_locations = {
            "forest": {
                "name": "Mystic Forest",
                "materials": ["Healing Herb", "Wood", "Nature Essence"],
                "energy_cost": 5,
                "description": "A magical forest rich in natural materials"
            },
            "mines": {
                "name": "Crystal Mines",
                "materials": ["Iron Ore", "Blue Crystal", "Raw Gem"],
                "energy_cost": 8,
                "description": "Deep mines containing precious ores and crystals"
            },
            "volcano": {
                "name": "Volcanic Caverns",
                "materials": ["Fire Crystal", "Molten Core", "Dragon Scale"],
                "energy_cost": 12,
                "description": "Dangerous volcanic caves with rare fire materials"
            }
        }
    
    @commands.group(name="craft", invoke_without_command=True)
    async def craft_group(self, ctx, recipe_name: str = None, amount: int = 1):
        """Craft items using materials from your inventory"""
        try:
            if recipe_name is None:
                # Show crafting menu
                embed = self.create_crafting_menu_embed()
                await ctx.send(embed=embed)
                return
            
            # Find recipe
            recipe = self.find_recipe(recipe_name)
            if not recipe:
                embed = self.embed_builder.error_embed(
                    "Recipe Not Found",
                    f"No recipe found for '{recipe_name}'. Use `!craft recipes` to see all recipes."
                )
                await ctx.send(embed=embed)
                return
            
            # Validate amount
            if amount < 1 or amount > 10:
                embed = self.embed_builder.error_embed(
                    "Invalid Amount",
                    "You can craft between 1 and 10 items at once."
                )
                await ctx.send(embed=embed)
                return
            
            # Perform crafting
            await self.perform_crafting(ctx, recipe, amount)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Crafting Error",
                "Unable to process crafting request. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Craft command error: {e}")
    
    @craft_group.command(name="recipes")
    async def view_recipes(self, ctx, category: str = None):
        """View all available crafting recipes"""
        try:
            if category:
                # Filter by category
                filtered_recipes = {k: v for k, v in self.recipes.items() if v["category"] == category.lower()}
                if not filtered_recipes:
                    categories = list(set(recipe["category"] for recipe in self.recipes.values()))
                    embed = self.embed_builder.error_embed(
                        "Invalid Category",
                        f"Available categories: {', '.join(categories)}"
                    )
                    await ctx.send(embed=embed)
                    return
                recipes_to_show = filtered_recipes
                title = f"🔨 {category.title()} Recipes"
            else:
                recipes_to_show = self.recipes
                title = "🔨 All Crafting Recipes"
            
            # Create recipe list embed
            embed = self.create_recipes_embed(recipes_to_show, title)
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Recipes Error",
                "Unable to load crafting recipes."
            )
            await ctx.send(embed=error_embed)
            print(f"Recipes command error: {e}")
    
    @craft_group.command(name="info")
    async def recipe_info(self, ctx, *, recipe_name: str):
        """View detailed information about a specific recipe"""
        try:
            recipe = self.find_recipe(recipe_name)
            if not recipe:
                embed = self.embed_builder.error_embed(
                    "Recipe Not Found",
                    f"No recipe found for '{recipe_name}'."
                )
                await ctx.send(embed=embed)
                return
            
            # Create detailed recipe info
            embed = self.create_recipe_info_embed(recipe)
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Recipe Info Error",
                "Unable to load recipe information."
            )
            await ctx.send(embed=error_embed)
            print(f"Recipe info error: {e}")
    
    @commands.command(name="gather")
    async def gather_materials(self, ctx, location: str = None):
        """Gather materials from various locations"""
        try:
            if location is None:
                # Show gathering locations
                embed = self.create_gathering_menu_embed()
                await ctx.send(embed=embed)
                return
            
            # Find location
            location_data = None
            for loc_id, loc_info in self.gathering_locations.items():
                if location.lower() in loc_id.lower() or location.lower() in loc_info["name"].lower():
                    location_data = loc_info
                    location_id = loc_id
                    break
            
            if not location_data:
                available_locations = ", ".join(self.gathering_locations.keys())
                embed = self.embed_builder.error_embed(
                    "Location Not Found",
                    f"Available locations: {available_locations}"
                )
                await ctx.send(embed=embed)
                return
            
            # Check energy (if implemented)
            user_data = data_manager.get_user_data(str(ctx.author.id))
            
            # Perform gathering
            await self.perform_gathering(ctx, location_data, location_id, user_data)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Gathering Error",
                "Unable to gather materials. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Gather command error: {e}")
    
    @commands.command(name="materials", aliases=["mats"])
    async def view_materials(self, ctx):
        """View your crafting materials inventory"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            inventory = user_data.get("inventory", {})
            
            # Filter for crafting materials
            materials = self.filter_crafting_materials(inventory)
            
            if not materials:
                embed = self.embed_builder.info_embed(
                    "No Materials",
                    "You don't have any crafting materials. Use `!gather` to collect some!"
                )
                await ctx.send(embed=embed)
                return
            
            # Create materials inventory embed
            embed = self.create_materials_embed(materials)
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Materials Error",
                "Unable to load materials inventory."
            )
            await ctx.send(embed=error_embed)
            print(f"Materials command error: {e}")
    
    async def perform_crafting(self, ctx, recipe: Dict, amount: int):
        """Perform the actual crafting process"""
        user_data = data_manager.get_user_data(str(ctx.author.id))
        inventory = user_data.get("inventory", {})
        
        # Check crafting level requirement
        user_crafting_level = user_data.get("crafting_level", 1)
        if user_crafting_level < recipe["crafting_level"]:
            embed = self.embed_builder.error_embed(
                "Insufficient Crafting Level",
                f"This recipe requires crafting level {recipe['crafting_level']}. "
                f"Your level: {user_crafting_level}"
            )
            await ctx.send(embed=embed)
            return
        
        # Check materials for all attempts
        total_materials_needed = {}
        for material, count in recipe["materials"].items():
            total_materials_needed[material] = count * amount
        
        # Verify user has enough materials
        missing_materials = []
        for material, needed in total_materials_needed.items():
            available = inventory.get(material, 0)
            if available < needed:
                missing_materials.append(f"{material}: {available}/{needed}")
        
        if missing_materials:
            embed = self.embed_builder.error_embed(
                "Insufficient Materials",
                f"Missing materials:\n" + "\n".join(missing_materials)
            )
            await ctx.send(embed=embed)
            return
        
        # Perform crafting attempts
        successful_crafts = 0
        for i in range(amount):
            success_rate = recipe["success_rate"]
            # Bonus success rate based on crafting level
            level_bonus = min(0.1, (user_crafting_level - recipe["crafting_level"]) * 0.02)
            final_success_rate = min(0.95, success_rate + level_bonus)
            
            if random.random() < final_success_rate:
                successful_crafts += 1
        
        # Consume materials
        for material, needed in total_materials_needed.items():
            inventory[material] -= needed
            if inventory[material] <= 0:
                del inventory[material]
        
        # Add crafted items
        if successful_crafts > 0:
            total_items = successful_crafts * recipe["result_count"]
            inventory[recipe["name"]] = inventory.get(recipe["name"], 0) + total_items
        
        # Update crafting stats
        crafting_stats = user_data.setdefault("crafting_stats", {})
        crafting_stats["items_crafted"] = crafting_stats.get("items_crafted", 0) + amount
        crafting_stats["successful_crafts"] = crafting_stats.get("successful_crafts", 0) + successful_crafts
        
        # Gain crafting XP and potentially level up
        xp_gained = amount * 10
        crafting_xp = user_data.get("crafting_xp", 0) + xp_gained
        new_level = self.calculate_crafting_level(crafting_xp)
        
        if new_level > user_crafting_level:
            user_data["crafting_level"] = new_level
            level_up_bonus = True
        else:
            level_up_bonus = False
        
        user_data["crafting_xp"] = crafting_xp
        
        # Save user data
        data_manager.save_user_data(str(ctx.author.id), user_data)
        
        # Create result embed
        embed = self.create_crafting_result_embed(
            recipe, amount, successful_crafts, xp_gained, level_up_bonus, new_level
        )
        await ctx.send(embed=embed)
    
    async def perform_gathering(self, ctx, location_data: Dict, location_id: str, user_data: Dict):
        """Perform material gathering"""
        # Simulate gathering (1-3 materials)
        materials_found = {}
        num_materials = random.randint(1, 3)
        
        for _ in range(num_materials):
            material = random.choice(location_data["materials"])
            amount = random.randint(1, 3)
            materials_found[material] = materials_found.get(material, 0) + amount
        
        # Add materials to inventory
        inventory = user_data.setdefault("inventory", {})
        for material, amount in materials_found.items():
            inventory[material] = inventory.get(material, 0) + amount
        
        # Update gathering stats
        crafting_stats = user_data.setdefault("crafting_stats", {})
        crafting_stats["materials_gathered"] = crafting_stats.get("materials_gathered", 0) + sum(materials_found.values())
        
        # Gain some XP
        xp_gained = 5
        user_data["crafting_xp"] = user_data.get("crafting_xp", 0) + xp_gained
        
        data_manager.save_user_data(str(ctx.author.id), user_data)
        
        # Create gathering result embed
        embed = self.create_gathering_result_embed(location_data, materials_found, xp_gained)
        await ctx.send(embed=embed)
    
    def find_recipe(self, recipe_name: str) -> Optional[Dict]:
        """Find a recipe by name (case-insensitive partial match)"""
        recipe_name = recipe_name.lower()
        
        # First try exact match
        for recipe_id, recipe_data in self.recipes.items():
            if recipe_id.lower() == recipe_name or recipe_data["name"].lower() == recipe_name:
                return recipe_data
        
        # Then try partial match
        for recipe_id, recipe_data in self.recipes.items():
            if recipe_name in recipe_id.lower() or recipe_name in recipe_data["name"].lower():
                return recipe_data
        
        return None
    
    def filter_crafting_materials(self, inventory: Dict) -> Dict:
        """Filter inventory to show only crafting materials"""
        # Get all materials used in recipes
        all_materials = set()
        for recipe in self.recipes.values():
            all_materials.update(recipe["materials"].keys())
        
        # Add gathering materials
        for location in self.gathering_locations.values():
            all_materials.update(location["materials"])
        
        # Filter inventory
        return {item: count for item, count in inventory.items() if item in all_materials}
    
    def calculate_crafting_level(self, xp: int) -> int:
        """Calculate crafting level from XP"""
        # XP formula: level = sqrt(xp/100) + 1
        import math
        level = int(math.sqrt(xp / 100)) + 1
        return min(level, 20)  # Cap at level 20
    
    def create_crafting_menu_embed(self) -> discord.Embed:
        """Create main crafting menu embed"""
        embed = self.embed_builder.create_embed(
            title="🔨 Crafting System",
            description="Craft powerful items and consumables using materials!",
            color=0x8B4513
        )
        
        # Show categories
        categories = list(set(recipe["category"] for recipe in self.recipes.values()))
        categories_text = "\n".join([f"• {cat.title()}" for cat in categories])
        
        embed.add_field(
            name="📋 Recipe Categories",
            value=categories_text,
            inline=True
        )
        
        embed.add_field(
            name="🔍 Commands",
            value="• `!craft <recipe> [amount]` - Craft items\n"
                  "• `!craft recipes [category]` - View recipes\n"
                  "• `!craft info <recipe>` - Recipe details\n"
                  "• `!gather [location]` - Gather materials\n"
                  "• `!materials` - View materials",
            inline=True
        )
        
        embed.add_field(
            name="💡 Crafting Tips",
            value="• Higher crafting level increases success rate\n"
                  "• Some recipes require specific levels\n"
                  "• Failed crafts still consume materials\n"
                  "• Gather materials from different locations",
            inline=False
        )
        
        return embed
    
    def create_recipes_embed(self, recipes: Dict, title: str) -> discord.Embed:
        """Create recipes list embed"""
        embed = self.embed_builder.create_embed(
            title=title,
            color=0x8B4513
        )
        
        # Group by category
        by_category = {}
        for recipe_id, recipe_data in recipes.items():
            category = recipe_data["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(recipe_data)
        
        # Add fields for each category
        for category, recipe_list in by_category.items():
            recipes_text = ""
            for recipe in recipe_list[:5]:  # Limit to 5 per category
                success_rate = int(recipe["success_rate"] * 100)
                recipes_text += f"**{recipe['name']}** (Lv.{recipe['crafting_level']}, {success_rate}%)\n"
                recipes_text += f"  {recipe['description']}\n\n"
            
            if len(recipe_list) > 5:
                recipes_text += f"... and {len(recipe_list) - 5} more"
            
            embed.add_field(
                name=f"🔨 {category.title()}",
                value=recipes_text or "No recipes",
                inline=True
            )
        
        return embed
    
    def create_recipe_info_embed(self, recipe: Dict) -> discord.Embed:
        """Create detailed recipe information embed"""
        embed = self.embed_builder.create_embed(
            title=f"🔨 {recipe['name']}",
            description=recipe["description"],
            color=0x8B4513
        )
        
        # Materials required
        materials_text = ""
        for material, count in recipe["materials"].items():
            materials_text += f"• {material}: {count}\n"
        
        embed.add_field(
            name="📦 Required Materials",
            value=materials_text,
            inline=True
        )
        
        # Recipe stats
        success_rate = int(recipe["success_rate"] * 100)
        embed.add_field(
            name="📊 Recipe Stats",
            value=f"Success Rate: {success_rate}%\n"
                  f"Required Level: {recipe['crafting_level']}\n"
                  f"Result Count: {recipe['result_count']}\n"
                  f"Category: {recipe['category'].title()}",
            inline=True
        )
        
        return embed
    
    def create_gathering_menu_embed(self) -> discord.Embed:
        """Create gathering locations menu"""
        embed = self.embed_builder.create_embed(
            title="🗺️ Material Gathering",
            description="Explore different locations to gather crafting materials!",
            color=0x228B22
        )
        
        for location_id, location_data in self.gathering_locations.items():
            materials_list = ", ".join(location_data["materials"])
            
            embed.add_field(
                name=f"🌍 {location_data['name']}",
                value=f"{location_data['description']}\n"
                      f"**Materials:** {materials_list}\n"
                      f"**Energy Cost:** {location_data['energy_cost']}",
                inline=True
            )
        
        embed.add_field(
            name="💡 Gathering Tips",
            value="• Different locations yield different materials\n"
                  "• Higher level areas have rarer materials\n"
                  "• Energy regenerates over time",
            inline=False
        )
        
        return embed
    
    def create_materials_embed(self, materials: Dict) -> discord.Embed:
        """Create materials inventory embed"""
        embed = self.embed_builder.create_embed(
            title="📦 Crafting Materials",
            description="Your collection of crafting materials",
            color=0x9370DB
        )
        
        # Sort materials by quantity
        sorted_materials = sorted(materials.items(), key=lambda x: x[1], reverse=True)
        
        # Group materials for display
        materials_text = ""
        for i, (material, count) in enumerate(sorted_materials):
            materials_text += f"• **{material}**: {count}\n"
            
            # Add field every 10 items to avoid embed limits
            if (i + 1) % 10 == 0 or i == len(sorted_materials) - 1:
                field_name = f"📋 Materials {((i // 10) * 10) + 1}-{i + 1}"
                embed.add_field(
                    name=field_name,
                    value=materials_text,
                    inline=True
                )
                materials_text = ""
        
        if not sorted_materials:
            embed.add_field(
                name="📦 No Materials",
                value="Use `!gather` to collect materials!",
                inline=False
            )
        
        return embed
    
    def create_crafting_result_embed(self, recipe: Dict, attempted: int, successful: int, 
                                   xp_gained: int, level_up: bool, new_level: int) -> discord.Embed:
        """Create crafting result embed"""
        if successful > 0:
            title = "🔨 Crafting Successful!"
            color = 0x00FF00
        else:
            title = "💔 Crafting Failed"
            color = 0xFF0000
        
        embed = self.embed_builder.create_embed(
            title=title,
            color=color
        )
        
        # Results
        total_items = successful * recipe["result_count"]
        success_rate = (successful / attempted * 100) if attempted > 0 else 0
        
        embed.add_field(
            name="📊 Results",
            value=f"Attempted: {attempted}\n"
                  f"Successful: {successful}\n"
                  f"Success Rate: {success_rate:.1f}%\n"
                  f"Items Created: {total_items}",
            inline=True
        )
        
        # XP and level info
        xp_text = f"XP Gained: +{xp_gained}"
        if level_up:
            xp_text += f"\n🎉 **Level Up!** New level: {new_level}"
        
        embed.add_field(
            name="⭐ Experience",
            value=xp_text,
            inline=True
        )
        
        if successful > 0:
            embed.add_field(
                name="🎁 Items Received",
                value=f"**{recipe['name']}** x{total_items}",
                inline=False
            )
        
        return embed
    
    def create_gathering_result_embed(self, location_data: Dict, materials_found: Dict, 
                                    xp_gained: int) -> discord.Embed:
        """Create gathering result embed"""
        embed = self.embed_builder.success_embed(
            "Gathering Successful!",
            f"You explored {location_data['name']} and found materials!"
        )
        
        # Materials found
        materials_text = ""
        for material, amount in materials_found.items():
            materials_text += f"• **{material}**: +{amount}\n"
        
        embed.add_field(
            name="📦 Materials Found",
            value=materials_text,
            inline=True
        )
        
        embed.add_field(
            name="⭐ Experience",
            value=f"Crafting XP: +{xp_gained}",
            inline=True
        )
        
        return embed


async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(CraftingCommands(bot))