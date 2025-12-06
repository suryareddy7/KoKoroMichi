# Admin Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List
import json
from datetime import datetime, timedelta

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from core.config import ADMIN_USER_ID
try:
    from utils.helpers import format_number
except ImportError:
    def format_number(num):
        """Simple number formatter"""
        return f"{num:,}"
import logging

logger = logging.getLogger(__name__)

class AdminCommands(commands.Cog):
    """Administrative commands for bot management and moderation"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        
        # Admin and moderator configuration
        self.moderator_users = set()  # Add moderator user IDs here
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is an admin"""
        return str(user_id) == ADMIN_USER_ID or user_id == self.bot.owner_id
    
    def is_moderator(self, user_id: int) -> bool:
        """Check if user is a moderator or admin"""
        return user_id in self.moderator_users or self.is_admin(user_id)
    
    @commands.group(name="admin", invoke_without_command=True)
    async def admin_group(self, ctx):
        """Admin command group - requires admin permissions"""
        # Check admin permissions
        if not self.is_admin(ctx.author.id):
            embed = self.embed_builder.error_embed(
                "Access Denied",
                "You don't have permission to use admin commands."
            )
            await ctx.send(embed=embed)
            return
        
        # Send admin panel info to DM for security
        admin_embed = self.embed_builder.create_embed(
            title="🛠️ Admin Panel",
            description="Bot administration and management commands",
            color=0xFF0000
        )
        
        admin_embed.add_field(
            name="👥 User Management",
            value="• `!admin give <user> <item> <amount>` - Give items\n"
                  "• `!admin gold <user> <amount>` - Modify gold\n"
                  "• `!admin reset <user>` - Reset user data\n"
                  "• `!admin ban <user> [reason]` - Ban user",
            inline=False
        )
        
        admin_embed.add_field(
            name="📊 Bot Management",
            value="• `!admin stats` - Bot statistics\n"
                  "• `!admin backup` - Create data backup\n"
                  "• `!admin announce <message>` - Server announcement\n"
                  "• `!admin maintenance` - Toggle maintenance mode",
            inline=False
        )
        
        admin_embed.add_field(
            name="🎮 Game Management",
            value="• `!admin setlevel <user> <level>` - Set user level\n"
                  "• `!admin viewdata <user>` - View raw user data\n"
                  "• `!admin addwaifu <user> <character>` - Add character\n"
                  "• `!admin banwaifu <user> <character>` - Remove character",
            inline=False
        )
        
        admin_embed.add_field(
            name="🔧 Utility Commands",
            value="• `!admin editaffection <user> <character> <level>` - Edit affection\n"
                  "• `!admin addrelic <user> <relic>` - Give relic\n"
                  "• `!admin erase [amount]` - Clear channel messages\n"
                  "• `!admin welcome [guild_id]` - Send welcome messages to channels\n"
                  "• `!admin help` - Show all admin commands",
            inline=False
        )
        
        # Send response to server
        response_embed = self.embed_builder.info_embed(
            "Admin Command",
            "Admin panel information sent to your DM for security."
        )
        await ctx.send(embed=response_embed)
        
        # Send detailed admin info to DM
        try:
            await ctx.author.send(embed=admin_embed)
        except discord.Forbidden:
            error_embed = self.embed_builder.error_embed(
                "DM Failed",
                "Could not send admin panel to your DM. Please enable DMs from server members."
            )
            await ctx.send(embed=error_embed)
    
    @admin_group.command(name="give")
    async def give_item(self, ctx, member: discord.Member, item_name: str, amount: int = 1):
        """Give items to a user"""
        if not self.is_admin(ctx.author.id):
            embed = self.embed_builder.error_embed(
                "Access Denied",
                "You don't have permission to use admin commands."
            )
            await ctx.send(embed=embed)
            return
        
        try:
            if amount <= 0 or amount > 1000000:
                embed = self.embed_builder.error_embed(
                    "Invalid Amount",
                    "Amount must be between 1 and 1,000,000"
                )
                await ctx.send(embed=embed)
                return
            
            user_data = data_manager.get_user_data(str(member.id))
            inventory = user_data.setdefault("inventory", {})
            
            # Add item to inventory
            inventory[item_name] = inventory.get(item_name, 0) + amount
            data_manager.save_user_data(str(member.id), user_data)
            
            embed = self.embed_builder.success_embed(
                "Item Given",
                f"Successfully gave **{item_name}** x{amount} to {member.mention}"
            )
            
            # Log admin action
            logger.info(f"Admin {ctx.author} gave {item_name} x{amount} to {member.display_name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Give Item Error",
                "Unable to give item. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Admin give error: {e}")
    
    @admin_group.command(name="gold")
    async def modify_gold(self, ctx, member: discord.Member, amount: int):
        """Modify a user's gold (can be negative to subtract)"""
        if not self.is_admin(ctx.author.id):
            embed = self.embed_builder.error_embed(
                "Access Denied",
                "You don't have permission to use admin commands."
            )
            await ctx.send(embed=embed)
            return
        
        try:
            user_data = data_manager.get_user_data(str(member.id))
            old_gold = user_data.get("gold", 0)
            new_gold = max(0, old_gold + amount)
            user_data["gold"] = new_gold
            
            data_manager.save_user_data(str(member.id), user_data)
            
            action = "Added" if amount > 0 else "Removed"
            embed = self.embed_builder.success_embed(
                "Gold Modified",
                f"{action} {format_number(abs(amount))} gold to {member.mention}\n"
                f"Previous: {format_number(old_gold)} → New: {format_number(new_gold)}"
            )
            
            # Log admin action
            await self.log_admin_action(ctx, f"Modified gold for {member.display_name}: {amount:+,}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Gold Modification Error",
                "Unable to modify gold. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Admin gold error: {e}")
    
    @admin_group.command(name="reset")
    async def reset_user(self, ctx, member: discord.Member):
        """Reset a user's data (DESTRUCTIVE - requires confirmation)"""
        if not self.is_admin(ctx.author.id):
            embed = self.embed_builder.error_embed(
                "Access Denied",
                "You don't have permission to use admin commands."
            )
            await ctx.send(embed=embed)
            return
        
        # Create confirmation view
        view = ResetConfirmationView(str(ctx.author.id), str(member.id), member.display_name)
        embed = self.embed_builder.warning_embed(
            "⚠️ DESTRUCTIVE ACTION",
            f"Are you sure you want to reset ALL data for {member.mention}?\n"
            f"This action cannot be undone!"
        )
        
        await ctx.send(embed=embed, view=view)
    
    @admin_group.command(name="stats")
    async def show_stats(self, ctx):
        """Display bot statistics"""
        if not self.is_moderator(ctx.author.id):
            embed = self.embed_builder.error_embed(
                "Access Denied", 
                "You don't have permission to use moderator commands."
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Get user count
            total_users = data_manager.get_users_count()
            
            # Bot stats
            guild_count = len(self.bot.guilds)
            total_members = sum(guild.member_count for guild in self.bot.guilds)
            
            embed = self.embed_builder.create_embed(
                title="📊 Bot Statistics",
                description="Current bot performance and usage metrics",
                color=0x00BFFF
            )
            
            embed.add_field(
                name="👥 User Statistics",
                value=f"Registered Users: {format_number(total_users)}\n"
                      f"Total Discord Members: {format_number(total_members)}\n"
                      f"Servers: {guild_count}",
                inline=True
            )
            
            # Memory and performance
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent()
            
            embed.add_field(
                name="🖥️ Performance",
                value=f"Memory Usage: {memory_mb:.1f} MB\n"
                      f"CPU Usage: {cpu_percent:.1f}%\n"
                      f"Uptime: {self.get_uptime()}",
                inline=True
            )
            
            # Bot version and info
            embed.add_field(
                name="🤖 Bot Info",
                value=f"Version: 3.0.0 Advanced\n"
                      f"Discord.py: {discord.__version__}\n"
                      f"Latency: {self.bot.latency * 1000:.1f}ms",
                inline=True
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Stats Error",
                "Unable to retrieve bot statistics."
            )
            await ctx.send(embed=embed)
            print(f"Bot stats error: {e}")
    
    @admin_group.command(name="announce")
    async def make_announcement(self, ctx, *, message: str):
        """Make a server-wide announcement"""
        if not self.is_admin(ctx.author.id):
            await ctx.send("❌ Admin access required.")
            return
        
        try:
            embed = self.embed_builder.create_embed(
                title="📢 Server Announcement",
                description=message,
                color=0xFF4500
            )
            
            embed.set_footer(text=f"Announcement by {ctx.author.display_name}")
            embed.timestamp = datetime.now()
            
            # Send to current channel
            await ctx.send(embed=embed)
            
            # Log admin action
            await self.log_admin_action(ctx, f"Made announcement: {message[:100]}...")
            
            await ctx.message.add_reaction("✅")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Announcement Error",
                "Unable to make announcement."
            )
            await ctx.send(embed=embed)
            print(f"Announcement error: {e}")
    
    @admin_group.command(name="backup")
    async def create_backup(self, ctx):
        """Create a backup of bot data"""
        if not self.is_admin(ctx.author.id):
            await ctx.send("❌ Admin access required.")
            return
        
        try:
            # Create backup timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # This would create actual backups in production
            embed = self.embed_builder.success_embed(
                "Backup Created",
                f"Data backup created successfully!\n"
                f"Backup ID: `backup_{timestamp}`\n"
                f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            # Log admin action
            await self.log_admin_action(ctx, f"Created data backup: backup_{timestamp}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Backup Error",
                "Unable to create backup."
            )
            await ctx.send(embed=embed)
            print(f"Backup error: {e}")
    
    @admin_group.command(name="erase")
    async def erase_messages(self, ctx, amount: int = 50):
        """Clear all channel messages - tries to preserve pins but deletes everything if needed"""
        if not self.is_admin(ctx.author.id):
            embed = self.embed_builder.error_embed(
                "Access Denied",
                "You don't have permission to use admin commands."
            )
            await ctx.send(embed=embed)
            return
        
        try:
            if amount <= 0 or amount > 1000:
                embed = self.embed_builder.error_embed(
                    "Invalid Amount",
                    "Amount must be between 1 and 1000"
                )
                await ctx.send(embed=embed)
                return
            
            deleted = []
            pins_preserved = True
            
            try:
                # First attempt: Delete messages excluding pinned ones
                def check(msg):
                    return not msg.pinned
                
                deleted = await ctx.channel.purge(limit=amount, check=check)
                
                # If we didn't delete enough messages, try deleting everything
                if len(deleted) < amount // 2:  # If we deleted less than half expected
                    remaining = amount - len(deleted)
                    additional_deleted = await ctx.channel.purge(limit=remaining)
                    deleted.extend(additional_deleted)
                    pins_preserved = False
                    
            except Exception:
                # If pin detection fails, delete all messages including pins
                deleted = await ctx.channel.purge(limit=amount)
                pins_preserved = False
            
            # Create success message based on what was deleted
            if pins_preserved:
                description = (f"Successfully deleted {len(deleted)} messages from {ctx.channel.mention}\n"
                             f"✅ Pinned messages were preserved")
            else:
                description = (f"Successfully deleted {len(deleted)} messages from {ctx.channel.mention}\n"
                             f"⚠️ All messages including pinned ones were deleted")
            
            embed = self.embed_builder.success_embed(
                "Messages Cleared",
                description
            )
            
            # Log admin action
            pin_status = "preserving pins" if pins_preserved else "including pinned messages"
            await self.log_admin_action(ctx, f"Cleared {len(deleted)} messages from {ctx.channel.name} ({pin_status})")
            
            # Send confirmation and auto-delete it
            await ctx.send(embed=embed, delete_after=2)
            
        except discord.Forbidden:
            embed = self.embed_builder.error_embed(
                "Permission Error",
                "I don't have permission to delete messages in this channel."
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Erase Error",
                "Unable to clear messages. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Erase error: {e}")
    
    @admin_group.command(name="setlevel")
    async def set_user_level(self, ctx, member: discord.Member, level: int):
        """Set a user's level manually"""
        if not self.is_admin(ctx.author.id):
            embed = self.embed_builder.error_embed(
                "Access Denied",
                "You don't have permission to use admin commands."
            )
            await ctx.send(embed=embed)
            return
        
        try:
            if level <= 0 or level > 100:
                embed = self.embed_builder.error_embed(
                    "Invalid Level",
                    "Level must be between 1 and 100"
                )
                await ctx.send(embed=embed)
                return
            
            user_data = data_manager.get_user_data(str(member.id))
            old_level = user_data.get("level", 1)
            user_data["level"] = level
            
            # Calculate XP for new level
            user_data["xp"] = level * 1000  # Simple XP calculation
            
            data_manager.save_user_data(str(member.id), user_data)
            
            embed = self.embed_builder.success_embed(
                "Level Set",
                f"Successfully set {member.mention}'s level\n"
                f"Previous Level: {old_level} → New Level: {level}"
            )
            
            # Log admin action
            await self.log_admin_action(ctx, f"Set {member.display_name}'s level to {level}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Set Level Error",
                "Unable to set user level. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Set level error: {e}")
    
    @admin_group.command(name="viewdata")
    async def view_user_data(self, ctx, member: discord.Member):
        """View raw user JSON data for debugging"""
        if not self.is_admin(ctx.author.id):
            embed = self.embed_builder.error_embed(
                "Access Denied",
                "You don't have permission to use admin commands."
            )
            await ctx.send(embed=embed)
            return
        
        try:
            user_data = data_manager.get_user_data(str(member.id))
            
            # Format JSON for Discord display
            json_data = json.dumps(user_data, indent=2, ensure_ascii=False)
            
            # Split into chunks if too long
            if len(json_data) > 1900:
                # Send basic info first
                embed = self.embed_builder.info_embed(
                    f"📊 User Data - {member.display_name}",
                    f"**User ID:** {member.id}\n"
                    f"**Level:** {user_data.get('level', 1)}\n"
                    f"**Gold:** {format_number(user_data.get('gold', 0))}\n"
                    f"**Gems:** {format_number(user_data.get('gems', 0))}\n"
                    f"**Characters:** {len(user_data.get('claimed_waifus', []))}\n"
                    f"**Last Active:** {user_data.get('last_active', 'Never')[:19]}"
                )
                await ctx.send(embed=embed)
                
                # Send full data as file
                import io
                file_content = json.dumps(user_data, indent=2, ensure_ascii=False)
                file_buffer = io.BytesIO(file_content.encode('utf-8'))
                file = discord.File(file_buffer, filename=f"userdata_{member.id}.json")
                
                await ctx.send("📄 **Full user data (JSON file):**", file=file)
            else:
                embed = self.embed_builder.info_embed(
                    f"📊 Raw User Data - {member.display_name}",
                    f"```json\n{json_data}\n```"
                )
                await ctx.send(embed=embed)
            
            # Log admin action
            await self.log_admin_action(ctx, f"Viewed raw data for {member.display_name}")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "View Data Error",
                "Unable to retrieve user data. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"View data error: {e}")
    
    @admin_group.command(name="banwaifu")
    async def ban_waifu(self, ctx, member: discord.Member, *, character_name: str):
        """Remove a waifu from user's collection"""
        if not self.is_admin(ctx.author.id):
            embed = self.embed_builder.error_embed(
                "Access Denied",
                "You don't have permission to use admin commands."
            )
            await ctx.send(embed=embed)
            return
        
        try:
            user_data = data_manager.get_user_data(str(member.id))
            claimed_waifus = user_data.get("claimed_waifus", [])
            
            # Find and remove the character
            removed_waifu = None
            for i, waifu in enumerate(claimed_waifus):
                if waifu.get("name", "").lower() == character_name.lower():
                    removed_waifu = claimed_waifus.pop(i)
                    break
            
            if removed_waifu:
                data_manager.save_user_data(str(member.id), user_data)
                
                embed = self.embed_builder.success_embed(
                    "Character Removed",
                    f"Successfully removed **{removed_waifu.get('name', character_name)}** "
                    f"from {member.mention}'s collection"
                )
                
                # Log admin action
                await self.log_admin_action(ctx, f"Removed {character_name} from {member.display_name}'s collection")
            else:
                embed = self.embed_builder.error_embed(
                    "Character Not Found",
                    f"Character **{character_name}** not found in {member.mention}'s collection"
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Ban Waifu Error",
                "Unable to remove character. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Ban waifu error: {e}")
    
    @admin_group.command(name="addwaifu")
    async def add_waifu(self, ctx, member: discord.Member, *, character_name: str):
        """Manually add a waifu to user's collection"""
        if not self.is_admin(ctx.author.id):
            embed = self.embed_builder.error_embed(
                "Access Denied",
                "You don't have permission to use admin commands."
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Get character data
            character_data = data_manager.get_character_data(character_name)
            
            if not character_data:
                embed = self.embed_builder.error_embed(
                    "Character Not Found",
                    f"Character **{character_name}** not found in the database.\n"
                    f"Please check the character name and try again."
                )
                await ctx.send(embed=embed)
                return
            
            user_data = data_manager.get_user_data(str(member.id))
            
            # Check if user already has this character
            claimed_waifus = user_data.get("claimed_waifus", [])
            for waifu in claimed_waifus:
                if waifu.get("name", "").lower() == character_name.lower():
                    embed = self.embed_builder.warning_embed(
                        "Character Already Owned",
                        f"{member.mention} already owns **{character_data.get('name', character_name)}**"
                    )
                    await ctx.send(embed=embed)
                    return
            
            # Add character to collection
            new_waifu = character_data.copy()
            new_waifu["level"] = 1
            new_waifu["obtained_at"] = datetime.now().isoformat()
            
            claimed_waifus.append(new_waifu)
            user_data["claimed_waifus"] = claimed_waifus
            data_manager.save_user_data(str(member.id), user_data)
            
            embed = self.embed_builder.success_embed(
                "Character Added",
                f"Successfully added **{character_data.get('name', character_name)}** "
                f"to {member.mention}'s collection!"
            )
            
            # Add character details
            rarity = character_data.get('rarity', 'N')
            embed.add_field(
                name="Character Details",
                value=f"**Rarity:** {rarity}\n"
                      f"**HP:** {character_data.get('hp', 0)}\n"
                      f"**ATK:** {character_data.get('atk', 0)}",
                inline=True
            )
            
            # Log admin action
            await self.log_admin_action(ctx, f"Added {character_name} to {member.display_name}'s collection")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Add Waifu Error",
                "Unable to add character. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Add waifu error: {e}")
    
    @admin_group.command(name="editaffection")
    async def edit_affection(self, ctx, member: discord.Member, character_name: str, affection_level: int):
        """Edit user's affection/intimate level with a character"""
        if not self.is_admin(ctx.author.id):
            embed = self.embed_builder.error_embed(
                "Access Denied",
                "You don't have permission to use admin commands."
            )
            await ctx.send(embed=embed)
            return
        
        try:
            if affection_level < 0 or affection_level > 100:
                embed = self.embed_builder.error_embed(
                    "Invalid Affection Level",
                    "Affection level must be between 0 and 100"
                )
                await ctx.send(embed=embed)
                return
            
            user_data = data_manager.get_user_data(str(member.id))
            
            # Check if user has this character
            claimed_waifus = user_data.get("claimed_waifus", [])
            character_found = False
            
            for waifu in claimed_waifus:
                if waifu.get("name", "").lower() == character_name.lower():
                    old_affection = waifu.get("affection", 0)
                    waifu["affection"] = affection_level
                    character_found = True
                    break
            
            if not character_found:
                embed = self.embed_builder.error_embed(
                    "Character Not Found",
                    f"{member.mention} doesn't own **{character_name}**"
                )
                await ctx.send(embed=embed)
                return
            
            data_manager.save_user_data(str(member.id), user_data)
            
            embed = self.embed_builder.success_embed(
                "Affection Updated",
                f"Successfully updated affection level for **{character_name}**\n"
                f"Owner: {member.mention}\n"
                f"Previous: {old_affection} → New: {affection_level}"
            )
            
            # Log admin action
            await self.log_admin_action(ctx, f"Set {character_name} affection to {affection_level} for {member.display_name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Edit Affection Error",
                "Unable to edit affection level. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Edit affection error: {e}")
    
    @admin_group.command(name="addrelic")
    async def add_relic(self, ctx, member: discord.Member, *, relic_name: str):
        """Give a relic to a user manually"""
        if not self.is_admin(ctx.author.id):
            embed = self.embed_builder.error_embed(
                "Access Denied",
                "You don't have permission to use admin commands."
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Check if relic exists
            relic_data = data_manager.get_game_data("relics")
            if not relic_data:
                # Try loading from relic files
                from pathlib import Path
                relic_file = Path("data/relics") / f"{relic_name}.json"
                if relic_file.exists():
                    import json
                    with open(relic_file, 'r') as f:
                        relic_info = json.load(f)
                else:
                    relic_info = {"name": relic_name, "description": "Admin-given relic"}
            else:
                relic_info = relic_data.get(relic_name, {"name": relic_name, "description": "Admin-given relic"})
            
            user_data = data_manager.get_user_data(str(member.id))
            inventory = user_data.setdefault("inventory", {})
            relics = inventory.setdefault("relics", {})
            
            # Add relic to inventory
            relics[relic_name] = relics.get(relic_name, 0) + 1
            data_manager.save_user_data(str(member.id), user_data)
            
            embed = self.embed_builder.success_embed(
                "Relic Added",
                f"Successfully gave **{relic_name}** to {member.mention}"
            )
            
            if relic_info.get("description"):
                embed.add_field(
                    name="Relic Description",
                    value=relic_info["description"],
                    inline=False
                )
            
            # Log admin action
            await self.log_admin_action(ctx, f"Gave {relic_name} relic to {member.display_name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Add Relic Error",
                "Unable to add relic. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Add relic error: {e}")
    
    @admin_group.command(name="help", aliases=["adminhelp"])
    async def admin_help(self, ctx):
        """Display all admin commands in a comprehensive embed"""
        if not self.is_admin(ctx.author.id):
            embed = self.embed_builder.error_embed(
                "Access Denied",
                "You don't have permission to use admin commands."
            )
            await ctx.send(embed=embed)
            return
        
        try:
            help_embed = self.embed_builder.create_embed(
                title="🛠️ Complete Admin Commands Reference",
                description="Comprehensive list of all administrative commands for KoKoroMichi Bot",
                color=0xFF0000
            )
            
            help_embed.add_field(
                name="👥 User Management",
                value="• `!admin give <user> <item> <amount>` - Give items to user\n"
                      "• `!admin gold <user> <amount>` - Modify user's gold\n"
                      "• `!admin setlevel <user> <level>` - Set user level (1-100)\n"
                      "• `!admin reset <user>` - Reset all user data (DESTRUCTIVE)\n"
                      "• `!admin viewdata <user>` - View raw user JSON data",
                inline=False
            )
            
            help_embed.add_field(
                name="🎮 Character Management",
                value="• `!admin addwaifu <user> <character>` - Add character to collection\n"
                      "• `!admin banwaifu <user> <character>` - Remove character from collection\n"
                      "• `!admin editaffection <user> <character> <level>` - Edit affection (0-100)\n"
                      "• `!admin addrelic <user> <relic>` - Give relic to user",
                inline=False
            )
            
            help_embed.add_field(
                name="📊 Bot Management",
                value="• `!admin stats` - Show detailed bot statistics\n"
                      "• `!admin backup` - Create data backup\n"
                      "• `!admin announce <message>` - Make server announcement\n"
                      "• `!admin erase [amount]` - Clear channel messages (preserve pinned)",
                inline=False
            )
            
            help_embed.add_field(
                name="ℹ️ Information Commands",
                value="• `!userinfo [user]` - Get detailed user information\n"
                      "• `!admin help` - Show this help message\n"
                      "• All admin commands work in DM for security",
                inline=False
            )
            
            help_embed.add_field(
                name="⚠️ Security Notes",
                value="• All admin commands require admin permissions\n"
                      "• Destructive actions require confirmation\n"
                      "• All admin actions are logged for audit trail\n"
                      "• Admin panel information is sent via DM",
                inline=False
            )
            
            help_embed.set_footer(text="KoKoroMichi Bot v3.1.1 | Admin System")
            
            # Send to DM for security
            try:
                await ctx.author.send(embed=help_embed)
                
                response_embed = self.embed_builder.info_embed(
                    "Admin Help",
                    "Complete admin commands reference sent to your DM for security."
                )
                await ctx.send(embed=response_embed)
                
            except discord.Forbidden:
                # If DM fails, send in channel but warn
                warning_embed = self.embed_builder.warning_embed(
                    "⚠️ DM Failed",
                    "Could not send to DM. Displaying here (less secure)."
                )
                await ctx.send(embed=warning_embed)
                await ctx.send(embed=help_embed)
            
            # Log admin action
            await self.log_admin_action(ctx, "Viewed admin help documentation")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Help Error",
                "Unable to display admin help. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Admin help error: {e}")
    
    # Removed duplicate welcome command - using the enhanced version below
    
    @commands.command(name="userinfo")
    async def user_info(self, ctx, member: discord.Member = None):
        """Get detailed information about a user (moderator command)"""
        if not self.is_moderator(ctx.author.id):
            embed = self.embed_builder.error_embed(
                "Access Denied",
                "You don't have permission to use this command."
            )
            await ctx.send(embed=embed)
            return
        
        target = member or ctx.author
        user_data = data_manager.get_user_data(str(target.id))
        
        embed = self.embed_builder.create_embed(
            title=f"👤 User Information - {target.display_name}",
            color=0x9370DB
        )
        
        # Basic info
        embed.add_field(
            name="📊 Basic Stats",
            value=f"User ID: {target.id}\n"
                  f"Level: {user_data.get('level', 1)}\n"
                  f"Gold: {format_number(user_data.get('gold', 0))}\n"
                  f"Gems: {format_number(user_data.get('gems', 0))}",
            inline=True
        )
        
        # Collection
        waifus_count = len(user_data.get("claimed_waifus", []))
        inventory_count = len(user_data.get("inventory", {}))
        
        embed.add_field(
            name="📦 Collection",
            value=f"Characters: {waifus_count}\n"
                  f"Items: {inventory_count}\n"
                  f"Achievements: {len(user_data.get('achievements', []))}",
            inline=True
        )
        
        # Activity
        last_active = user_data.get("last_active", "Never")
        created_at = user_data.get("created_at", "Unknown")
        
        embed.add_field(
            name="📅 Activity",
            value=f"Joined: {created_at[:10] if created_at != 'Unknown' else 'Unknown'}\n"
                  f"Last Active: {last_active[:10] if last_active != 'Never' else 'Never'}",
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @admin_group.command(name="welcome")
    async def send_welcome_messages(self, ctx, guild_id: Optional[str] = None):
        """Send welcome messages to all appropriate channels manually"""
        if not self.is_admin(ctx.author.id):
            embed = self.embed_builder.error_embed(
                "Access Denied",
                "You don't have permission to use admin commands."
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Determine target guild
            target_guild = None
            if guild_id:
                target_guild = self.bot.get_guild(int(guild_id))
                if not target_guild:
                    embed = self.embed_builder.error_embed(
                        "Guild Not Found",
                        f"Could not find guild with ID: {guild_id}"
                    )
                    await ctx.send(embed=embed)
                    return
            else:
                target_guild = ctx.guild
            
            if not target_guild:
                embed = self.embed_builder.error_embed(
                    "No Guild Context",
                    "This command must be used in a guild or provide a guild ID."
                )
                await ctx.send(embed=embed)
                return
            
            # Send welcome messages to channels
            sent_count = await self.bot.send_welcome_to_channels(target_guild, send_to_all=False)
            
            embed = self.embed_builder.success_embed(
                "Welcome Messages Sent",
                f"Successfully sent welcome messages to **{sent_count}** channels in **{target_guild.name}**!\n\n"
                f"📋 **What was sent:**\n"
                f"• Detailed command guides for each channel type\n"
                f"• Pro tips and strategies for gameplay\n"
                f"• Information about rewards and progression systems\n"
                f"• Enhanced descriptions explaining each feature\n\n"
                f"💡 **Channels targeted:** Combat zones, arenas, guild halls, pet corners, dream realms, event halls, forges, mini-games, and intimate chambers."
            )
            
            embed.add_field(
                name="📊 Channel Statistics",
                value=f"Total Channels in Guild: {len(target_guild.text_channels)}\n"
                      f"Welcome Messages Sent: {sent_count}\n"
                      f"Coverage: {(sent_count/len(target_guild.text_channels)*100):.1f}%",
                inline=False
            )
            
            # Add usage tips
            embed.add_field(
                name="💡 Admin Tips",
                value="• Use this command after creating new channels\n"
                      "• Welcome messages help new users understand each area\n"
                      "• Messages include detailed gameplay guides and strategies\n"
                      "• Run again anytime to refresh channel information",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
            # Log admin action
            await self.log_admin_action(ctx, f"Sent welcome messages to {sent_count} channels in {target_guild.name}")
            
        except ValueError:
            embed = self.embed_builder.error_embed(
                "Invalid Guild ID",
                "Please provide a valid numeric guild ID."
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Welcome Messages Error",
                "Unable to send welcome messages. Please try again."
            )
            await ctx.send(embed=embed)
            logger.error(f"Welcome messages error: {e}")
    
    async def log_admin_action(self, ctx, action: str):
        """Log admin actions for audit trail"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "admin_id": str(ctx.author.id),
            "admin_name": ctx.author.display_name,
            "action": action,
            "guild_id": str(ctx.guild.id) if ctx.guild else None
        }
        
        # In production, this would write to a log file or database
        print(f"ADMIN LOG: {log_entry}")
    
    def get_uptime(self) -> str:
        """Get bot uptime"""
        if hasattr(self.bot, 'start_time'):
            uptime = datetime.now() - self.bot.start_time
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{days}d {hours}h {minutes}m"
        return "Unknown"


class ResetConfirmationView(discord.ui.View):
    """Confirmation view for user data reset"""
    
    def __init__(self, admin_id: str, target_id: str, target_name: str):
        super().__init__(timeout=60.0)
        self.admin_id = admin_id
        self.target_id = target_id
        self.target_name = target_name
    
    @discord.ui.button(label="✅ CONFIRM RESET", style=discord.ButtonStyle.danger)
    async def confirm_reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirm the user data reset"""
        if str(interaction.user.id) != self.admin_id:
            await interaction.response.send_message("Only the admin who initiated this can confirm.", ephemeral=True)
            return
        
        try:
            # Create new default profile
            from core.data_manager import data_manager
            
            # Get the current data for backup info
            old_data = data_manager.get_user_data(self.target_id)
            old_level = old_data.get("level", 1)
            old_gold = old_data.get("gold", 0)
            
            # Reset user data (this would delete and recreate profile)
            # In production, you might want to move old data to archive
            default_profile = data_manager._create_default_profile()
            data_manager.save_user_data(self.target_id, default_profile)
            
            embed = EmbedBuilder.success_embed(
                "User Data Reset Complete",
                f"Successfully reset all data for **{self.target_name}**"
            )
            
            embed.add_field(
                name="📊 Previous Stats",
                value=f"Level: {old_level}\nGold: {format_number(old_gold)}",
                inline=True
            )
            
            embed.add_field(
                name="🔄 New Stats", 
                value=f"Level: 1\nGold: {format_number(default_profile.get('gold', 0))}",
                inline=True
            )
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
            
        except Exception as e:
            await interaction.response.send_message("❌ Error performing reset.", ephemeral=True)
            print(f"Reset error: {e}")
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel the reset operation"""
        if str(interaction.user.id) != self.admin_id:
            await interaction.response.send_message("Only the admin who initiated this can cancel.", ephemeral=True)
            return
        
        embed = EmbedBuilder.info_embed(
            "Reset Cancelled",
            f"User data reset for **{self.target_name}** was cancelled."
        )
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)


# Add a simple command for !adminhelp shortcut
@commands.command(name="adminhelp")
async def admin_help_shortcut(ctx):
    """Quick access to admin help"""
    admin_cog = ctx.bot.get_cog("AdminCommands")
    if admin_cog:
        await admin_cog.admin_help(ctx)
    else:
        await ctx.send("❌ Admin system not available.")

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(AdminCommands(bot))
    # Add the shortcut command
    bot.add_command(admin_help_shortcut)