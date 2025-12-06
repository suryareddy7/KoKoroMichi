# Gallery System Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List
import os
import random
from datetime import datetime

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from core.config import CHARACTERS_DIR
from utils.helpers import format_number

LEVEL_REQUIREMENTS = {1: 1, 2: 30, 3: 60, 4: 90, 5: 120}

class GalleryImageView(discord.ui.View):
    """Interactive image viewer for character gallery"""
    
    def __init__(self, character_data: Dict, user_id: int, character_name: str):
        super().__init__(timeout=300)
        self.character_data = character_data
        self.user_id = user_id
        self.character_name = character_name
        self.current_image = 0
        self.max_images = self.get_available_images()
        self.update_buttons()
    
    def get_available_images(self) -> int:
        """Count available images for this character"""
        # Check how many image files exist for this character
        char_level = self.character_data.get("level", 1)
        available = 1  # Always have at least image 1
        
        for serial in range(2, 6):  # Check images 2-5
            required_level = LEVEL_REQUIREMENTS.get(serial, 999)
            if char_level >= required_level:
                # Check if image file exists
                image_path = CHARACTERS_DIR / f"{self.character_name.lower()} - {serial}.webp"
                if image_path.exists():
                    available = serial
        
        return available
    
    def update_buttons(self):
        """Update navigation buttons"""
        self.clear_items()
        
        if self.current_image > 0:
            prev_btn = discord.ui.Button(label="⬅️ Previous", style=discord.ButtonStyle.secondary)
            prev_btn.callback = self.previous_image
            self.add_item(prev_btn)
        
        if self.current_image < self.max_images - 1:
            next_btn = discord.ui.Button(label="➡️ Next", style=discord.ButtonStyle.secondary)
            next_btn.callback = self.next_image
            self.add_item(next_btn)
        
        # Info button
        info_btn = discord.ui.Button(label="ℹ️ Details", style=discord.ButtonStyle.primary)
        info_btn.callback = self.show_details
        self.add_item(info_btn)
    
    async def previous_image(self, interaction: discord.Interaction):
        """Navigate to previous image"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your gallery session.", ephemeral=True)
            return
        
        self.current_image = max(0, self.current_image - 1)
        await self.update_gallery_display(interaction)
    
    async def next_image(self, interaction: discord.Interaction):
        """Navigate to next image"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your gallery session.", ephemeral=True)
            return
        
        self.current_image = min(self.max_images - 1, self.current_image + 1)
        await self.update_gallery_display(interaction)
    
    async def show_details(self, interaction: discord.Interaction):
        """Show detailed character information"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your gallery session.", ephemeral=True)
            return
        
        embed = self.create_character_details_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def update_gallery_display(self, interaction: discord.Interaction):
        """Update the gallery display"""
        self.update_buttons()
        embed = self.create_gallery_embed()
        
        # Try to load and attach image
        image_file = None
        serial_number = self.current_image + 1
        char_level = self.character_data.get("level", 1)
        required_level = LEVEL_REQUIREMENTS.get(serial_number, 1)
        
        if char_level >= required_level:
            image_path = CHARACTERS_DIR / f"{self.character_name.lower()} - {serial_number}.webp"
            if image_path.exists():
                image_file = discord.File(str(image_path), filename=f"gallery_{serial_number}.webp")
                embed.set_image(url=f"attachment://gallery_{serial_number}.webp")
        
        if image_file:
            await interaction.response.edit_message(embed=embed, attachments=[image_file], view=self)
        else:
            await interaction.response.edit_message(embed=embed, attachments=[], view=self)
    
    def create_gallery_embed(self) -> discord.Embed:
        """Create gallery display embed"""
        char_name = self.character_data.get("name", "Unknown")
        char_level = self.character_data.get("level", 1)
        rarity = self.character_data.get("rarity", "N")
        
        serial_number = self.current_image + 1
        required_level = LEVEL_REQUIREMENTS.get(serial_number, 1)
        is_unlocked = char_level >= required_level
        
        embed = EmbedBuilder.create_embed(
            title=f"🖼️ {char_name} Gallery",
            description=f"**{rarity}** • Level {char_level}",
            color=0xFF69B4
        )
        
        # Image status
        if is_unlocked:
            embed.add_field(
                name="📸 Current Image",
                value=f"**Outfit {serial_number}** of {self.max_images}\n✅ Unlocked",
                inline=True
            )
        else:
            embed.add_field(
                name="🔒 Locked Image",
                value=f"**Outfit {serial_number}** of {self.max_images}\n🔒 Unlock at Level {required_level}",
                inline=True
            )
        
        # Progress info
        embed.add_field(
            name="📊 Progress",
            value=f"Current Level: {char_level}\n"
                  f"Next Unlock: Level {LEVEL_REQUIREMENTS.get(self.max_images + 1, 'MAX')}",
            inline=True
        )
        
        return embed
    
    def create_character_details_embed(self) -> discord.Embed:
        """Create detailed character information embed"""
        char_name = self.character_data.get("name", "Unknown")
        
        embed = EmbedBuilder.create_embed(
            title=f"📋 {char_name} Details",
            color=0x9370DB
        )
        
        # Basic stats
        hp = self.character_data.get("hp", 0)
        atk = self.character_data.get("atk", 0)
        defense = self.character_data.get("def", 0)
        potential = self.character_data.get("potential", 0)
        
        embed.add_field(
            name="⚔️ Combat Stats",
            value=f"❤️ HP: {format_number(hp)}\n"
                  f"⚔️ ATK: {format_number(atk)}\n"
                  f"🛡️ DEF: {format_number(defense)}\n"
                  f"🔮 Potential: {format_number(potential)}",
            inline=True
        )
        
        # Additional info
        element = self.character_data.get("element", "Neutral")
        affection = self.character_data.get("affection", 0)
        summoned_date = self.character_data.get("summoned_at", "Unknown")
        
        embed.add_field(
            name="✨ Character Info",
            value=f"🌟 Element: {element}\n"
                  f"💖 Affection: {affection}\n"
                  f"📅 Summoned: {summoned_date[:10] if summoned_date != 'Unknown' else 'Unknown'}",
            inline=True
        )
        
        # Skills and fate
        skills = self.character_data.get("skills", [])
        if skills:
            skills_text = "\n".join([f"• {skill}" for skill in skills[:3]])
            embed.add_field(name="🎯 Skills", value=skills_text, inline=False)
        
        return embed

class GallerySelectView(discord.ui.View):
    """Character selection view for gallery"""
    
    def __init__(self, characters: List[Dict], user_id: int, page: int = 0):
        super().__init__(timeout=180)
        self.characters = characters
        self.user_id = user_id
        self.page = page
        self.chars_per_page = 10
        self.create_selection_menu()
    
    def create_selection_menu(self):
        """Create character selection dropdown"""
        start_idx = self.page * self.chars_per_page
        end_idx = start_idx + self.chars_per_page
        page_characters = self.characters[start_idx:end_idx]
        
        if not page_characters:
            return
        
        # Create dropdown options
        options = []
        for i, char in enumerate(page_characters):
            name = char.get("name", f"Character {i+1}")
            level = char.get("level", 1)
            rarity = char.get("rarity", "N").split()[0]  # Extract rarity tier
            
            options.append(discord.SelectOption(
                label=f"{name} (Lv.{level})",
                description=f"{rarity} • Level {level}",
                value=str(start_idx + i),
                emoji="🖼️"
            ))
        
        select = discord.ui.Select(
            placeholder="Choose a character to view...",
            options=options,
            min_values=1,
            max_values=1
        )
        select.callback = self.character_selected
        self.add_item(select)
        
        # Add page navigation if needed
        total_pages = (len(self.characters) - 1) // self.chars_per_page + 1
        if total_pages > 1:
            if self.page > 0:
                prev_btn = discord.ui.Button(label="⬅️ Previous Page", style=discord.ButtonStyle.secondary)
                prev_btn.callback = self.previous_page
                self.add_item(prev_btn)
            
            if self.page < total_pages - 1:
                next_btn = discord.ui.Button(label="➡️ Next Page", style=discord.ButtonStyle.secondary)
                next_btn.callback = self.next_page
                self.add_item(next_btn)
    
    async def character_selected(self, interaction: discord.Interaction):
        """Handle character selection"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your gallery session.", ephemeral=True)
            return
        
        char_index = int(interaction.data["values"][0])
        selected_character = self.characters[char_index]
        character_name = selected_character.get("name", "Unknown")
        
        # Create image view for selected character
        image_view = GalleryImageView(selected_character, self.user_id, character_name)
        embed = image_view.create_gallery_embed()
        
        await interaction.response.edit_message(embed=embed, view=image_view, attachments=[])
    
    async def previous_page(self, interaction: discord.Interaction):
        """Navigate to previous page"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your gallery session.", ephemeral=True)
            return
        
        self.page = max(0, self.page - 1)
        new_view = GallerySelectView(self.characters, self.user_id, self.page)
        embed = self.create_page_embed()
        await interaction.response.edit_message(embed=embed, view=new_view)
    
    async def next_page(self, interaction: discord.Interaction):
        """Navigate to next page"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your gallery session.", ephemeral=True)
            return
        
        total_pages = (len(self.characters) - 1) // self.chars_per_page + 1
        self.page = min(total_pages - 1, self.page + 1)
        new_view = GallerySelectView(self.characters, self.user_id, self.page)
        embed = self.create_page_embed()
        await interaction.response.edit_message(embed=embed, view=new_view)
    
    def create_page_embed(self) -> discord.Embed:
        """Create character selection page embed"""
        total_pages = (len(self.characters) - 1) // self.chars_per_page + 1
        
        embed = EmbedBuilder.create_embed(
            title="🖼️ Character Gallery",
            description=f"Select a character to view their image gallery\n**Page {self.page + 1} of {total_pages}**",
            color=0xFF69B4
        )
        
        # Show character count by rarity
        rarity_counts = {}
        for char in self.characters:
            rarity_tier = char.get("rarity", "N").split()[0]
            rarity_counts[rarity_tier] = rarity_counts.get(rarity_tier, 0) + 1
        
        rarity_text = ""
        for rarity in ["Mythic", "LR", "UR", "SSR", "SR", "R", "N"]:
            count = rarity_counts.get(rarity, 0)
            if count > 0:
                emoji = {"Mythic": "🌈✨", "LR": "⚡", "UR": "🌟", "SSR": "🌈✨", "SR": "🔥", "R": "🔧", "N": "🌿"}.get(rarity, "❓")
                rarity_text += f"{emoji} {rarity}: {count}  "
        
        if rarity_text:
            embed.add_field(
                name="📊 Collection Summary",
                value=rarity_text,
                inline=False
            )
        
        return embed

