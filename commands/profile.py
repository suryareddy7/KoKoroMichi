# Profile Management Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional
import asyncio

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from utils.helpers import format_number, calculate_level_from_xp, create_progress_bar

class ProfileCommands(commands.Cog):
    """Profile management and user statistics"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
    
    @commands.command(name="profile")
    async def profile(self, ctx, member: Optional[discord.Member] = None):
        """Display user profile with stats and collection info"""
        try:
            target_user = member or ctx.author
            user_data = data_manager.get_user_data(str(target_user.id))
            
            # Update user name if not set
            if not user_data.get("name"):
                user_data["name"] = target_user.display_name
                data_manager.save_user_data(str(target_user.id), user_data)
            
            # Create profile embed
            embed = self.create_profile_embed(user_data, target_user)
            
            # Add interaction buttons if viewing own profile
            if target_user == ctx.author:
                view = ProfileView(str(ctx.author.id), user_data)
                await ctx.send(embed=embed, view=view)
            else:
                await ctx.send(embed=embed)
                
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Profile Error",
                "Unable to load profile. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Profile command error: {e}")
    
    def create_profile_embed(self, user_data: dict, user: discord.Member) -> discord.Embed:
        """Create a detailed profile embed"""
        embed = self.embed_builder.create_embed(
            title=f"📊 {user.display_name}'s Profile",
            color=0xFF69B4
        )
        
        # Set user avatar as thumbnail
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        
        # Basic resources
        gold = user_data.get("gold", 0)
        gems = user_data.get("gems", 0)
        embed.add_field(
            name="💰 Resources",
            value=f"💰 Gold: {format_number(gold)}\n💎 Gems: {format_number(gems)}",
            inline=True
        )
        
        # Level and experience
        level = user_data.get("level", 1)
        xp = user_data.get("xp", 0)
        next_level_xp = (level ** 2) * 100
        xp_progress = create_progress_bar(xp, next_level_xp)
        
        embed.add_field(
            name="⭐ Level & Experience",
            value=f"Level: **{level}**\nXP: {format_number(xp)}/{format_number(next_level_xp)}\n{xp_progress}",
            inline=True
        )
        
        # Collection statistics
        waifus = user_data.get("claimed_waifus", [])
        waifu_count = len(waifus)
        
        # Count by rarity
        rarity_counts = {}
        for waifu in waifus:
            rarity = waifu.get("rarity", "N").split()[0]  # Extract rarity tier
            rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
        
        collection_text = f"Total Waifus: **{waifu_count}**\n"
        if rarity_counts:
            # Show top 3 rarities
            sorted_rarities = sorted(rarity_counts.items(), 
                                   key=lambda x: ["N", "R", "SR", "SSR", "UR", "LR", "Mythic"].index(x[0]) if x[0] in ["N", "R", "SR", "SSR", "UR", "LR", "Mythic"] else 0,
                                   reverse=True)
            for rarity, count in sorted_rarities[:3]:
                collection_text += f"{rarity}: {count} | "
            collection_text = collection_text.rstrip(" | ")
        
        embed.add_field(
            name="💕 Waifu Collection",
            value=collection_text,
            inline=True
        )
        
        # Battle statistics
        battle_stats = user_data.get("battle_stats", {})
        wins = battle_stats.get("battles_won", 0)
        losses = battle_stats.get("battles_lost", 0)
        total_battles = wins + losses
        winrate = (wins / total_battles * 100) if total_battles > 0 else 0
        
        embed.add_field(
            name="⚔️ Battle Record",
            value=f"Wins: **{wins}** | Losses: **{losses}**\nWin Rate: **{winrate:.1f}%**",
            inline=True
        )
        
        # Guild information
        guild_id = user_data.get("guild_id")
        if guild_id:
            embed.add_field(
                name="🏰 Guild",
                value=f"Member of Guild #{guild_id}",
                inline=True
            )
        else:
            embed.add_field(
                name="🏰 Guild",
                value="Not in a guild",
                inline=True
            )
        
        # Recent activity or achievements
        achievements = user_data.get("achievements", [])
        if achievements:
            recent_achievement = achievements[-1] if achievements else None
            embed.add_field(
                name="🏆 Latest Achievement",
                value=recent_achievement or "None",
                inline=False
            )
        
        # Add creation date in footer
        created_at = user_data.get("created_at", "Unknown")
        try:
            from datetime import datetime
            created_date = datetime.fromisoformat(created_at).strftime("%B %d, %Y")
            embed.set_footer(text=f"Adventurer since {created_date}")
        except:
            pass
        
        return embed
    
    @commands.command(name="collection", aliases=["waifus", "characters"])
    async def collection(self, ctx, page: int = 1):
        """View your character collection with pagination"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            waifus = user_data.get("claimed_waifus", [])
            
            if not waifus:
                embed = self.embed_builder.info_embed(
                    "Empty Collection",
                    "You don't have any characters yet! Use `!summon` to get started."
                )
                await ctx.send(embed=embed)
                return
            
            # Sort waifus by potential/level
            waifus.sort(key=lambda w: w.get("potential", 0), reverse=True)
            
            # Create paginated view
            view = CollectionView(waifus, page - 1)
            embed = view.create_embed()
            
            await ctx.send(embed=embed, view=view)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Collection Error",
                "Unable to load your collection. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Collection command error: {e}")
    
    @commands.command(name="stats", aliases=["mystats"])
    async def stats(self, ctx):
        """View detailed personal statistics"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            
            embed = self.embed_builder.create_embed(
                title=f"📈 {ctx.author.display_name}'s Detailed Stats",
                color=0x00BFFF
            )
            
            # Combat statistics
            battle_stats = user_data.get("battle_stats", {})
            embed.add_field(
                name="⚔️ Combat Stats",
                value=f"Battles Won: {battle_stats.get('battles_won', 0)}\n"
                      f"Battles Lost: {battle_stats.get('battles_lost', 0)}\n"
                      f"Damage Dealt: {format_number(battle_stats.get('total_damage_dealt', 0))}\n"
                      f"Damage Taken: {format_number(battle_stats.get('total_damage_taken', 0))}",
                inline=True
            )
            
            # Economic statistics
            embed.add_field(
                name="💰 Economic Stats",
                value=f"Current Gold: {format_number(user_data.get('gold', 0))}\n"
                      f"Current Gems: {format_number(user_data.get('gems', 0))}\n"
                      f"Investments: {len(user_data.get('investments', {}))}\n"
                      f"Items Owned: {len(user_data.get('inventory', {}))}",
                inline=True
            )
            
            # Crafting statistics
            crafting_stats = user_data.get("crafting_stats", {})
            embed.add_field(
                name="🛠️ Crafting Stats",
                value=f"Items Crafted: {crafting_stats.get('items_crafted', 0)}\n"
                      f"Materials Gathered: {crafting_stats.get('materials_gathered', 0)}\n"
                      f"Successful Crafts: {crafting_stats.get('successful_crafts', 0)}",
                inline=True
            )
            
            # Waifu collection statistics
            waifus = user_data.get("claimed_waifus", [])
            unique_elements = set(w.get("element", "Neutral") for w in waifus)
            highest_level = max((w.get("level", 1) for w in waifus), default=1)
            
            embed.add_field(
                name="👥 Collection Stats",
                value=f"Total Characters: {len(waifus)}\n"
                      f"Unique Elements: {len(unique_elements)}\n"
                      f"Highest Level: {highest_level}\n"
                      f"Achievements: {len(user_data.get('achievements', []))}",
                inline=True
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Stats Error",
                "Unable to load your statistics. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Stats command error: {e}")


class ProfileView(discord.ui.View):
    """Interactive profile view with buttons"""
    
    def __init__(self, user_id: str, user_data: dict):
        super().__init__(timeout=60.0)
        self.user_id = user_id
        self.user_data = user_data
    
    @discord.ui.button(label="📊 Detailed Stats", style=discord.ButtonStyle.primary)
    async def detailed_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show detailed statistics"""
        try:
            # Create detailed stats embed
            embed = EmbedBuilder.create_embed(
                title="📈 Detailed Statistics",
                color=0x00BFFF
            )
            
            battle_stats = self.user_data.get("battle_stats", {})
            crafting_stats = self.user_data.get("crafting_stats", {})
            
            embed.add_field(
                name="⚔️ Battle Details",
                value=f"Total Damage: {format_number(battle_stats.get('total_damage_dealt', 0))}\n"
                      f"Damage Received: {format_number(battle_stats.get('total_damage_taken', 0))}",
                inline=True
            )
            
            embed.add_field(
                name="🛠️ Crafting Details",
                value=f"Success Rate: {crafting_stats.get('successful_crafts', 0)}/{crafting_stats.get('items_crafted', 1)}\n"
                      f"Materials Found: {crafting_stats.get('materials_gathered', 0)}",
                inline=True
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message("❌ Error loading detailed stats.", ephemeral=True)
    
    @discord.ui.button(label="🎯 Quick Actions", style=discord.ButtonStyle.secondary)
    async def quick_actions(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show quick action menu"""
        embed = EmbedBuilder.info_embed(
            "Quick Actions",
            "• `!summon` - Summon new characters\n"
            "• `!battle` - Start a battle\n"
            "• `!invest` - Manage investments\n"
            "• `!daily` - Claim daily rewards\n"
            "• `!guild` - Guild management"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class CollectionView(discord.ui.View):
    """Paginated collection view"""
    
    def __init__(self, waifus: list, page: int = 0):
        super().__init__(timeout=300.0)
        self.waifus = waifus
        self.page = page
        self.per_page = 5
        self.max_page = max(0, (len(waifus) - 1) // self.per_page)
        
        # Update button states
        self.update_buttons()
    
    def update_buttons(self):
        """Update button enabled/disabled state"""
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.custom_id == "prev":
                    item.disabled = (self.page <= 0)
                elif item.custom_id == "next":
                    item.disabled = (self.page >= self.max_page)
    
    def create_embed(self) -> discord.Embed:
        """Create embed for current page"""
        embed = EmbedBuilder.create_embed(
            title="👥 Character Collection",
            description=f"Your collected characters (Page {self.page + 1}/{self.max_page + 1})",
            color=0xFF69B4
        )
        
        start_idx = self.page * self.per_page
        end_idx = start_idx + self.per_page
        page_waifus = self.waifus[start_idx:end_idx]
        
        for i, waifu in enumerate(page_waifus, start_idx + 1):
            name = waifu.get("name", "Unknown")
            rarity = waifu.get("rarity", "N")
            level = waifu.get("level", 1)
            potential = waifu.get("potential", 0)
            
            value = f"Level {level} • Potential: {format_number(potential)}\n"
            value += f"❤️ {waifu.get('hp', 0)} | ⚔️ {waifu.get('atk', 0)} | 🛡️ {waifu.get('def', 0)}"
            
            embed.add_field(
                name=f"{i}. {rarity} {name}",
                value=value,
                inline=False
            )
        
        if not page_waifus:
            embed.description = "No characters found."
        
        return embed
    
    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.primary, custom_id="prev")
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous page"""
        if self.page > 0:
            self.page -= 1
            self.update_buttons()
            embed = self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.primary, custom_id="next")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next page"""
        if self.page < self.max_page:
            self.page += 1
            self.update_buttons()
            embed = self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="🔍 Filter", style=discord.ButtonStyle.secondary, custom_id="filter")
    async def filter_collection(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Filter collection by rarity"""
        # Create modal for filtering
        modal = FilterModal(self)
        await interaction.response.send_modal(modal)


class FilterModal(discord.ui.Modal, title="Filter Collection"):
    """Modal for filtering collection"""
    
    def __init__(self, collection_view):
        super().__init__()
        self.collection_view = collection_view
    
    rarity = discord.ui.TextInput(
        label="Rarity Filter",
        placeholder="Enter rarity (N, R, SR, SSR, UR, LR, Mythic) or leave empty for all",
        required=False,
        max_length=10
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Apply filter"""
        try:
            filter_rarity = self.rarity.value.strip().upper()
            
            if filter_rarity:
                # Filter waifus by rarity
                filtered_waifus = [
                    w for w in self.collection_view.waifus 
                    if w.get("rarity", "N").split()[0].upper() == filter_rarity
                ]
                
                if not filtered_waifus:
                    await interaction.response.send_message(
                        f"❌ No characters found with rarity: {filter_rarity}", 
                        ephemeral=True
                    )
                    return
                
                self.collection_view.waifus = filtered_waifus
            else:
                # Reset to show all waifus - would need original list
                pass
            
            # Reset to first page and update
            self.collection_view.page = 0
            self.collection_view.max_page = max(0, (len(self.collection_view.waifus) - 1) // self.collection_view.per_page)
            self.collection_view.update_buttons()
            
            embed = self.collection_view.create_embed()
            await interaction.response.edit_message(embed=embed, view=self.collection_view)
            
        except Exception as e:
            await interaction.response.send_message("❌ Error applying filter.", ephemeral=True)


async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(ProfileCommands(bot))