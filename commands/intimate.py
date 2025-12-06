# Intimate Interactions Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List, Any
import random
from datetime import datetime, timedelta

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from core.config import FEATURES
from utils.helpers import format_number
from utils.channel_restriction import check_channel_restriction

class IntimateCommands(commands.Cog):
    """Character relationship and affection system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        
        # Intimate interaction types
        self.interaction_types = {
            "gentle": {
                "headpat": {
                    "name": "Gentle Headpat",
                    "description": "Give your character a loving headpat",
                    "affection_gain": (3, 8),
                    "emoji": "🤗",
                    "responses": [
                        "blushes softly and leans into your touch",
                        "closes eyes peacefully and smiles",
                        "giggles happily at your affection",
                        "nuzzles against your hand lovingly"
                    ]
                },
                "hug": {
                    "name": "Warm Hug",
                    "description": "Embrace your character warmly",
                    "affection_gain": (5, 12),
                    "emoji": "🤗",
                    "responses": [
                        "melts into your embrace",
                        "hugs you back tightly",
                        "feels safe and content in your arms",
                        "whispers 'thank you' softly"
                    ]
                },
                "compliment": {
                    "name": "Heartfelt Compliment",
                    "description": "Tell your character how amazing they are",
                    "affection_gain": (4, 10),
                    "emoji": "💝",
                    "responses": [
                        "blushes deeply and smiles shyly",
                        "beams with happiness at your words",
                        "covers face bashfully but peeks through fingers",
                        "feels truly appreciated and valued"
                    ]
                }
            },
            "playful": {
                "tickle": {
                    "name": "Playful Tickle",
                    "description": "Engage in playful tickling",
                    "affection_gain": (2, 6),
                    "emoji": "😆",
                    "responses": [
                        "laughs uncontrollably and tries to escape",
                        "squeals with delight and giggles",
                        "playfully swats at your hands while laughing",
                        "collapses in a fit of giggles"
                    ]
                },
                "play_game": {
                    "name": "Play Together",
                    "description": "Spend time playing games together",
                    "affection_gain": (6, 15),
                    "emoji": "🎮",
                    "responses": [
                        "enjoys the fun competition",
                        "gets competitive but keeps smiling",
                        "celebrates victories together",
                        "has a wonderful time playing"
                    ]
                }
            },
            "romantic": {
                "hand_hold": {
                    "name": "Hold Hands",
                    "description": "Gently hold your character's hand",
                    "affection_gain": (8, 18),
                    "emoji": "👫",
                    "responses": [
                        "intertwines fingers with yours",
                        "feels butterflies and smiles warmly",
                        "squeezes your hand affectionately",
                        "looks into your eyes lovingly"
                    ],
                    "min_affection": 50
                },
                "kiss_cheek": {
                    "name": "Gentle Kiss",
                    "description": "Give a sweet kiss on the cheek",
                    "affection_gain": (12, 25),
                    "emoji": "💋",
                    "responses": [
                        "turns red as a tomato but smiles",
                        "touches the spot where you kissed",
                        "feels overwhelmed with happiness",
                        "gives you a shy kiss back"
                    ],
                    "min_affection": 80
                }
            }
        }
    
    @commands.command(name="intimate", aliases=["interact", "affection"])
    async def intimate_interaction(self, ctx, character_name: str = None, *, interaction_type: str = None):
        """Interact intimately with your characters to build affection"""
        # Enforce channel restrictions for intimate commands
        restriction_result = await check_channel_restriction(
            ctx, ["intimate-chambers", "affection-alcove", "private-moments"], ctx.bot
        )
        if not restriction_result:
            await ctx.send("💕 Intimate commands can only be used in intimate channels!", delete_after=10)
            return
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            user_characters = user_data.get("claimed_waifus", [])
            
            if not user_characters:
                embed = self.embed_builder.error_embed(
                    "No Waifus Found",
                    "You don't have any waifus yet! Use `!summon` to get your first waifu."
                )
                await ctx.send(embed=embed)
                return
            
            # If no character name provided, pick a random one
            if not character_name:
                selected_character = random.choice(user_characters)
                character_name = selected_character.get("name", "Unknown")
                embed = self.embed_builder.info_embed(
                    "Random Waifu Selected",
                    f"Interacting with **{character_name}** since no specific waifu was mentioned!"
                )
                await ctx.send(embed=embed)
            
            # This block is now handled above with random selection
            
            # Find character
            character = self.find_character_by_name(user_characters, character_name)
            if not character:
                embed = self.embed_builder.error_embed(
                    "Character Not Found",
                    f"'{character_name}' not found in your collection."
                )
                await ctx.send(embed=embed)
                return
            
            if not interaction_type:
                # Show available interactions for this character
                embed = self.create_character_interactions_embed(character)
                await ctx.send(embed=embed)
                return
            
            # Find interaction
            interaction_data = self.find_interaction_by_name(interaction_type)
            if not interaction_data:
                embed = self.embed_builder.error_embed(
                    "Invalid Interaction",
                    f"Interaction '{interaction_type}' not found. Use `!intimate {character_name}` to see options."
                )
                await ctx.send(embed=embed)
                return
            
            interaction_info, category = interaction_data
            
            # Check affection requirements
            current_affection = character.get("affection", 0)
            min_affection = interaction_info.get("min_affection", 0)
            
            if current_affection < min_affection:
                embed = self.embed_builder.warning_embed(
                    "Affection Too Low",
                    f"This interaction requires {min_affection} affection.\n"
                    f"{character['name']} currently has {current_affection} affection."
                )
                await ctx.send(embed=embed)
                return
            
            # Check interaction cooldown (30 minutes)
            last_interaction = character.get("last_intimate_interaction", "")
            if last_interaction:
                last_time = datetime.fromisoformat(last_interaction)
                if datetime.now() - last_time < timedelta(minutes=30):
                    time_left = timedelta(minutes=30) - (datetime.now() - last_time)
                    minutes_left = int(time_left.total_seconds() / 60)
                    
                    embed = self.embed_builder.warning_embed(
                        "Interaction Cooldown",
                        f"Please wait {minutes_left} minutes before another intimate interaction with {character['name']}."
                    )
                    await ctx.send(embed=embed)
                    return
            
            # Perform interaction
            min_gain, max_gain = interaction_info["affection_gain"]
            affection_gained = random.randint(min_gain, max_gain)
            
            # Bonus affection for high-level characters
            char_level = character.get("level", 1)
            if char_level >= 25:
                affection_gained = int(affection_gained * 1.2)
            
            # Apply affection gain
            character["affection"] = min(100, current_affection + affection_gained)
            character["last_intimate_interaction"] = datetime.now().isoformat()
            
            # Update interaction statistics
            char_stats = character.setdefault("interaction_stats", {})
            char_stats["total_interactions"] = char_stats.get("total_interactions", 0) + 1
            char_stats["total_affection_gained"] = char_stats.get("total_affection_gained", 0) + affection_gained
            
            # Save data
            data_manager.save_user_data(str(ctx.author.id), user_data)
            
            # Select random response
            response = random.choice(interaction_info["responses"])
            
            # Create interaction result embed
            embed = self.embed_builder.create_embed(
                title=f"{interaction_info['emoji']} {interaction_info['name']}",
                description=f"You {interaction_info['description'].lower()} **{character['name']}**",
                color=0xFF69B4
            )
            
            embed.add_field(
                name="💖 Character Response",
                value=f"*{character['name']} {response}*",
                inline=False
            )
            
            embed.add_field(
                name="📈 Affection Change",
                value=f"**Before:** {current_affection}/100\n"
                      f"**Gained:** +{affection_gained}\n"
                      f"**After:** {character['affection']}/100",
                inline=True
            )
            
            # Check for affection milestones
            milestone_message = self.check_affection_milestones(character['affection'], current_affection)
            if milestone_message:
                embed.add_field(
                    name="🌟 Milestone Reached!",
                    value=milestone_message,
                    inline=True
                )
            
            # Relationship status
            relationship_level = self.get_relationship_level(character['affection'])
            embed.add_field(
                name="💝 Relationship Status",
                value=f"**Level:** {relationship_level}\n"
                      f"**Bond Strength:** {self.get_bond_strength(character['affection'])}",
                inline=False
            )
            
            await ctx.send(embed=embed)
            await self.log_intimate_activity(ctx, "interaction", f"{character_name} - {interaction_info['name']}")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Interaction Error",
                "Unable to perform interaction. Please try again."
            )
            await ctx.send(embed=embed)
            print(f"Intimate command error: {e}")
    
    @commands.command(name="relationship", aliases=["bond", "affection_status"])
    async def view_relationship(self, ctx, *, character_name: str = None):
        """View relationship status with your characters"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            user_characters = user_data.get("claimed_waifus", [])
            
            if not user_characters:
                embed = self.embed_builder.error_embed(
                    "No Characters",
                    "You don't have any characters yet!"
                )
                await ctx.send(embed=embed)
                return
            
            if character_name:
                # Show specific character relationship
                character = self.find_character_by_name(user_characters, character_name)
                if not character:
                    embed = self.embed_builder.error_embed(
                        "Character Not Found",
                        f"'{character_name}' not found in your collection."
                    )
                    await ctx.send(embed=embed)
                    return
                
                embed = self.create_character_relationship_embed(character)
                await ctx.send(embed=embed)
            else:
                # Show all relationships
                embed = self.create_all_relationships_embed(user_characters)
                await ctx.send(embed=embed)
            
            await self.log_intimate_activity(ctx, "relationship_check", character_name)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Relationship Error",
                "Unable to load relationship information."
            )
            await ctx.send(embed=embed)
            print(f"Relationship command error: {e}")
    
    def find_character_by_name(self, characters: List[Dict], name: str) -> Optional[Dict]:
        """Find character by name (case insensitive)"""
        name_lower = name.lower()
        for char in characters:
            if char.get("name", "").lower() == name_lower:
                return char
        return None
    
    def find_interaction_by_name(self, name: str) -> Optional[tuple]:
        """Find interaction by name"""
        name_lower = name.lower().replace(" ", "_")
        for category, interactions in self.interaction_types.items():
            if name_lower in interactions:
                return (interactions[name_lower], category)
            # Also check by display name
            for int_key, int_data in interactions.items():
                if int_data["name"].lower() == name.lower():
                    return (int_data, category)
        return None
    
    def create_interaction_menu_embed(self, characters: List[Dict]) -> discord.Embed:
        """Create interaction menu for all characters"""
        embed = self.embed_builder.create_embed(
            title="💖 Intimate Interactions",
            description="Build deeper relationships with your characters!",
            color=0xFF69B4
        )
        
        # Show top characters by affection
        top_chars = sorted(characters, key=lambda c: c.get("affection", 0), reverse=True)[:5]
        
        chars_text = ""
        for char in top_chars:
            affection = char.get("affection", 0)
            relationship = self.get_relationship_level(affection)
            chars_text += f"💖 **{char['name']}** - {affection}/100 ({relationship})\n"
        
        embed.add_field(
            name="👥 Your Characters",
            value=chars_text,
            inline=False
        )
        
        # Show interaction categories
        embed.add_field(
            name="🌟 Interaction Types",
            value="**Gentle** 🤗 - Headpats, hugs, compliments\n"
                  "**Playful** 😆 - Games, tickling, fun activities\n"
                  "**Romantic** 💋 - Hand-holding, kisses (high affection required)",
            inline=False
        )
        
        embed.add_field(
            name="💡 Usage",
            value="• `!intimate <character>` - See available interactions\n"
                  "• `!intimate <character> <interaction>` - Perform interaction\n"
                  "• `!relationship <character>` - Check relationship status\n"
                  "• 30-minute cooldown between interactions",
            inline=False
        )
        
        return embed
    
    def create_character_interactions_embed(self, character: Dict) -> discord.Embed:
        """Create available interactions embed for a character"""
        char_name = character.get("name", "Unknown")
        current_affection = character.get("affection", 0)
        
        embed = self.embed_builder.create_embed(
            title=f"💖 Interactions with {char_name}",
            description=f"Current affection: {current_affection}/100",
            color=0xFF69B4
        )
        
        for category, interactions in self.interaction_types.items():
            category_text = ""
            for int_key, int_data in interactions.items():
                min_affection = int_data.get("min_affection", 0)
                
                if current_affection >= min_affection:
                    status = "✅ Available"
                    min_gain, max_gain = int_data["affection_gain"]
                    category_text += f"{int_data['emoji']} **{int_data['name']}** - +{min_gain}-{max_gain} affection\n"
                else:
                    status = f"🔒 Requires {min_affection} affection"
                    category_text += f"🔒 **{int_data['name']}** - {status}\n"
            
            if category_text:
                embed.add_field(
                    name=f"{category.title()} Interactions",
                    value=category_text,
                    inline=False
                )
        
        # Show relationship info
        relationship_level = self.get_relationship_level(current_affection)
        bond_strength = self.get_bond_strength(current_affection)
        
        embed.add_field(
            name="💝 Current Relationship",
            value=f"**Level:** {relationship_level}\n"
                  f"**Bond:** {bond_strength}\n"
                  f"**Next Milestone:** {self.get_next_milestone(current_affection)}",
            inline=True
        )
        
        return embed
    
    def create_character_relationship_embed(self, character: Dict) -> discord.Embed:
        """Create detailed relationship embed for a character"""
        char_name = character.get("name", "Unknown")
        affection = character.get("affection", 0)
        
        embed = self.embed_builder.create_embed(
            title=f"💝 Relationship with {char_name}",
            description=f"Your bond with **{char_name}**",
            color=0xFF69B4
        )
        
        # Relationship details
        relationship_level = self.get_relationship_level(affection)
        bond_strength = self.get_bond_strength(affection)
        
        embed.add_field(
            name="💖 Bond Status",
            value=f"**Affection:** {affection}/100\n"
                  f"**Relationship:** {relationship_level}\n"
                  f"**Bond Strength:** {bond_strength}",
            inline=True
        )
        
        # Interaction history
        char_stats = character.get("interaction_stats", {})
        total_interactions = char_stats.get("total_interactions", 0)
        total_affection_gained = char_stats.get("total_affection_gained", 0)
        
        embed.add_field(
            name="📊 Interaction History",
            value=f"**Total Interactions:** {total_interactions}\n"
                  f"**Affection Gained:** {total_affection_gained}\n"
                  f"**Average per Interaction:** {total_affection_gained // max(1, total_interactions)}",
            inline=True
        )
        
        # Unlocked interactions
        unlocked_count = 0
        total_interactions_available = 0
        
        for category, interactions in self.interaction_types.items():
            for int_key, int_data in interactions.items():
                total_interactions_available += 1
                min_affection = int_data.get("min_affection", 0)
                if affection >= min_affection:
                    unlocked_count += 1
        
        embed.add_field(
            name="🔓 Available Interactions",
            value=f"**Unlocked:** {unlocked_count}/{total_interactions_available}\n"
                  f"**Next Unlock:** {self.get_next_interaction_unlock(affection)}",
            inline=False
        )
        
        # Relationship benefits
        benefits = self.get_relationship_benefits(affection)
        if benefits:
            embed.add_field(
                name="🎁 Relationship Benefits",
                value=benefits,
                inline=False
            )
        
        return embed
    
    def create_all_relationships_embed(self, characters: List[Dict]) -> discord.Embed:
        """Create overview of all character relationships"""
        embed = self.embed_builder.create_embed(
            title="💝 All Relationships",
            description="Your bonds with all characters",
            color=0xFF69B4
        )
        
        # Sort by affection
        sorted_chars = sorted(characters, key=lambda c: c.get("affection", 0), reverse=True)
        
        relationships_text = ""
        for char in sorted_chars[:10]:  # Show top 10
            affection = char.get("affection", 0)
            relationship = self.get_relationship_level(affection)
            relationships_text += f"💖 **{char['name']}** - {affection}/100 ({relationship})\n"
        
        if len(characters) > 10:
            relationships_text += f"\n*... and {len(characters) - 10} more characters*"
        
        embed.add_field(
            name="💞 Character Bonds",
            value=relationships_text,
            inline=False
        )
        
        # Calculate relationship statistics
        total_affection = sum(char.get("affection", 0) for char in characters)
        avg_affection = total_affection // len(characters) if characters else 0
        max_affection = max(char.get("affection", 0) for char in characters) if characters else 0
        
        embed.add_field(
            name="📊 Relationship Statistics",
            value=f"**Average Affection:** {avg_affection}/100\n"
                  f"**Highest Bond:** {max_affection}/100\n"
                  f"**Total Characters:** {len(characters)}\n"
                  f"**Master of Hearts Level:** {self.calculate_heart_master_level(total_affection)}",
            inline=True
        )
        
        return embed
    
    def get_relationship_level(self, affection: int) -> str:
        """Get relationship level name"""
        if affection >= 95:
            return "💕 Soulmates"
        elif affection >= 85:
            return "💖 True Love"
        elif affection >= 70:
            return "💝 Deep Bond"
        elif affection >= 55:
            return "💗 Close Friends"
        elif affection >= 40:
            return "💛 Good Friends"
        elif affection >= 25:
            return "💚 Friends"
        elif affection >= 10:
            return "💙 Acquaintances"
        else:
            return "🤝 Strangers"
    
    def get_bond_strength(self, affection: int) -> str:
        """Get bond strength description"""
        if affection >= 90:
            return "🌟 Unbreakable"
        elif affection >= 75:
            return "💎 Diamond Strong"
        elif affection >= 60:
            return "🔥 Passionate"
        elif affection >= 45:
            return "⭐ Solid"
        elif affection >= 30:
            return "🌱 Growing"
        else:
            return "🧊 Fragile"
    
    def get_next_milestone(self, affection: int) -> str:
        """Get next affection milestone"""
        milestones = [10, 25, 40, 55, 70, 85, 95, 100]
        for milestone in milestones:
            if affection < milestone:
                return f"{milestone} affection"
        return "Maximum reached!"
    
    def check_affection_milestones(self, new_affection: int, old_affection: int) -> Optional[str]:
        """Check if any affection milestones were reached"""
        milestones = {
            25: "Friendship unlocked! New interactions available!",
            50: "Close bond formed! Romantic interactions unlocked!",
            75: "Deep love achieved! Maximum affection gains unlocked!",
            95: "Soulmate status reached! Perfect harmony achieved!"
        }
        
        for milestone, message in milestones.items():
            if old_affection < milestone <= new_affection:
                return message
        
        return None
    
    def get_next_interaction_unlock(self, affection: int) -> str:
        """Get next interaction unlock requirement"""
        unlock_levels = [50, 80]
        for level in unlock_levels:
            if affection < level:
                return f"{level} affection"
        return "All unlocked!"
    
    def get_relationship_benefits(self, affection: int) -> str:
        """Get relationship benefits description"""
        benefits = []
        
        if affection >= 25:
            benefits.append("• +10% battle performance bonus")
        if affection >= 50:
            benefits.append("• +15% XP gain bonus")
        if affection >= 75:
            benefits.append("• +20% gold find bonus")
        if affection >= 90:
            benefits.append("• +25% all activities bonus")
        
        return "\n".join(benefits) if benefits else "Build affection to unlock benefits!"
    
    def calculate_heart_master_level(self, total_affection: int) -> int:
        """Calculate Master of Hearts level"""
        return min(50, 1 + (total_affection // 500))
    
    async def log_intimate_activity(self, ctx, activity_type: str, details: str = ""):
        """Log intimate activity to history channel"""
        try:
            history_channel = discord.utils.get(ctx.guild.text_channels, name='history')
            if not history_channel:
                return
            
            emojis = ["💖", "💝", "🤗", "💕", "✨", "🌸"]
            emoji = random.choice(emojis)
            
            if activity_type == "interaction":
                message = f"{emoji} **{ctx.author.display_name}** shared a tender moment with {details}!"
            elif activity_type == "relationship_check":
                if details:
                    message = f"{emoji} **{ctx.author.display_name}** reflected on their beautiful relationship with {details}!"
                else:
                    message = f"{emoji} **{ctx.author.display_name}** reviewed all their precious character relationships!"
            else:
                message = f"{emoji} **{ctx.author.display_name}** strengthened their bonds through intimate interactions!"
            
            embed = self.embed_builder.create_embed(
                description=message,
                color=0xFF69B4
            )
            
            await history_channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error logging intimate activity: {e}")

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(IntimateCommands(bot))