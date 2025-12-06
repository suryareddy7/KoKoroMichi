# Miscellaneous Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List
import random
import asyncio
from datetime import datetime

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from utils.helpers import format_number
from utils.channel_manager import check_channel_restriction

class MiscCommands(commands.Cog):
    """Miscellaneous utility commands and fun features"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        
        # Fun responses and interactions
        self.greetings = [
            "Hello there, adventurer! Ready for another day in the realm?",
            "Greetings! The waifus are excited to see you today!",
            "Welcome back! Your adventure continues...",
            "Hey there! What epic quest will you embark on today?",
            "Salutations, brave soul! The realm awaits your presence!"
        ]
        
        self.compliments = [
            "You're an amazing adventurer!",
            "Your collection is truly impressive!",
            "You have excellent taste in characters!",
            "Your dedication to the realm is inspiring!",
            "You're one of the finest players I've encountered!"
        ]
        
        # 8-ball responses
        self.eight_ball_responses = [
            "🎱 It is certain", "🎱 It is decidedly so", "🎱 Without a doubt",
            "🎱 Yes definitely", "🎱 You may rely on it", "🎱 As I see it, yes",
            "🎱 Most likely", "🎱 Outlook good", "🎱 Yes", "🎱 Signs point to yes",
            "🎱 Reply hazy, try again", "🎱 Ask again later", "🎱 Better not tell you now",
            "🎱 Cannot predict now", "🎱 Concentrate and ask again",
            "🎱 Don't count on it", "🎱 My reply is no", "🎱 My sources say no",
            "🎱 Outlook not so good", "🎱 Very doubtful"
        ]
    
    @commands.command(name="about", aliases=["info", "botinfo"])
    async def about_bot(self, ctx):
        """Information about the KoKoroMichi bot"""
        embed = self.embed_builder.create_embed(
            title="🌸 KoKoroMichi - Advanced RPG Bot",
            description="An immersive anime-themed RPG experience for Discord!",
            color=0xFF69B4
        )
        
        embed.add_field(
            name="🎮 Features",
            value="• Character Collection & Gacha System\n"
                  "• Strategic RPG Combat\n"
                  "• Guild & Faction Warfare\n"
                  "• Economy & Investment System\n"
                  "• Crafting & Alchemy\n"
                  "• Seasonal Events & Activities\n"
                  "• Achievement & Lore System",
            inline=False
        )
        
        embed.add_field(
            name="📊 Statistics",
            value=f"Servers: {len(self.bot.guilds)}\n"
                  f"Users: {data_manager.get_users_count()}\n"
                  f"Commands: 35+\n"
                  f"Version: 3.0.0 Advanced",
            inline=True
        )
        
        embed.add_field(
            name="🛠️ Technical",
            value=f"Built with Discord.py {discord.__version__}\n"
                  f"Language: Python 3.11+\n"
                  f"Architecture: Advanced Modular\n"
                  f"Latency: {self.bot.latency * 1000:.1f}ms",
            inline=True
        )
        
        embed.add_field(
            name="🚀 Getting Started",
            value="Use `!help` to see all commands\n"
                  "Start with `!profile` to create your account\n"
                  "Then try `!summon` to get your first character!",
            inline=False
        )
        
        embed.set_footer(text="Created with ❤️ for the anime community")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="ping")
    async def ping(self, ctx):
        """Check bot latency and response time"""
        start_time = datetime.now()
        
        embed = self.embed_builder.create_embed(
            title="🏓 Pong!",
            description="Checking connection...",
            color=0x00FF00
        )
        
        message = await ctx.send(embed=embed)
        
        # Calculate response time
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds() * 1000
        
        # Update embed with results
        embed = self.embed_builder.create_embed(
            title="🏓 Pong!",
            color=0x00FF00
        )
        
        embed.add_field(
            name="📡 Latency",
            value=f"Bot Latency: {self.bot.latency * 1000:.1f}ms\n"
                  f"Response Time: {response_time:.1f}ms",
            inline=True
        )
        
        # Status indicator
        if self.bot.latency * 1000 < 100:
            status = "🟢 Excellent"
        elif self.bot.latency * 1000 < 200:
            status = "🟡 Good"
        else:
            status = "🟠 Fair"
        
        embed.add_field(
            name="📈 Status",
            value=status,
            inline=True
        )
        
        await message.edit(embed=embed)
    
    @commands.command(name="hello", aliases=["hi", "hey"])
    async def greet_user(self, ctx):
        """Greet the user with a friendly message"""
        user_data = data_manager.get_user_data(str(ctx.author.id))
        greeting = random.choice(self.greetings)
        
        embed = self.embed_builder.create_embed(
            title=f"👋 Hello, {ctx.author.display_name}!",
            description=greeting,
            color=0xFFB6C1
        )
        
        # Add personalized info if user has data
        if user_data.get("level", 1) > 1:
            embed.add_field(
                name="🌟 Your Progress",
                value=f"Level: {user_data.get('level', 1)}\n"
                      f"Characters: {len(user_data.get('claimed_waifus', []))}\n"
                      f"Gold: {format_number(user_data.get('gold', 0))}",
                inline=True
            )
        
        embed.add_field(
            name="💡 Quick Actions",
            value="• `!daily` - Claim daily rewards\n"
                  "• `!profile` - View your profile\n"
                  "• `!summon` - Get new characters",
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="8ball", aliases=["eightball", "ask"])
    @check_channel_restriction()
    async def eight_ball(self, ctx, *, question: str = None):
        """Ask the magic 8-ball a question"""
        if not question:
            embed = self.embed_builder.error_embed(
                "No Question",
                "Please ask a question! Example: `!8ball Will I get a legendary character?`"
            )
            await ctx.send(embed=embed)
            return
        
        if len(question) > 200:
            embed = self.embed_builder.error_embed(
                "Question Too Long",
                "Please keep your question under 200 characters."
            )
            await ctx.send(embed=embed)
            return
        
        # Add thinking animation
        thinking_embed = self.embed_builder.create_embed(
            title="🔮 Consulting the Oracle...",
            description="*The magic 8-ball swirls with mystical energy...*",
            color=0x9370DB
        )
        message = await ctx.send(embed=thinking_embed)
        
        await asyncio.sleep(2)  # Dramatic pause
        
        response = random.choice(self.eight_ball_responses)
        
        embed = self.embed_builder.create_embed(
            title="🔮 The Oracle Speaks",
            color=0x9370DB
        )
        
        embed.add_field(
            name="❓ Your Question",
            value=question,
            inline=False
        )
        
        embed.add_field(
            name="💬 Answer",
            value=response,
            inline=False
        )
        
        await message.edit(embed=embed)
    
    @commands.command(name="roll", aliases=["dice"])
    @check_channel_restriction()
    async def roll_dice(self, ctx, dice: str = "1d6"):
        """Roll dice (format: XdY, e.g., 2d6, 1d20)"""
        try:
            # Parse dice notation
            if 'd' not in dice.lower():
                embed = self.embed_builder.error_embed(
                    "Invalid Format",
                    "Use format like `1d6`, `2d20`, or `3d8`"
                )
                await ctx.send(embed=embed)
                return
            
            parts = dice.lower().split('d')
            if len(parts) != 2:
                raise ValueError("Invalid format")
            
            num_dice = int(parts[0]) if parts[0] else 1
            num_sides = int(parts[1])
            
            # Validate input
            if num_dice < 1 or num_dice > 20:
                embed = self.embed_builder.error_embed(
                    "Invalid Dice Count",
                    "Number of dice must be between 1 and 20"
                )
                await ctx.send(embed=embed)
                return
            
            if num_sides < 2 or num_sides > 100:
                embed = self.embed_builder.error_embed(
                    "Invalid Sides",
                    "Number of sides must be between 2 and 100"
                )
                await ctx.send(embed=embed)
                return
            
            # Roll dice
            rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
            total = sum(rolls)
            
            embed = self.embed_builder.create_embed(
                title=f"🎲 Rolling {dice.upper()}",
                color=0x32CD32
            )
            
            if num_dice == 1:
                embed.add_field(
                    name="Result",
                    value=f"**{total}**",
                    inline=True
                )
            else:
                embed.add_field(
                    name="Individual Rolls",
                    value=" + ".join(map(str, rolls)),
                    inline=False
                )
                
                embed.add_field(
                    name="Total",
                    value=f"**{total}**",
                    inline=True
                )
                
                embed.add_field(
                    name="Average",
                    value=f"{total / num_dice:.1f}",
                    inline=True
                )
            
            await ctx.send(embed=embed)
            
        except ValueError:
            embed = self.embed_builder.error_embed(
                "Invalid Format",
                "Use format like `1d6`, `2d20`, or `3d8`"
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Roll Error",
                "Unable to roll dice. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Roll error: {e}")
    
    @commands.command(name="coinflip", aliases=["flip", "coin"])
    async def coin_flip(self, ctx):
        """Flip a coin"""
        # Add suspense
        embed = self.embed_builder.create_embed(
            title="🪙 Flipping Coin...",
            description="*The coin spins through the air...*",
            color=0xFFD700
        )
        message = await ctx.send(embed=embed)
        
        await asyncio.sleep(1.5)
        
        result = random.choice(["Heads", "Tails"])
        emoji = "👑" if result == "Heads" else "🏛️"
        
        embed = self.embed_builder.create_embed(
            title=f"🪙 {emoji} {result}!",
            description=f"The coin landed on **{result}**",
            color=0xFFD700
        )
        
        await message.edit(embed=embed)
    
    @commands.command(name="choose", aliases=["pick"])
    @check_channel_restriction()
    async def choose_option(self, ctx, *, options: str):
        """Choose randomly from a list of options (separate with commas)"""
        if not options:
            embed = self.embed_builder.error_embed(
                "No Options",
                "Please provide options separated by commas!\n"
                "Example: `!choose pizza, burger, sushi`"
            )
            await ctx.send(embed=embed)
            return
        
        # Split and clean options
        option_list = [option.strip() for option in options.split(',')]
        option_list = [opt for opt in option_list if opt]  # Remove empty strings
        
        if len(option_list) < 2:
            embed = self.embed_builder.error_embed(
                "Not Enough Options",
                "Please provide at least 2 options separated by commas!"
            )
            await ctx.send(embed=embed)
            return
        
        if len(option_list) > 20:
            embed = self.embed_builder.error_embed(
                "Too Many Options",
                "Please provide no more than 20 options!"
            )
            await ctx.send(embed=embed)
            return
        
        # Thinking animation
        embed = self.embed_builder.create_embed(
            title="🤔 Deciding...",
            description="*Carefully considering all options...*",
            color=0x9370DB
        )
        message = await ctx.send(embed=embed)
        
        await asyncio.sleep(1.5)
        
        chosen = random.choice(option_list)
        
        embed = self.embed_builder.create_embed(
            title="🎯 Decision Made!",
            color=0x00FF00
        )
        
        embed.add_field(
            name="🎲 Options",
            value=", ".join(option_list),
            inline=False
        )
        
        embed.add_field(
            name="✨ I choose",
            value=f"**{chosen}**",
            inline=False
        )
        
        await message.edit(embed=embed)
    
    @commands.command(name="compliment", aliases=["praise"])
    async def give_compliment(self, ctx, member: discord.Member = None):
        """Give a compliment to yourself or someone else"""
        target = member or ctx.author
        compliment = random.choice(self.compliments)
        
        embed = self.embed_builder.create_embed(
            title="💝 Compliment Time!",
            description=f"{target.mention}, {compliment}",
            color=0xFFB6C1
        )
        
        # Add some encouraging stats if available
        if target == ctx.author:
            user_data = data_manager.get_user_data(str(target.id))
            if user_data.get("level", 1) > 1:
                embed.add_field(
                    name="🌟 Your Achievements",
                    value=f"You've reached level {user_data.get('level', 1)} and collected "
                          f"{len(user_data.get('claimed_waifus', []))} characters!",
                    inline=False
                )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="serverinfo", aliases=["server"])
    async def server_info(self, ctx):
        """Display information about the current server"""
        if not ctx.guild:
            embed = self.embed_builder.error_embed(
                "DM Channel",
                "This command can only be used in a server!"
            )
            await ctx.send(embed=embed)
            return
        
        guild = ctx.guild
        
        embed = self.embed_builder.create_embed(
            title=f"🏰 {guild.name}",
            color=0x7289DA
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Basic server info
        embed.add_field(
            name="📊 Server Stats",
            value=f"Members: {guild.member_count:,}\n"
                  f"Channels: {len(guild.channels)}\n"
                  f"Roles: {len(guild.roles)}\n"
                  f"Emojis: {len(guild.emojis)}",
            inline=True
        )
        
        # Creation date
        created_at = guild.created_at.strftime("%B %d, %Y")
        embed.add_field(
            name="📅 Created",
            value=created_at,
            inline=True
        )
        
        # Owner info
        embed.add_field(
            name="👑 Owner",
            value=guild.owner.mention if guild.owner else "Unknown",
            inline=True
        )
        
        # Boost info
        if guild.premium_subscription_count:
            embed.add_field(
                name="💎 Nitro Boosts",
                value=f"Level {guild.premium_tier}\n"
                      f"{guild.premium_subscription_count} boosts",
                inline=True
            )
        
        embed.set_footer(text=f"Server ID: {guild.id}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="avatar")
    async def show_avatar(self, ctx, member: discord.Member = None):
        """Display a user's avatar"""
        target = member or ctx.author
        
        embed = self.embed_builder.create_embed(
            title=f"🖼️ {target.display_name}'s Avatar",
            color=0x9370DB
        )
        
        # Get avatar URL
        avatar_url = target.avatar.url if target.avatar else target.default_avatar.url
        embed.set_image(url=avatar_url)
        
        embed.add_field(
            name="🔗 Direct Link",
            value=f"[Click here for full size]({avatar_url})",
            inline=False
        )
        
        await ctx.send(embed=embed)


async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(MiscCommands(bot))