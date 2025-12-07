# Economy and Investment Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List
import random
from datetime import datetime, timedelta

from core.data_manager import data_manager
from core.provider_manager import get_user_async, save_user_async
from core.embed_utils import EmbedBuilder
from utils.helpers import format_number, validate_amount, is_on_cooldown

class EconomyCommands(commands.Cog):
    """Investment system, auction house, and business management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        
        # Business types for investment
        self.business_types = {
            "cafe": {
                "name": "Waifu Café",
                "cost": 10000,
                "daily_income": 500,
                "description": "A cozy café where waifus serve customers",
                "requirements": {"level": 5, "waifus": 3}
            },
            "dojo": {
                "name": "Training Dojo",
                "cost": 25000,
                "daily_income": 800,
                "description": "Training facility that generates income from students",
                "requirements": {"level": 10, "battles_won": 20}
            },
            "shop": {
                "name": "Enchanted Shop",
                "cost": 50000,
                "daily_income": 1500,
                "description": "Magical shop selling rare items and artifacts",
                "requirements": {"level": 15, "gold": 50000}
            },
            "guild_hall": {
                "name": "Adventure Guild",
                "cost": 100000,
                "daily_income": 3000,
                "description": "Hub for adventurers providing quest services",
                "requirements": {"level": 20, "waifus": 10, "battles_won": 50}
            },
            "spa": {
                "name": "Waifu Spa",
                "cost": 75000,
                "daily_income": 2000,
                "description": "Relaxing spa that pampers waifus and customers",
                "requirements": {"level": 18, "waifus": 8}
            }
        }
    
    @commands.group(name="invest", invoke_without_command=True)
    async def invest_group(self, ctx, business_type: str = None):
        """Investment system for passive income generation"""
        try:
            if business_type is None:
                # Show investment menu
                embed = self.create_investment_menu_embed()
                await ctx.send(embed=embed)
                return
            
            # Purchase specific business
            await self.purchase_business(ctx, business_type.lower())
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Investment Error",
                "Unable to process investment. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Investment command error: {e}")
    
    @commands.command(name="businesses", aliases=["portfolio"])
    async def view_businesses(self, ctx):
        """View your business portfolio and accumulated income"""
        try:
            try:
                user_data = await get_user_async(str(ctx.author.id))
                if user_data is None:
                    user_data = data_manager.get_user_data(str(ctx.author.id))
            except Exception:
                user_data = data_manager.get_user_data(str(ctx.author.id))
            investments = user_data.get("investments", {})
            
            if not investments:
                embed = self.embed_builder.info_embed(
                    "No Investments",
                    "You don't own any businesses yet! Use `!invest` to get started."
                )
                await ctx.send(embed=embed)
                return
            
            # Calculate total accumulated income
            total_value = 0
            total_daily_income = 0
            accumulated_income = 0
            
            for business_id, business_data in investments.items():
                business_info = self.business_types.get(business_id, {})
                if not business_info:
                    continue
                
                level = business_data.get("level", 1)
                daily_income = business_info["daily_income"] * level
                total_daily_income += daily_income
                total_value += business_info["cost"] * level
                
                # Calculate accumulated income since last collection
                last_collected = business_data.get("last_collected")
                if last_collected:
                    try:
                        last_time = datetime.fromisoformat(last_collected)
                        hours_passed = (datetime.now() - last_time).total_seconds() / 3600
                        hourly_income = daily_income / 24
                        accumulated_income += int(hourly_income * min(hours_passed, 72))  # Max 3 days
                    except:
                        pass
            
            # Create portfolio embed
            embed = self.create_portfolio_embed(investments, total_value, total_daily_income, accumulated_income)
            
            # Add collection button if there's income to collect
            if accumulated_income > 0:
                view = CollectionView(str(ctx.author.id), accumulated_income)
                await ctx.send(embed=embed, view=view)
            else:
                await ctx.send(embed=embed)
                
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Portfolio Error",
                "Unable to load your business portfolio."
            )
            await ctx.send(embed=error_embed)
            print(f"Businesses command error: {e}")
    
    @commands.command(name="collect")
    async def collect_income(self, ctx):
        """Collect accumulated income from all businesses"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            investments = user_data.get("investments", {})
            
            if not investments:
                embed = self.embed_builder.info_embed(
                    "No Businesses",
                    "You don't have any businesses to collect from!"
                )
                await ctx.send(embed=embed)
                return
            
            total_collected = 0
            business_details = []
            
            for business_id, business_data in investments.items():
                business_info = self.business_types.get(business_id, {})
                if not business_info:
                    continue
                
                level = business_data.get("level", 1)
                daily_income = business_info["daily_income"] * level
                
                # Calculate income since last collection
                last_collected = business_data.get("last_collected")
                current_time = datetime.now()
                
                if last_collected:
                    try:
                        last_time = datetime.fromisoformat(last_collected)
                        hours_passed = (current_time - last_time).total_seconds() / 3600
                    except:
                        hours_passed = 24  # Default to 24 hours if error
                else:
                    hours_passed = 24  # First collection
                
                # Cap at 72 hours (3 days) to prevent abuse
                hours_passed = min(hours_passed, 72)
                hourly_income = daily_income / 24
                income = int(hourly_income * hours_passed)
                
                if income > 0:
                    total_collected += income
                    business_details.append({
                        "name": business_info["name"],
                        "income": income,
                        "hours": hours_passed
                    })
                
                # Update last collected time
                business_data["last_collected"] = current_time.isoformat()
            
            if total_collected <= 0:
                embed = self.embed_builder.warning_embed(
                    "No Income Available",
                    "There's no income to collect at this time. Check back later!"
                )
                await ctx.send(embed=embed)
                return
            
            # Add gold to user
            user_data["gold"] = user_data.get("gold", 0) + total_collected
            try:
                await save_user_async(str(ctx.author.id), user_data)
            except Exception:
                data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Create collection result embed
            embed = self.create_collection_embed(business_details, total_collected)
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Collection Error",
                "Unable to collect income. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Collect command error: {e}")
    
    @commands.group(name="auction", invoke_without_command=True)
    async def auction_group(self, ctx):
        """Auction house system for trading items"""
        embed = self.embed_builder.create_embed(
            title="🏪 Auction House",
            description="Trade items with other players!",
            color=0xFFD700
        )
        
        embed.add_field(
            name="📋 Commands",
            value="• `!auction create <item> <price>` - List item for sale\n"
                  "• `!auction list [category]` - Browse auctions\n"
                  "• `!auction bid <id> <amount>` - Bid on auction\n"
                  "• `!auction cancel <id>` - Cancel your auction",
            inline=False
        )
        
        embed.add_field(
            name="💡 Tips",
            value="• Auctions last 24 hours\n"
                  "• 5% fee on successful sales\n"
                  "• Outbid protection: +10% minimum",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @auction_group.command(name="create")
    async def create_auction(self, ctx, item_name: str, starting_price: int):
        """Create a new auction listing"""
        try:
            if starting_price <= 0:
                embed = self.embed_builder.error_embed(
                    "Invalid Price",
                    "Starting price must be greater than 0."
                )
                await ctx.send(embed=embed)
                return
            
            user_data = data_manager.get_user_data(str(ctx.author.id))
            inventory = user_data.get("inventory", {})
            
            # Find item in inventory
            found_item = None
            for inv_item in inventory.keys():
                if item_name.lower() in inv_item.lower():
                    found_item = inv_item
                    break
            
            if not found_item or inventory[found_item] <= 0:
                embed = self.embed_builder.error_embed(
                    "Item Not Found",
                    f"You don't have '{item_name}' in your inventory."
                )
                await ctx.send(embed=embed)
                return
            
            # Create auction listing
            auction_id = f"auction_{ctx.author.id}_{int(datetime.now().timestamp())}"
            auction_data = {
                "id": auction_id,
                "seller_id": str(ctx.author.id),
                "seller_name": ctx.author.display_name,
                "item_name": found_item,
                "starting_price": starting_price,
                "current_bid": starting_price,
                "highest_bidder": None,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
                "status": "active"
            }
            
            # Remove item from inventory temporarily
            inventory[found_item] -= 1
            if inventory[found_item] <= 0:
                del inventory[found_item]
            
            # Save auction (in a real implementation, this would go to a separate auctions file)
            auctions = user_data.setdefault("active_auctions", {})
            auctions[auction_id] = auction_data
            
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            embed = self.embed_builder.success_embed(
                "Auction Created!",
                f"Successfully listed **{found_item}** for auction!"
            )
            
            embed.add_field(
                name="📊 Auction Details",
                value=f"Item: {found_item}\n"
                      f"Starting Price: {format_number(starting_price)} gold\n"
                      f"Duration: 24 hours\n"
                      f"Auction ID: `{auction_id[:12]}...`",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Auction Creation Error",
                "Unable to create auction. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Create auction error: {e}")
    
    async def purchase_business(self, ctx, business_type: str):
        """Purchase a business for investment"""
        try:
            if business_type not in self.business_types:
                available = ", ".join(self.business_types.keys())
                embed = self.embed_builder.error_embed(
                    "Invalid Business Type",
                    f"Available businesses: {available}"
                )
                await ctx.send(embed=embed)
                return
            
            user_data = data_manager.get_user_data(str(ctx.author.id))
            business_info = self.business_types[business_type]
            
            # Check requirements
            requirements_met, missing_req = self.check_business_requirements(user_data, business_info)
            if not requirements_met:
                embed = self.create_requirements_embed(business_info, missing_req)
                await ctx.send(embed=embed)
                return
            
            # Check if user already owns this business
            investments = user_data.get("investments", {})
            if business_type in investments:
                # Upgrade existing business
                current_level = investments[business_type].get("level", 1)
                if current_level >= 5:
                    embed = self.embed_builder.warning_embed(
                        "Max Level Reached",
                        f"Your {business_info['name']} is already at maximum level (5)!"
                    )
                    await ctx.send(embed=embed)
                    return
                
                upgrade_cost = business_info["cost"] * (current_level + 1)
                if user_data.get("gold", 0) < upgrade_cost:
                    embed = self.embed_builder.error_embed(
                        "Insufficient Gold",
                        f"Upgrading to level {current_level + 1} costs {format_number(upgrade_cost)} gold."
                    )
                    await ctx.send(embed=embed)
                    return
                
                # Perform upgrade
                user_data["gold"] -= upgrade_cost
                investments[business_type]["level"] = current_level + 1
                
                embed = self.embed_builder.success_embed(
                    "Business Upgraded!",
                    f"Upgraded {business_info['name']} to level {current_level + 1}!"
                )
                
                new_daily = business_info["daily_income"] * (current_level + 1)
                embed.add_field(
                    name="📈 New Stats",
                    value=f"Level: {current_level + 1}\n"
                          f"Daily Income: {format_number(new_daily)} gold\n"
                          f"Upgrade Cost: {format_number(upgrade_cost)} gold",
                    inline=False
                )
                
            else:
                # Purchase new business
                cost = business_info["cost"]
                if user_data.get("gold", 0) < cost:
                    embed = self.embed_builder.error_embed(
                        "Insufficient Gold",
                        f"This business costs {format_number(cost)} gold."
                    )
                    await ctx.send(embed=embed)
                    return
                
                # Purchase business
                user_data["gold"] -= cost
                investments[business_type] = {
                    "level": 1,
                    "purchased_at": datetime.now().isoformat(),
                    "last_collected": datetime.now().isoformat()
                }
                
                embed = self.embed_builder.success_embed(
                    "Business Purchased!",
                    f"Congratulations! You now own **{business_info['name']}**!"
                )
                
                embed.add_field(
                    name="💼 Business Details",
                    value=f"Cost: {format_number(cost)} gold\n"
                          f"Daily Income: {format_number(business_info['daily_income'])} gold\n"
                          f"Description: {business_info['description']}",
                    inline=False
                )
            
            user_data["investments"] = investments
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Purchase Error",
                "Unable to purchase business. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Purchase business error: {e}")
    
    def check_business_requirements(self, user_data: Dict, business_info: Dict) -> tuple:
        """Check if user meets business requirements"""
        requirements = business_info.get("requirements", {})
        missing = {}
        
        for req_type, req_value in requirements.items():
            if req_type == "level":
                if user_data.get("level", 1) < req_value:
                    missing["level"] = req_value
            elif req_type == "waifus":
                if len(user_data.get("claimed_waifus", [])) < req_value:
                    missing["waifus"] = req_value
            elif req_type == "battles_won":
                battle_stats = user_data.get("battle_stats", {})
                if battle_stats.get("battles_won", 0) < req_value:
                    missing["battles_won"] = req_value
            elif req_type == "gold":
                if user_data.get("gold", 0) < req_value:
                    missing["gold"] = req_value
        
        return len(missing) == 0, missing
    
    def create_investment_menu_embed(self) -> discord.Embed:
        """Create investment menu embed"""
        embed = self.embed_builder.create_embed(
            title="💼 Investment Opportunities",
            description="Build your business empire and generate passive income!",
            color=0x32CD32
        )
        
        for business_id, business_info in self.business_types.items():
            cost = business_info["cost"]
            daily_income = business_info["daily_income"]
            roi_days = cost / daily_income
            
            embed.add_field(
                name=f"🏪 {business_info['name']}",
                value=f"{business_info['description']}\n"
                      f"💰 Cost: {format_number(cost)} gold\n"
                      f"📈 Daily: {format_number(daily_income)} gold\n"
                      f"⏱️ ROI: {roi_days:.1f} days",
                inline=True
            )
        
        embed.add_field(
            name="💡 Investment Tips",
            value="• Businesses generate income every hour\n"
                  "• Collect regularly with `!collect`\n"
                  "• Upgrade businesses to increase income\n"
                  "• Each business has different requirements",
            inline=False
        )
        
        return embed
    
    def create_portfolio_embed(self, investments: Dict, total_value: int, 
                             daily_income: int, accumulated: int) -> discord.Embed:
        """Create business portfolio embed"""
        embed = self.embed_builder.create_embed(
            title="💼 Your Business Portfolio",
            color=0x4169E1
        )
        
        portfolio_text = ""
        for business_id, business_data in investments.items():
            business_info = self.business_types.get(business_id, {})
            if business_info:
                level = business_data.get("level", 1)
                daily = business_info["daily_income"] * level
                portfolio_text += f"**{business_info['name']}** (Lv.{level})\n"
                portfolio_text += f"  Daily Income: {format_number(daily)} gold\n\n"
        
        embed.add_field(
            name="🏢 Your Businesses",
            value=portfolio_text or "No businesses owned",
            inline=False
        )
        
        embed.add_field(
            name="📊 Portfolio Summary",
            value=f"Total Value: {format_number(total_value)} gold\n"
                  f"Daily Income: {format_number(daily_income)} gold\n"
                  f"Available to Collect: {format_number(accumulated)} gold",
            inline=False
        )
        
        if accumulated > 0:
            embed.add_field(
                name="💰 Collection Ready",
                value="Click the button below to collect your income!",
                inline=False
            )
        
        return embed
    
    def create_collection_embed(self, business_details: List[Dict], total: int) -> discord.Embed:
        """Create income collection embed"""
        embed = self.embed_builder.success_embed(
            "Income Collected!",
            f"Successfully collected {format_number(total)} gold!"
        )
        
        details_text = ""
        for business in business_details:
            hours = business["hours"]
            details_text += f"**{business['name']}**\n"
            details_text += f"  {format_number(business['income'])} gold ({hours:.1f}h)\n\n"
        
        embed.add_field(
            name="💰 Collection Details",
            value=details_text,
            inline=False
        )
        
        return embed
    
    def create_requirements_embed(self, business_info: Dict, missing: Dict) -> discord.Embed:
        """Create business requirements embed"""
        embed = self.embed_builder.error_embed(
            "Requirements Not Met",
            f"You don't meet the requirements for {business_info['name']}"
        )
        
        requirements_text = ""
        all_reqs = business_info.get("requirements", {})
        
        for req_type, req_value in all_reqs.items():
            status = "❌" if req_type in missing else "✅"
            req_name = req_type.replace("_", " ").title()
            requirements_text += f"{status} {req_name}: {req_value}\n"
        
        embed.add_field(
            name="📋 Requirements",
            value=requirements_text,
            inline=False
        )
        
        return embed


class CollectionView(discord.ui.View):
    """Quick collection button for business income"""
    
    def __init__(self, user_id: str, amount: int):
        super().__init__(timeout=300.0)
        self.user_id = user_id
        self.amount = amount
    
    @discord.ui.button(label=f"💰 Collect Income", style=discord.ButtonStyle.success)
    async def collect_income(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Collect business income"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This is not your portfolio!", ephemeral=True)
            return
        
        try:
            user_data = data_manager.get_user_data(self.user_id)
            user_data["gold"] = user_data.get("gold", 0) + self.amount
            
            # Update last collected times
            investments = user_data.get("investments", {})
            current_time = datetime.now().isoformat()
            for business_data in investments.values():
                business_data["last_collected"] = current_time
            
            data_manager.save_user_data(self.user_id, user_data)
            
            embed = EmbedBuilder.success_embed(
                "Income Collected!",
                f"Collected {format_number(self.amount)} gold from your businesses!"
            )
            
            # Disable button
            button.disabled = True
            button.label = "✅ Collected"
            
            await interaction.response.edit_message(embed=embed, view=self)
            
        except Exception as e:
            await interaction.response.send_message("❌ Error collecting income.", ephemeral=True)


async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(EconomyCommands(bot))