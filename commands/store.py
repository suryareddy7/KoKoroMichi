# Store Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from discord import ui
from typing import Optional, Dict, List
from datetime import datetime

from core.embed_utils import EmbedBuilder
from core.store_models import VipTierSpec, TransactionStatus
from services.store_service import StoreService
from utils.helpers import format_number, is_admin


class StorePaginationView(ui.View):
    """Pagination view for store catalog browsing."""

    def __init__(self, store_service: StoreService, user_id: str, category: Optional[str] = None, currency: str = "gold", per_page: int = 5):
        super().__init__(timeout=300.0)
        self.store_service = store_service
        self.user_id = user_id
        self.category = category
        self.currency = currency
        self.per_page = per_page
        self.current_page = 1
        self.total_pages = 1
        self.embed_builder = EmbedBuilder()

    async def fetch_page(self, page: int) -> Dict:
        """Fetch a page of items from the store."""
        return self.store_service.get_catalog(page=page, per_page=self.per_page, category=self.category)

    async def update_page_display(self, interaction: discord.Interaction, page: int) -> None:
        """Update the embed to show the requested page."""
        page_data = await self.fetch_page(page)
        items = page_data.get("items", [])
        self.total_pages = (page_data["total"] + self.per_page - 1) // self.per_page

        if not items:
            embed = self.embed_builder.warning_embed("No Items", "No items found on this page.")
            await interaction.response.edit_message(embed=embed, view=self)
            return

        embed = self.embed_builder.create_embed(
            title="🛍️ Store Catalog",
            description=f"Page {page}/{self.total_pages} | Category: {self.category or 'All'}",
            color=0x0099CC,
        )

        for item in items:
            # Compute price for this user (without VIP for now; extend with user VIP tier lookup)
            price_snap = self.store_service.preview_price(
                item["id"],
                quantity=1,
                vip_tier=None,
                currency=self.currency,
            )

            # Format price with indicators
            price_text = f"{format_number(price_snap.final_price)} {self.currency}"
            if price_snap.inflation_multiplier > 1.01:
                price_text += " 📈 (inflated)"

            stock_text = "∞" if item.get("stock") is None else format_number(item.get("stock", 0))

            embed.add_field(
                name=f"{item['name']} (ID: `{item['id']}`)",
                value=f"{item.get('description', '')}\n"
                f"💰 **{price_text}**\n"
                f"📦 Stock: {stock_text}",
                inline=False,
            )

        embed.set_footer(text=f"Use !buy <item_id> <quantity> [currency] to purchase | Page {page}/{self.total_pages}")
        self.current_page = page

        # Update button states
        self.update_buttons()

        await interaction.response.edit_message(embed=embed, view=self)

    def update_buttons(self) -> None:
        """Enable/disable navigation buttons based on current page."""
        self.prev_button.disabled = self.current_page <= 1
        self.next_button.disabled = self.current_page >= self.total_pages

    @ui.button(label="◀ Previous", style=discord.ButtonStyle.blurple)
    async def prev_button(self, interaction: discord.Interaction, button: ui.Button) -> None:
        await interaction.response.defer()
        if self.current_page > 1:
            await self.update_page_display(interaction, self.current_page - 1)

    @ui.button(label="Next ▶", style=discord.ButtonStyle.blurple)
    async def next_button(self, interaction: discord.Interaction, button: ui.Button) -> None:
        await interaction.response.defer()
        if self.current_page < self.total_pages:
            await self.update_page_display(interaction, self.current_page + 1)


