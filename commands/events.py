# Events and Seasonal Activities Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List
import random
from datetime import datetime, timedelta

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from utils.helpers import format_number, is_on_cooldown
from utils.channel_manager import check_channel_restriction

class EventsCommands(commands.Cog):
    """Seasonal events, special activities, and limited-time content"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        
        # Seasonal events configuration
        self.seasonal_events = {
            "spring_festival": {
                "name": "Cherry Blossom Festival",
                "description": "Celebrate the beauty of spring with enhanced summoning rates",
                "season": "spring",
                "duration_days": 14,
                "bonuses": {"summon_rates": 1.2, "flower_materials": 2.0},
                "special_rewards": ["Sakura Petal", "Spring Blessing", "Cherry Blossom Crown"],
                "activities": ["flower_viewing", "poetry_contest", "tea_ceremony"]
            },
            "summer_games": {
                "name": "Summer Beach Olympics",
                "description": "Compete in beach games for exclusive rewards",
                "season": "summer",
                "duration_days": 21,
                "bonuses": {"battle_rewards": 1.5, "daily_gold": 2.0},
                "special_rewards": ["Golden Seashell", "Beach Ball", "Summer Crown"],
                "activities": ["beach_volleyball", "surfing_contest", "sandcastle_building"]
            },
            "autumn_harvest": {
                "name": "Autumn Harvest Festival",
                "description": "Gather abundant resources during the harvest season",
                "season": "autumn",
                "duration_days": 18,
                "bonuses": {"crafting_success": 1.3, "gathering_yield": 2.5},
                "special_rewards": ["Golden Apple", "Harvest Moon", "Autumn Leaves"],
                "activities": ["apple_picking", "cooking_contest", "moon_gazing"]
            },
            "winter_celebration": {
                "name": "Winter Wonderland",
                "description": "Magical winter celebration with gift exchanges",
                "season": "winter",
                "duration_days": 25,
                "bonuses": {"guild_bonuses": 1.4, "gift_drops": 3.0},
                "special_rewards": ["Snowflake Crystal", "Winter Gift", "Frost Crown"],
                "activities": ["snowball_fight", "gift_exchange", "ice_skating"]
            }
        }
        
        # Random mini-events that can occur
        self.mini_events = {
            "meteor_shower": {
                "name": "Meteor Shower",
                "description": "Falling stars grant bonus star fragments",
                "duration_hours": 4,
                "bonuses": {"star_fragment_chance": 0.3},
                "trigger_chance": 0.02  # 2% chance per hour
            },
            "merchant_visit": {
                "name": "Traveling Merchant",
                "description": "A mysterious merchant offers rare trades",
                "duration_hours": 6,
                "bonuses": {"rare_trade_items": 1.0},
                "trigger_chance": 0.015  # 1.5% chance per hour
            },
            "double_xp": {
                "name": "Training Surge",
                "description": "All characters gain double experience",
                "duration_hours": 3,
                "bonuses": {"battle_xp": 2.0, "training_xp": 2.0},
                "trigger_chance": 0.025  # 2.5% chance per hour
            }
        }
        
        # Dream events - narrative experiences
        self.dream_events = {
            "ancient_library": {
                "name": "Dream of the Ancient Library",
                "description": "You find yourself in a vast library of forgotten knowledge",
                "rewards": ["Ancient Scroll", "Wisdom Crystal", "Mystic Tome"],
                "story_fragments": [
                    "The dusty tomes whisper secrets of ages past...",
                    "A golden book catches your eye, radiating warm light...",
                    "The librarian's ghostly figure nods approvingly..."
                ]
            },
            "celestial_garden": {
                "name": "Dream of the Celestial Garden",
                "description": "A garden where stars grow like flowers",
                "rewards": ["Star Seed", "Celestial Dew", "Heaven's Flower"],
                "story_fragments": [
                    "Flowers of pure starlight bloom around you...",
                    "The constellation spirits dance in the moonbeams...",
                    "A shooting star plants itself in the cosmic soil..."
                ]
            },
            "dragon_realm": {
                "name": "Dream of the Dragon Realm",
                "description": "You walk among ancient dragons in their sacred domain",
                "rewards": ["Dragon Scale", "Fire Heart", "Ancient Wisdom"],
                "story_fragments": [
                    "The eldest dragon regards you with knowing eyes...",
                    "Flames of wisdom dance around your spirit...",
                    "The dragon's blessing fills you with power..."
                ]
            }
        }
    
    @commands.group(name="events", invoke_without_command=True)
    @check_channel_restriction()
    async def events_group(self, ctx):
        """View current and upcoming events"""
        try:
            embed = self.create_events_overview_embed()
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Events Error",
                "Unable to load events information."
            )
            await ctx.send(embed=error_embed)
            print(f"Events command error: {e}")
    
    @events_group.command(name="participate")
    @check_channel_restriction()
    async def participate_event(self, ctx, activity: str = None):
        """Participate in current event activities"""
        try:
            if not activity:
                embed = self.embed_builder.info_embed(
                    "Event Activities",
                    "Use `!events participate <activity>` to join an activity!\n"
                    "Check `!events` to see available activities."
                )
                await ctx.send(embed=embed)
                return
            
            # Check if there's an active seasonal event
            current_event = self.get_current_seasonal_event()
            if not current_event:
                embed = self.embed_builder.info_embed(
                    "No Active Events",
                    "There are no seasonal events currently active."
                )
                await ctx.send(embed=embed)
                return
            
            # Check if activity is valid for current event
            if activity.lower() not in current_event["activities"]:
                available = ", ".join(current_event["activities"])
                embed = self.embed_builder.error_embed(
                    "Invalid Activity",
                    f"Available activities for {current_event['name']}: {available}"
                )
                await ctx.send(embed=embed)
                return
            
            # Participate in the activity
            await self.handle_event_participation(ctx, current_event, activity.lower())
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Participation Error",
                "Unable to participate in event activity."
            )
            await ctx.send(embed=error_embed)
            print(f"Event participation error: {e}")
    
    @commands.command(name="dream", aliases=["dreamtime"])
    async def dream_event(self, ctx):
        """Experience a random dream event"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            
            # Check cooldown (can dream once every 8 hours)
            last_dream = user_data.get("last_dream")
            if last_dream:
                is_cooldown, hours_remaining = is_on_cooldown(last_dream, 8)
                if is_cooldown:
                    next_dream = datetime.fromisoformat(last_dream) + timedelta(hours=8)
                    embed = self.embed_builder.warning_embed(
                        "Still Dreaming",
                        f"You can enter another dream <t:{int(next_dream.timestamp())}:R>"
                    )
                    await ctx.send(embed=embed)
                    return
            
            # Select random dream event
            dream_id = random.choice(list(self.dream_events.keys()))
            dream_data = self.dream_events[dream_id]
            
            # Create dream experience
            embed = await self.create_dream_experience(ctx, dream_data, user_data)
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Dream Error",
                "Unable to enter the dream realm."
            )
            await ctx.send(embed=error_embed)
            print(f"Dream command error: {e}")
    
    @commands.command(name="dailyquest", aliases=["dq"])
    @check_channel_restriction()
    async def daily_quest(self, ctx):
        """Get a daily quest for extra rewards"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            
            # Check if daily quest already completed
            last_quest = user_data.get("last_daily_quest")
            if last_quest:
                last_time = datetime.fromisoformat(last_quest)
                if last_time.date() == datetime.now().date():
                    embed = self.embed_builder.warning_embed(
                        "Quest Already Completed",
                        "You've already completed today's quest! Come back tomorrow."
                    )
                    await ctx.send(embed=embed)
                    return
            
            # Generate daily quest
            quest = self.generate_daily_quest(user_data)
            
            # Check if quest can be completed immediately
            can_complete = self.check_quest_completion(user_data, quest)
            
            if can_complete:
                # Auto-complete quest
                embed = await self.complete_daily_quest(ctx, quest, user_data)
            else:
                # Show quest requirements
                embed = self.create_quest_embed(quest)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Daily Quest Error",
                "Unable to generate daily quest."
            )
            await ctx.send(embed=error_embed)
            print(f"Daily quest error: {e}")
    
    async def handle_event_participation(self, ctx, event_data: Dict, activity: str):
        """Handle participation in a specific event activity"""
        user_data = data_manager.get_user_data(str(ctx.author.id))
        
        # Check participation cooldown (once per 4 hours per activity)
        last_participation = user_data.get("event_participation", {}).get(activity)
        if last_participation:
            is_cooldown, hours_remaining = is_on_cooldown(last_participation, 4)
            if is_cooldown:
                embed = self.embed_builder.warning_embed(
                    "Activity Cooldown",
                    f"You can participate in {activity.replace('_', ' ').title()} again in {hours_remaining} hours."
                )
                await ctx.send(embed=embed)
                return
        
        # Activity-specific logic
        activity_results = await self.process_activity(activity, event_data, user_data)
        
        # Update participation time
        user_data.setdefault("event_participation", {})[activity] = datetime.now().isoformat()
        
        # Save user data
        data_manager.save_user_data(str(ctx.author.id), user_data)
        
        # Create result embed
        embed = self.create_activity_result_embed(activity, activity_results, event_data)
        await ctx.send(embed=embed)
    
    async def process_activity(self, activity: str, event_data: Dict, user_data: Dict) -> Dict:
        """Process a specific event activity"""
        results = {"rewards": {}, "experience": "", "success": True}
        
        # Activity-specific processing
        if activity == "flower_viewing":
            # Spring activity
            results["experience"] = "You find a peaceful spot under the cherry blossoms and enjoy their beauty."
            results["rewards"] = {"Sakura Petal": random.randint(2, 5), "gold": random.randint(500, 1000)}
        
        elif activity == "beach_volleyball":
            # Summer activity
            success = random.random() < 0.7  # 70% success rate
            if success:
                results["experience"] = "You win the beach volleyball match with amazing teamwork!"
                results["rewards"] = {"Golden Seashell": 1, "gold": random.randint(800, 1500)}
            else:
                results["experience"] = "You gave it your best effort but lost the match. Better luck next time!"
                results["rewards"] = {"Beach Sand": random.randint(1, 3), "gold": random.randint(200, 500)}
                results["success"] = False
        
        elif activity == "apple_picking":
            # Autumn activity
            apples_picked = random.randint(5, 15)
            results["experience"] = f"You spent the day picking apples and gathered {apples_picked} delicious ones!"
            results["rewards"] = {"Golden Apple": apples_picked // 3, "Regular Apple": apples_picked, "gold": apples_picked * 50}
        
        elif activity == "gift_exchange":
            # Winter activity
            gift_quality = random.choices(["common", "rare", "legendary"], weights=[60, 35, 5])[0]
            if gift_quality == "legendary":
                results["experience"] = "You received an incredibly rare and beautiful gift!"
                results["rewards"] = {"Winter Gift": 1, "Legendary Crystal": 1, "gold": 2000}
            elif gift_quality == "rare":
                results["experience"] = "You exchanged wonderful gifts with fellow adventurers!"
                results["rewards"] = {"Winter Gift": 1, "Rare Ornament": 1, "gold": 1000}
            else:
                results["experience"] = "You had a lovely time exchanging gifts!"
                results["rewards"] = {"Winter Gift": 1, "Festive Cookie": random.randint(2, 5), "gold": 500}
        
        else:
            # Default activity
            results["experience"] = f"You participated in {activity.replace('_', ' ')} and had a great time!"
            results["rewards"] = {"Event Token": 1, "gold": random.randint(300, 800)}
        
        # Apply event bonuses
        for reward_type, amount in results["rewards"].items():
            if reward_type == "gold" and "daily_gold" in event_data.get("bonuses", {}):
                results["rewards"][reward_type] = int(amount * event_data["bonuses"]["daily_gold"])
        
        # Add rewards to user inventory
        inventory = user_data.setdefault("inventory", {})
        for item, amount in results["rewards"].items():
            if item == "gold":
                user_data["gold"] = user_data.get("gold", 0) + amount
            else:
                inventory[item] = inventory.get(item, 0) + amount
        
        return results
    
    def get_current_seasonal_event(self) -> Optional[Dict]:
        """Get currently active seasonal event based on date"""
        # This is a simplified implementation
        # In practice, you'd check actual dates and event schedules
        current_month = datetime.now().month
        
        if current_month in [3, 4, 5]:  # Spring
            return self.seasonal_events["spring_festival"]
        elif current_month in [6, 7, 8]:  # Summer
            return self.seasonal_events["summer_games"]
        elif current_month in [9, 10, 11]:  # Autumn
            return self.seasonal_events["autumn_harvest"]
        elif current_month in [12, 1, 2]:  # Winter
            return self.seasonal_events["winter_celebration"]
        
        return None
    
    def generate_daily_quest(self, user_data: Dict) -> Dict:
        """Generate a random daily quest"""
        quest_types = [
            {
                "name": "Battle Training",
                "description": "Win 3 battles against any opponent",
                "requirements": {"battles_won": 3},
                "rewards": {"gold": 2000, "Experience Scroll": 2}
            },
            {
                "name": "Material Gathering",
                "description": "Gather 10 crafting materials",
                "requirements": {"materials_gathered": 10},
                "rewards": {"gold": 1500, "Mystic Crystal": 1}
            },
            {
                "name": "Character Summoning",
                "description": "Summon 5 new characters",
                "requirements": {"summons_performed": 5},
                "rewards": {"gems": 100, "Star Fragment": 1}
            },
            {
                "name": "Investment Mogul",
                "description": "Collect income from your businesses",
                "requirements": {"income_collected": 1},
                "rewards": {"gold": 3000, "Business License": 1}
            }
        ]
        
        return random.choice(quest_types)
    
    def check_quest_completion(self, user_data: Dict, quest: Dict) -> bool:
        """Check if a quest can be completed with current user stats"""
        requirements = quest["requirements"]
        
        if "battles_won" in requirements:
            daily_battles = user_data.get("daily_battles_won", 0)
            return daily_battles >= requirements["battles_won"]
        
        if "materials_gathered" in requirements:
            daily_gathered = user_data.get("daily_materials_gathered", 0)
            return daily_gathered >= requirements["materials_gathered"]
        
        if "summons_performed" in requirements:
            daily_summons = user_data.get("daily_summons", 0)
            return daily_summons >= requirements["summons_performed"]
        
        if "income_collected" in requirements:
            last_collection = user_data.get("last_income_collection")
            if last_collection:
                last_time = datetime.fromisoformat(last_collection)
                return last_time.date() == datetime.now().date()
        
        return False
    
    async def complete_daily_quest(self, ctx, quest: Dict, user_data: Dict) -> discord.Embed:
        """Complete a daily quest and give rewards"""
        # Add rewards
        inventory = user_data.setdefault("inventory", {})
        for item, amount in quest["rewards"].items():
            if item == "gold":
                user_data["gold"] = user_data.get("gold", 0) + amount
            elif item == "gems":
                user_data["gems"] = user_data.get("gems", 0) + amount
            else:
                inventory[item] = inventory.get(item, 0) + amount
        
        # Mark quest as completed
        user_data["last_daily_quest"] = datetime.now().isoformat()
        
        # Update quest completion stats
        user_data["quests_completed"] = user_data.get("quests_completed", 0) + 1
        
        data_manager.save_user_data(str(ctx.author.id), user_data)
        
        # Create completion embed
        embed = self.embed_builder.success_embed(
            "Quest Completed!",
            f"Successfully completed: **{quest['name']}**"
        )
        
        rewards_text = ""
        for item, amount in quest["rewards"].items():
            if item == "gold":
                rewards_text += f"💰 {format_number(amount)} gold\n"
            elif item == "gems":
                rewards_text += f"💎 {format_number(amount)} gems\n"
            else:
                rewards_text += f"🎁 {item} x{amount}\n"
        
        embed.add_field(
            name="🎁 Rewards Received",
            value=rewards_text,
            inline=False
        )
        
        return embed
    
    async def create_dream_experience(self, ctx, dream_data: Dict, user_data: Dict) -> discord.Embed:
        """Create a dream experience and apply rewards"""
        # Select random story fragment
        story_fragment = random.choice(dream_data["story_fragments"])
        
        # Give random reward
        reward_item = random.choice(dream_data["rewards"])
        reward_amount = random.randint(1, 3)
        
        # Add reward to inventory
        inventory = user_data.setdefault("inventory", {})
        inventory[reward_item] = inventory.get(reward_item, 0) + reward_amount
        
        # Give some dream XP
        dream_xp = random.randint(50, 150)
        user_data["xp"] = user_data.get("xp", 0) + dream_xp
        
        # Update dream timestamp
        user_data["last_dream"] = datetime.now().isoformat()
        
        # Track dream experiences
        user_data.setdefault("dreams_experienced", []).append(dream_data["name"])
        
        data_manager.save_user_data(str(ctx.author.id), user_data)
        
        # Create dream embed
        embed = self.embed_builder.create_embed(
            title=f"✨ {dream_data['name']}",
            description=dream_data["description"],
            color=0x9370DB
        )
        
        embed.add_field(
            name="🌙 Dream Vision",
            value=story_fragment,
            inline=False
        )
        
        embed.add_field(
            name="🎁 Dream Gift",
            value=f"**{reward_item}** x{reward_amount}\n⭐ {dream_xp} XP",
            inline=True
        )
        
        embed.add_field(
            name="💤 Next Dream",
            value="You can enter another dream in 8 hours",
            inline=True
        )
        
        return embed
    
    def create_events_overview_embed(self) -> discord.Embed:
        """Create events overview embed"""
        embed = self.embed_builder.create_embed(
            title="🎊 Events & Activities",
            description="Participate in special events for exclusive rewards!",
            color=0xFF69B4
        )
        
        # Current seasonal event
        current_event = self.get_current_seasonal_event()
        if current_event:
            embed.add_field(
                name=f"🌟 {current_event['name']} (Active)",
                value=f"{current_event['description']}\n"
                      f"**Activities:** {', '.join(current_event['activities'])}",
                inline=False
            )
        else:
            embed.add_field(
                name="🌟 Seasonal Events",
                value="No seasonal events currently active",
                inline=False
            )
        
        # Available commands
        embed.add_field(
            name="🎮 Event Commands",
            value="• `!events participate <activity>` - Join event activity\n"
                  "• `!dream` - Experience a dream event\n"
                  "• `!dailyquest` - Get daily quest rewards",
            inline=True
        )
        
        # Special features
        embed.add_field(
            name="✨ Special Features",
            value="• Dream events every 8 hours\n"
                  "• Daily quests for bonus rewards\n"
                  "• Seasonal bonuses and exclusive items\n"
                  "• Random mini-events throughout the day",
            inline=True
        )
        
        return embed
    
    def create_activity_result_embed(self, activity: str, results: Dict, event_data: Dict) -> discord.Embed:
        """Create activity participation result embed"""
        activity_name = activity.replace("_", " ").title()
        
        if results["success"]:
            embed = self.embed_builder.success_embed(
                f"{activity_name} Complete!",
                results["experience"]
            )
        else:
            embed = self.embed_builder.create_embed(
                title=f"{activity_name} Attempt",
                description=results["experience"],
                color=0xFFA500
            )
        
        # Show rewards
        rewards_text = ""
        for item, amount in results["rewards"].items():
            if item == "gold":
                rewards_text += f"💰 {format_number(amount)} gold\n"
            else:
                rewards_text += f"🎁 {item} x{amount}\n"
        
        embed.add_field(
            name="🎁 Rewards",
            value=rewards_text or "No rewards",
            inline=True
        )
        
        embed.add_field(
            name="⏰ Next Participation",
            value="You can participate again in 4 hours",
            inline=True
        )
        
        return embed
    
    def create_quest_embed(self, quest: Dict) -> discord.Embed:
        """Create daily quest information embed"""
        embed = self.embed_builder.create_embed(
            title=f"📜 Daily Quest: {quest['name']}",
            description=quest["description"],
            color=0x4169E1
        )
        
        # Show requirements
        requirements_text = ""
        for req_type, req_value in quest["requirements"].items():
            req_name = req_type.replace("_", " ").title()
            requirements_text += f"• {req_name}: {req_value}\n"
        
        embed.add_field(
            name="📋 Requirements",
            value=requirements_text,
            inline=True
        )
        
        # Show rewards
        rewards_text = ""
        for item, amount in quest["rewards"].items():
            if item == "gold":
                rewards_text += f"💰 {format_number(amount)} gold\n"
            elif item == "gems":
                rewards_text += f"💎 {format_number(amount)} gems\n"
            else:
                rewards_text += f"🎁 {item} x{amount}\n"
        
        embed.add_field(
            name="🎁 Rewards",
            value=rewards_text,
            inline=True
        )
        
        embed.add_field(
            name="💡 Tip",
            value="Progress towards this quest through normal gameplay, then use `!dailyquest` again to claim rewards!",
            inline=False
        )
        
        return embed


async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(EventsCommands(bot))