class GalleryCommands(commands.Cog):
    """Character gallery and image viewing system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
    
    @commands.command(name="gallery", aliases=["images", "pics"])
    async def view_gallery(self, ctx, *, character_name: str = None):
        """View character gallery with unlockable images"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            user_characters = user_data.get("claimed_waifus", [])
            
            if not user_characters:
                embed = self.embed_builder.error_embed(
                    "Empty Collection",
                    "You don't have any characters yet! Use `!summon` to get started."
                )
                await ctx.send(embed=embed)
                return
            
            if character_name:
                # Show specific character gallery
                character = self.find_character_by_name(user_characters, character_name)
                if not character:
                    embed = self.embed_builder.error_embed(
                        "Character Not Found",
                        f"'{character_name}' not found in your collection."
                    )
                    await ctx.send(embed=embed)
                    return
                
                # Create image viewer for specific character
                image_view = GalleryImageView(character, ctx.author.id, character.get("name", "Unknown"))
                embed = image_view.create_gallery_embed()
                
                # Try to load initial image
                image_file = None
                if character.get("level", 1) >= 1:  # First image always unlocked
                    image_path = CHARACTERS_DIR / f"{character.get('name', '').lower()} - 1.webp"
                    if image_path.exists():
                        image_file = discord.File(str(image_path), filename="gallery_1.webp")
                        embed.set_image(url="attachment://gallery_1.webp")
                
                if image_file:
                    await ctx.send(embed=embed, file=image_file, view=image_view)
                else:
                    await ctx.send(embed=embed, view=image_view)
            
            else:
                # Show character selection
                select_view = GallerySelectView(user_characters, ctx.author.id)
                embed = select_view.create_page_embed()
                await ctx.send(embed=embed, view=select_view)
            
            # Log activity
            await self.log_gallery_activity(ctx, character_name)
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Gallery Error",
                "Unable to load gallery. Please try again later."
            )
            await ctx.send(embed=embed)
            print(f"Gallery command error: {e}")
    
    @commands.command(name="unlock", aliases=["unlocks"])
    async def view_unlock_progress(self, ctx, *, character_name: str = None):
        """View image unlock progress for characters"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            user_characters = user_data.get("claimed_waifus", [])
            
            if not user_characters:
                embed = self.embed_builder.error_embed(
                    "Empty Collection",
                    "You don't have any characters yet!"
                )
                await ctx.send(embed=embed)
                return
            
            if character_name:
                character = self.find_character_by_name(user_characters, character_name)
                if not character:
                    embed = self.embed_builder.error_embed(
                        "Character Not Found",
                        f"'{character_name}' not found in your collection."
                    )
                    await ctx.send(embed=embed)
                    return
                
                embed = self.create_unlock_progress_embed(character)
                await ctx.send(embed=embed)
            
            else:
                # Show unlock progress for all characters
                embed = self.create_collection_unlock_embed(user_characters)
                await ctx.send(embed=embed)
            
            # Log activity
            await self.log_gallery_activity(ctx, character_name, "unlock_check")
            
        except Exception as e:
            embed = self.embed_builder.error_embed(
                "Unlock Progress Error",
                "Unable to load unlock progress."
            )
            await ctx.send(embed=embed)
            print(f"Unlock progress error: {e}")
    
    def find_character_by_name(self, characters: List[Dict], name: str) -> Optional[Dict]:
        """Find character by name (case insensitive)"""
        name_lower = name.lower()
        for char in characters:
            if char.get("name", "").lower() == name_lower:
                return char
        return None
    
    def create_unlock_progress_embed(self, character: Dict) -> discord.Embed:
        """Create unlock progress embed for a character"""
        char_name = character.get("name", "Unknown")
        char_level = character.get("level", 1)
        rarity = character.get("rarity", "N")
        
        embed = self.embed_builder.create_embed(
            title=f"🔓 {char_name} Unlock Progress",
            description=f"**{rarity}** • Level {char_level}",
            color=0x9370DB
        )
        
        # Show unlock status for each image
        progress_text = ""
        for serial, required_level in LEVEL_REQUIREMENTS.items():
            if char_level >= required_level:
                status = "✅ Unlocked"
                color_code = ""
            else:
                status = f"🔒 Level {required_level} required"
                color_code = "```diff\n- "
            
            progress_text += f"{color_code}Image {serial}: {status}\n"
            if color_code:
                progress_text += "```"
        
        embed.add_field(
            name="📸 Image Gallery Status",
            value=progress_text,
            inline=False
        )
        
        # Next unlock info
        next_unlock = None
        for serial, required_level in LEVEL_REQUIREMENTS.items():
            if char_level < required_level:
                next_unlock = (serial, required_level)
                break
        
        if next_unlock:
            levels_needed = next_unlock[1] - char_level
            embed.add_field(
                name="🎯 Next Unlock",
                value=f"**Image {next_unlock[0]}** at Level {next_unlock[1]}\n"
                      f"({levels_needed} levels to go!)",
                inline=True
            )
        else:
            embed.add_field(
                name="🌟 All Unlocked!",
                value="You've unlocked all available images for this character!",
                inline=True
            )
        
        return embed
    
    def create_collection_unlock_embed(self, characters: List[Dict]) -> discord.Embed:
        """Create collection-wide unlock progress embed"""
        embed = self.embed_builder.create_embed(
            title="🔓 Collection Unlock Progress",
            description="Image unlock status for your character collection",
            color=0x9370DB
        )
        
        # Calculate overall progress
        total_possible = len(characters) * len(LEVEL_REQUIREMENTS)
        total_unlocked = 0
        
        progress_text = ""
        for char in characters[:10]:  # Show first 10 characters
            char_name = char.get("name", "Unknown")
            char_level = char.get("level", 1)
            
            unlocked_count = sum(1 for req_level in LEVEL_REQUIREMENTS.values() if char_level >= req_level)
            total_unlocked += unlocked_count
            
            progress_bar = "█" * unlocked_count + "░" * (len(LEVEL_REQUIREMENTS) - unlocked_count)
            progress_text += f"**{char_name}**: {progress_bar} ({unlocked_count}/{len(LEVEL_REQUIREMENTS)})\n"
        
        if len(characters) > 10:
            progress_text += f"\n*... and {len(characters) - 10} more characters*"
        
        embed.add_field(
            name="📊 Progress Overview",
            value=progress_text,
            inline=False
        )
        
        # Overall statistics
        overall_percentage = (total_unlocked / total_possible * 100) if total_possible > 0 else 0
        embed.add_field(
            name="🌟 Collection Stats",
            value=f"**Total Unlocked:** {total_unlocked}/{total_possible}\n"
                  f"**Progress:** {overall_percentage:.1f}%\n"
                  f"**Characters:** {len(characters)}",
            inline=True
        )
        
        return embed
    
    async def log_gallery_activity(self, ctx, character_name: Optional[str] = None, activity_type: str = "view"):
        """Log gallery activity to history channel"""
        try:
            history_channel = discord.utils.get(ctx.guild.text_channels, name='history')
            if not history_channel:
                return
            
            emojis = ["🖼️", "🎨", "✨", "🌟", "💫", "🎭"]
            emoji = random.choice(emojis)
            
            if activity_type == "unlock_check":
                if character_name:
                    message = f"{emoji} **{ctx.author.display_name}** checked unlock progress for their beloved {character_name}!"
                else:
                    message = f"{emoji} **{ctx.author.display_name}** reviewed their entire collection's unlock progress!"
            else:
                if character_name:
                    message = f"{emoji} **{ctx.author.display_name}** admired beautiful images of {character_name} in their private gallery!"
                else:
                    message = f"{emoji} **{ctx.author.display_name}** browsed their magnificent character gallery collection!"
            
            embed = self.embed_builder.create_embed(
                description=message,
                color=0xFF69B4
            )
            
            await history_channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error logging gallery activity: {e}")

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(GalleryCommands(bot))