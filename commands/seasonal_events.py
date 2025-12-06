# ---------------- Metadata ----------------
name = "seasonal_events_system"
description = "Dynamic seasonal events and multi-chapter story quests with branching outcomes and special rewards."
features = (
    "• `events` → View current seasonal bonuses and available story events\n"
    "• `startevent <event_name> <waifu1> [waifu2] [waifu3]` → Begin story quest with selected waifus\n"
    "• `eventchoice <event_id> <choice>` → Make decisions in active story events\n"
    "• `eventprogress` → Check status of all your active story events\n"
    "• `seasonal` → View current season bonuses and special rewards\n"
    "• Seasonal bonuses: Spring (XP+20%), Summer (Gold+30%), Autumn (Rare drops+20%), Winter (Affinity+50%)\n"
    "• Story events with multiple chapters, branching narratives, and relationship-based outcomes\n"
    "• Limited-time events with rare collectibles and exclusive rewards"
)
# ------------------------------------------

import discord
from discord.ext import commands
import json
import os
import random
import asyncio
from datetime import datetime
from utils.seasonal_manager import SeasonalManager
from utils.fileManager import load_users, save_users

class SeasonalEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.seasonal_manager = SeasonalManager()
        self.users_file = os.path.join(os.path.dirname(__file__), '../data/users.json')
        self.encouraging_emojis = ["✨", "🌟", "💫", "🎭", "🎨", "🌈"]

    def get_user_stats(self, user_id: str) -> dict:
        """Get user stats for requirement checking"""
        users = load_users()
        if str(user_id) not in users:
            return {}
        
        user_data = users[str(user_id)]
        waifus = user_data.get("claimed_waifus", [])
        total_level = sum(user_data.get("waifu_stats", {}).get(w, {}).get("level", 1) for w in waifus)
        total_affinity = sum(user_data.get("waifu_stats", {}).get(w, {}).get("affinity", 0) for w in waifus)
        
        return {
            "level": user_data.get("level", 1),
            "waifus": len(waifus),
            "total_level": total_level,
            "total_affinity": total_affinity,
            "claimed_waifus": waifus,
            "waifu_stats": user_data.get("waifu_stats", {})
        }

    @commands.command(name="seasonal")
    async def view_events(self, ctx):
        """Display current seasonal bonuses and available story events"""
        current_season = self.seasonal_manager.get_current_season()
        seasonal_bonuses = self.seasonal_manager.get_active_season_bonuses(str(ctx.author.id))
        
        user_stats = self.get_user_stats(ctx.author.id)
        available_events = self.seasonal_manager.get_available_story_events(
            user_stats.get("level", 1),
            user_stats.get("waifus", 0),
            user_stats.get("total_affinity", 0)
        )

        embed = discord.Embed(
            title=f"🌟 Seasonal Events & Stories - {current_season.title()}",
            color=0x00ff00,
            timestamp=datetime.now()
        )

        # Current season info
        season_info = self.seasonal_manager.seasonal_data["seasons"].get(current_season, {})
        if season_info:
            embed.add_field(
                name=f"🍃 Current Season: {season_info['name']}",
                value=f"{season_info['description']}\n**Active Bonuses:**",
                inline=False
            )
            
            bonus_text = ""
            for bonus_type, value in seasonal_bonuses.items():
                if "multiplier" in bonus_type:
                    bonus_text += f"• {bonus_type.replace('_', ' ').title()}: {int((value-1)*100)}%\n"
                else:
                    bonus_text += f"• {bonus_type.replace('_', ' ').title()}: +{int(value*100)}%\n"
            
            if bonus_text:
                embed.add_field(name="✨ Seasonal Bonuses", value=bonus_text, inline=True)

        # Available story events
        if available_events:
            events_text = ""
            for i, event in enumerate(available_events[:5], 1):
                events_text += f"`{i}.` **{event['name']}**\n{event['description'][:100]}...\n"
                events_text += f"*Requires: {event['requirements']['required_waifus']} waifus, "
                events_text += f"Level {event['requirements'].get('min_level', 1)}*\n\n"
            
            embed.add_field(name="📖 Available Story Events", value=events_text, inline=False)
        else:
            embed.add_field(
                name="📖 Story Events", 
                value="No events available at your current level.\nKeep playing to unlock epic adventures!", 
                inline=False
            )

        # Usage instructions
        embed.add_field(
            name="🎮 Commands",
            value="• `!startevent <event_name> <waifu1> [waifu2]` - Start story quest\n"
                  "• `!eventprogress` - Check active events\n"
                  "• `!seasonal` - View season details",
            inline=False
        )

        embed.set_footer(text="Seasonal events refresh with real-world seasons!")
        await ctx.send(embed=embed)

    @commands.command(name="startevent")
    async def start_event(self, ctx, event_name: str = None, *waifu_names):
        """Start a story event with selected waifus"""
        if not event_name:
            await ctx.send("❌ Please specify an event name! Use `!events` to see available events.")
            return

        if not waifu_names:
            await ctx.send("❌ Please specify at least one waifu to participate!")
            return

        # Validate user owns these waifus
        users = load_users()
        user_data = users.get(str(ctx.author.id), {})
        owned_waifus = user_data.get("claimed_waifus", [])
        
        invalid_waifus = [w for w in waifu_names if w not in owned_waifus]
        if invalid_waifus:
            await ctx.send(f"❌ You don't own these waifus: {', '.join(invalid_waifus)}")
            return

        # Start the event
        success, message, event_data = self.seasonal_manager.start_story_event(
            str(ctx.author.id), event_name, list(waifu_names)
        )

        if not success:
            await ctx.send(f"❌ {message}")
            return

        # Display first chapter
        chapter = event_data["chapter"]
        
        embed = discord.Embed(
            title=f"📖 {event_name} - Chapter 1",
            description=f"**{chapter['title']}**\n\n{chapter['story']}",
            color=0x9932cc,
            timestamp=datetime.now()
        )

        embed.add_field(
            name="👥 Participating Waifus",
            value=", ".join(waifu_names),
            inline=False
        )

        choices_text = ""
        for i, choice in enumerate(chapter['choices'], 1):
            choices_text += f"`{i}.` {choice}\n"

        embed.add_field(name="🔮 Your Choices", value=choices_text, inline=False)
        embed.add_field(
            name="📝 Next Step",
            value=f"Use `!eventchoice {event_data['event_id'][:8]} <choice>` to continue!",
            inline=False
        )

        emoji = random.choice(self.encouraging_emojis)
        await ctx.send(f"{emoji} Story event started!", embed=embed)

    @commands.command(name="eventchoice")
    async def make_choice(self, ctx, event_id_short: str = None, *, choice: str = None):
        """Make a choice in an active story event"""
        if not event_id_short or not choice:
            await ctx.send("❌ Usage: `!eventchoice <event_id> <choice>`")
            return

        # Find full event ID
        full_event_id = None
        for active_id in self.seasonal_manager.user_events["active_events"]:
            if active_id.startswith(f"{ctx.author.id}_{choice}") or event_id_short in active_id:
                if self.seasonal_manager.user_events["active_events"][active_id]["user_id"] == str(ctx.author.id):
                    full_event_id = active_id
                    break

        if not full_event_id:
            await ctx.send("❌ Event not found! Use `!eventprogress` to see your active events.")
            return

        success, message, result_data = self.seasonal_manager.make_story_choice(full_event_id, choice)

        if not success:
            await ctx.send(f"❌ {message}")
            return

        # Check if event completed or continuing
        if "rewards" in result_data:
            # Event completed!
            rewards = result_data
            embed = discord.Embed(
                title="🎉 Story Event Completed!",
                description=f"**{message}**\n\nYour choices have led to this conclusion!",
                color=0xffd700,
                timestamp=datetime.now()
            )

            reward_text = f"• **XP:** {rewards['xp']}\n• **Gold:** {rewards['gold']}\n"
            if rewards.get('special_items'):
                reward_text += f"• **Items:** {', '.join(rewards['special_items'])}"

            embed.add_field(name="🎁 Rewards Earned", value=reward_text, inline=False)

            # Apply rewards to user
            users = load_users()
            if str(ctx.author.id) in users:
                user_data = users[str(ctx.author.id)]
                user_data["xp"] = user_data.get("xp", 0) + rewards["xp"]
                user_data["gold"] = user_data.get("gold", 0) + rewards["gold"]
                
                # Add special items
                for item in rewards.get("special_items", []):
                    if "inventory" not in user_data:
                        user_data["inventory"] = {}
                    user_data["inventory"][item] = user_data["inventory"].get(item, 0) + 1
                
                save_users(users)

        else:
            # Continue to next chapter
            outcome = result_data["outcome"]
            next_chapter = result_data["next_chapter"]
            
            embed = discord.Embed(
                title=f"📖 Story Continues... - {next_chapter['title']}",
                description=f"**Your Choice:** {choice}\n\n*{message}*\n\n{next_chapter['story']}",
                color=0x9932cc,
                timestamp=datetime.now()
            )

            # Show outcome effects
            embed.add_field(
                name="🎲 Outcome",
                value=f"Success Rate: {int(outcome['success_rate']*100)}%\n"
                      f"Reward Bonus: {int(outcome['reward_bonus']*100)}%",
                inline=True
            )

            choices_text = ""
            for i, next_choice in enumerate(next_chapter['choices'], 1):
                choices_text += f"`{i}.` {next_choice}\n"

            embed.add_field(name="🔮 Next Choices", value=choices_text, inline=False)
            embed.add_field(
                name="📈 Progress",
                value=result_data["progress"],
                inline=True
            )

        await ctx.send(embed=embed)

    @commands.command(name="eventprogress")
    async def check_progress(self, ctx):
        """Check status of all active story events"""
        user_events = {k: v for k, v in self.seasonal_manager.user_events["active_events"].items() 
                      if v["user_id"] == str(ctx.author.id)}

        if not user_events:
            await ctx.send("📖 You have no active story events. Use `!events` to see available adventures!")
            return

        embed = discord.Embed(
            title="📚 Your Active Story Events",
            color=0x9932cc,
            timestamp=datetime.now()
        )

        for event_id, event_data in user_events.items():
            event_name = event_data["event_name"]
            current_chapter = event_data["current_chapter"] + 1
            participating = ", ".join(event_data["participating_waifus"])
            
            # Find total chapters
            total_chapters = 0
            for event in self.seasonal_manager.seasonal_data["story_events"]:
                if event["name"] == event_name:
                    total_chapters = len(event["chapters"])
                    break

            embed.add_field(
                name=f"📖 {event_name}",
                value=f"**Progress:** Chapter {current_chapter}/{total_chapters}\n"
                      f"**Waifus:** {participating}\n"
                      f"**Event ID:** `{event_id[:8]}...`",
                inline=True
            )

        embed.set_footer(text="Use !eventchoice <event_id> <choice> to continue your adventures!")
        await ctx.send(embed=embed)

    @commands.command(name="season_info")
    async def seasonal_info(self, ctx):
        """Detailed seasonal information and bonuses"""
        current_season = self.seasonal_manager.get_current_season()
        season_data = self.seasonal_manager.seasonal_data["seasons"].get(current_season, {})

        embed = discord.Embed(
            title=f"🌟 {season_data.get('name', current_season.title())} Season",
            description=season_data.get('description', 'Enjoy the current season!'),
            color=0x00ff00,
            timestamp=datetime.now()
        )

        bonuses = season_data.get("bonuses", {})
        bonus_text = ""
        for bonus_type, value in bonuses.items():
            if "multiplier" in bonus_type:
                bonus_text += f"• **{bonus_type.replace('_', ' ').title()}:** {int((value-1)*100)}% boost\n"
            else:
                bonus_text += f"• **{bonus_type.replace('_', ' ').title()}:** +{int(value*100)}% bonus\n"

        if bonus_text:
            embed.add_field(name="✨ Active Bonuses", value=bonus_text, inline=False)

        special_rewards = season_data.get("special_rewards", [])
        if special_rewards:
            embed.add_field(
                name="🎁 Special Seasonal Rewards",
                value="\n".join([f"• {reward}" for reward in special_rewards]),
                inline=False
            )

        embed.add_field(
            name="⏰ Duration",
            value=f"{season_data.get('duration_days', 30)} days per season\nBonuses automatically applied to all activities!",
            inline=False
        )

        seasons_preview = {
            "spring": "🌸 Cherry Blossom Festival (XP +20%, Affinity +10%)",
            "summer": "🏖️ Beach Paradise (Gold +30%, Quest success +15%)", 
            "autumn": "🍂 Harvest Moon (Relic drops +20%, Legendary quests +10%)",
            "winter": "❄️ Winter Wonderland (Affinity +50%, Intimate cooldown -30%)"
        }

        embed.add_field(
            name="🗓️ Seasonal Calendar",
            value="\n".join([f"{'**' if season == current_season else ''}{preview}{'**' if season == current_season else ''}" 
                           for season, preview in seasons_preview.items()]),
            inline=False
        )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SeasonalEvents(bot))