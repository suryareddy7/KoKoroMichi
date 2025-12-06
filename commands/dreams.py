# Dream Events System Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List, Any
import random
import asyncio
from datetime import datetime, timedelta
import uuid

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from core.config import FEATURES
from utils.helpers import format_number
from utils.channel_manager import check_channel_restriction

class DreamEventsCommands(commands.Cog):
    """Mystical dream events with legendary rewards and buffs"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        
        # Dream event templates
        self.dream_events = {
            "common": [
                {"name": "Peaceful Slumber", "description": "A restful dream grants small recovery", "rewards": {"gold": 100, "xp": 50}, "duration": 30},
                {"name": "Memory Echo", "description": "Past memories surface, bringing wisdom", "rewards": {"xp": 75}, "duration": 45},
                {"name": "Gentle Breeze", "description": "Soothing winds carry minor blessings", "rewards": {"gold": 150}, "duration": 60}
            ],
            "uncommon": [
                {"name": "Starlit Vision", "description": "Stars align to reveal hidden treasures", "rewards": {"gold": 300, "xp": 150}, "duration": 60},
                {"name": "Ancient Whisper", "description": "Forgotten voices share ancient knowledge", "rewards": {"xp": 200, "gems": 5}, "duration": 90},
                {"name": "Crystal Dream", "description": "Crystalline visions enhance mental clarity", "rewards": {"gold": 250, "buff": "xp_boost"}, "duration": 120}
            ],
            "rare": [
                {"name": "Divine Revelation", "description": "Gods speak through dreams, bestowing power", "rewards": {"gold": 500, "xp": 300, "gems": 10}, "duration": 120},
                {"name": "Heroic Memory", "description": "Dreams of legendary heroes inspire greatness", "rewards": {"xp": 400, "buff": "battle_boost"}, "duration": 180},
                {"name": "Mystical Gateway", "description": "Portals open to realms of wonder and treasure", "rewards": {"gold": 800, "gems": 15}, "duration": 150}
            ],
            "epic": [
                {"name": "Cosmic Convergence", "description": "Universe aligns to grant extraordinary power", "rewards": {"gold": 1500, "xp": 800, "gems": 25}, "duration": 240},
                {"name": "Phoenix Rebirth", "description": "Fiery dreams of renewal and transformation", "rewards": {"xp": 1000, "buff": "phoenix_blessing"}, "duration": 300},
                {"name": "Time Spiral", "description": "Temporal magic accelerates your growth", "rewards": {"gold": 2000, "xp": 1200}, "duration": 180}
            ],
            "legendary": [
                {"name": "Goddess's Blessing", "description": "Divine entities bestow their sacred favor", "rewards": {"gold": 5000, "xp": 2000, "gems": 50, "buff": "divine_blessing"}, "duration": 600},
                {"name": "World Tree Vision", "description": "Ancient world tree shares its infinite wisdom", "rewards": {"xp": 3000, "permanent_bonus": True}, "duration": 720},
                {"name": "Primordial Dream", "description": "Dreams from the birth of existence itself", "rewards": {"gold": 8000, "gems": 100, "buff": "primordial_power"}, "duration": 900}
            ],
            "mythical": [
                {"name": "Creator's Vision", "description": "The ultimate dream - glimpse of creation itself", "rewards": {"gold": 20000, "xp": 10000, "gems": 200, "buff": "creators_blessing", "permanent_bonus": True}, "duration": 1800}
            ]
        }
        
        # Dream buffs
        self.dream_buffs = {
            "xp_boost": {"name": "Dream Wisdom", "multiplier": 1.5, "duration_hours": 4, "emoji": "🧠"},
            "battle_boost": {"name": "Heroic Spirit", "multiplier": 1.3, "duration_hours": 3, "emoji": "⚔️"},
            "phoenix_blessing": {"name": "Phoenix Blessing", "multiplier": 2.0, "duration_hours": 6, "emoji": "🔥"},
            "divine_blessing": {"name": "Divine Blessing", "multiplier": 2.5, "duration_hours": 8, "emoji": "✨"},
            "primordial_power": {"name": "Primordial Power", "multiplier": 3.0, "duration_hours": 12, "emoji": "🌌"},
            "creators_blessing": {"name": "Creator's Blessing", "multiplier": 5.0, "duration_hours": 24, "emoji": "🌈"}
        }
    
    @commands.command(name="dreams", aliases=["dreamstatus"])
    @check_channel_restriction()
    async def view_dreams(self, ctx):
        """View active dream events and buffs"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            dream_data = user_data.get("dream_events", {})
            
            embed = self.embed_builder.create_embed(
                title="🌙 Dream Realm Status",
                description="Your mystical dream events and ethereal buffs",
                color=0x9932CC
            )
            
            # Active dream events
            active_events = dream_data.get("active_events", [])
            if active_events:
                events_text = ""
                for event in active_events:
                    status_emoji = "✅" if event["status"] == "ready" else "⏳"
                    events_text += f"{status_emoji} **{event['name']}**\n"
                    events_text += f"*{event['description'][:60]}...*\n"
                    
                    if event["status"] == "ready":
                        events_text += f"💫 Ready to collect! ID: `{event['id'][:8]}`\n\n"
                    else:
                        time_left = datetime.fromisoformat(event["completion_time"]) - datetime.now()
                        minutes_left = max(0, int(time_left.total_seconds() / 60))
                        events_text += f"⏱️ {minutes_left}m remaining\n\n"
                
                embed.add_field(
                    name="🌟 Active Dream Events",
                    value=events_text,
                    inline=False
                )
            else:
                embed.add_field(
                    name="😴 Peaceful Rest",
                    value="Your mind is at peace. Dream events trigger randomly while using other commands!",
                    inline=False
                )
            
            # Active buffs
            active_buffs = dream_data.get("active_buffs", [])
            if active_buffs:
                buffs_text = ""
                for buff in active_buffs:
                    buff_info = self.dream_buffs.get(buff["type"], {})
                    emoji = buff_info.get("emoji", "✨")
                    buffs_text += f"{emoji} **{buff_info.get('name', buff['type'])}**\n"
                    buffs_text += f"Boost: +{int((buff['multiplier']-1)*100)}% | {buff['hours_remaining']}h left\n\n"
                
                embed.add_field(
                    name="💫 Active Dream Buffs",
                    value=buffs_text,
                    inline=False
                )
            
            # Daily progress
            daily_events = dream_data.get("daily_events", 0)
            embed.add_field(
                name="📊 Daily Progress",
                value=f"**Dream Events Today:** {daily_events}/5\n"
                      f"**Total Dreams:** {dream_data.get('total_events', 0)}\n"
                      f"**Legendary Dreams:** {dream_data.get('legendary_count', 0)}",
                inline=False
            )
            
            await ctx.send(embed=embed)
            await self.log_dream_activity(ctx, "status_check")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Dream Status Error",
                "Unable to access the dream realm. Try again later."
            )
            await ctx.send(embed=embed)
            print(f"Dreams status error: {e}")
    
    @commands.command(name="complete_dream", aliases=["collect_dream"])
    @check_channel_restriction()
    async def complete_dream(self, ctx, event_id: str):
        """Complete a finished dream event and collect rewards"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            dream_data = user_data.get("dream_events", {})
            active_events = dream_data.get("active_events", [])
            
            # Find the event
            event_to_complete = None
            for i, event in enumerate(active_events):
                if event["id"].startswith(event_id):
                    event_to_complete = (i, event)
                    break
            
            if not event_to_complete:
                embed = self.embed_builder.error_embed(
                    "Event Not Found",
                    f"No ready dream event found with ID `{event_id}`. Use `!dreams` to view active events."
                )
                await ctx.send(embed=embed)
                return
            
            event_index, event = event_to_complete
            
            # Check if event is ready
            if event["status"] != "ready":
                completion_time = datetime.fromisoformat(event["completion_time"])
                time_left = completion_time - datetime.now()
                minutes_left = max(0, int(time_left.total_seconds() / 60))
                
                embed = self.embed_builder.warning_embed(
                    "Dream Not Ready",
                    f"This dream event needs {minutes_left} more minutes to complete."
                )
                await ctx.send(embed=embed)
                return
            
            # Apply rewards
            rewards = event["rewards"]
            reward_text = ""
            
            if "gold" in rewards:
                user_data["gold"] = user_data.get("gold", 0) + rewards["gold"]
                reward_text += f"💰 Gold: +{format_number(rewards['gold'])}\n"
            
            if "xp" in rewards:
                user_data["xp"] = user_data.get("xp", 0) + rewards["xp"]
                reward_text += f"⭐ XP: +{format_number(rewards['xp'])}\n"
            
            if "gems" in rewards:
                user_data["gems"] = user_data.get("gems", 0) + rewards["gems"]
                reward_text += f"💎 Gems: +{format_number(rewards['gems'])}\n"
            
            # Apply buffs
            if "buff" in rewards:
                self.apply_dream_buff(user_data, rewards["buff"])
                buff_info = self.dream_buffs.get(rewards["buff"], {})
                reward_text += f"✨ Buff: {buff_info.get('name', 'Dream Buff')}\n"
            
            # Apply permanent bonuses
            if rewards.get("permanent_bonus"):
                user_data["permanent_bonuses"] = user_data.get("permanent_bonuses", {})
                user_data["permanent_bonuses"]["dream_blessing"] = user_data["permanent_bonuses"].get("dream_blessing", 0) + 0.05
                reward_text += f"🌟 Permanent Blessing: +5% to all activities!\n"
            
            # Remove completed event
            active_events.pop(event_index)
            dream_data["completed_events"] = dream_data.get("completed_events", 0) + 1
            
            # Save data
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Create completion embed
            embed = self.embed_builder.create_embed(
                title="🌟 Dream Event Completed!",
                description=f"**{event['name']}** has been fulfilled!",
                color=0x9932CC
            )
            
            embed.add_field(
                name="📖 Dream Story",
                value=event["description"],
                inline=False
            )
            
            embed.add_field(
                name="🎁 Rewards Received",
                value=reward_text,
                inline=False
            )
            
            await ctx.send(embed=embed)
            await self.log_dream_activity(ctx, "completion", event["name"])
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Dream Completion Error",
                "Unable to complete dream event. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Dream completion error: {e}")
    
    @commands.command(name="dream_buffs", aliases=["buffs"])
    @check_channel_restriction()
    async def view_dream_buffs(self, ctx):
        """View all active dream buffs and their effects"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            dream_data = user_data.get("dream_events", {})
            active_buffs = dream_data.get("active_buffs", [])
            
            embed = self.embed_builder.create_embed(
                title="💫 Dream Buff Status",
                description="Active mystical enhancements from the dream realm",
                color=0x8A2BE2
            )
            
            if active_buffs:
                for buff in active_buffs:
                    buff_info = self.dream_buffs.get(buff["type"], {})
                    emoji = buff_info.get("emoji", "✨")
                    name = buff_info.get("name", buff["type"])
                    multiplier = buff["multiplier"]
                    hours_left = buff["hours_remaining"]
                    
                    embed.add_field(
                        name=f"{emoji} {name}",
                        value=f"**Effect:** +{int((multiplier-1)*100)}% boost\n"
                              f"**Duration:** {hours_left}h remaining\n"
                              f"**Source:** {buff.get('source', 'Dream Event')}",
                        inline=True
                    )
            else:
                embed.add_field(
                    name="😴 No Active Buffs",
                    value="Complete dream events to gain mystical buffs!",
                    inline=False
                )
            
            # Permanent bonuses
            permanent_bonuses = user_data.get("permanent_bonuses", {})
            dream_blessing = permanent_bonuses.get("dream_blessing", 0)
            
            if dream_blessing > 0:
                embed.add_field(
                    name="🌟 Permanent Dream Blessing",
                    value=f"**Eternal Boost:** +{int(dream_blessing*100)}% to all activities\n"
                          f"*Gained from completing legendary dream events*",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            await self.log_dream_activity(ctx, "buff_check")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Buff Status Error",
                "Unable to check dream buff status."
            )
            await ctx.send(embed=embed)
            print(f"Dream buffs error: {e}")
    
    async def trigger_random_dream_event(self, ctx, trigger_command: str = "unknown"):
        """Trigger a random dream event (called by other commands)"""
        if not FEATURES.get("dream_events_enabled", True):
            return
        
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            dream_data = user_data.get("dream_events", {})
            
            # Check daily limits
            today = datetime.now().date().isoformat()
            daily_events = dream_data.get("daily_events", 0)
            last_event_date = dream_data.get("last_event_date", "")
            
            if last_event_date != today:
                daily_events = 0
                dream_data["last_event_date"] = today
            
            if daily_events >= 5:
                return  # Daily limit reached
            
            # 15% chance to trigger dream event
            if random.random() > 0.15:
                return
            
            # Check cooldown (2 hours between events)
            last_event_time = dream_data.get("last_event_time", "")
            if last_event_time:
                last_time = datetime.fromisoformat(last_event_time)
                if datetime.now() - last_time < timedelta(hours=2):
                    return
            
            # Determine dream event rarity
            rarity_chances = {
                "common": 60.0,
                "uncommon": 25.0,
                "rare": 10.0,
                "epic": 4.0,
                "legendary": 0.9,
                "mythical": 0.1
            }
            
            rand = random.uniform(0, 100)
            cumulative = 0
            selected_rarity = "common"
            
            for rarity, chance in rarity_chances.items():
                cumulative += chance
                if rand <= cumulative:
                    selected_rarity = rarity
                    break
            
            # Select random event of chosen rarity
            available_events = self.dream_events[selected_rarity]
            event_template = random.choice(available_events)
            
            # Create dream event
            dream_event = {
                "id": str(uuid.uuid4()),
                "name": event_template["name"],
                "description": event_template["description"],
                "rarity": selected_rarity,
                "rewards": event_template["rewards"],
                "status": "active",
                "triggered_by": trigger_command,
                "start_time": datetime.now().isoformat(),
                "completion_time": (datetime.now() + timedelta(minutes=event_template["duration"])).isoformat()
            }
            
            # Add to user data
            active_events = dream_data.get("active_events", [])
            active_events.append(dream_event)
            dream_data["active_events"] = active_events
            dream_data["daily_events"] = daily_events + 1
            dream_data["last_event_time"] = datetime.now().isoformat()
            dream_data["total_events"] = dream_data.get("total_events", 0) + 1
            
            if selected_rarity in ["legendary", "mythical"]:
                dream_data["legendary_count"] = dream_data.get("legendary_count", 0) + 1
            
            user_data["dream_events"] = dream_data
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Announce dream event
            await self.announce_dream_event(ctx, dream_event)
            
        except Exception as e:
            print(f"Dream event trigger error: {e}")
    
    async def announce_dream_event(self, ctx, dream_event: Dict):
        """Announce a triggered dream event"""
        try:
            rarity = dream_event["rarity"]
            
            # Rarity colors
            rarity_colors = {
                "common": 0x87CEEB,
                "uncommon": 0x90EE90,
                "rare": 0x9370DB,
                "epic": 0xFF6347,
                "legendary": 0xFFD700,
                "mythical": 0xFF1493
            }
            
            # Rarity emojis
            rarity_emojis = {
                "common": "🌙",
                "uncommon": "🌟",
                "rare": "✨",
                "epic": "🔥",
                "legendary": "👑",
                "mythical": "🌈"
            }
            
            color = rarity_colors.get(rarity, 0x9932CC)
            emoji = rarity_emojis.get(rarity, "🌙")
            
            embed = self.embed_builder.create_embed(
                title=f"{emoji} Dream Event Triggered! {emoji}",
                description=f"A {rarity} dream event has begun in your sleep...",
                color=color
            )
            
            embed.add_field(
                name="💭 Dream Vision",
                value=f"**{dream_event['name']}**\n*{dream_event['description']}*",
                inline=False
            )
            
            # Show completion time
            completion_time = datetime.fromisoformat(dream_event["completion_time"])
            time_until = completion_time - datetime.now()
            minutes_until = int(time_until.total_seconds() / 60)
            
            embed.add_field(
                name="⏱️ Dream Duration",
                value=f"**Completion:** {minutes_until} minutes\n"
                      f"**Event ID:** `{dream_event['id'][:8]}`\n"
                      f"Use `!complete_dream {dream_event['id'][:8]}` when ready!",
                inline=False
            )
            
            # Preview rewards
            rewards = dream_event["rewards"]
            preview_text = ""
            if "gold" in rewards:
                preview_text += f"💰 {format_number(rewards['gold'])} gold  "
            if "xp" in rewards:
                preview_text += f"⭐ {format_number(rewards['xp'])} XP  "
            if "gems" in rewards:
                preview_text += f"💎 {rewards['gems']} gems  "
            if "buff" in rewards:
                buff_info = self.dream_buffs.get(rewards["buff"], {})
                preview_text += f"✨ {buff_info.get('name', 'Mystical Buff')}  "
            
            embed.add_field(
                name="🎁 Potential Rewards",
                value=preview_text,
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"Dream announcement error: {e}")
    
    def apply_dream_buff(self, user_data: Dict, buff_type: str):
        """Apply a dream buff to user"""
        dream_data = user_data.get("dream_events", {})
        active_buffs = dream_data.get("active_buffs", [])
        
        buff_info = self.dream_buffs.get(buff_type, {})
        
        dream_buff = {
            "type": buff_type,
            "multiplier": buff_info.get("multiplier", 1.5),
            "hours_remaining": buff_info.get("duration_hours", 4),
            "applied_at": datetime.now().isoformat(),
            "source": "Dream Event"
        }
        
        active_buffs.append(dream_buff)
        dream_data["active_buffs"] = active_buffs
        user_data["dream_events"] = dream_data
    
    async def log_dream_activity(self, ctx, activity_type: str, event_name: str = None):
        """Log dream activity to history channel"""
        try:
            history_channel = discord.utils.get(ctx.guild.text_channels, name='history')
            if not history_channel:
                return
            
            emojis = ["🌙", "💭", "✨", "🌟", "💫", "🔮"]
            emoji = random.choice(emojis)
            
            if activity_type == "status_check":
                message = f"{emoji} **{ctx.author.display_name}** gazed into the mystical dream realm to check their ethereal status!"
            elif activity_type == "completion":
                message = f"{emoji} **{ctx.author.display_name}** awakened from a powerful dream vision '{event_name}' and claimed divine rewards!"
            elif activity_type == "buff_check":
                message = f"{emoji} **{ctx.author.display_name}** examined their mystical dream buffs and ethereal enhancements!"
            else:
                message = f"{emoji} **{ctx.author.display_name}** explored the mysterious realm of dreams!"
            
            embed = self.embed_builder.create_embed(
                description=message,
                color=0x9932CC
            )
            
            await history_channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error logging dream activity: {e}")

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(DreamEventsCommands(bot))