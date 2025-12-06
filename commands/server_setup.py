# ---------------- Metadata ----------------
name = "server_setup_system"
description = "Comprehensive server setup system for managing required channels and bot configuration."
features = (
    "• `!setup` → Show current channel configurations with status\n"
    "• `!link <feature> <#channel>` → Link features to specific channels\n"
    "• `!replace <feature> <#channel>` → Replace existing channel links\n"
    "• `!unlink <feature>` → Remove channel mappings\n"
    "• Admin/owner permission controls for setup commands\n"
    "• Automatic JSON configuration management\n"
    "• Support for Arena, Summon, and Guild channel features\n"
    "• Error handling and validation for all setup operations"
)
# ------------------------------------------

import discord
from discord.ext import commands
import json
import os
from typing import Optional

CONFIG_FILE = os.path.join(os.path.dirname(__file__), '../data/server_config.json')

class ServerSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.features = ["arena", "summon", "guild"]
        self.ensure_config_file()

    def ensure_config_file(self):
        """Create config file if it doesn't exist"""
        if not os.path.exists(CONFIG_FILE):
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, 'w') as f:
                json.dump({}, f, indent=2)

    def load_config(self):
        """Load server configuration"""
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_config(self, config):
        """Save server configuration"""
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

    def check_admin_permissions(self, ctx):
        """Check if user is server owner or administrator"""
        return (ctx.author.guild_permissions.administrator or 
                ctx.author == ctx.guild.owner)

    @commands.command(name="setup")
    async def setup_status(self, ctx):
        """Show current channel setup status"""
        if not self.check_admin_permissions(ctx):
            embed = discord.Embed(
                title="⚠️ Permission Denied",
                description="Only server owner or administrators can use setup commands.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return

        config = self.load_config()
        guild_id = str(ctx.guild.id)
        guild_config = config.get(guild_id, {})

        embed = discord.Embed(
            title="🔧 Server Setup Status",
            description="Current channel configuration for bot features:",
            color=0x00ff00
        )

        for feature in self.features:
            channel_key = f"{feature}_channel"
            channel_id = guild_config.get(channel_key)
            
            if channel_id:
                channel = ctx.guild.get_channel(int(channel_id))
                if channel:
                    status = f"✅ {channel.mention}"
                else:
                    status = "❌ Channel not found (deleted?)"
            else:
                status = "❌ Not linked"
            
            embed.add_field(
                name=f"{feature.capitalize()} Commands",
                value=status,
                inline=True
            )

        embed.add_field(
            name="📝 Available Commands",
            value="`!link <feature> <#channel>` - Link feature to channel\n"
                  "`!replace <feature> <#channel>` - Replace existing link\n"
                  "`!unlink <feature>` - Remove channel link",
            inline=False
        )

        embed.add_field(
            name="🎯 Supported Features",
            value="• **arena** - Arena and battle commands\n"
                  "• **summon** - Waifu summoning commands\n"
                  "• **guild** - Guild management commands",
            inline=False
        )

        embed.set_footer(text="Use these commands to configure where bot features can be used.")
        await ctx.send(embed=embed)

    @commands.command(name="link")
    async def link_channel(self, ctx, feature: str = None, channel: Optional[discord.TextChannel] = None):
        """Link a feature to a channel"""
        if not self.check_admin_permissions(ctx):
            embed = discord.Embed(
                title="⚠️ Permission Denied",
                description="Only server owner or administrators can use setup commands.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return

        if not feature or not channel:
            embed = discord.Embed(
                title="❌ Missing Parameters",
                description="Usage: `!link <feature> <#channel>`\n\n"
                          f"Available features: {', '.join(self.features)}",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return

        feature = feature.lower()
        if feature not in self.features:
            embed = discord.Embed(
                title="❌ Invalid Feature",
                description=f"Available features: {', '.join(self.features)}",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return

        config = self.load_config()
        guild_id = str(ctx.guild.id)
        
        if guild_id not in config:
            config[guild_id] = {}

        channel_key = f"{feature}_channel"
        
        # Check if already linked
        if channel_key in config[guild_id]:
            existing_channel_id = config[guild_id][channel_key]
            existing_channel = ctx.guild.get_channel(int(existing_channel_id))
            embed = discord.Embed(
                title="⚠️ Already Linked",
                description=f"{feature.capitalize()} is already linked to {existing_channel.mention if existing_channel else 'a deleted channel'}.\n"
                          f"Use `!replace {feature} {channel.mention}` to change it.",
                color=0xffa500
            )
            await ctx.send(embed=embed)
            return

        # Link the channel
        config[guild_id][channel_key] = str(channel.id)
        self.save_config(config)

        embed = discord.Embed(
            title="✅ Channel Linked",
            description=f"{feature.capitalize()} commands are now linked to {channel.mention}",
            color=0x00ff00
        )
        await ctx.send(embed=embed)

    @commands.command(name="replace")
    async def replace_channel(self, ctx, feature: str = None, channel: Optional[discord.TextChannel] = None):
        """Replace existing channel link"""
        if not self.check_admin_permissions(ctx):
            embed = discord.Embed(
                title="⚠️ Permission Denied", 
                description="Only server owner or administrators can use setup commands.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return

        if not feature or not channel:
            embed = discord.Embed(
                title="❌ Missing Parameters",
                description="Usage: `!replace <feature> <#channel>`\n\n"
                          f"Available features: {', '.join(self.features)}",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return

        feature = feature.lower()
        if feature not in self.features:
            embed = discord.Embed(
                title="❌ Invalid Feature",
                description=f"Available features: {', '.join(self.features)}",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return

        config = self.load_config()
        guild_id = str(ctx.guild.id)
        
        if guild_id not in config:
            config[guild_id] = {}

        channel_key = f"{feature}_channel"
        config[guild_id][channel_key] = str(channel.id)
        self.save_config(config)

        embed = discord.Embed(
            title="✅ Channel Replaced",
            description=f"{feature.capitalize()} commands are now linked to {channel.mention}",
            color=0x00ff00
        )
        await ctx.send(embed=embed)

    @commands.command(name="unlink")
    async def unlink_channel(self, ctx, feature: str = None):
        """Remove channel link for a feature"""
        if not self.check_admin_permissions(ctx):
            embed = discord.Embed(
                title="⚠️ Permission Denied",
                description="Only server owner or administrators can use setup commands.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return

        if not feature:
            embed = discord.Embed(
                title="❌ Missing Parameter",
                description="Usage: `!unlink <feature>`\n\n"
                          f"Available features: {', '.join(self.features)}",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return

        feature = feature.lower()
        if feature not in self.features:
            embed = discord.Embed(
                title="❌ Invalid Feature",
                description=f"Available features: {', '.join(self.features)}",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return

        config = self.load_config()
        guild_id = str(ctx.guild.id)
        
        if guild_id not in config or f"{feature}_channel" not in config[guild_id]:
            embed = discord.Embed(
                title="⚠️ Not Linked",
                description=f"{feature.capitalize()} is not currently linked to any channel.",
                color=0xffa500
            )
            await ctx.send(embed=embed)
            return

        # Remove the link
        del config[guild_id][f"{feature}_channel"]
        
        # Clean up empty guild config
        if not config[guild_id]:
            del config[guild_id]
            
        self.save_config(config)

        embed = discord.Embed(
            title="✅ Channel Unlinked",
            description=f"{feature.capitalize()} commands are no longer restricted to a specific channel.",
            color=0x00ff00
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerSetup(bot))