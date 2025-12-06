# Store System Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List, Any
import random
import math
from datetime import datetime, timezone, timedelta

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from core.config import FEATURES
from utils.helpers import format_number
import logging

logger = logging.getLogger(__name__)

class StoreCommands(commands.Cog):
    """Advanced store with dynamic pricing and VIP discounts"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        
        # Store items with base prices
        self.store_items = {
            "healing_potion": {
                "name": "Healing Potion",
                "description": "Restores 500 HP to your character",
                "base_price": 200,
                "category": "consumables",
                "emoji": "🧪",
                "effect": {"type": "heal", "value": 500}
            },
            "experience_boost": {
                "name": "Experience Elixir",
                "description": "Grants 1000 bonus XP",
                "base_price": 500,
                "category": "consumables", 
                "emoji": "⭐",
                "effect": {"type": "xp", "value": 1000}
            },
            "strength_enhancer": {
                "name": "Strength Enhancer",
                "description": "Permanently increases ATK by 10",
                "base_price": 1000,
                "category": "enhancements",
                "emoji": "⚔️",
                "effect": {"type": "stat_boost", "stat": "atk", "value": 10}
            },
            "defense_crystal": {
                "name": "Defense Crystal",
                "description": "Permanently increases DEF by 8",
                "base_price": 1000,
                "category": "enhancements",
                "emoji": "🛡️",
                "effect": {"type": "stat_boost", "stat": "def", "value": 8}
            },
            "vitality_gem": {
                "name": "Vitality Gem",
                "description": "Permanently increases HP by 50",
                "base_price": 800,
                "category": "enhancements",
                "emoji": "❤️",
                "effect": {"type": "stat_boost", "stat": "hp", "value": 50}
            },
            "arena_pass": {
                "name": "Arena Pass",
                "description": "Grants access to premium arena battles",
                "base_price": 2000,
                "category": "passes",
                "emoji": "🎫",
                "effect": {"type": "access", "feature": "premium_arena"}
            },
            "summon_ticket": {
                "name": "Summon Ticket",
                "description": "Free character summon with 2x rare rates",
                "base_price": 1500,
                "category": "tickets",
                "emoji": "🎟️",
                "effect": {"type": "summon", "bonus": "double_rates"}
            },
            "affection_candy": {
                "name": "Affection Candy",
                "description": "Increases character affection by 10",
                "base_price": 300,
                "category": "consumables",
                "emoji": "🍭",
                "effect": {"type": "affection", "value": 10}
            },
            "element_shard": {
                "name": "Element Shard",
                "description": "Change your character's element",
                "base_price": 5000,
                "category": "special",
                "emoji": "🔮",
                "effect": {"type": "element_change"}
            },
            "mystery_box": {
                "name": "Mystery Box",
                "description": "Contains random valuable items",
                "base_price": 2500,
                "category": "mystery",
                "emoji": "📦",
                "effect": {"type": "random_rewards"}
            }
        }
        
        # VIP discount tiers
        self.vip_discounts = {
            "consumables": 0.10,  # 10% discount
            "enhancements": 0.15, # 15% discount
            "passes": 0.20,       # 20% discount
            "tickets": 0.25,      # 25% discount
            "special": 0.30       # 30% discount
        }
    
    @commands.command(name="store", aliases=["shop", "market"])
    async def view_store(self, ctx, category: str = None):
        """Browse the store by category with dynamic pricing"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            
            # Update daily pricing
            self.update_daily_pricing()
            
            if not category:
                # Show categories
                embed = self.create_category_menu()
                await ctx.send(embed=embed)
                return
            
            # Filter items by category
            category_items = {k: v for k, v in self.store_items.items() if v["category"] == category.lower()}
            
            if not category_items:
                embed = self.embed_builder.error_embed(
                    "Invalid Category",
                    f"Category '{category}' not found. Use `!store` to see all categories."
                )
                await ctx.send(embed=embed)
                return
            
            embed = self.embed_builder.create_embed(
                title="🏪 KoKoroMichi Store",
                description=f"Premium items and enhancements • Page {page}/{total_pages}",
                color=0x32CD32
            )
            
            # Add user's current resources
            user_gold = user_data.get("gold", 0)
            user_gems = user_data.get("gems", 0)
            is_vip = self.check_vip_status(user_data)
            
            embed.add_field(
                name="💰 Your Resources",
                value=f"Gold: {format_number(user_gold)}\n"
                      f"Gems: {format_number(user_gems)}\n"
                      f"VIP Status: {'✅ Active' if is_vip else '❌ Inactive'}",
                inline=True
            )
            
            # Show items
            for item_id, item_data in page_items:
                current_price = self.calculate_current_price(item_id, item_data, is_vip)
                price_change = self.get_price_change_indicator(item_id, item_data["base_price"])
                
                embed.add_field(
                    name=f"{item_data['emoji']} {item_data['name']}",
                    value=f"*{item_data['description']}*\n"
                          f"💰 **{format_number(current_price)} gold** {price_change}\n"
                          f"Use: `!buy {item_id}`",
                    inline=True
                )
            
            # Navigation info
            embed.add_field(
                name="📄 Navigation",
                value=f"Use `!store {page+1}` for next page\n"
                      f"Items refresh daily at 5:30 UTC" + 
                      ("\n🌟 VIP discounts active!" if is_vip else ""),
                inline=False
            )
            
            await ctx.send(embed=embed)
            await self.log_store_activity(ctx, "browse", f"page {page}")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Store Error",
                "Unable to load store. Please try again later."
            )
            await ctx.send(embed=embed)
            print(f"Store command error: {e}")
    
    def create_category_menu(self) -> discord.Embed:
        """Create store category selection menu"""
        embed = self.embed_builder.create_embed(
            title="🏪 KoKoroMichi Store - Categories",
            description="Choose a category to browse items. Each category resets prices daily at 5:30 UTC.",
            color=0x32CD32
        )
        
        # Get unique categories
        categories = {}
        for item_data in self.store_items.values():
            category = item_data["category"]
            if category not in categories:
                categories[category] = {"count": 0, "emoji": "📦"}
            categories[category]["count"] += 1
        
        # Category emojis
        category_emojis = {
            "consumables": "🧪",
            "enhancements": "⚔️", 
            "passes": "🎫",
            "tickets": "🎟️",
            "special": "🔮",
            "mystery": "📦"
        }
        
        # Add categories
        for i, (category, data) in enumerate(categories.items(), 1):
            emoji = category_emojis.get(category, "📦")
            embed.add_field(
                name=f"{emoji} {i}. {category.title()}",
                value=f"{data['count']} items available\nUse: `!store {category}`",
                inline=True
            )
        
        embed.add_field(
            name="💡 How to Buy",
            value="1️⃣ `!store <category>` - Browse category\n2️⃣ `!buy <item_id> <amount>` - Purchase item\n3️⃣ Choose currency (gold/gems)",
            inline=False
        )
        
        return embed
    
    @commands.command(name="buy", aliases=["purchase"])
    async def buy_item(self, ctx, item_id: str, quantity: int = 1):
        """Purchase items from the store"""
        try:
            if item_id not in self.store_items:
                embed = self.embed_builder.error_embed(
                    "Item Not Found",
                    f"Item '{item_id}' not found in store. Use `!store` to browse items."
                )
                await ctx.send(embed=embed)
                return
            
            if quantity < 1 or quantity > 99:
                embed = self.embed_builder.error_embed(
                    "Invalid Quantity",
                    "You can buy between 1 and 99 items at once."
                )
                await ctx.send(embed=embed)
                return
            
            user_data = data_manager.get_user_data(str(ctx.author.id))
            item_data = self.store_items[item_id]
            is_vip = self.check_vip_status(user_data)
            
            # Calculate total cost
            unit_price = self.calculate_current_price(item_id, item_data, is_vip)
            total_cost = unit_price * quantity
            
            # Check if user has enough gold
            user_gold = user_data.get("gold", 0)
            if user_gold < total_cost:
                embed = self.embed_builder.error_embed(
                    "Insufficient Gold",
                    f"You need {format_number(total_cost)} gold but only have {format_number(user_gold)}."
                )
                await ctx.send(embed=embed)
                return
            
            # Process purchase
            user_data["gold"] -= total_cost
            
            # Apply item effects
            for _ in range(quantity):
                self.apply_item_effect(user_data, item_data)
            
            # Update purchase history
            self.update_purchase_stats(user_data, item_id, quantity, total_cost)
            
            # Save data
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Create purchase confirmation
            embed = self.embed_builder.success_embed(
                "Purchase Successful!",
                f"You bought **{quantity}x {item_data['name']}**!"
            )
            
            embed.add_field(
                name="💰 Transaction",
                value=f"**Item:** {item_data['emoji']} {item_data['name']}\n"
                      f"**Quantity:** {quantity}\n"
                      f"**Unit Price:** {format_number(unit_price)} gold\n"
                      f"**Total Cost:** {format_number(total_cost)} gold",
                inline=True
            )
            
            embed.add_field(
                name="💳 Account Balance",
                value=f"**Remaining Gold:** {format_number(user_data['gold'])}\n"
                      f"**VIP Status:** {'✅ Active' if is_vip else '❌ None'}",
                inline=True
            )
            
            # Show item effect
            effect_text = self.get_effect_description(item_data["effect"], quantity)
            embed.add_field(
                name="✨ Item Effect",
                value=effect_text,
                inline=False
            )
            
            await ctx.send(embed=embed)
            await self.log_store_activity(ctx, "purchase", f"{quantity}x {item_data['name']}")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Purchase Error",
                "Unable to complete purchase. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Buy command error: {e}")
    
    @commands.command(name="store_inventory", aliases=["store_items", "bag"])
    async def view_inventory(self, ctx):
        """View purchased items and consumables"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            inventory = user_data.get("inventory", {})
            
            embed = self.embed_builder.create_embed(
                title="🎒 Your Inventory",
                description="Items you've purchased and collected",
                color=0x4169E1
            )
            
            if not inventory:
                embed.add_field(
                    name="📦 Empty Inventory",
                    value="You don't have any items yet. Visit the `!store` to buy some!",
                    inline=False
                )
            else:
                # Group items by category
                categories = {}
                for item_id, count in inventory.items():
                    if count > 0:
                        item_data = self.store_items.get(item_id, {})
                        category = item_data.get("category", "other")
                        if category not in categories:
                            categories[category] = []
                        categories[category].append((item_id, item_data, count))
                
                # Display by category
                for category, items in categories.items():
                    category_text = ""
                    for item_id, item_data, count in items:
                        emoji = item_data.get("emoji", "📦")
                        name = item_data.get("name", item_id)
                        category_text += f"{emoji} **{name}** x{count}\n"
                    
                    embed.add_field(
                        name=f"📋 {category.title()}",
                        value=category_text,
                        inline=True
                    )
            
            # Show purchase statistics
            purchase_stats = user_data.get("purchase_stats", {})
            total_spent = purchase_stats.get("total_gold_spent", 0)
            total_purchases = purchase_stats.get("total_purchases", 0)
            
            embed.add_field(
                name="📊 Purchase History",
                value=f"**Total Spent:** {format_number(total_spent)} gold\n"
                      f"**Total Purchases:** {total_purchases}\n"
                      f"**VIP Status:** {'✅ Active' if self.check_vip_status(user_data) else '❌ Inactive'}",
                inline=False
            )
            
            await ctx.send(embed=embed)
            await self.log_store_activity(ctx, "inventory_check")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Inventory Error",
                "Unable to load inventory. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Inventory command error: {e}")
    
    def calculate_current_price(self, item_id: str, item_data: Dict, is_vip: bool) -> int:
        """Calculate current price with dynamic pricing and VIP discounts"""
        base_price = item_data["base_price"]
        
        # Get current day's purchase count for price inflation
        store_data = data_manager.get_game_data().get("store_data", {})
        daily_data = store_data.get("daily_purchases", {})
        today = datetime.now(timezone.utc).date().isoformat()
        
        if daily_data.get("date") != today:
            daily_data = {"date": today, "item_counts": {}}
        
        purchase_count = daily_data["item_counts"].get(item_id, 0)
        
        # Dynamic pricing: 5% increase per purchase
        inflation_multiplier = 1 + (purchase_count * 0.05)
        inflated_price = int(base_price * inflation_multiplier)
        
        # Apply VIP discount
        if is_vip:
            category = item_data.get("category", "other")
            discount = self.vip_discounts.get(category, 0)
            inflated_price = int(inflated_price * (1 - discount))
        
        return inflated_price
    
    def get_price_change_indicator(self, item_id: str, base_price: int) -> str:
        """Get price change indicator"""
        store_data = data_manager.get_game_data().get("store_data", {})
        daily_data = store_data.get("daily_purchases", {})
        today = datetime.now(timezone.utc).date().isoformat()
        
        if daily_data.get("date") != today:
            return ""
        
        purchase_count = daily_data["item_counts"].get(item_id, 0)
        
        if purchase_count == 0:
            return ""
        elif purchase_count <= 2:
            return "📈"
        elif purchase_count <= 5:
            return "📈📈"
        else:
            return "📈📈📈"
    
    def check_vip_status(self, user_data: Dict) -> bool:
        """Check if user has VIP status"""
        # VIP based on total spending or special items
        purchase_stats = user_data.get("purchase_stats", {})
        total_spent = purchase_stats.get("total_gold_spent", 0)
        
        # VIP if spent 50,000+ gold or has VIP item
        vip_items = user_data.get("inventory", {}).get("vip_pass", 0)
        return total_spent >= 50000 or vip_items > 0
    
    def apply_item_effect(self, user_data: Dict, item_data: Dict):
        """Apply item effect to user data"""
        effect = item_data["effect"]
        effect_type = effect["type"]
        
        if effect_type == "heal":
            # Add to inventory for later use
            inventory = user_data.setdefault("inventory", {})
            item_id = "healing_potion"
            inventory[item_id] = inventory.get(item_id, 0) + 1
        
        elif effect_type == "xp":
            user_data["xp"] = user_data.get("xp", 0) + effect["value"]
        
        elif effect_type == "stat_boost":
            # Apply to strongest character
            characters = user_data.get("claimed_waifus", [])
            if characters:
                strongest = max(characters, key=lambda c: c.get("potential", 0))
                stat = effect["stat"]
                strongest[stat] = strongest.get(stat, 0) + effect["value"]
                strongest["potential"] = strongest.get("potential", 0) + effect["value"] * 10
        
        elif effect_type == "access":
            # Add access permissions
            permissions = user_data.setdefault("permissions", {})
            permissions[effect["feature"]] = True
        
        elif effect_type == "summon":
            # Add summon tickets
            inventory = user_data.setdefault("inventory", {})
            inventory["summon_ticket"] = inventory.get("summon_ticket", 0) + 1
        
        elif effect_type == "affection":
            # Apply to random character
            characters = user_data.get("claimed_waifus", [])
            if characters:
                random_char = random.choice(characters)
                random_char["affection"] = random_char.get("affection", 0) + effect["value"]
        
        elif effect_type == "random_rewards":
            # Open mystery box
            self.open_mystery_box(user_data)
    
    def open_mystery_box(self, user_data: Dict):
        """Open mystery box and give random rewards"""
        possible_rewards = [
            {"type": "gold", "amount": random.randint(1000, 5000)},
            {"type": "xp", "amount": random.randint(500, 2000)},
            {"type": "gems", "amount": random.randint(10, 50)},
            {"type": "item", "item": random.choice(list(self.store_items.keys()))}
        ]
        
        # Give 2-4 random rewards
        reward_count = random.randint(2, 4)
        for _ in range(reward_count):
            reward = random.choice(possible_rewards)
            
            if reward["type"] == "gold":
                user_data["gold"] = user_data.get("gold", 0) + reward["amount"]
            elif reward["type"] == "xp":
                user_data["xp"] = user_data.get("xp", 0) + reward["amount"]
            elif reward["type"] == "gems":
                user_data["gems"] = user_data.get("gems", 0) + reward["amount"]
            elif reward["type"] == "item":
                inventory = user_data.setdefault("inventory", {})
                inventory[reward["item"]] = inventory.get(reward["item"], 0) + 1
    
    def get_effect_description(self, effect: Dict, quantity: int) -> str:
        """Get human-readable effect description"""
        effect_type = effect["type"]
        
        if effect_type == "heal":
            return f"Added {quantity}x Healing Potion to inventory"
        elif effect_type == "xp":
            total_xp = effect["value"] * quantity
            return f"Gained {format_number(total_xp)} XP immediately!"
        elif effect_type == "stat_boost":
            stat_name = {"atk": "Attack", "def": "Defense", "hp": "Health"}.get(effect["stat"], effect["stat"])
            total_boost = effect["value"] * quantity
            return f"Boosted strongest character's {stat_name} by {total_boost}!"
        elif effect_type == "access":
            return f"Unlocked access to {effect['feature'].replace('_', ' ').title()}!"
        elif effect_type == "summon":
            return f"Added {quantity}x Summon Ticket with double rare rates!"
        elif effect_type == "affection":
            total_affection = effect["value"] * quantity
            return f"Increased random character's affection by {total_affection}!"
        elif effect_type == "random_rewards":
            return f"Opened {quantity}x Mystery Box with random treasures!"
        else:
            return "Item effect applied!"
    
    def update_daily_pricing(self):
        """Update daily pricing data"""
        game_data = data_manager.get_game_data()
        store_data = game_data.setdefault("store_data", {})
        daily_data = store_data.setdefault("daily_purchases", {})
        
        today = datetime.now(timezone.utc).date().isoformat()
        
        # Reset if new day
        if daily_data.get("date") != today:
            daily_data = {
                "date": today,
                "item_counts": {},
                "reset_time": datetime.now(timezone.utc).isoformat()
            }
            store_data["daily_purchases"] = daily_data
            data_manager.save_game_data(game_data)
    
    def update_purchase_stats(self, user_data: Dict, item_id: str, quantity: int, total_cost: int):
        """Update user purchase statistics"""
        # Update user stats
        purchase_stats = user_data.setdefault("purchase_stats", {})
        purchase_stats["total_purchases"] = purchase_stats.get("total_purchases", 0) + quantity
        purchase_stats["total_gold_spent"] = purchase_stats.get("total_gold_spent", 0) + total_cost
        
        # Update global store data
        game_data = data_manager.get_game_data()
        store_data = game_data.setdefault("store_data", {})
        daily_data = store_data.setdefault("daily_purchases", {})
        item_counts = daily_data.setdefault("item_counts", {})
        
        item_counts[item_id] = item_counts.get(item_id, 0) + quantity
        data_manager.save_game_data(game_data)
    
    async def log_store_activity(self, ctx, activity_type: str, details: str = ""):
        """Log store activity to history channel"""
        try:
            history_channel = discord.utils.get(ctx.guild.text_channels, name='history')
            if not history_channel:
                return
            
            emojis = ["🏪", "💰", "🛍️", "💎", "✨", "🎁"]
            emoji = random.choice(emojis)
            
            if activity_type == "browse":
                message = f"{emoji} **{ctx.author.display_name}** browsed the mystical marketplace on {details}!"
            elif activity_type == "purchase":
                message = f"{emoji} **{ctx.author.display_name}** acquired {details} from the enchanted store!"
            elif activity_type == "inventory_check":
                message = f"{emoji} **{ctx.author.display_name}** examined their treasure inventory!"
            else:
                message = f"{emoji} **{ctx.author.display_name}** visited the magical store!"
            
            embed = self.embed_builder.create_embed(
                description=message,
                color=0x32CD32
            )
            
            await history_channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error logging store activity: {e}")

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(StoreCommands(bot))