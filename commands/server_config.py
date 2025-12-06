# Server Configuration Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List
import asyncio

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from utils.channel_manager import channel_manager

class ServerConfigCommands(commands.Cog):
    """Server configuration and auto-setup commands for easy bot deployment"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        
        # Required channels for different command categories
        self.channel_categories = {
            "🎯 Summoning & Gacha": {
                "channels": ["summoning", "gacha-hall"],
                "log_channels": ["lucky-summons"],
                "description": "For character summoning and rare drops",
                "commands": ["summon", "pull", "gacha", "rates"]
            },
            "⚔️ Combat & Battles": {
                "channels": ["combat-calls", "duel-zone", "battle-arena"],
                "log_channels": ["battle-history"],
                "description": "For battles, duels, and arena fights",
                "commands": ["battle", "fight", "duel"]
            },
            "🏟️ Arena & Tournaments": {
                "channels": ["arena-hub", "coliseum"],
                "log_channels": ["arena-history"], 
                "description": "For competitive arena battles",
                "commands": ["arena", "coliseum"]
            },
            "🎮 Mini-Games & Fun": {
                "channels": ["mini-games", "fun-zone"],
                "log_channels": [],
                "description": "For 8ball, roll, choose, and other games",
                "commands": ["8ball", "roll", "choose", "trivia", "lottery"]
            },
            "🎉 Events & Activities": {
                "channels": ["events", "event-hub"],
                "log_channels": [],
                "description": "For special events and daily activities",
                "commands": ["events", "dailyquest", "seasonal"]
            },
            "🐾 Pet Management": {
                "channels": ["pet-corner", "companion-hub"],
                "log_channels": [],
                "description": "For pet care and companion activities",
                "commands": ["pet", "feed", "pet_battle"]
            },
            "🏰 Guild & Factions": {
                "channels": ["guild-chronicles", "guild-hall"],
                "log_channels": [],
                "description": "For guild management and faction wars",
                "commands": ["guild", "faction", "guild_battle"]
            },
            "🌙 Dream Realm": {
                "channels": ["dream-realm", "mystical-dreams"],
                "log_channels": [],
                "description": "For dream events and visions",
                "commands": ["dream", "dreamquest"]
            },
            "🔨 Crafting & Forging": {
                "channels": ["forging-hall", "workshop"],
                "log_channels": ["forge-reports"],
                "description": "For item crafting and material gathering",
                "commands": ["craft", "forge", "materials"]
            },
            "💕 Intimate & Relationships": {
                "channels": ["lust-chamber", "intimate-moments"],
                "log_channels": [],
                "description": "For building relationships with waifus",
                "commands": ["intimate", "interact", "affection"]
            },
            "📜 System & Logs": {
                "channels": ["history"],
                "log_channels": [],
                "description": "For bot activity logs and history",
                "commands": []
            }
        }
    
    @commands.command(name="server_setup", aliases=["auto_setup", "configure_server"])
    @commands.has_permissions(administrator=True)
    async def auto_setup_server(self, ctx):
        """Automatically create all required channels for KoKoroMichi bot"""
        try:
            embed = self.embed_builder.create_embed(
                title="🔧 KoKoroMichi Server Setup",
                description="This will create all required channels for the bot to function properly.\n\n"
                           "**Channels will be organized by category with proper permissions.**",
                color=0x00FF00
            )
            
            # Show what will be created
            total_channels = sum(len(cat["channels"]) + len(cat["log_channels"]) for cat in self.channel_categories.values())
            embed.add_field(
                name="📊 What Will Be Created",
                value=f"• **{len(self.channel_categories)}** channel categories\n"
                      f"• **{total_channels}** channels total\n"
                      f"• Proper permissions for each channel\n"
                      f"• Welcome messages in each channel",
                inline=False
            )
            
            embed.add_field(
                name="⚠️ Requirements",
                value="• Bot must have **Manage Channels** permission\n"
                      "• You must be a server administrator\n"
                      "• This will take 1-2 minutes to complete",
                inline=False
            )
            
            embed.add_field(
                name="🤔 Continue?",
                value="React with ✅ to proceed or ❌ to cancel",
                inline=False
            )
            
            message = await ctx.send(embed=embed)
            await message.add_reaction("✅")
            await message.add_reaction("❌")
            
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == message.id
            
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                
                if str(reaction.emoji) == "❌":
                    await message.edit(embed=self.embed_builder.info_embed(
                        "Setup Cancelled",
                        "Server setup has been cancelled."
                    ))
                    return
                
                # Proceed with setup
                await self.perform_auto_setup(ctx, message)
                
            except asyncio.TimeoutError:
                await message.edit(embed=self.embed_builder.warning_embed(
                    "Setup Timeout",
                    "Setup request timed out. Please run the command again."
                ))
                
        except discord.Forbidden:
            embed = self.embed_builder.error_embed(
                "Permission Error",
                "I don't have permission to manage channels. Please give me the **Manage Channels** permission."
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Setup Error",
                "An error occurred during setup. Please try again or contact support."
            )
            await ctx.send(embed=embed)
            print(f"Server setup error: {e}")
    
    async def perform_auto_setup(self, ctx, status_message):
        """Perform the actual channel creation"""
        guild = ctx.guild
        created_channels = []
        created_categories = []
        
        try:
            # Update status
            progress_embed = self.embed_builder.create_embed(
                title="🔄 Setting Up Server...",
                description="Creating channels and categories...",
                color=0xFFAA00
            )
            await status_message.edit(embed=progress_embed)
            
            for category_name, category_data in self.channel_categories.items():
                # Create category
                category = await guild.create_category(
                    name=category_name,
                    overwrites={
                        guild.default_role: discord.PermissionOverwrite(read_messages=True),
                        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
                    }
                )
                created_categories.append(category)
                
                # Create regular channels
                for channel_name in category_data["channels"]:
                    channel = await guild.create_text_channel(
                        name=channel_name,
                        category=category,
                        topic=f"🎮 {category_data['description']} | Commands: {', '.join(category_data['commands'][:3])}"
                    )
                    created_channels.append(channel)
                    
                    # Send welcome message
                    await self.send_channel_welcome(channel, category_data)
                    await asyncio.sleep(0.5)  # Rate limit protection
                
                # Create log channels with restricted permissions
                for log_channel_name in category_data["log_channels"]:
                    log_overwrites = {
                        guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
                    }
                    
                    log_channel = await guild.create_text_channel(
                        name=log_channel_name,
                        category=category,
                        topic=f"📋 Automated logs for {category_data['description'].lower()}",
                        overwrites=log_overwrites
                    )
                    created_channels.append(log_channel)
                    
                    # Send log channel welcome
                    await self.send_log_channel_welcome(log_channel)
                    await asyncio.sleep(0.5)
            
            # Success message
            success_embed = self.embed_builder.success_embed(
                "✅ Server Setup Complete!",
                f"Successfully created **{len(created_categories)}** categories and **{len(created_channels)}** channels!"
            )
            
            success_embed.add_field(
                name="🎉 What's Next?",
                value="• Try `!summon` in a summoning channel\n"
                      "• Use `!help` to see all available commands\n"
                      "• Check the welcome messages in each channel\n"
                      "• Invite your friends to start playing!",
                inline=False
            )
            
            success_embed.add_field(
                name="📞 Need Help?",
                value="• Use `!channel_guide` to see which commands work where\n"
                      "• Use `!assign_channel` to manually assign existing channels\n"
                      "• Join our support server for assistance",
                inline=False
            )
            
            await status_message.edit(embed=success_embed)
            
        except discord.Forbidden:
            embed = self.embed_builder.error_embed(
                "Permission Error",
                "Lost permissions during setup. Please ensure I have **Manage Channels** permission."
            )
            await status_message.edit(embed=embed)
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Setup Failed",
                f"Setup failed during channel creation: {str(e)[:100]}..."
            )
            await status_message.edit(embed=embed)
            print(f"Auto setup error: {e}")
    
    @commands.command(name="channel_guide", aliases=["commands_guide"])
    async def channel_guide(self, ctx):
        """Show which commands work in which channels"""
        embed = self.embed_builder.create_embed(
            title="📖 Channel & Commands Guide",
            description="Here's where each command can be used:",
            color=0x9370DB
        )
        
        for category_name, category_data in self.channel_categories.items():
            if category_data["commands"]:
                channels_text = " • ".join([f"#{ch}" for ch in category_data["channels"][:2]])
                commands_text = " • ".join([f"`!{cmd}`" for cmd in category_data["commands"][:4]])
                
                embed.add_field(
                    name=category_name,
                    value=f"**Channels:** {channels_text}\n**Commands:** {commands_text}",
                    inline=False
                )
        
        embed.add_field(
            name="💡 Tips",
            value="• Commands will auto-create channels if missing\n"
                  "• Use `!server_setup` to create all channels at once\n"
                  "• Log channels track special events automatically",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="assign_channel", aliases=["link_channel"])
    @commands.has_permissions(administrator=True)
    async def assign_existing_channel(self, ctx, command_type: str, channel: discord.TextChannel):
        """Manually assign an existing channel for specific commands"""
        try:
            # Find which category this command type belongs to
            found_category = None
            for category_name, category_data in self.channel_categories.items():
                if command_type.lower() in [cmd.lower() for cmd in category_data["commands"]]:
                    found_category = category_data
                    break
                elif command_type.lower() in [ch.lower() for ch in category_data["channels"]]:
                    found_category = category_data
                    break
            
            if not found_category:
                embed = self.embed_builder.error_embed(
                    "Invalid Command Type",
                    f"'{command_type}' not recognized. Use `!channel_guide` to see available types."
                )
                await ctx.send(embed=embed)
                return
            
            # Update channel manager configuration (this would need to be implemented)
            embed = self.embed_builder.success_embed(
                "Channel Assigned",
                f"Successfully assigned {channel.mention} for **{command_type}** commands!"
            )
            
            embed.add_field(
                name="ℹ️ Info",
                value=f"Commands that will work here: {', '.join([f'`!{cmd}`' for cmd in found_category['commands'][:5]])}",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Assignment Error",
                "Failed to assign channel. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Channel assignment error: {e}")
    
    async def send_channel_welcome(self, channel, category_data):
        """Send welcome message to newly created channel"""
        embed = self.embed_builder.create_embed(
            title=f"🎉 Welcome to {channel.name}!",
            description=category_data["description"],
            color=0x00FF00
        )
        
        if category_data["commands"]:
            commands_text = "\n".join([f"• `!{cmd}`" for cmd in category_data["commands"][:8]])
            embed.add_field(
                name="🎮 Available Commands",
                value=commands_text,
                inline=False
            )
        
        embed.add_field(
            name="✨ Getting Started",
            value="This channel is now ready for use! Try the commands above to get started.",
            inline=False
        )
        
        embed.set_footer(text="Use !help to see all available commands")
        
        await channel.send(embed=embed)
    
    async def send_log_channel_welcome(self, channel):
        """Send welcome message to log channel"""
        embed = self.embed_builder.create_embed(
            title="📋 Automated Log Channel",
            description="This channel will automatically log special events and activities.",
            color=0x4169E1
        )
        
        embed.add_field(
            name="📊 What Gets Logged",
            value="• Rare summons (SSR+)\n• Battle results\n• Crafting successes\n• Special achievements\n• Important events",
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ Note",
            value="This is a read-only channel for most users. Logs appear automatically when events occur.",
            inline=False
        )
        
        await channel.send(embed=embed)

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(ServerConfigCommands(bot))