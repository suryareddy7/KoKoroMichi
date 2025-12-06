# Pet System Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List, Any
import random
from datetime import datetime, timedelta

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from core.config import FEATURES
from utils.helpers import format_number
from utils.shared import channel_manager
from utils.channel_restriction import check_channel_restriction
import logging

logger = logging.getLogger(__name__)

class PetCommands(commands.Cog):
    """Pet companion system with care, training, and adventures"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        
        # Load pet data from JSON file
        self.load_pet_data()
    
    def load_pet_data(self):
        """Load pet data from pets_companions.json"""
        try:
            pet_data = data_manager.get_game_data("pets_companions")
            self.pet_species = pet_data.get("pet_species", [])
            self.pet_settings = pet_data.get("pet_settings", {})
            self.pet_activities = pet_data.get("pet_activities", [])
            self.pet_foods = pet_data.get("pet_foods", [])
        except Exception as e:
            logger.error(f"Failed to load pet data: {e}")
            self.pet_species = []
            self.pet_settings = {}
            self.pet_activities = []
            self.pet_foods = []
    
    @commands.command(name="pets", aliases=["mypets", "companions"])
    async def view_pets(self, ctx):
        """View your pet companions"""
        # Enforce channel restrictions for pet commands
        restriction_result = await check_channel_restriction(
            ctx, ["pet-corner", "companion-grove", "animal-sanctuary"], ctx.bot
        )
        if not restriction_result:
            await ctx.send("🐾 Pet commands can only be used in pet channels!", delete_after=10)
            return
        
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            user_pets = user_data.get("pets", [])
            
            embed = self.embed_builder.create_embed(
                title="🐾 Your Pet Companions",
                description="Loyal companions on your adventure",
                color=0xFF8C00
            )
            
            if user_pets:
                for pet in user_pets:
                    pet_emoji = pet.get("emoji", "🐾")
                    pet_name = pet.get("name", "Unknown Pet")
                    pet_level = pet.get("level", 1)
                    loyalty = pet.get("loyalty", 0)
                    happiness = pet.get("happiness", 50)
                    
                    # Calculate pet power
                    pet_power = sum(pet.get("stats", {}).values()) * pet_level
                    
                    embed.add_field(
                        name=f"{pet_emoji} {pet_name}",
                        value=f"**Level:** {pet_level}\n"
                              f"**Loyalty:** {loyalty}/100\n"
                              f"**Happiness:** {happiness}/100\n"
                              f"**Power:** {format_number(pet_power)}",
                        inline=True
                    )
            else:
                embed.add_field(
                    name="🌱 No Pets Yet",
                    value="You don't have any pet companions yet!\n"
                          "Use `!adopt_pet` to find a loyal companion!",
                    inline=False
                )
            
            # Pet care tips
            embed.add_field(
                name="💡 Pet Care Tips",
                value="• Feed pets daily to maintain happiness\n"
                      "• Train pets to increase their abilities\n"
                      "• Send pets on adventures for rewards\n"
                      "• Happy pets provide better bonuses",
                inline=False
            )
            
            await ctx.send(embed=embed)
            # Log activity if needed
            pass
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Pet Error",
                "Unable to load pet information."
            )
            await ctx.send(embed=embed)
            print(f"Pets command error: {e}")
    
    @commands.command(name="adopt_pet", aliases=["get_pet"])
    async def adopt_pet(self, ctx, *, pet_type: str = None):
        """Adopt a new pet companion"""
        # Enforce channel restrictions for pet commands
        restriction_result = await check_channel_restriction(
            ctx, ["pet-corner", "companion-grove", "animal-sanctuary"], ctx.bot
        )
        if not restriction_result:
            await ctx.send("🐾 Pet commands can only be used in pet channels!", delete_after=10)
            return
        
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            user_pets = user_data.get("pets", [])
            
            # Check pet limit
            if len(user_pets) >= 3:
                embed = self.embed_builder.warning_embed(
                    "Pet Limit Reached",
                    "You can only have 3 pet companions at once. Release a pet first if you want a new one."
                )
                await ctx.send(embed=embed)
                return
            
            if not pet_type:
                # Show available pets
                embed = self.create_pet_shop_embed()
                await ctx.send(embed=embed)
                return
            
            # Find pet type from JSON data
            pet_template = None
            for species in self.pet_species:
                if species.get("name", "").lower() == pet_type.lower() or species.get("id", "").lower() == pet_type.lower():
                    pet_template = species
                    break
            
            if not pet_template:
                embed = self.embed_builder.error_embed(
                    "Pet Not Found",
                    f"Pet type '{pet_type}' not available. Use `!adopt_pet` to see available pets."
                )
                await ctx.send(embed=embed)
                return
            adoption_cost = pet_template.get("adoption_cost", 3000)
            
            # Check if user has enough gold
            user_gold = user_data.get("gold", 0)
            if user_gold < adoption_cost:
                embed = self.embed_builder.error_embed(
                    "Insufficient Gold",
                    f"Adopting a {pet_template['name']} costs {format_number(adoption_cost)} gold.\n"
                    f"You have: {format_number(user_gold)} gold"
                )
                await ctx.send(embed=embed)
                return
            
            # Create new pet
            new_pet = {
                "type": pet_type_lower,
                "name": pet_template["name"],
                "emoji": pet_template["emoji"],
                "level": 1,
                "exp": 0,
                "stats": pet_template["stats"].copy(),
                "loyalty": random.randint(20, 40),
                "happiness": random.randint(60, 80),
                "special_ability": pet_template["special_ability"],
                "adopted_at": datetime.now().isoformat(),
                "last_fed": datetime.now().isoformat(),
                "last_trained": "",
                "adventures_completed": 0
            }
            
            # Deduct cost and add pet
            user_data["gold"] -= adoption_cost
            user_pets.append(new_pet)
            user_data["pets"] = user_pets
            
            # Save data
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Create adoption success embed
            embed = self.embed_builder.success_embed(
                "Pet Adopted!",
                f"Welcome your new companion: **{pet_template['name']}**!"
            )
            
            embed.add_field(
                name=f"{pet_template['emoji']} New Companion",
                value=f"**{pet_template['name']}**\n*{pet_template['description']}*",
                inline=False
            )
            
            # Show initial stats
            stats = new_pet["stats"]
            embed.add_field(
                name="📊 Initial Stats",
                value=f"💪 Strength: {stats['strength']}\n"
                      f"🧠 Intelligence: {stats['intelligence']}\n"
                      f"⚡ Agility: {stats['agility']}\n"
                      f"💖 Loyalty: {new_pet['loyalty']}/100",
                inline=True
            )
            
            embed.add_field(
                name="✨ Special Ability",
                value=f"🎯 **{new_pet['special_ability']}**\n"
                      f"Happiness: {new_pet['happiness']}/100\n"
                      f"Growth Rate: {pet_template['growth_rate'].title()}",
                inline=True
            )
            
            embed.add_field(
                name="💰 Adoption Cost",
                value=f"Paid: {format_number(adoption_cost)} gold\n"
                      f"Remaining: {format_number(user_data['gold'])} gold",
                inline=False
            )
            
            await ctx.send(embed=embed)
            # Log activity
            logger.info(f"User {ctx.author} adopted {pet_template['name']}")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Adoption Error",
                "Unable to complete pet adoption."
            )
            await ctx.send(embed=embed)
            print(f"Adopt pet error: {e}")
    
    @commands.command(name="feed_pet", aliases=["feed"])
    async def feed_pet(self, ctx, *, pet_name: str = None):
        """Feed your pet to maintain happiness"""
        # Check channel restriction
        if not await channel_manager.check_channel_restriction(ctx, "feed"):
            return
        
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            user_pets = user_data.get("pets", [])
            
            if not user_pets:
                embed = self.embed_builder.error_embed(
                    "No Pets",
                    "You don't have any pets to feed. Use `!adopt_pet` first!"
                )
                await ctx.send(embed=embed)
                return
            
            # Select pet
            if pet_name:
                pet = self.find_pet_by_name(user_pets, pet_name)
                if not pet:
                    embed = self.embed_builder.error_embed(
                        "Pet Not Found",
                        f"Pet '{pet_name}' not found. Use `!pets` to see your companions."
                    )
                    await ctx.send(embed=embed)
                    return
            else:
                # Feed first pet
                pet = user_pets[0]
            
            # Check feeding cooldown (4 hours)
            last_fed = datetime.fromisoformat(pet.get("last_fed", datetime.now().isoformat()))
            if datetime.now() - last_fed < timedelta(hours=4):
                time_left = timedelta(hours=4) - (datetime.now() - last_fed)
                hours_left = int(time_left.total_seconds() / 3600)
                minutes_left = int((time_left.total_seconds() % 3600) / 60)
                
                embed = self.embed_builder.warning_embed(
                    "Pet Not Hungry",
                    f"{pet['name']} isn't hungry yet! Wait {hours_left}h {minutes_left}m before feeding again."
                )
                await ctx.send(embed=embed)
                return
            
            # Feeding cost
            feeding_cost = 100 * pet.get("level", 1)
            user_gold = user_data.get("gold", 0)
            
            if user_gold < feeding_cost:
                embed = self.embed_builder.error_embed(
                    "Insufficient Gold",
                    f"Feeding costs {format_number(feeding_cost)} gold. You have {format_number(user_gold)} gold."
                )
                await ctx.send(embed=embed)
                return
            
            # Feed pet
            user_data["gold"] -= feeding_cost
            pet["happiness"] = min(100, pet.get("happiness", 50) + random.randint(10, 25))
            pet["loyalty"] = min(100, pet.get("loyalty", 0) + random.randint(1, 5))
            pet["last_fed"] = datetime.now().isoformat()
            
            # Chance for bonus rewards from happy pet
            if pet["happiness"] >= 80:
                bonus_gold = random.randint(50, 200)
                user_data["gold"] += bonus_gold
                bonus_text = f"💰 Happy pet brought you {format_number(bonus_gold)} gold!"
            else:
                bonus_text = "🍖 Pet enjoyed the meal!"
            
            # Save data
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Create feeding result embed
            embed = self.embed_builder.success_embed(
                "Pet Fed Successfully!",
                f"**{pet['name']}** enjoyed their meal!"
            )
            
            embed.add_field(
                name=f"{pet['emoji']} Pet Status",
                value=f"**Happiness:** {pet['happiness']}/100\n"
                      f"**Loyalty:** {pet['loyalty']}/100\n"
                      f"**Level:** {pet.get('level', 1)}",
                inline=True
            )
            
            embed.add_field(
                name="💰 Feeding Cost",
                value=f"**Cost:** {format_number(feeding_cost)} gold\n"
                      f"**Remaining:** {format_number(user_data['gold'])} gold",
                inline=True
            )
            
            embed.add_field(
                name="🎁 Result",
                value=bonus_text,
                inline=False
            )
            
            await ctx.send(embed=embed)
            # Log activity
            logger.info(f"User {ctx.author} fed {pet['name']}")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Feeding Error",
                "Unable to feed pet. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Feed pet error: {e}")
    
    @commands.command(name="train_pet", aliases=["pet_train"])
    async def train_pet(self, ctx, pet_name: str = None, *, stat: str = None):
        """Train your pet to improve their abilities"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            user_pets = user_data.get("pets", [])
            
            if not user_pets:
                embed = self.embed_builder.error_embed(
                    "No Pets",
                    "You don't have any pets to train. Use `!adopt_pet` first!"
                )
                await ctx.send(embed=embed)
                return
            
            # Select pet
            if pet_name:
                pet = self.find_pet_by_name(user_pets, pet_name)
                if not pet:
                    embed = self.embed_builder.error_embed(
                        "Pet Not Found",
                        f"Pet '{pet_name}' not found."
                    )
                    await ctx.send(embed=embed)
                    return
            else:
                pet = user_pets[0]
            
            # Check training cooldown (6 hours)
            last_trained = pet.get("last_trained", "")
            if last_trained:
                last_time = datetime.fromisoformat(last_trained)
                if datetime.now() - last_time < timedelta(hours=6):
                    time_left = timedelta(hours=6) - (datetime.now() - last_time)
                    hours_left = int(time_left.total_seconds() / 3600)
                    
                    embed = self.embed_builder.warning_embed(
                        "Pet Tired",
                        f"{pet['name']} needs rest! Training available in {hours_left}h."
                    )
                    await ctx.send(embed=embed)
                    return
            
            # Training cost
            training_cost = 200 * pet.get("level", 1)
            user_gold = user_data.get("gold", 0)
            
            if user_gold < training_cost:
                embed = self.embed_builder.error_embed(
                    "Insufficient Gold",
                    f"Training costs {format_number(training_cost)} gold."
                )
                await ctx.send(embed=embed)
                return
            
            # Determine stat to train
            trainable_stats = ["strength", "intelligence", "agility", "loyalty"]
            if stat and stat.lower() in trainable_stats:
                target_stat = stat.lower()
            else:
                target_stat = random.choice(trainable_stats)
            
            # Perform training
            user_data["gold"] -= training_cost
            stat_increase = random.randint(1, 3)
            pet_stats = pet.setdefault("stats", {})
            pet_stats[target_stat] = pet_stats.get(target_stat, 5) + stat_increase
            pet["last_trained"] = datetime.now().isoformat()
            pet["exp"] = pet.get("exp", 0) + 25
            
            # Check for level up
            level_up = False
            required_exp = pet.get("level", 1) * 100
            if pet["exp"] >= required_exp:
                pet["level"] = pet.get("level", 1) + 1
                pet["exp"] = 0
                level_up = True
            
            # Save data
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Create training result
            embed = self.embed_builder.success_embed(
                "Training Complete!",
                f"**{pet['name']}** completed training!"
            )
            
            embed.add_field(
                name="📈 Training Results",
                value=f"**{target_stat.title()}:** +{stat_increase}\n"
                      f"**XP Gained:** +25\n"
                      f"**Cost:** {format_number(training_cost)} gold",
                inline=True
            )
            
            if level_up:
                embed.add_field(
                    name="🎉 Level Up!",
                    value=f"**{pet['name']}** reached Level {pet['level']}!\n"
                          f"All stats increased!",
                    inline=True
                )
            
            # Show current stats
            stats_text = ""
            for stat_name, value in pet_stats.items():
                stats_text += f"{stat_name.title()}: {value}  "
            
            embed.add_field(
                name=f"{pet['emoji']} Current Stats",
                value=stats_text,
                inline=False
            )
            
            await ctx.send(embed=embed)
            await self.log_pet_activity(ctx, "training", f"{pet['name']} - {target_stat}")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Training Error",
                "Unable to complete pet training."
            )
            await ctx.send(embed=embed)
            print(f"Train pet error: {e}")
    
    @commands.command(name="pet_adventure", aliases=["send_pet"])
    async def pet_adventure(self, ctx, *, pet_name: str = None):
        """Send your pet on an adventure for rewards"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            user_pets = user_data.get("pets", [])
            
            if not user_pets:
                embed = self.embed_builder.error_embed(
                    "No Pets",
                    "You need a pet companion for adventures!"
                )
                await ctx.send(embed=embed)
                return
            
            # Select pet
            if pet_name:
                pet = self.find_pet_by_name(user_pets, pet_name)
                if not pet:
                    embed = self.embed_builder.error_embed(
                        "Pet Not Found",
                        f"Pet '{pet_name}' not found."
                    )
                    await ctx.send(embed=embed)
                    return
            else:
                pet = user_pets[0]
            
            # Check if pet is on adventure
            if pet.get("on_adventure"):
                embed = self.embed_builder.warning_embed(
                    "Pet On Adventure",
                    f"{pet['name']} is already on an adventure! Use `!pet_status` to check progress."
                )
                await ctx.send(embed=embed)
                return
            
            # Check pet happiness requirement
            if pet.get("happiness", 0) < 30:
                embed = self.embed_builder.warning_embed(
                    "Pet Unhappy",
                    f"{pet['name']} is too unhappy for adventures. Feed them first!"
                )
                await ctx.send(embed=embed)
                return
            
            # Start adventure
            adventure_duration = random.randint(60, 180)  # 1-3 hours
            completion_time = datetime.now() + timedelta(minutes=adventure_duration)
            
            pet["on_adventure"] = True
            pet["adventure_completion"] = completion_time.isoformat()
            pet["adventure_type"] = random.choice(["treasure_hunt", "monster_patrol", "herb_gathering", "exploration"])
            
            # Save data
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Create adventure start embed
            embed = self.embed_builder.create_embed(
                title="🗺️ Adventure Begins!",
                description=f"**{pet['name']}** has set off on an adventure!",
                color=0xFF8C00
            )
            
            adventure_types = {
                "treasure_hunt": "🏴‍☠️ Treasure Hunt - Searching for hidden gold and gems",
                "monster_patrol": "⚔️ Monster Patrol - Hunting dangerous creatures for XP",
                "herb_gathering": "🌿 Herb Gathering - Collecting magical plants and materials",
                "exploration": "🗺️ Exploration - Discovering new lands and secrets"
            }
            
            adventure_desc = adventure_types.get(pet["adventure_type"], "Unknown adventure")
            
            embed.add_field(
                name="🎯 Adventure Type",
                value=adventure_desc,
                inline=False
            )
            
            embed.add_field(
                name="⏱️ Duration",
                value=f"**Time Required:** {adventure_duration} minutes\n"
                      f"**Return Time:** {completion_time.strftime('%H:%M UTC')}\n"
                      f"Check back with `!pet_status`!",
                inline=False
            )
            
            await ctx.send(embed=embed)
            await self.log_pet_activity(ctx, "adventure", f"{pet['name']} - {pet['adventure_type']}")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Adventure Error", 
                "Unable to start pet adventure."
            )
            await ctx.send(embed=embed)
            print(f"Pet adventure error: {e}")
    
    def find_pet_by_name(self, pets: List[Dict], name: str) -> Optional[Dict]:
        """Find pet by name (case insensitive)"""
        name_lower = name.lower()
        for pet in pets:
            if pet.get("name", "").lower() == name_lower:
                return pet
        return None
    
    def create_pet_shop_embed(self) -> discord.Embed:
        """Create pet shop display embed"""
        embed = self.embed_builder.create_embed(
            title="🐾 Pet Adoption Center",
            description="Choose a loyal companion for your adventures!",
            color=0xFF8C00
        )
        
        for pet_id, pet_data in self.pet_types.items():
            stats_text = ""
            for stat, value in pet_data["stats"].items():
                stats_text += f"{stat.title()}: {value}  "
            
            embed.add_field(
                name=f"{pet_data['emoji']} {pet_data['name']}",
                value=f"*{pet_data['description']}*\n"
                      f"**Stats:** {stats_text}\n"
                      f"**Special:** {pet_data['special_ability']}\n"
                      f"**Cost:** {format_number(pet_data['cost'])} gold\n"
                      f"Use: `!adopt_pet {pet_data['name']}`",
                inline=True
            )
        
        embed.add_field(
            name="💡 Pet Care Tips",
            value="• Feed pets every 4 hours to keep them happy\n"
                  "• Train pets every 6 hours to improve stats\n"
                  "• Send happy pets on adventures for rewards\n"
                  "• Loyal pets provide better battle bonuses",
            inline=False
        )
        
        return embed
    
    async def log_pet_activity(self, ctx, activity_type: str, details: str = ""):
        """Log pet activity to history channel"""
        try:
            history_channel = discord.utils.get(ctx.guild.text_channels, name='history')
            if not history_channel:
                return
            
            emojis = ["🐾", "🐲", "🦊", "🐱", "🐦", "❤️"]
            emoji = random.choice(emojis)
            
            if activity_type == "view":
                message = f"{emoji} **{ctx.author.display_name}** spent quality time checking on their beloved pet companions!"
            elif activity_type == "adoption":
                message = f"{emoji} **{ctx.author.display_name}** welcomed a new companion {details} into their family!"
            elif activity_type == "feeding":
                message = f"{emoji} **{ctx.author.display_name}** lovingly fed their faithful companion {details}!"
            elif activity_type == "training":
                message = f"{emoji} **{ctx.author.display_name}** trained their pet {details} to become stronger!"
            elif activity_type == "adventure":
                message = f"{emoji} **{ctx.author.display_name}** sent their brave pet {details} on an exciting adventure!"
            else:
                message = f"{emoji} **{ctx.author.display_name}** cared for their pet companions!"
            
            embed = self.embed_builder.create_embed(
                description=message,
                color=0xFF8C00
            )
            
            await history_channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error logging pet activity: {e}")

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(PetCommands(bot))