class StoreCommands(commands.Cog):
    """Store system for buying items."""

    def __init__(self, bot):
        self.bot = bot
        self.store_service = StoreService()
        self.embed_builder = EmbedBuilder()

    @commands.command(name="store", aliases=["shop"])
    async def store_browse(self, ctx, page: int = 1, category: Optional[str] = None, currency: str = "gold"):
        """Browse the store catalog with pagination.

        Usage:
            !store [page] [category] [currency]
            !store 1 consumable gold
            !store 2 loot gems
        """
        try:
            # Validate page
            if page < 1:
                page = 1

            # Create pagination view
            view = StorePaginationView(self.store_service, str(ctx.author.id), category=category, currency=currency)

            # Fetch and display first page
            page_data = await view.fetch_page(page)
            items = page_data.get("items", [])
            view.total_pages = (page_data["total"] + view.per_page - 1) // view.per_page

            if not items:
                embed = self.embed_builder.warning_embed("No Items", "No items found on this page.")
                await ctx.send(embed=embed)
                return

            embed = self.embed_builder.create_embed(
                title="🛍️ Store Catalog",
                description=f"Page {page}/{view.total_pages} | Category: {category or 'All'}",
                color=0x0099CC,
            )

            for item in items:
                price_snap = self.store_service.preview_price(
                    item["id"],
                    quantity=1,
                    vip_tier=None,
                    currency=currency,
                )

                price_text = f"{format_number(price_snap.final_price)} {currency}"
                if price_snap.inflation_multiplier > 1.01:
                    price_text += " 📈 (inflated)"

                stock_text = "∞" if item.get("stock") is None else format_number(item.get("stock", 0))

                embed.add_field(
                    name=f"{item['name']} (ID: `{item['id']}`)",
                    value=f"{item.get('description', '')}\n"
                    f"💰 **{price_text}**\n"
                    f"📦 Stock: {stock_text}",
                    inline=False,
                )

            embed.set_footer(text=f"Use !buy <item_id> <quantity> [currency] to purchase | Page {page}/{view.total_pages}")
            view.current_page = page
            view.update_buttons()

            await ctx.send(embed=embed, view=view)

        except Exception as e:
            embed = self.embed_builder.error_embed("Store Error", f"Unable to load store: {str(e)}")
            await ctx.send(embed=embed)
            print(f"Store browse error: {e}")

    @commands.command(name="buy")
    async def buy_item(self, ctx, item_id: str, quantity: int = 1, currency: str = "gold"):
        """Purchase an item from the store.

        Usage:
            !buy health_potion_small 1 gold
            !buy treasure_chest 2 gems
        """
        try:
            quantity = max(1, quantity)
            user_id = str(ctx.author.id)

            # Load user VIP tier (if applicable; for now, no VIP)
            vip_tier = None

            # Execute purchase
            result = await self.store_service.purchase_item(
                user_id=user_id,
                item_id=item_id,
                quantity=quantity,
                currency=currency,
                vip_tier=vip_tier,
                simulate_provider_offline=False,
            )

            if not result.success:
                embed = self.embed_builder.warning_embed("Purchase Failed", result.message or "Unable to complete purchase.")
                await ctx.send(embed=embed)
                return

            # Success embed
            item = self.store_service.get_item(item_id)
            if not item:
                embed = self.embed_builder.error_embed("Item Error", "Item not found after purchase.")
                await ctx.send(embed=embed)
                return

            embed = self.embed_builder.success_embed(
                "Purchase Successful!",
                f"You bought {quantity}x **{item['name']}** for {format_number(result.new_balances[currency])} {currency}.",
            )
            embed.add_field(
                name="Transaction ID",
                value=f"`{result.tx_id}`",
                inline=False,
            )
            embed.add_field(
                name="New Balance",
                value=f"💰 Gold: {format_number(result.new_balances.get('gold', 0))}\n"
                f"💎 Gems: {format_number(result.new_balances.get('gems', 0))}",
                inline=True,
            )
            if "offline" in result.message.lower():
                embed.add_field(
                    name="⚠️ Offline Mode",
                    value="This purchase was recorded locally and will sync when the provider is available.",
                    inline=False,
                )

            await ctx.send(embed=embed)

        except Exception as e:
            embed = self.embed_builder.error_embed("Purchase Error", f"An error occurred: {str(e)}")
            await ctx.send(embed=embed)
            print(f"Buy item error: {e}")

    @commands.command(name="inventory")
    async def view_inventory(self, ctx):
        """View your current inventory."""
        try:
            from core.data_manager import data_manager

            user_id = str(ctx.author.id)
            user_data = data_manager.get_user_data(user_id)
            inventory = user_data.get("inventory", {})

            if not inventory:
                embed = self.embed_builder.warning_embed("Empty Inventory", "You don't have any items yet.")
                await ctx.send(embed=embed)
                return

            embed = self.embed_builder.create_embed(
                title="📦 Your Inventory",
                description=f"You have {len(inventory)} different item(s)",
                color=0x00AA00,
            )

            for item_id, quantity in sorted(inventory.items()):
                item = self.store_service.get_item(item_id)
                if item:
                    embed.add_field(
                        name=item["name"],
                        value=f"Quantity: **{quantity}**",
                        inline=True,
                    )
                else:
                    embed.add_field(
                        name=item_id,
                        value=f"Quantity: **{quantity}** (item not found in catalog)",
                        inline=True,
                    )

            embed.set_footer(text="Use !store to browse more items")
            await ctx.send(embed=embed)

        except Exception as e:
            embed = self.embed_builder.error_embed("Inventory Error", f"Unable to load inventory: {str(e)}")
            await ctx.send(embed=embed)
            print(f"Inventory error: {e}")

    @commands.command(name="ledger")
    async def view_ledger(self, ctx, limit: int = 10):
        """View your purchase history and transaction ledger."""
        try:
            user_id = str(ctx.author.id)
            txs = self.store_service.get_ledger(user_id, limit=limit, offset=0)

            if not txs:
                embed = self.embed_builder.info_embed("No Transactions", "You haven't made any purchases yet.")
                await ctx.send(embed=embed)
                return

            embed = self.embed_builder.create_embed(
                title="📋 Purchase Ledger",
                description=f"Last {len(txs)} transactions",
                color=0x9370DB,
            )

            for tx in txs[-10:]:  # Show last 10
                created = tx.get("created_at", "Unknown")
                status = tx.get("status", "UNKNOWN")
                item_id = tx.get("item_id", "?")
                qty = tx.get("quantity", 1)
                currency = tx.get("currency", "gold")

                status_emoji = {
                    "COMMITTED": "✅",
                    "PENDING": "⏳",
                    "PENDING_OFFLINE": "📡",
                    "FAILED": "❌",
                }.get(status, "❓")

                embed.add_field(
                    name=f"{status_emoji} {item_id} × {qty}",
                    value=f"Status: **{status}**\nTime: {created}\nCurrency: {currency}",
                    inline=False,
                )

            embed.set_footer(text="Transaction ID can be used for support inquiries")
            await ctx.send(embed=embed)

        except Exception as e:
            embed = self.embed_builder.error_embed("Ledger Error", f"Unable to load ledger: {str(e)}")
            await ctx.send(embed=embed)
            print(f"Ledger error: {e}")

    # ===== ADMIN COMMANDS =====

    @commands.command(name="store_restock", hidden=True)
    @commands.check(is_admin)
    async def admin_restock(self, ctx, item_id: str, amount: int):
        """[ADMIN] Restock an item."""
        try:
            if amount < 0:
                embed = self.embed_builder.warning_embed("Invalid Amount", "Amount must be positive.")
                await ctx.send(embed=embed)
                return

            updated = self.store_service.restock_item(str(ctx.author.id), item_id, amount)
            embed = self.embed_builder.success_embed(
                "Item Restocked",
                f"**{updated['name']}** stock is now {format_number(updated.get('stock', 'infinite'))}",
            )
            await ctx.send(embed=embed)

        except ValueError as e:
            embed = self.embed_builder.warning_embed("Error", str(e))
            await ctx.send(embed=embed)
        except Exception as e:
            embed = self.embed_builder.error_embed("Admin Error", str(e))
            await ctx.send(embed=embed)

    @commands.command(name="store_setprice", hidden=True)
    @commands.check(is_admin)
    async def admin_setprice(self, ctx, item_id: str, gold: int = 0, gems: int = 0):
        """[ADMIN] Set item price (both gold and gems)."""
        try:
            if gold < 0 or gems < 0:
                embed = self.embed_builder.warning_embed("Invalid Price", "Prices must be non-negative.")
                await ctx.send(embed=embed)
                return

            new_price = {"gold": gold, "gems": gems}
            updated = self.store_service.set_price(str(ctx.author.id), item_id, new_price)

            embed = self.embed_builder.success_embed(
                "Price Updated",
                f"**{updated['name']}** price: {gold} gold, {gems} gems",
            )
            await ctx.send(embed=embed)

        except ValueError as e:
            embed = self.embed_builder.warning_embed("Error", str(e))
            await ctx.send(embed=embed)
        except Exception as e:
            embed = self.embed_builder.error_embed("Admin Error", str(e))
            await ctx.send(embed=embed)

    @commands.command(name="store_sync", hidden=True)
    @commands.check(is_admin)
    async def admin_sync_pending(self, ctx):
        """[ADMIN] Sync pending offline transactions to the provider."""
        try:
            report = self.store_service.sync_pending_transactions()

            embed = self.embed_builder.create_embed(
                title="Sync Report",
                description="Pending transaction sync completed",
                color=0x0099CC,
            )
            embed.add_field(name="Applied", value=format_number(report["applied"]), inline=True)
            embed.add_field(name="Retried", value=format_number(report["retry"]), inline=True)
            embed.add_field(name="Failed", value=format_number(report["failed"]), inline=True)

            if report["errors"]:
                error_text = "\n".join(report["errors"][:5])  # Show first 5 errors
                embed.add_field(name="Errors", value=f"```{error_text}```", inline=False)

            await ctx.send(embed=embed)

        except Exception as e:
            embed = self.embed_builder.error_embed("Sync Error", str(e))
            await ctx.send(embed=embed)


async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(StoreCommands(bot))
