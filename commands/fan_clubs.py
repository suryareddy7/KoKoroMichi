# Fan Clubs System Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List, Any
import random
from datetime import datetime, timedelta

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from core.config import FEATURES
from utils.helpers import format_number

class FanClubCommands(commands.Cog):
    """Character fan clubs with voting, events, and exclusive rewards"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        
        # Fan club activities
        self.club_activities = {
            "photo_contest": {
                "name": "Photo Contest",
                "description": "Vote for the best character photos",
                "duration_hours": 24,
                "rewards": {"winner": {"gems": 50, "gold": 2000}, "participants": {"gold": 200}},
                "emoji": "📸"
            },
            "popularity_poll": {
                "name": "Popularity Poll",
                "description": "Vote for most popular character",
                "duration_hours": 48,
                "rewards": {"winner": {"gems": 100, "gold": 5000}, "participants": {"gold": 500}},
                "emoji": "🗳️"
            },
            "fan_art_event": {
                "name": "Fan Art Event",
                "description": "Celebrate character with art appreciation",
                "duration_hours": 72,
                "rewards": {"winner": {"gems": 150, "special_item": 1}, "participants": {"gems": 10}},
                "emoji": "🎨"
            }
        }
    
    @commands.command(name="fanclubs", aliases=["clubs", "fan_club"])
    async def view_fan_clubs(self, ctx):
        """View active fan clubs and your memberships"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            game_data = data_manager.get_game_data()
            
            embed = self.embed_builder.create_embed(
                title="🌟 Character Fan Clubs",
                description="Join communities dedicated to your favorite characters!",
                color=0xFF69B4
            )
            
            # Show user's club memberships
            user_memberships = user_data.get("fan_club_memberships", [])
            if user_memberships:
                memberships_text = ""
                for membership in user_memberships:
                    char_name = membership["character_name"]
                    role = membership.get("role", "member")
                    joined_date = membership.get("joined_at", "")[:10]
                    memberships_text += f"💖 **{char_name}** ({role}) - Joined {joined_date}\n"
                
                embed.add_field(
                    name="💝 Your Memberships",
                    value=memberships_text,
                    inline=False
                )
            
            # Show popular clubs
            fan_clubs = game_data.get("fan_clubs", {})
            popular_clubs = sorted(fan_clubs.items(), key=lambda x: len(x[1].get("members", [])), reverse=True)[:5]
            
            if popular_clubs:
                popular_text = ""
                for char_name, club_data in popular_clubs:
                    member_count = len(club_data.get("members", []))
                    activity_level = self.get_activity_level(member_count)
                    popular_text += f"⭐ **{char_name}** - {member_count} members ({activity_level})\n"
                
                embed.add_field(
                    name="🔥 Most Popular Clubs",
                    value=popular_text,
                    inline=False
                )
            
            # Show active events
            active_events = game_data.get("fan_club_events", [])
            current_events = [event for event in active_events if event["status"] == "active"]
            
            if current_events:
                events_text = ""
                for event in current_events[:3]:
                    activity = self.club_activities.get(event["activity_type"], {})
                    char_name = event["character_name"]
                    time_left = self.calculate_time_remaining(event["end_time"])
                    events_text += f"{activity.get('emoji', '🎉')} **{char_name}** - {activity.get('name', 'Event')}\n"
                    events_text += f"   Time left: {time_left}\n"
                
                embed.add_field(
                    name="🎉 Active Events",
                    value=events_text,
                    inline=False
                )
            
            embed.add_field(
                name="💡 How to Participate",
                value="• `!join_club <character>` - Join a fan club\n"
                      "• `!vote <character>` - Vote in club events\n"
                      "• `!club_events` - View all active events\n"
                      "• `!create_club <character>` - Start a new club",
                inline=False
            )
            
            await ctx.send(embed=embed)
            await self.log_fan_club_activity(ctx, "browse")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Fan Clubs Error",
                "Unable to load fan club information."
            )
            await ctx.send(embed=embed)
            print(f"Fan clubs command error: {e}")
    
    @commands.command(name="join_club", aliases=["join_fanclub"])
    async def join_fan_club(self, ctx, *, character_name: str):
        """Join a character's fan club"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            game_data = data_manager.get_game_data()
            
            # Check if user owns this character
            user_characters = user_data.get("claimed_waifus", [])
            owned_character = self.find_character_by_name(user_characters, character_name)
            
            if not owned_character:
                embed = self.embed_builder.warning_embed(
                    "Character Not Owned",
                    f"You need to own {character_name} to join their fan club! Use `!summon` to get them first."
                )
                await ctx.send(embed=embed)
                return
            
            # Check if already a member
            user_memberships = user_data.get("fan_club_memberships", [])
            for membership in user_memberships:
                if membership["character_name"].lower() == character_name.lower():
                    embed = self.embed_builder.warning_embed(
                        "Already a Member",
                        f"You're already a member of {character_name}'s fan club!"
                    )
                    await ctx.send(embed=embed)
                    return
            
            # Create or join fan club
            fan_clubs = game_data.setdefault("fan_clubs", {})
            if character_name not in fan_clubs:
                # Create new fan club
                fan_clubs[character_name] = {
                    "created_at": datetime.now().isoformat(),
                    "creator_id": str(ctx.author.id),
                    "members": [],
                    "events": [],
                    "total_activity": 0
                }
            
            # Add user to club
            club_data = fan_clubs[character_name]
            member_data = {
                "user_id": str(ctx.author.id),
                "username": ctx.author.display_name,
                "joined_at": datetime.now().isoformat(),
                "activity_points": 0,
                "role": "creator" if str(ctx.author.id) == club_data.get("creator_id") else "member"
            }
            
            club_data["members"].append(member_data)
            
            # Add membership to user data
            user_memberships.append({
                "character_name": character_name,
                "joined_at": datetime.now().isoformat(),
                "role": member_data["role"],
                "activity_points": 0
            })
            
            user_data["fan_club_memberships"] = user_memberships
            
            # Save data
            data_manager.save_game_data(game_data)
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Create join confirmation
            is_creator = member_data["role"] == "creator"
            action = "Created and joined" if is_creator else "Joined"
            
            embed = self.embed_builder.success_embed(
                f"Fan Club {action.split()[0]}!" if is_creator else "Fan Club Joined!",
                f"{action} **{character_name}'s** fan club!"
            )
            
            embed.add_field(
                name=f"💖 {character_name} Fan Club",
                value=f"**Members:** {len(club_data['members'])}\n"
                      f"**Your Role:** {member_data['role'].title()}\n"
                      f"**Activity Level:** {self.get_activity_level(len(club_data['members']))}",
                inline=True
            )
            
            # Show character info
            char_level = owned_character.get("level", 1)
            char_rarity = owned_character.get("rarity", "N")
            
            embed.add_field(
                name="✨ Character Details",
                value=f"**Level:** {char_level}\n"
                      f"**Rarity:** {char_rarity}\n"
                      f"**Element:** {owned_character.get('element', 'Neutral')}",
                inline=True
            )
            
            embed.add_field(
                name="🎉 Fan Club Benefits",
                value="• Participate in exclusive events\n"
                      "• Vote in character polls\n"
                      "• Earn special rewards and recognition\n"
                      "• Connect with other fans",
                inline=False
            )
            
            await ctx.send(embed=embed)
            await self.log_fan_club_activity(ctx, "join", character_name)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Join Club Error",
                "Unable to join fan club. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Join fan club error: {e}")
    
    @commands.command(name="vote", aliases=["fan_vote"])
    async def vote_in_event(self, ctx, *, character_name: str):
        """Vote for a character in active fan club events"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            game_data = data_manager.get_game_data()
            
            # Check if user is member of any fan clubs
            user_memberships = user_data.get("fan_club_memberships", [])
            if not user_memberships:
                embed = self.embed_builder.error_embed(
                    "Not a Fan Club Member",
                    "You need to join a fan club before voting! Use `!join_club <character>` first."
                )
                await ctx.send(embed=embed)
                return
            
            # Find active events
            active_events = game_data.get("fan_club_events", [])
            current_events = [event for event in active_events if event["status"] == "active"]
            
            if not current_events:
                embed = self.embed_builder.warning_embed(
                    "No Active Events",
                    "There are no fan club events to vote in right now."
                )
                await ctx.send(embed=embed)
                return
            
            # Find event for this character
            target_event = None
            for event in current_events:
                if event["character_name"].lower() == character_name.lower():
                    target_event = event
                    break
            
            if not target_event:
                embed = self.embed_builder.error_embed(
                    "No Event Found",
                    f"No active fan club event found for {character_name}."
                )
                await ctx.send(embed=embed)
                return
            
            # Check if user already voted
            voters = target_event.get("voters", [])
            if str(ctx.author.id) in voters:
                embed = self.embed_builder.warning_embed(
                    "Already Voted",
                    f"You've already voted in {character_name}'s event!"
                )
                await ctx.send(embed=embed)
                return
            
            # Record vote
            target_event["votes"] = target_event.get("votes", 0) + 1
            voters.append(str(ctx.author.id))
            target_event["voters"] = voters
            
            # Award participation points
            user_data["fan_club_activity_points"] = user_data.get("fan_club_activity_points", 0) + 10
            
            # Save data
            data_manager.save_game_data(game_data)
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Create vote confirmation
            activity = self.club_activities.get(target_event["activity_type"], {})
            
            embed = self.embed_builder.success_embed(
                "Vote Submitted!",
                f"You voted for **{character_name}** in the {activity.get('name', 'fan club event')}!"
            )
            
            embed.add_field(
                name=f"{activity.get('emoji', '🗳️')} Event Details",
                value=f"**Event:** {activity.get('name', 'Fan Event')}\n"
                      f"**Character:** {character_name}\n"
                      f"**Total Votes:** {target_event['votes']}\n"
                      f"**Time Remaining:** {self.calculate_time_remaining(target_event['end_time'])}",
                inline=False
            )
            
            embed.add_field(
                name="🎁 Participation Reward",
                value="💰 +200 gold (when event ends)\n"
                      "⭐ +10 activity points\n"
                      "🏆 Chance for bonus rewards if character wins!",
                inline=False
            )
            
            await ctx.send(embed=embed)
            await self.log_fan_club_activity(ctx, "vote", f"{character_name} - {activity.get('name', 'event')}")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Voting Error",
                "Unable to submit vote. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Vote command error: {e}")
    
    @commands.command(name="club_events", aliases=["fan_events"])
    async def view_club_events(self, ctx):
        """View all active fan club events"""
        try:
            game_data = data_manager.get_game_data()
            active_events = game_data.get("fan_club_events", [])
            current_events = [event for event in active_events if event["status"] == "active"]
            
            embed = self.embed_builder.create_embed(
                title="🎉 Active Fan Club Events",
                description="Participate in events to earn rewards and show your support!",
                color=0xFF69B4
            )
            
            if current_events:
                for event in current_events:
                    activity = self.club_activities.get(event["activity_type"], {})
                    char_name = event["character_name"]
                    votes = event.get("votes", 0)
                    time_left = self.calculate_time_remaining(event["end_time"])
                    
                    embed.add_field(
                        name=f"{activity.get('emoji', '🎉')} {char_name} - {activity.get('name', 'Event')}",
                        value=f"*{activity.get('description', 'Fan club event')}*\n"
                              f"**Votes:** {votes}\n"
                              f"**Time Left:** {time_left}\n"
                              f"Use: `!vote {char_name}`",
                        inline=True
                    )
            else:
                embed.add_field(
                    name="😴 No Active Events",
                    value="No fan club events are currently running.\n"
                          "Events start randomly throughout the day!",
                    inline=False
                )
            
            # Show upcoming events
            embed.add_field(
                name="📅 Event Schedule",
                value="• Photo contests every 2-3 days\n"
                      "• Popularity polls weekly\n"
                      "• Special seasonal events\n"
                      "• Fan art celebrations monthly",
                inline=False
            )
            
            await ctx.send(embed=embed)
            await self.log_fan_club_activity(ctx, "events_check")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Events Error",
                "Unable to load fan club events."
            )
            await ctx.send(embed=embed)
            print(f"Club events error: {e}")
    
    @commands.command(name="create_club", aliases=["start_club"])
    async def create_fan_club(self, ctx, *, character_name: str):
        """Create a new fan club for a character"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            game_data = data_manager.get_game_data()
            
            # Check if user owns this character
            user_characters = user_data.get("claimed_waifus", [])
            owned_character = self.find_character_by_name(user_characters, character_name)
            
            if not owned_character:
                embed = self.embed_builder.error_embed(
                    "Character Not Owned",
                    f"You need to own {character_name} to create their fan club!"
                )
                await ctx.send(embed=embed)
                return
            
            # Check if club already exists
            fan_clubs = game_data.get("fan_clubs", {})
            if character_name in fan_clubs:
                embed = self.embed_builder.warning_embed(
                    "Club Already Exists",
                    f"{character_name}'s fan club already exists! Use `!join_club {character_name}` instead."
                )
                await ctx.send(embed=embed)
                return
            
            # Check creation cost
            creation_cost = 5000
            user_gold = user_data.get("gold", 0)
            
            if user_gold < creation_cost:
                embed = self.embed_builder.error_embed(
                    "Insufficient Gold",
                    f"Creating a fan club costs {format_number(creation_cost)} gold."
                )
                await ctx.send(embed=embed)
                return
            
            # Create fan club
            fan_clubs[character_name] = {
                "created_at": datetime.now().isoformat(),
                "creator_id": str(ctx.author.id),
                "creator_name": ctx.author.display_name,
                "members": [{
                    "user_id": str(ctx.author.id),
                    "username": ctx.author.display_name,
                    "joined_at": datetime.now().isoformat(),
                    "role": "creator",
                    "activity_points": 0
                }],
                "events": [],
                "total_activity": 0,
                "description": f"Official fan club for the amazing {character_name}!"
            }
            
            # Deduct cost
            user_data["gold"] -= creation_cost
            
            # Add membership to user
            user_memberships = user_data.get("fan_club_memberships", [])
            user_memberships.append({
                "character_name": character_name,
                "joined_at": datetime.now().isoformat(),
                "role": "creator",
                "activity_points": 0
            })
            user_data["fan_club_memberships"] = user_memberships
            
            # Save data
            data_manager.save_game_data(game_data)
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Create success embed
            embed = self.embed_builder.success_embed(
                "Fan Club Created!",
                f"Successfully created **{character_name}'s** official fan club!"
            )
            
            embed.add_field(
                name=f"💖 {character_name} Fan Club",
                value=f"**Founder:** {ctx.author.display_name}\n"
                      f"**Members:** 1 (you!)\n"
                      f"**Created:** {datetime.now().strftime('%B %d, %Y')}",
                inline=True
            )
            
            embed.add_field(
                name="👑 Creator Benefits",
                value="• Organize club events\n"
                      "• Set club description\n"
                      "• Moderate discussions\n"
                      "• Exclusive creator rewards",
                inline=True
            )
            
            embed.add_field(
                name="💰 Creation Cost",
                value=f"**Paid:** {format_number(creation_cost)} gold\n"
                      f"**Remaining:** {format_number(user_data['gold'])} gold",
                inline=False
            )
            
            await ctx.send(embed=embed)
            await self.log_fan_club_activity(ctx, "create", character_name)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Club Creation Error",
                "Unable to create fan club. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Create club error: {e}")
    
    def find_character_by_name(self, characters: List[Dict], name: str) -> Optional[Dict]:
        """Find character by name (case insensitive)"""
        name_lower = name.lower()
        for char in characters:
            if char.get("name", "").lower() == name_lower:
                return char
        return None
    
    def get_activity_level(self, member_count: int) -> str:
        """Get activity level based on member count"""
        if member_count >= 50:
            return "🔥 Very Active"
        elif member_count >= 20:
            return "⭐ Active"
        elif member_count >= 10:
            return "💫 Growing"
        elif member_count >= 5:
            return "🌱 Small"
        else:
            return "👶 New"
    
    def calculate_time_remaining(self, end_time: str) -> str:
        """Calculate time remaining for an event"""
        try:
            end_datetime = datetime.fromisoformat(end_time)
            time_left = end_datetime - datetime.now()
            
            if time_left.total_seconds() <= 0:
                return "Ended"
            
            hours = int(time_left.total_seconds() / 3600)
            minutes = int((time_left.total_seconds() % 3600) / 60)
            
            if hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
                
        except:
            return "Unknown"
    
    async def log_fan_club_activity(self, ctx, activity_type: str, details: str = ""):
        """Log fan club activity to history channel"""
        try:
            history_channel = discord.utils.get(ctx.guild.text_channels, name='history')
            if not history_channel:
                return
            
            emojis = ["💖", "🌟", "🎉", "🗳️", "💝", "✨"]
            emoji = random.choice(emojis)
            
            if activity_type == "browse":
                message = f"{emoji} **{ctx.author.display_name}** explored the vibrant world of character fan clubs!"
            elif activity_type == "join":
                message = f"{emoji} **{ctx.author.display_name}** joined the passionate fan club for {details}!"
            elif activity_type == "create":
                message = f"{emoji} **{ctx.author.display_name}** founded the official fan club for {details}!"
            elif activity_type == "vote":
                message = f"{emoji} **{ctx.author.display_name}** cast their heartfelt vote in the {details}!"
            elif activity_type == "events_check":
                message = f"{emoji} **{ctx.author.display_name}** checked the latest fan club events and activities!"
            else:
                message = f"{emoji} **{ctx.author.display_name}** participated in fan club activities!"
            
            embed = self.embed_builder.create_embed(
                description=message,
                color=0xFF69B4
            )
            
            await history_channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error logging fan club activity: {e}")

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(FanClubCommands(bot))