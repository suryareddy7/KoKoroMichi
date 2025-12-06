# Inventory Management Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List
import asyncio

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from utils.helpers import format_number, validate_amount

class InventoryCommands(commands.Cog):
    """Inventory and item management commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
    
    @commands.command(name="inventory", aliases=["inv", "items"])
    async def inventory(self, ctx, category: Optional[str] = None):
        """View your inventory with optional category filtering"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            inventory = user_data.get("inventory", {})
            
            if not inventory:
                embed = self.embed_builder.info_embed(
                    "Empty Inventory",
                    "Your inventory is empty! Battle, craft, or complete quests to get items."
                )
                await ctx.send(embed=embed)
                return
            
            # Filter by category if specified
            if category:
                filtered_items = self.filter_items_by_category(inventory, category)
                if not filtered_items:
                    embed = self.embed_builder.warning_embed(
                        "Category Not Found",
                        f"No items found in category: {category}\n"
                        f"Available categories: {', '.join(self.get_item_categories(inventory))}"
                    )
                    await ctx.send(embed=embed)
                    return
                inventory = filtered_items
            
            # Create paginated inventory view
            view = InventoryView(inventory, category)
            embed = view.create_embed()
            
            await ctx.send(embed=embed, view=view)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Inventory Error",
                "Unable to load your inventory. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Inventory command error: {e}")
    
    @commands.command(name="use")
    async def use_item(self, ctx, *, item_name: str):
        """Use an item from your inventory"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            inventory = user_data.get("inventory", {})
            
            # Find item (case-insensitive)
            actual_item_name = None
            for name in inventory.keys():
                if name.lower() == item_name.lower():
                    actual_item_name = name
                    break
            
            if not actual_item_name:
                embed = self.embed_builder.error_embed(
                    "Item Not Found",
                    f"You don't have '{item_name}' in your inventory."
                )
                await ctx.send(embed=embed)
                return
            
            item_count = inventory[actual_item_name]
            if item_count <= 0:
                embed = self.embed_builder.error_embed(
                    "No Items Available",
                    f"You don't have any '{actual_item_name}' to use."
                )
                await ctx.send(embed=embed)
                return
            
            # Use the item
            result = await self.process_item_use(ctx, actual_item_name, user_data)
            
            if result["success"]:
                # Remove item from inventory
                inventory[actual_item_name] -= 1
                if inventory[actual_item_name] <= 0:
                    del inventory[actual_item_name]
                
                # Update user data
                user_data["inventory"] = inventory
                if result.get("user_updates"):
                    user_data.update(result["user_updates"])
                
                data_manager.save_user_data(str(ctx.author.id), user_data)
                
                embed = self.embed_builder.success_embed(
                    "Item Used Successfully",
                    result["message"]
                )
            else:
                embed = self.embed_builder.error_embed(
                    "Cannot Use Item",
                    result["message"]
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Use Item Error",
                "Unable to use the item. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Use item command error: {e}")
    
    @commands.command(name="give")
    async def give_item(self, ctx, member: discord.Member, *, item_name: str):
        """Give an item to another user"""
        try:
            if member == ctx.author:
                embed = self.embed_builder.error_embed(
                    "Invalid Target",
                    "You cannot give items to yourself!"
                )
                await ctx.send(embed=embed)
                return
            
            if member.bot:
                embed = self.embed_builder.error_embed(
                    "Invalid Target",
                    "You cannot give items to bots!"
                )
                await ctx.send(embed=embed)
                return
            
            # Get user inventories
            sender_data = data_manager.get_user_data(str(ctx.author.id))
            receiver_data = data_manager.get_user_data(str(member.id))
            
            sender_inventory = sender_data.get("inventory", {})
            receiver_inventory = receiver_data.get("inventory", {})
            
            # Find item in sender's inventory
            actual_item_name = None
            for name in sender_inventory.keys():
                if name.lower() == item_name.lower():
                    actual_item_name = name
                    break
            
            if not actual_item_name or sender_inventory[actual_item_name] <= 0:
                embed = self.embed_builder.error_embed(
                    "Item Not Available",
                    f"You don't have '{item_name}' to give."
                )
                await ctx.send(embed=embed)
                return
            
            # Create confirmation view
            view = GiveConfirmationView(ctx.author, member, actual_item_name, sender_data, receiver_data)
            embed = self.embed_builder.create_embed(
                title="🎁 Confirm Gift",
                description=f"Are you sure you want to give **{actual_item_name}** to {member.mention}?",
                color=0xFFD700
            )
            
            await ctx.send(embed=embed, view=view)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Give Item Error",
                "Unable to give the item. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Give item command error: {e}")
    
    async def process_item_use(self, ctx, item_name: str, user_data: dict) -> dict:
        """Process the effects of using an item"""
        item_effects = {
            # Health Potions
            "Health Potion Small": {"type": "heal", "amount": 50},
            "Health Potion": {"type": "heal", "amount": 100},
            "Health Potion Large": {"type": "heal", "amount": 200},
            
            # Experience Items
            "Experience Scroll": {"type": "xp", "amount": 500},
            "Experience Tome": {"type": "xp", "amount": 1000},
            "Ancient Codex": {"type": "xp", "amount": 2500},
            
            # Currency Items
            "Gold Pouch": {"type": "gold", "amount": 1000},
            "Treasure Chest": {"type": "gold", "amount": 5000},
            "Gem Shard": {"type": "gems", "amount": 10},
            "Precious Gem": {"type": "gems", "amount": 50},
            
            # Boost Items
            "Lucky Charm": {"type": "buff", "effect": "luck_boost", "duration": 3600},
            "Battle Banner": {"type": "buff", "effect": "battle_boost", "duration": 3600},
            "Crafting Kit": {"type": "buff", "effect": "crafting_boost", "duration": 3600},
        }
        
        effect = item_effects.get(item_name)
        if not effect:
            return {
                "success": False,
                "message": f"'{item_name}' cannot be used directly. It might be a crafting material or equipment."
            }
        
        user_updates = {}
        
        if effect["type"] == "heal":
            # Heal user (if health system implemented)
            current_hp = user_data.get("hp", 100)
            max_hp = 100  # Could be calculated based on level/stats
            heal_amount = min(effect["amount"], max_hp - current_hp)
            
            if heal_amount <= 0:
                return {
                    "success": False,
                    "message": "You are already at full health!"
                }
            
            user_updates["hp"] = current_hp + heal_amount
            message = f"Restored {heal_amount} HP! Current HP: {user_updates['hp']}/{max_hp}"
        
        elif effect["type"] == "xp":
            current_xp = user_data.get("xp", 0)
            user_updates["xp"] = current_xp + effect["amount"]
            
            # Check for level up
            from utils.helpers import calculate_level_from_xp
            old_level = user_data.get("level", 1)
            new_level = calculate_level_from_xp(user_updates["xp"])
            
            if new_level > old_level:
                user_updates["level"] = new_level
                message = f"Gained {format_number(effect['amount'])} XP and leveled up to {new_level}! 🎉"
            else:
                message = f"Gained {format_number(effect['amount'])} XP!"
        
        elif effect["type"] == "gold":
            current_gold = user_data.get("gold", 0)
            user_updates["gold"] = current_gold + effect["amount"]
            message = f"Gained {format_number(effect['amount'])} gold! 💰"
        
        elif effect["type"] == "gems":
            current_gems = user_data.get("gems", 0)
            user_updates["gems"] = current_gems + effect["amount"]
            message = f"Gained {format_number(effect['amount'])} gems! 💎"
        
        elif effect["type"] == "buff":
            # Apply temporary buff (would need buff system)
            message = f"Applied {effect['effect']} for {effect['duration']} seconds! ✨"
        
        else:
            return {
                "success": False,
                "message": "Unknown item effect."
            }
        
        return {
            "success": True,
            "message": message,
            "user_updates": user_updates
        }
    
    def filter_items_by_category(self, inventory: dict, category: str) -> dict:
        """Filter inventory items by category"""
        categories = {
            "potions": ["potion", "elixir", "brew"],
            "materials": ["ore", "cloth", "shard", "essence", "fragment"],
            "scrolls": ["scroll", "tome", "codex", "book"],
            "gems": ["gem", "crystal", "stone"],
            "equipment": ["sword", "armor", "shield", "weapon"],
            "consumables": ["potion", "scroll", "charm", "banner"]
        }
        
        category_keywords = categories.get(category.lower(), [category.lower()])
        
        filtered = {}
        for item_name, count in inventory.items():
            if any(keyword in item_name.lower() for keyword in category_keywords):
                filtered[item_name] = count
        
        return filtered
    
    def get_item_categories(self, inventory: dict) -> List[str]:
        """Get all available item categories"""
        categories = set()
        
        category_map = {
            "potions": ["potion", "elixir"],
            "materials": ["ore", "cloth", "shard"],
            "scrolls": ["scroll", "tome"],
            "gems": ["gem", "crystal"],
            "equipment": ["sword", "armor"]
        }
        
        for item_name in inventory.keys():
            for category, keywords in category_map.items():
                if any(keyword in item_name.lower() for keyword in keywords):
                    categories.add(category)
        
        return sorted(list(categories))


class InventoryView(discord.ui.View):
    """Paginated inventory view"""
    
    def __init__(self, inventory: dict, category: str = None):
        super().__init__(timeout=300.0)
        self.inventory = inventory
        self.category = category
        self.page = 0
        self.per_page = 10
        self.items = list(inventory.items())
        self.max_page = max(0, (len(self.items) - 1) // self.per_page)
        
        self.update_buttons()
    
    def update_buttons(self):
        """Update button states"""
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.custom_id == "prev":
                    item.disabled = (self.page <= 0)
                elif item.custom_id == "next":
                    item.disabled = (self.page >= self.max_page)
    
    def create_embed(self) -> discord.Embed:
        """Create inventory embed for current page"""
        title = "🎒 Inventory"
        if self.category:
            title += f" - {self.category.title()}"
        
        embed = EmbedBuilder.create_embed(
            title=title,
            description=f"Page {self.page + 1}/{self.max_page + 1}",
            color=0x9932CC
        )
        
        start_idx = self.page * self.per_page
        end_idx = start_idx + self.per_page
        page_items = self.items[start_idx:end_idx]
        
        if page_items:
            items_text = ""
            for item_name, count in page_items:
                items_text += f"**{item_name}** x{count}\n"
            
            embed.add_field(
                name="📦 Items",
                value=items_text or "No items found",
                inline=False
            )
        else:
            embed.description = "No items found."
        
        # Add usage tip
        embed.add_field(
            name="💡 Usage Tips",
            value="• Use `!use <item_name>` to use items\n"
                  "• Use `!give @user <item_name>` to gift items\n"
                  "• Use `!inventory <category>` to filter by category",
            inline=False
        )
        
        return embed
    
    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.primary, custom_id="prev")
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            self.update_buttons()
            embed = self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.primary, custom_id="next")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.max_page:
            self.page += 1
            self.update_buttons()
            embed = self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()


class GiveConfirmationView(discord.ui.View):
    """Confirmation view for giving items"""
    
    def __init__(self, sender: discord.Member, receiver: discord.Member, 
                 item_name: str, sender_data: dict, receiver_data: dict):
        super().__init__(timeout=60.0)
        self.sender = sender
        self.receiver = receiver
        self.item_name = item_name
        self.sender_data = sender_data
        self.receiver_data = receiver_data
    
    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.green)
    async def confirm_give(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirm the gift"""
        if interaction.user != self.sender:
            await interaction.response.send_message("Only the sender can confirm this action.", ephemeral=True)
            return
        
        try:
            # Transfer item
            sender_inventory = self.sender_data.get("inventory", {})
            receiver_inventory = self.receiver_data.get("inventory", {})
            
            # Remove from sender
            sender_inventory[self.item_name] -= 1
            if sender_inventory[self.item_name] <= 0:
                del sender_inventory[self.item_name]
            
            # Add to receiver
            receiver_inventory[self.item_name] = receiver_inventory.get(self.item_name, 0) + 1
            
            # Update data
            self.sender_data["inventory"] = sender_inventory
            self.receiver_data["inventory"] = receiver_inventory
            
            data_manager.save_user_data(str(self.sender.id), self.sender_data)
            data_manager.save_user_data(str(self.receiver.id), self.receiver_data)
            
            embed = EmbedBuilder.success_embed(
                "Gift Sent! 🎁",
                f"{self.sender.mention} gave **{self.item_name}** to {self.receiver.mention}!"
            )
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
            
        except Exception as e:
            await interaction.response.send_message("❌ Error processing gift.", ephemeral=True)
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.red)
    async def cancel_give(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel the gift"""
        if interaction.user != self.sender:
            await interaction.response.send_message("Only the sender can cancel this action.", ephemeral=True)
            return
        
        embed = EmbedBuilder.info_embed("Gift Cancelled", "The gift was cancelled.")
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)


async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(InventoryCommands(bot))