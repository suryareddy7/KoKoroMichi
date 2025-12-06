# Guild System Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List
import random
from datetime import datetime, timedelta

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from utils.helpers import format_number, validate_amount, generate_unique_id
from utils.channel_restriction import check_channel_restriction

class GuildCommands(commands.Cog):
    """Guild management and faction warfare system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        
        # Faction system
        self.factions = {
            "celestial": {
                "name": "Celestial Order",
                "description": "Guardians of light and justice",
                "bonuses": {"battle_xp": 1.2, "summon_luck": 1.1},
                "color": 0xFFD700,
                "emoji": "☀️"
            },
            "shadow": {
                "name": "Shadow Covenant",
                "description": "Masters of darkness and stealth",
                "bonuses": {"critical_chance": 1.3, "stealth_bonus": 1.2},
                "color": 0x4B0082,
                "emoji": "🌙"
            },
            "elemental": {
                "name": "Elemental Harmony",
                "description": "Wielders of natural forces",
                "bonuses": {"elemental_damage": 1.25, "mana_regen": 1.15},
                "color": 0x228B22,
                "emoji": "🌿"
            },
            "arcane": {
                "name": "Arcane Scholars",
                "description": "Seekers of magical knowledge",
                "bonuses": {"spell_power": 1.3, "research_speed": 1.2},
                "color": 0x9370DB,
                "emoji": "🔮"
            }
        }
        
        # Guild level benefits
        self.guild_benefits = {
            1: {"max_members": 10, "bank_limit": 50000, "perks": ["Basic Guild Hall"]},
            2: {"max_members": 15, "bank_limit": 100000, "perks": ["Training Grounds", "5% Battle XP Bonus"]},
            3: {"max_members": 20, "bank_limit": 200000, "perks": ["Guild Store", "10% Gold Bonus"]},
            4: {"max_members": 30, "bank_limit": 500000, "perks": ["War Room", "Territory Control"]},
            5: {"max_members": 50, "bank_limit": 1000000, "perks": ["Elite Quarters", "Legendary Quests"]}
        }
    
    @commands.group(name="guild", invoke_without_command=True)
    async def guild_group(self, ctx):
        """Guild system main command"""
        if ctx.invoked_subcommand is None:
            embed = self.create_guild_overview_embed()
            await ctx.send(embed=embed)
    
    @guild_group.command(name="create")
    async def create_guild(self, ctx, guild_name: str, faction: str = None):
        """Create a new guild with faction alignment"""
        # Enforce channel restrictions for guild commands
        restriction_result = await check_channel_restriction(
            ctx, ["guild-hall", "guild-chronicles", "faction-realm"], ctx.bot
        )
        if not restriction_result:
            await ctx.send("🏰 Guild commands can only be used in guild channels!", delete_after=10)
            return
        try:
            if not guild_name or len(guild_name.strip()) < 3:
                embed = self.embed_builder.error_embed(
                    "Invalid Guild Name",
                    "Guild name must be at least 3 characters long."
                )
                await ctx.send(embed=embed)
                return
            
            if faction and faction.lower() not in self.factions:
                available_factions = ", ".join(self.factions.keys())
                embed = self.embed_builder.error_embed(
                    "Invalid Faction",
                    f"Available factions: {available_factions}"
                )
                await ctx.send(embed=embed)
                return
            
            user_data = data_manager.get_user_data(str(ctx.author.id))
            
            # Check if user is already in a guild
            if user_data.get("guild_id"):
                embed = self.embed_builder.error_embed(
                    "Already in Guild",
                    "You must leave your current guild before creating a new one."
                )
                await ctx.send(embed=embed)
                return
            
            # Check requirements
            if user_data.get("level", 1) < 10:
                embed = self.embed_builder.error_embed(
                    "Level Requirement",
                    "You must be level 10 or higher to create a guild."
                )
                await ctx.send(embed=embed)
                return
            
            creation_cost = 50000
            if user_data.get("gold", 0) < creation_cost:
                embed = self.embed_builder.error_embed(
                    "Insufficient Gold",
                    f"Creating a guild costs {format_number(creation_cost)} gold."
                )
                await ctx.send(embed=embed)
                return
            
            # Create guild
            guild_id = generate_unique_id("guild_")
            guild_data = {
                "id": guild_id,
                "name": guild_name.strip(),
                "faction": faction.lower() if faction else None,
                "leader_id": str(ctx.author.id),
                "leader_name": ctx.author.display_name,
                "members": [str(ctx.author.id)],
                "officers": [],
                "level": 1,
                "xp": 0,
                "bank": 0,
                "created_at": datetime.now().isoformat(),
                "description": f"A guild led by {ctx.author.display_name}",
                "territories": [],
                "wars": [],
                "activities": []
            }
            
            # Deduct creation cost and set user's guild
            user_data["gold"] -= creation_cost
            user_data["guild_id"] = guild_id
            user_data["guild_role"] = "leader"
            
            # Save guild data (in real implementation, this would be in a separate guilds file)
            guilds_data = data_manager.get_game_data("guilds") or {}
            guilds_data[guild_id] = guild_data
            
            # Save user data
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Create success embed
            embed = self.create_guild_creation_embed(guild_data, creation_cost)
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Guild Creation Error",
                "Unable to create guild. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Guild creation error: {e}")
    
    @guild_group.command(name="join")
    async def join_guild(self, ctx, guild_id: str):
        """Join an existing guild"""
        # Enforce channel restrictions for guild commands
        restriction_result = await check_channel_restriction(
            ctx, ["guild-hall", "guild-chronicles", "faction-realm"], ctx.bot
        )
        if not restriction_result:
            await ctx.send("🏰 Guild commands can only be used in guild channels!", delete_after=10)
            return
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            
            # Check if user is already in a guild
            if user_data.get("guild_id"):
                embed = self.embed_builder.error_embed(
                    "Already in Guild",
                    "You must leave your current guild before joining another."
                )
                await ctx.send(embed=embed)
                return
            
            # Find guild
            guilds_data = data_manager.get_game_data("guilds") or {}
            guild_data = None
            
            # Try to find guild by partial ID or name
            for gid, gdata in guilds_data.items():
                if guild_id.lower() in gid.lower() or guild_id.lower() in gdata.get("name", "").lower():
                    guild_data = gdata
                    guild_id = gid
                    break
            
            if not guild_data:
                embed = self.embed_builder.error_embed(
                    "Guild Not Found",
                    f"Could not find guild with ID or name containing '{guild_id}'"
                )
                await ctx.send(embed=embed)
                return
            
            # Check if guild is full
            max_members = self.guild_benefits[guild_data.get("level", 1)]["max_members"]
            if len(guild_data.get("members", [])) >= max_members:
                embed = self.embed_builder.error_embed(
                    "Guild Full",
                    f"This guild is full ({max_members} members maximum for level {guild_data.get('level', 1)})."
                )
                await ctx.send(embed=embed)
                return
            
            # Add user to guild
            guild_data["members"].append(str(ctx.author.id))
            user_data["guild_id"] = guild_id
            user_data["guild_role"] = "member"
            user_data["guild_joined_at"] = datetime.now().isoformat()
            
            # Save data
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            embed = self.embed_builder.success_embed(
                "Joined Guild!",
                f"Welcome to **{guild_data['name']}**!"
            )
            
            faction_info = ""
            if guild_data.get("faction"):
                faction_data = self.factions[guild_data["faction"]]
                faction_info = f"\n🏆 Faction: {faction_data['emoji']} {faction_data['name']}"
            
            embed.add_field(
                name="🏰 Guild Info",
                value=f"Leader: {guild_data['leader_name']}\n"
                      f"Level: {guild_data.get('level', 1)}\n"
                      f"Members: {len(guild_data['members'])}/{max_members}"
                      f"{faction_info}",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Join Guild Error",
                "Unable to join guild. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Join guild error: {e}")
    
    @guild_group.command(name="info")
    async def guild_info(self, ctx, guild_id: str = None):
        """View detailed guild information"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            
            if not guild_id:
                # Show user's own guild
                guild_id = user_data.get("guild_id")
                if not guild_id:
                    embed = self.embed_builder.info_embed(
                        "No Guild",
                        "You're not in a guild! Use `!guild join <id>` or `!guild create <name>`"
                    )
                    await ctx.send(embed=embed)
                    return
            
            # Find guild
            guilds_data = data_manager.get_game_data("guilds") or {}
            guild_data = guilds_data.get(guild_id)
            
            if not guild_data:
                embed = self.embed_builder.error_embed(
                    "Guild Not Found",
                    f"Could not find guild with ID '{guild_id}'"
                )
                await ctx.send(embed=embed)
                return
            
            # Create detailed guild info embed
            embed = self.create_guild_info_embed(guild_data)
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Guild Info Error",
                "Unable to load guild information."
            )
            await ctx.send(embed=error_embed)
            print(f"Guild info error: {e}")
    
    @guild_group.command(name="bank")
    async def guild_bank(self, ctx, action: str = None, amount: str = None):
        """Manage guild bank (deposit/withdraw/view)"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            guild_id = user_data.get("guild_id")
            
            if not guild_id:
                embed = self.embed_builder.error_embed(
                    "No Guild",
                    "You must be in a guild to use the bank!"
                )
                await ctx.send(embed=embed)
                return
            
            guilds_data = data_manager.get_game_data("guilds") or {}
            guild_data = guilds_data.get(guild_id)
            
            if not guild_data:
                embed = self.embed_builder.error_embed(
                    "Guild Not Found",
                    "Your guild data could not be found."
                )
                await ctx.send(embed=embed)
                return
            
            if not action:
                # Show bank status
                embed = self.create_bank_status_embed(guild_data)
                await ctx.send(embed=embed)
                return
            
            if action.lower() == "deposit":
                await self.handle_bank_deposit(ctx, guild_data, user_data, amount)
            elif action.lower() == "withdraw":
                await self.handle_bank_withdraw(ctx, guild_data, user_data, amount)
            else:
                embed = self.embed_builder.error_embed(
                    "Invalid Action",
                    "Valid actions: `deposit`, `withdraw`, or leave empty to view bank."
                )
                await ctx.send(embed=embed)
                
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Bank Error",
                "Unable to process bank request."
            )
            await ctx.send(embed=error_embed)
            print(f"Guild bank error: {e}")
    
    @guild_group.command(name="leave")
    async def leave_guild(self, ctx):
        """Leave your current guild"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            guild_id = user_data.get("guild_id")
            
            if not guild_id:
                embed = self.embed_builder.info_embed(
                    "No Guild",
                    "You're not in a guild!"
                )
                await ctx.send(embed=embed)
                return
            
            # Confirmation for guild leaders
            if user_data.get("guild_role") == "leader":
                embed = self.embed_builder.warning_embed(
                    "Guild Leader",
                    "As the guild leader, leaving will disband the guild. Are you sure?"
                )
                view = LeaveConfirmationView(str(ctx.author.id), guild_id, is_leader=True)
                await ctx.send(embed=embed, view=view)
            else:
                # Regular member leaving
                view = LeaveConfirmationView(str(ctx.author.id), guild_id, is_leader=False)
                embed = self.embed_builder.create_embed(
                    title="Leave Guild",
                    description="Are you sure you want to leave your guild?",
                    color=0xFFA500
                )
                await ctx.send(embed=embed, view=view)
                
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Leave Guild Error",
                "Unable to process guild leave request."
            )
            await ctx.send(embed=error_embed)
            print(f"Leave guild error: {e}")
    
    @commands.command(name="factions")
    async def view_factions(self, ctx):
        """View all available factions and their bonuses"""
        embed = self.embed_builder.create_embed(
            title="🏆 Faction System",
            description="Choose your faction when creating a guild for special bonuses!",
            color=0x9370DB
        )
        
        for faction_id, faction_data in self.factions.items():
            bonuses_text = ""
            for bonus_type, multiplier in faction_data["bonuses"].items():
                bonus_name = bonus_type.replace("_", " ").title()
                bonus_percent = int((multiplier - 1) * 100)
                bonuses_text += f"• {bonus_name}: +{bonus_percent}%\n"
            
            embed.add_field(
                name=f"{faction_data['emoji']} {faction_data['name']}",
                value=f"{faction_data['description']}\n\n**Bonuses:**\n{bonuses_text}",
                inline=True
            )
        
        embed.add_field(
            name="💡 Faction Benefits",
            value="• Unique bonuses for guild members\n"
                  "• Special faction-only quests\n"
                  "• Faction warfare events\n"
                  "• Exclusive faction rewards",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    async def handle_bank_deposit(self, ctx, guild_data: Dict, user_data: Dict, amount: str):
        """Handle guild bank deposit"""
        if not amount:
            embed = self.embed_builder.error_embed(
                "Amount Required",
                "Please specify how much gold to deposit."
            )
            await ctx.send(embed=embed)
            return
        
        valid, deposit_amount, error_msg = validate_amount(amount, user_data.get("gold", 0))
        if not valid:
            embed = self.embed_builder.error_embed("Invalid Amount", error_msg)
            await ctx.send(embed=embed)
            return
        
        if user_data.get("gold", 0) < deposit_amount:
            embed = self.embed_builder.error_embed(
                "Insufficient Gold",
                f"You only have {format_number(user_data.get('gold', 0))} gold."
            )
            await ctx.send(embed=embed)
            return
        
        # Check bank limit
        guild_level = guild_data.get("level", 1)
        bank_limit = self.guild_benefits[guild_level]["bank_limit"]
        current_bank = guild_data.get("bank", 0)
        
        if current_bank + deposit_amount > bank_limit:
            max_deposit = bank_limit - current_bank
            embed = self.embed_builder.error_embed(
                "Bank Limit Exceeded",
                f"Guild bank limit: {format_number(bank_limit)} gold\n"
                f"Current: {format_number(current_bank)} gold\n"
                f"Max deposit: {format_number(max_deposit)} gold"
            )
            await ctx.send(embed=embed)
            return
        
        # Process deposit
        user_data["gold"] -= deposit_amount
        guild_data["bank"] = current_bank + deposit_amount
        
        # Record transaction
        guild_data.setdefault("bank_history", []).append({
            "type": "deposit",
            "user_id": str(ctx.author.id),
            "user_name": ctx.author.display_name,
            "amount": deposit_amount,
            "timestamp": datetime.now().isoformat()
        })
        
        data_manager.save_user_data(str(ctx.author.id), user_data)
        
        embed = self.embed_builder.success_embed(
            "Deposit Successful!",
            f"Deposited {format_number(deposit_amount)} gold to the guild bank."
        )
        
        embed.add_field(
            name="🏦 Bank Status",
            value=f"Total: {format_number(guild_data['bank'])} / {format_number(bank_limit)} gold",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    async def handle_bank_withdraw(self, ctx, guild_data: Dict, user_data: Dict, amount: str):
        """Handle guild bank withdrawal"""
        # Check permissions
        user_role = user_data.get("guild_role", "member")
        if user_role not in ["leader", "officer"]:
            embed = self.embed_builder.error_embed(
                "Insufficient Permissions",
                "Only guild leaders and officers can withdraw from the bank."
            )
            await ctx.send(embed=embed)
            return
        
        if not amount:
            embed = self.embed_builder.error_embed(
                "Amount Required",
                "Please specify how much gold to withdraw."
            )
            await ctx.send(embed=embed)
            return
        
        current_bank = guild_data.get("bank", 0)
        valid, withdraw_amount, error_msg = validate_amount(amount, current_bank)
        if not valid:
            embed = self.embed_builder.error_embed("Invalid Amount", error_msg)
            await ctx.send(embed=embed)
            return
        
        if current_bank < withdraw_amount:
            embed = self.embed_builder.error_embed(
                "Insufficient Bank Funds",
                f"Guild bank only has {format_number(current_bank)} gold."
            )
            await ctx.send(embed=embed)
            return
        
        # Process withdrawal
        user_data["gold"] = user_data.get("gold", 0) + withdraw_amount
        guild_data["bank"] = current_bank - withdraw_amount
        
        # Record transaction
        guild_data.setdefault("bank_history", []).append({
            "type": "withdrawal",
            "user_id": str(ctx.author.id),
            "user_name": ctx.author.display_name,
            "amount": withdraw_amount,
            "timestamp": datetime.now().isoformat()
        })
        
        data_manager.save_user_data(str(ctx.author.id), user_data)
        
        embed = self.embed_builder.success_embed(
            "Withdrawal Successful!",
            f"Withdrew {format_number(withdraw_amount)} gold from the guild bank."
        )
        
        embed.add_field(
            name="🏦 Remaining Bank",
            value=f"{format_number(guild_data['bank'])} gold",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    def create_guild_overview_embed(self) -> discord.Embed:
        """Create guild system overview embed"""
        embed = self.embed_builder.create_embed(
            title="🏰 Guild System",
            description="Join forces with other players for enhanced rewards and cooperative gameplay!",
            color=0x4169E1
        )
        
        embed.add_field(
            name="🏗️ Guild Commands",
            value="• `!guild create <name> [faction]` - Create new guild\n"
                  "• `!guild join <id>` - Join existing guild\n"
                  "• `!guild info [id]` - View guild details\n"
                  "• `!guild bank [deposit/withdraw] [amount]` - Manage guild bank\n"
                  "• `!guild leave` - Leave current guild",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Guild Benefits",
            value="• Shared guild bank for resources\n"
                  "• Guild level progression and perks\n"
                  "• Faction bonuses and special quests\n"
                  "• Cooperative activities and wars\n"
                  "• Exclusive guild-only content",
            inline=False
        )
        
        embed.add_field(
            name="🌟 Faction System",
            value="Use `!factions` to view all available factions and their unique bonuses!",
            inline=False
        )
        
        return embed
    
    def create_guild_creation_embed(self, guild_data: Dict, cost: int) -> discord.Embed:
        """Create guild creation success embed"""
        embed = self.embed_builder.success_embed(
            "Guild Created Successfully!",
            f"Welcome to **{guild_data['name']}**!"
        )
        
        embed.add_field(
            name="🏰 Guild Details",
            value=f"Guild ID: `{guild_data['id'][:12]}...`\n"
                  f"Leader: {guild_data['leader_name']}\n"
                  f"Level: {guild_data['level']}\n"
                  f"Creation Cost: {format_number(cost)} gold",
            inline=True
        )
        
        if guild_data.get("faction"):
            faction_data = self.factions[guild_data["faction"]]
            embed.add_field(
                name="🏆 Faction",
                value=f"{faction_data['emoji']} **{faction_data['name']}**\n{faction_data['description']}",
                inline=True
            )
        
        benefits = self.guild_benefits[1]
        embed.add_field(
            name="🎁 Level 1 Benefits",
            value=f"• Max Members: {benefits['max_members']}\n"
                  f"• Bank Limit: {format_number(benefits['bank_limit'])} gold\n"
                  f"• Perks: {', '.join(benefits['perks'])}",
            inline=False
        )
        
        return embed
    
    def create_guild_info_embed(self, guild_data: Dict) -> discord.Embed:
        """Create detailed guild information embed"""
        faction_data = None
        if guild_data.get("faction"):
            faction_data = self.factions[guild_data["faction"]]
        
        color = faction_data["color"] if faction_data else 0x4169E1
        
        embed = self.embed_builder.create_embed(
            title=f"🏰 {guild_data['name']}",
            description=guild_data.get("description", "A mighty guild"),
            color=color
        )
        
        # Basic info
        guild_level = guild_data.get("level", 1)
        benefits = self.guild_benefits[guild_level]
        
        embed.add_field(
            name="📊 Guild Stats",
            value=f"Level: {guild_level}\n"
                  f"XP: {format_number(guild_data.get('xp', 0))}\n"
                  f"Members: {len(guild_data.get('members', []))}/{benefits['max_members']}\n"
                  f"Bank: {format_number(guild_data.get('bank', 0))} / {format_number(benefits['bank_limit'])}",
            inline=True
        )
        
        # Leadership
        embed.add_field(
            name="👑 Leadership",
            value=f"Leader: {guild_data['leader_name']}\n"
                  f"Officers: {len(guild_data.get('officers', []))}",
            inline=True
        )
        
        # Faction info
        if faction_data:
            embed.add_field(
                name=f"🏆 {faction_data['name']}",
                value=faction_data["description"],
                inline=True
            )
        
        # Current benefits
        perks_text = "\n".join([f"• {perk}" for perk in benefits["perks"]])
        embed.add_field(
            name="🎁 Current Perks",
            value=perks_text,
            inline=False
        )
        
        # Created date
        try:
            created_date = datetime.fromisoformat(guild_data["created_at"]).strftime("%B %d, %Y")
            embed.set_footer(text=f"Established {created_date}")
        except:
            pass
        
        return embed
    
    def create_bank_status_embed(self, guild_data: Dict) -> discord.Embed:
        """Create guild bank status embed"""
        guild_level = guild_data.get("level", 1)
        benefits = self.guild_benefits[guild_level]
        current_bank = guild_data.get("bank", 0)
        bank_limit = benefits["bank_limit"]
        
        embed = self.embed_builder.create_embed(
            title="🏦 Guild Bank",
            description=f"Managing funds for {guild_data['name']}",
            color=0x32CD32
        )
        
        # Bank status
        percentage = (current_bank / bank_limit * 100) if bank_limit > 0 else 0
        from utils.helpers import create_progress_bar
        progress_bar = create_progress_bar(current_bank, bank_limit)
        
        embed.add_field(
            name="💰 Current Balance",
            value=f"{format_number(current_bank)} / {format_number(bank_limit)} gold\n"
                  f"{progress_bar} ({percentage:.1f}%)",
            inline=False
        )
        
        # Recent transactions
        bank_history = guild_data.get("bank_history", [])
        if bank_history:
            recent_transactions = bank_history[-5:]  # Last 5 transactions
            history_text = ""
            for transaction in reversed(recent_transactions):
                action = "📈" if transaction["type"] == "deposit" else "📉"
                amount = format_number(transaction["amount"])
                user = transaction["user_name"]
                history_text += f"{action} {amount} gold by {user}\n"
            
            embed.add_field(
                name="📜 Recent Transactions",
                value=history_text or "No recent transactions",
                inline=False
            )
        
        embed.add_field(
            name="💡 Bank Commands",
            value="• `!guild bank deposit <amount>` - Deposit gold\n"
                  "• `!guild bank withdraw <amount>` - Withdraw gold (officers+)",
            inline=False
        )
        
        return embed


class LeaveConfirmationView(discord.ui.View):
    """Confirmation view for leaving a guild"""
    
    def __init__(self, user_id: str, guild_id: str, is_leader: bool = False):
        super().__init__(timeout=60.0)
        self.user_id = user_id
        self.guild_id = guild_id
        self.is_leader = is_leader
    
    @discord.ui.button(label="✅ Confirm Leave", style=discord.ButtonStyle.danger)
    async def confirm_leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirm leaving the guild"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This is not your confirmation!", ephemeral=True)
            return
        
        try:
            user_data = data_manager.get_user_data(self.user_id)
            
            if self.is_leader:
                # Disband guild
                embed = EmbedBuilder.success_embed(
                    "Guild Disbanded",
                    "You have disbanded your guild as the leader."
                )
                # In a real implementation, this would remove the guild and notify all members
            else:
                # Leave guild
                embed = EmbedBuilder.success_embed(
                    "Left Guild",
                    "You have successfully left your guild."
                )
            
            # Clear user's guild data
            user_data["guild_id"] = None
            user_data["guild_role"] = None
            data_manager.save_user_data(self.user_id, user_data)
            
            # Disable buttons
            for item in self.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
            
        except Exception as e:
            await interaction.response.send_message("❌ Error processing guild leave.", ephemeral=True)
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel leaving the guild"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This is not your confirmation!", ephemeral=True)
            return
        
        embed = EmbedBuilder.info_embed("Cancelled", "Guild leave cancelled.")
        
        # Disable buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)


async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(GuildCommands(bot))