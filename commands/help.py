# Custom Help System for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List

from core.embed_utils import EmbedBuilder
from core.config import ADMIN_USER_ID

class CustomHelpCommand(commands.HelpCommand):
    """Custom help command with beautiful embeds and organized information"""
    
    def __init__(self):
        super().__init__(
            command_attrs={
                "help": "Show help information for commands",
                "aliases": ["h", "help_info"]
            }
        )
        self.embed_builder = EmbedBuilder()
    
    async def send_bot_help(self, mapping):
        """Send help for the entire bot"""
        embed = self.embed_builder.create_embed(
            title="🌸 KoKoroMichi - Command Help",
            description="Welcome to the advanced RPG bot! Here are all available commands organized by category.",
            color=0xFF69B4
        )
        
        # Command categories with their descriptions
        categories = {
            "Profile & Collection": {
                "commands": ["profile", "collection", "inspect", "inventory", "stats", "gallery", "showcase"],
                "description": "Manage your profile and character collection",
                "emoji": "👤"
            },
            "Summoning & Battles": {
                "commands": ["summon", "battle", "arena", "duel", "fight", "upgrade", "train", "rates", "quick_arena"],
                "description": "Summon characters and engage in combat",
                "emoji": "⚔️"
            },
            "Economy & Trading": {
                "commands": ["invest", "businesses", "collect", "auction", "daily", "portfolio", "market", "sell", "buy"],
                "description": "Build wealth and trade with others",
                "emoji": "💰"
            },
            "Guilds & Social": {
                "commands": ["guild", "factions", "join_guild", "leave_guild", "guild_info"],
                "description": "Join guilds and participate in faction warfare",
                "emoji": "🏰"
            },
            "Crafting & Materials": {
                "commands": ["craft", "gather", "materials", "relics", "equip", "unequip", "forge", "enhance"],
                "description": "Create items, collect materials, and manage relics",
                "emoji": "🔨"
            },
            "Pets & Companions": {
                "commands": ["pets", "adopt_pet", "feed_pet", "train_pet", "pet_adventure", "petrace"],
                "description": "Care for and train loyal pet companions",
                "emoji": "🐾"
            },
            "Events & Activities": {
                "commands": ["events", "dream", "dailyquest", "seasonal", "participate", "randomevent"],
                "description": "Participate in special events and activities",
                "emoji": "🎊"
            },
            "Achievements & Lore": {
                "commands": ["achievements", "lorebooks", "lore_achievements", "contests", "moodpoll", "fancontest"],
                "description": "Track progress, discover history, and join community events",
                "emoji": "🏆"
            },
            "Relationships & Fun": {
                "commands": ["intimate", "interact", "affection", "8ball", "roll", "choose", "fanclub", "mood"],
                "description": "Build relationships with characters and entertainment",
                "emoji": "💕"
            },
            "Boss Fights & Raids": {
                "commands": ["bossfight", "raid", "pvpboss", "challenge"],
                "description": "Take on powerful bosses and raid challenges",
                "emoji": "🐉"
            },
            "Mini Games & Quests": {
                "commands": ["quest", "trivia", "rps", "coinflip", "riddle", "mishap"],
                "description": "Enjoy mini-games and complete quests",
                "emoji": "🎲"
            },
            "Character Enhancement": {
                "commands": ["traits", "apply_trait", "remove_trait", "evolve", "awaken"],
                "description": "Enhance and customize your characters",
                "emoji": "✨"
            },
            "Server & Admin": {
                "commands": ["setup", "config", "admin", "backup", "maintenance"],
                "description": "Server management and administration",
                "emoji": "🛠️"
            },
            "Utility & Info": {
                "commands": ["about", "ping", "help", "status", "info"],
                "description": "Bot information and utilities",
                "emoji": "🔧"
            }
        }
        
        for category_name, category_data in categories.items():
            commands_list = []
            for cmd_name in category_data["commands"]:
                command = self.context.bot.get_command(cmd_name)
                if command and not command.hidden:
                    commands_list.append(f"`{self.context.clean_prefix}{cmd_name}`")
            
            if commands_list:
                embed.add_field(
                    name=f"{category_data['emoji']} {category_name}",
                    value=f"{category_data['description']}\n{' • '.join(commands_list)}",
                    inline=False
                )
        
        # Add footer with usage tips
        embed.add_field(
            name="💡 How to Use",
            value=f"• Use `{self.context.clean_prefix}help <command>` for detailed help on a specific command\n"
                  f"• Use `{self.context.clean_prefix}help <category>` for help on a command category\n"
                  f"• Arguments in `<>` are required, arguments in `[]` are optional",
            inline=False
        )
        
        embed.add_field(
            name="🚀 Getting Started",
            value=f"New to KoKoroMichi? Start with:\n"
                  f"1. `{self.context.clean_prefix}profile` - Create your profile\n"
                  f"2. `{self.context.clean_prefix}daily` - Claim daily rewards\n"
                  f"3. `{self.context.clean_prefix}summon` - Get your first character!",
            inline=False
        )
        
        embed.set_footer(text="Have fun exploring the realm! 🌸")
        
        await self.get_destination().send(embed=embed)
        
        # Send admin commands to DM if user is admin
        await self.send_admin_help_if_applicable()
    
    async def send_admin_help_if_applicable(self):
        """Send admin help to DM if user is admin"""
        user_id = str(self.context.author.id)
        if user_id == ADMIN_USER_ID:
            admin_embed = self.embed_builder.create_embed(
                title="🛠️ Admin Commands",
                description="Administrative commands available to you",
                color=0xFF0000
            )
            
            admin_embed.add_field(
                name="👥 User Management",
                value="• `!admin give <user> <item> <amount>` - Give items to users\n"
                      "• `!admin gold <user> <amount>` - Modify user's gold\n"
                      "• `!admin reset <user>` - Reset user data\n"
                      "• `!admin ban <user> [reason]` - Ban user from bot",
                inline=False
            )
            
            admin_embed.add_field(
                name="📊 Bot Management", 
                value="• `!admin stats` - View bot statistics\n"
                      "• `!admin backup` - Create data backup\n"
                      "• `!admin announce <message>` - Send announcements\n"
                      "• `!admin maintenance` - Toggle maintenance mode",
                inline=False
            )
            
            admin_embed.add_field(
                name="🔐 Security Note",
                value="Admin commands work in any channel but send detailed responses to DM for security.",
                inline=False
            )
            
            try:
                await self.context.author.send(embed=admin_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
    
    async def send_command_help(self, command):
        """Send help for a specific command"""
        embed = self.embed_builder.create_embed(
            title=f"📖 Command: {self.context.clean_prefix}{command.qualified_name}",
            description=command.help or "No description available.",
            color=0x00BFFF
        )
        
        # Command signature
        signature = self.get_command_signature(command)
        embed.add_field(
            name="📝 Usage",
            value=f"`{signature}`",
            inline=False
        )
        
        # Aliases
        if command.aliases:
            aliases = [f"`{self.context.clean_prefix}{alias}`" for alias in command.aliases]
            embed.add_field(
                name="🔗 Aliases",
                value=" • ".join(aliases),
                inline=True
            )
        
        # Cooldown info
        if command.cooldown:
            embed.add_field(
                name="⏱️ Cooldown",
                value=f"{command.cooldown.rate} times per {command.cooldown.per} seconds",
                inline=True
            )
        
        # Add examples if available
        examples = self.get_command_examples(command.name)
        if examples:
            embed.add_field(
                name="💡 Examples",
                value="\n".join(examples),
                inline=False
            )
        
        await self.get_destination().send(embed=embed)
    
    async def send_group_help(self, group):
        """Send help for a command group"""
        embed = self.embed_builder.create_embed(
            title=f"📚 Command Group: {self.context.clean_prefix}{group.qualified_name}",
            description=group.help or "No description available.",
            color=0x9370DB
        )
        
        # Subcommands
        if group.commands:
            subcommands = []
            for cmd in group.commands:
                if not cmd.hidden:
                    subcommands.append(f"`{self.context.clean_prefix}{cmd.qualified_name}` - {cmd.short_doc or 'No description'}")
            
            if subcommands:
                embed.add_field(
                    name="🔧 Subcommands",
                    value="\n".join(subcommands[:10]),  # Limit to 10 to avoid embed limits
                    inline=False
                )
                
                if len(subcommands) > 10:
                    embed.add_field(
                        name="📝 Note",
                        value=f"... and {len(subcommands) - 10} more subcommands",
                        inline=False
                    )
        
        # Usage
        signature = self.get_command_signature(group)
        embed.add_field(
            name="📝 Usage",
            value=f"`{signature}`",
            inline=False
        )
        
        await self.get_destination().send(embed=embed)
    
    async def send_category_help(self, cog):
        """Send help for a cog (command category)"""
        embed = self.embed_builder.create_embed(
            title=f"📂 Category: {cog.qualified_name}",
            description=cog.description or "No description available.",
            color=0x32CD32
        )
        
        # Get commands in this cog
        commands_list = []
        for command in cog.get_commands():
            if not command.hidden:
                commands_list.append(f"`{self.context.clean_prefix}{command.name}` - {command.short_doc or 'No description'}")
        
        if commands_list:
            # Split into chunks if too many commands
            chunk_size = 10
            chunks = [commands_list[i:i + chunk_size] for i in range(0, len(commands_list), chunk_size)]
            
            for i, chunk in enumerate(chunks):
                field_name = "🔧 Commands" if i == 0 else f"🔧 Commands (cont. {i + 1})"
                embed.add_field(
                    name=field_name,
                    value="\n".join(chunk),
                    inline=False
                )
        
        await self.get_destination().send(embed=embed)
    
    async def command_not_found(self, string):
        """Handle when a command is not found"""
        # Try to find similar commands
        all_commands = [cmd.name for cmd in self.context.bot.commands if not cmd.hidden]
        all_commands.extend([alias for cmd in self.context.bot.commands for alias in cmd.aliases])
        
        # Simple similarity check
        similar = [cmd for cmd in all_commands if string.lower() in cmd.lower() or cmd.lower() in string.lower()]
        
        if similar:
            suggestions = " • ".join([f"`{self.context.clean_prefix}{cmd}`" for cmd in similar[:5]])
            return f"Command `{string}` not found. Did you mean: {suggestions}?"
        else:
            return f"Command `{string}` not found. Use `{self.context.clean_prefix}help` to see all commands."
    
    def get_command_examples(self, command_name: str) -> List[str]:
        """Get example usage for specific commands"""
        examples = {
            "profile": [
                f"`{self.context.clean_prefix}profile` - View your own profile",
                f"`{self.context.clean_prefix}profile @user` - View another user's profile"
            ],
            "summon": [
                f"`{self.context.clean_prefix}summon` - Summon 1 character",
                f"`{self.context.clean_prefix}summon 10` - Summon 10 characters"
            ],
            "battle": [
                f"`{self.context.clean_prefix}battle` - Battle with your strongest character",
                f"`{self.context.clean_prefix}battle Sakura` - Battle with specific character"
            ],
            "invest": [
                f"`{self.context.clean_prefix}invest cafe` - Invest in a café",
                f"`{self.context.clean_prefix}invest` - View investment options"
            ],
            "craft": [
                f"`{self.context.clean_prefix}craft health_potion` - Craft a health potion",
                f"`{self.context.clean_prefix}craft iron_sword 3` - Craft 3 iron swords"
            ],
            "guild": [
                f"`{self.context.clean_prefix}guild create \"My Guild\" celestial` - Create a guild",
                f"`{self.context.clean_prefix}guild join guild123` - Join a guild"
            ]
        }
        
        return examples.get(command_name, [])


class HelpCommands(commands.Cog):
    """Help command system and documentation"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        
        # Set the custom help command
        self.original_help = bot.help_command
        bot.help_command = CustomHelpCommand()
        bot.help_command.cog = self
    
    def help_cog_unload(self):
        """Restore original help command when cog is unloaded"""
        self.bot.help_command = self.original_help
    
    @commands.command(name="quickstart", aliases=["start", "guide"])
    async def quickstart_guide(self, ctx):
        """Get a quick start guide for new players"""
        embed = self.embed_builder.create_embed(
            title="🚀 Quick Start Guide",
            description="Welcome to KoKoroMichi! Here's how to get started on your adventure.",
            color=0x00FF7F
        )
        
        steps = [
            {
                "title": "1️⃣ Create Your Profile",
                "content": f"Use `{ctx.prefix}profile` to create your account and get starting resources!",
                "commands": [f"{ctx.prefix}profile"]
            },
            {
                "title": "2️⃣ Claim Daily Rewards",
                "content": f"Use `{ctx.prefix}daily` to get your first gold and gems!",
                "commands": [f"{ctx.prefix}daily"]
            },
            {
                "title": "3️⃣ Summon Your First Character",
                "content": f"Use `{ctx.prefix}summon` to get your first character using gold!",
                "commands": [f"{ctx.prefix}summon", f"{ctx.prefix}rates"]
            },
            {
                "title": "4️⃣ Start Battling",
                "content": f"Use `{ctx.prefix}battle` to fight NPCs and earn XP and gold!",
                "commands": [f"{ctx.prefix}battle", f"{ctx.prefix}arena"]
            },
            {
                "title": "5️⃣ Build Your Economy",
                "content": f"Use `{ctx.prefix}invest` to start businesses for passive income!",
                "commands": [f"{ctx.prefix}invest", f"{ctx.prefix}businesses"]
            }
        ]
        
        for step in steps:
            commands_text = " • ".join([f"`{cmd}`" for cmd in step["commands"]])
            embed.add_field(
                name=step["title"],
                value=f"{step['content']}\n**Commands:** {commands_text}",
                inline=False
            )
        
        embed.add_field(
            name="🎯 Pro Tips",
            value="• Check `!achievements` to see what goals to work towards\n"
                  "• Join a guild with `!guild` for team bonuses\n"
                  "• Participate in events with `!events` for special rewards\n"
                  "• Use `!help <command>` to learn more about any command",
            inline=False
        )
        
        embed.set_footer(text="Have questions? Use !help for detailed command information!")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="features")
    async def show_features(self, ctx):
        """Display detailed information about bot features"""
        embed = self.embed_builder.create_embed(
            title="🌟 KoKoroMichi Features",
            description="Discover all the amazing features this bot has to offer!",
            color=0xFF1493
        )
        
        features = [
            {
                "name": "🎭 Character Collection",
                "description": "Summon and collect over 50 unique characters with 7 rarity tiers from N to Mythic!"
            },
            {
                "name": "⚔️ Strategic Combat",
                "description": "Engage in turn-based battles with elemental advantages, critical hits, and skill systems!"
            },
            {
                "name": "🏰 Guild System", 
                "description": "Join one of 4 factions, create guilds, manage resources, and participate in guild wars!"
            },
            {
                "name": "💼 Economy & Investment",
                "description": "Build businesses, trade in auction houses, and generate passive income!"
            },
            {
                "name": "🔨 Crafting & Alchemy",
                "description": "Gather materials, craft equipment, and create powerful enhancement items!"
            },
            {
                "name": "🎊 Events & Activities",
                "description": "Participate in seasonal events, dream sequences, and daily quests!"
            },
            {
                "name": "🏆 Achievements & Lore",
                "description": "Unlock achievements, collect lore books, and discover the realm's rich history!"
            },
            {
                "name": "📈 Progression Systems",
                "description": "Level up characters, increase crafting skills, build daily streaks, and earn achievement points!"
            }
        ]
        
        for feature in features:
            embed.add_field(
                name=feature["name"],
                value=feature["description"],
                inline=False
            )
        
        embed.add_field(
            name="🚀 Getting Started",
            value=f"Use `{ctx.prefix}quickstart` for a step-by-step guide to begin your adventure!",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="commands")
    async def list_commands(self, ctx, category: str = None):
        """List all commands, optionally filtered by category"""
        if category:
            # Try to find the cog
            cog = self.bot.get_cog(category.title() + "Commands")
            if cog:
                await ctx.send_help(cog)
                return
            else:
                embed = self.embed_builder.error_embed(
                    "Category Not Found",
                    f"Category '{category}' not found. Use `{ctx.prefix}help` to see all categories."
                )
                await ctx.send(embed=embed)
                return
        
        # Send general help
        await ctx.send_help()


async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(HelpCommands(bot))