# Contest and Social Events System for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List, Any
import random
from datetime import datetime, timedelta
import asyncio

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from core.config import FEATURES

class ContestsCommands(commands.Cog):
    """Contest system and social events for community engagement"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        self.active_contests = {}
        self.active_polls = {}
        
    @commands.command(name="contests", aliases=["contest"])
    async def view_contests(self, ctx):
        """View active contests and competitions"""
        try:
            contest_data = data_manager.get_game_data("contest_system")
            if not contest_data:
                contest_data = data_manager._load_json(data_manager.data_dir / "contest_system.json")
            
            embed = self.embed_builder.create_embed(
                title="🏆 Active Contests & Competitions",
                description="Join exciting community contests to win amazing rewards!",
                color=0xFFD700
            )
            
            # Arena tournaments
            arena_info = contest_data.get("global_events", {}).get("arena_tournaments", {})
            if arena_info:
                rewards = arena_info.get("rewards", {})
                arena_text = ""
                for place, reward in rewards.items():
                    arena_text += f"**{place} Place**: {reward.get('coins', 0):,} coins, {reward.get('title', 'Title')}\n"
                
                embed.add_field(
                    name="⚔️ Arena Tournament",
                    value=arena_text,
                    inline=False
                )
            
            # Guild competitions
            guild_info = contest_data.get("global_events", {}).get("guild_competitions", {})
            if guild_info:
                embed.add_field(
                    name="🏰 Guild Competitions",
                    value="Compete with your guild for ultimate glory! Use `!guild compete` to participate.",
                    inline=False
                )
            
            embed.add_field(
                name="📝 How to Participate",
                value="• Use `!contest join <type>` to enter a contest\n• Check `!leaderboard` for current standings\n• Contests reset weekly with new themes",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Contest Error",
                "Unable to load contest information. Please try again later."
            )
            await ctx.send(embed=embed)
    
    @commands.command(name="moodpoll", aliases=["mood"])
    async def mood_poll(self, ctx):
        """Participate in daily mood polls"""
        try:
            social_data = data_manager._load_json(data_manager.data_dir / "social_events.json")
            mood_polls = social_data.get("mood_polls", {})
            
            # Get today's theme
            today = datetime.now().day % len(mood_polls.get("daily_themes", []))
            theme_data = mood_polls["daily_themes"][today]
            
            embed = self.embed_builder.create_embed(
                title=f"🎭 Today's Mood: {theme_data['theme']}",
                description="Vote for your character's mood to receive special buffs!",
                color=0xFF69B4
            )
            
            mood_text = ""
            for i, mood in enumerate(theme_data["moods"], 1):
                buff = theme_data.get("buffs", {}).get(mood, "No special effect")
                mood_text += f"{i}️⃣ **{mood}** - {buff}\n"
            
            embed.add_field(
                name="🗳️ Available Moods",
                value=mood_text,
                inline=False
            )
            
            embed.add_field(
                name="💰 Rewards",
                value=f"Participation: {mood_polls.get('rewards', {}).get('participation', 100)} coins\nWinning mood: {mood_polls.get('rewards', {}).get('winning_mood', 250)} coins",
                inline=True
            )
            
            # Add reaction buttons
            message = await ctx.send(embed=embed)
            for i in range(len(theme_data["moods"])):
                await message.add_reaction(f"{i+1}️⃣")
            
            # Store poll data
            poll_id = f"{ctx.guild.id}_{datetime.now().strftime('%Y%m%d')}"
            self.active_polls[poll_id] = {
                "message_id": message.id,
                "theme": theme_data,
                "votes": {},
                "expires": datetime.now() + timedelta(hours=1)
            }
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Mood Poll Error",
                "Unable to create mood poll. Please try again later."
            )
            await ctx.send(embed=embed)
    
    @commands.command(name="fancontest", aliases=["fanart"])
    async def fan_contest(self, ctx, contest_type: str = None):
        """Join fan contests for creative expression"""
        try:
            social_data = data_manager._load_json(data_manager.data_dir / "social_events.json")
            contests = social_data.get("fan_contests", {})
            contest_types = contests.get("contest_types", [])
            
            if not contest_type:
                # Show available contest types
                embed = self.embed_builder.create_embed(
                    title="🎨 Fan Contest Hub",
                    description="Express your creativity and win amazing rewards!",
                    color=0x9370DB
                )
                
                types_text = ""
                for contest in contest_types:
                    types_text += f"**{contest['type'].title()}**: {contest['description']}\n"
                
                embed.add_field(
                    name="📝 Contest Types",
                    value=types_text,
                    inline=False
                )
                
                embed.add_field(
                    name="🏆 Rewards",
                    value=f"Winner: {contests.get('rewards', {}).get('winner', {}).get('coins', 1000)} coins + {contests.get('rewards', {}).get('winner', {}).get('title', 'Champion')} title\nParticipant: {contests.get('rewards', {}).get('participant', {}).get('coins', 200)} coins",
                    inline=False
                )
                
                embed.add_field(
                    name="💡 How to Join",
                    value="Use `!fancontest <type>` to join a specific contest!",
                    inline=False
                )
                
                await ctx.send(embed=embed)
                return
            
            # Find specific contest type
            contest_info = None
            for contest in contest_types:
                if contest["type"].lower() == contest_type.lower():
                    contest_info = contest
                    break
            
            if not contest_info:
                embed = self.embed_builder.error_embed(
                    "Contest Not Found",
                    f"Contest type '{contest_type}' not found. Use `!fancontest` to see available types."
                )
                await ctx.send(embed=embed)
                return
            
            # Create contest participation embed
            embed = self.embed_builder.create_embed(
                title=f"🎨 {contest_info['title']}",
                description=contest_info['description'],
                color=0x9370DB
            )
            
            embed.add_field(
                name="⏰ Duration",
                value=f"{contest_info['duration'] // 60} minutes",
                inline=True
            )
            
            embed.add_field(
                name="🎯 Instructions",
                value="Reply to this message with your entry! Others can vote using reactions.",
                inline=False
            )
            
            message = await ctx.send(embed=embed)
            
            # Add voting reactions
            for emoji in contests.get("emoji_reactions", ["🏆", "⭐", "💖"])[:5]:
                await message.add_reaction(emoji)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Fan Contest Error",
                "Unable to create fan contest. Please try again later."
            )
            await ctx.send(embed=embed)
    
    @commands.command(name="petrace", aliases=["race"])
    async def pet_race(self, ctx):
        """Organize pet racing events"""
        try:
            social_data = data_manager._load_json(data_manager.data_dir / "social_events.json")
            race_data = social_data.get("pet_races", {})
            
            # Check if user has pets
            user_data = data_manager.get_user_data(str(ctx.author.id))
            user_pets = user_data.get("pets", [])
            
            if not user_pets:
                embed = self.embed_builder.info_embed(
                    "No Pets",
                    "You need pets to participate in races! Use `!pets` to get started with pet companions."
                )
                await ctx.send(embed=embed)
                return
            
            # Show race types
            embed = self.embed_builder.create_embed(
                title="🏁 Pet Racing Championship",
                description="Enter your fastest companion in exciting races!",
                color=0x00FF7F
            )
            
            race_types = race_data.get("race_types", [])
            types_text = ""
            for race in race_types:
                duration_min = race["duration"] // 60
                types_text += f"**{race['name']}**: {race['distance']} distance, {duration_min}min, {race['participants']} racers\n"
            
            embed.add_field(
                name="🏃 Race Types",
                value=types_text,
                inline=False
            )
            
            # Show rewards
            rewards = race_data.get("rewards", {})
            reward_text = ""
            for place, reward in rewards.items():
                if place != "participation":
                    reward_text += f"**{place}**: {reward.get('coins', 0)} coins + {reward.get('item', 'No item')}\n"
            reward_text += f"**Participation**: {rewards.get('participation', {}).get('coins', 50)} coins"
            
            embed.add_field(
                name="🏆 Rewards",
                value=reward_text,
                inline=True
            )
            
            embed.add_field(
                name="🐾 Your Pets",
                value=f"You have {len(user_pets)} pet(s) ready to race!",
                inline=True
            )
            
            embed.add_field(
                name="🎯 Join Race",
                value="React with 🏃 to join the next available race!",
                inline=False
            )
            
            message = await ctx.send(embed=embed)
            await message.add_reaction("🏃")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Pet Race Error",
                "Unable to start pet race. Please try again later."
            )
            await ctx.send(embed=embed)
    
    @commands.command(name="randomevent", aliases=["event_trigger"])
    async def trigger_random_event(self, ctx):
        """Check for random events and treasure hunts"""
        try:
            random_data = data_manager._load_json(data_manager.data_dir / "random_events.json")
            
            # Check for dream popups
            dream_events = random_data.get("dream_popups", {})
            if random.random() < dream_events.get("trigger_chance", 0.05):
                events = dream_events.get("events", [])
                if events:
                    event = random.choices(
                        events,
                        weights=[e.get("probability", 0.1) for e in events],
                        k=1
                    )[0]
                    
                    embed = self.embed_builder.create_embed(
                        title="✨ Random Dream Event!",
                        description=event["message"],
                        color=0x9370DB
                    )
                    
                    # Apply reward
                    user_data = data_manager.get_user_data(str(ctx.author.id))
                    reward = event.get("reward", {})
                    
                    if reward.get("type") == "coins":
                        amount = reward.get("amount", 0)
                        user_data["gold"] = user_data.get("gold", 0) + amount
                        embed.add_field(
                            name="💰 Reward Applied",
                            value=f"Your gold: {user_data['gold']:,}",
                            inline=False
                        )
                    elif reward.get("type") == "experience":
                        amount = reward.get("amount", 0)
                        user_data["xp"] = user_data.get("xp", 0) + amount
                        embed.add_field(
                            name="⭐ Experience Gained",
                            value=f"Your XP: {user_data['xp']:,}",
                            inline=False
                        )
                    
                    data_manager.save_user_data(str(ctx.author.id), user_data)
                    await ctx.send(embed=embed)
                    return
            
            # Check for treasure hunts
            treasure_data = random_data.get("treasure_hunts", {})
            if random.random() < treasure_data.get("spawn_probability", 0.02):
                hidden_commands = treasure_data.get("hidden_commands", [])
                if hidden_commands:
                    treasure = random.choice(hidden_commands)
                    
                    embed = self.embed_builder.create_embed(
                        title="🏴‍☠️ Treasure Hunt Discovered!",
                        description=f"A mysterious command has appeared: `{treasure['command']}`\n\nUse this command within the next 30 minutes to claim your treasure!",
                        color=0xFFD700
                    )
                    
                    embed.add_field(
                        name="💎 Potential Reward",
                        value=treasure["message"],
                        inline=False
                    )
                    
                    await ctx.send(embed=embed)
                    return
            
            # No event triggered
            embed = self.embed_builder.info_embed(
                "Peaceful Moment",
                "No random events occurred this time. Keep adventuring for more chances!"
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Event Error",
                "Unable to check for random events. Please try again later."
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ContestsCommands(bot))