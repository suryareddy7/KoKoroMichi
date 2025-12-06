# Character Inspection Commands for KoKoroMichi Advanced Bot
import discord
from discord.ext import commands
from typing import Optional, Dict, List
import random

from core.data_manager import data_manager
from core.embed_utils import EmbedBuilder
from utils.helpers import format_number, find_character_by_name, calculate_battle_power

class InspectCommands(commands.Cog):
    """Character inspection and detailed viewing commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
    
    @commands.command(name="inspect", aliases=["char", "character"])
    async def inspect_character(self, ctx, *, character_name: str):
        """Inspect a character in your collection with detailed information"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            waifus = user_data.get("claimed_waifus", [])
            
            if not waifus:
                embed = self.embed_builder.info_embed(
                    "No Characters",
                    "You don't have any characters yet! Use `!summon` to get started."
                )
                await ctx.send(embed=embed)
                return
            
            # Find character in user's collection
            character = find_character_by_name(waifus, character_name)
            
            if not character:
                # Show similar names
                similar = self.find_similar_names(waifus, character_name)
                description = f"Character '{character_name}' not found in your collection."
                if similar:
                    description += f"\n\n**Did you mean?**\n{' • '.join(similar[:5])}"
                
                embed = self.embed_builder.error_embed("Character Not Found", description)
                await ctx.send(embed=embed)
                return
            
            # Create detailed character view
            view = CharacterInspectView(character, str(ctx.author.id))
            embed = view.create_main_embed()
            
            await ctx.send(embed=embed, view=view)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Inspect Error",
                "Unable to inspect character. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Inspect command error: {e}")
    
    @commands.command(name="compare")
    async def compare_characters(self, ctx, char1_name: str, char2_name: str):
        """Compare two characters from your collection"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            waifus = user_data.get("claimed_waifus", [])
            
            if len(waifus) < 2:
                embed = self.embed_builder.info_embed(
                    "Not Enough Characters",
                    "You need at least 2 characters to compare!"
                )
                await ctx.send(embed=embed)
                return
            
            # Find both characters
            char1 = find_character_by_name(waifus, char1_name)
            char2 = find_character_by_name(waifus, char2_name)
            
            if not char1:
                embed = self.embed_builder.error_embed(
                    "Character Not Found",
                    f"'{char1_name}' not found in your collection."
                )
                await ctx.send(embed=embed)
                return
            
            if not char2:
                embed = self.embed_builder.error_embed(
                    "Character Not Found", 
                    f"'{char2_name}' not found in your collection."
                )
                await ctx.send(embed=embed)
                return
            
            if char1 == char2:
                embed = self.embed_builder.error_embed(
                    "Same Character",
                    "Please choose two different characters to compare."
                )
                await ctx.send(embed=embed)
                return
            
            # Create comparison embed
            embed = self.create_comparison_embed(char1, char2)
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Compare Error",
                "Unable to compare characters. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Compare command error: {e}")
    
    @commands.command(name="top", aliases=["strongest", "best"])
    async def top_characters(self, ctx, sort_by: str = "potential"):
        """Show your top characters sorted by various criteria"""
        try:
            user_data = data_manager.get_user_data(str(ctx.author.id))
            waifus = user_data.get("claimed_waifus", [])
            
            if not waifus:
                embed = self.embed_builder.info_embed(
                    "No Characters",
                    "You don't have any characters yet! Use `!summon` to get started."
                )
                await ctx.send(embed=embed)
                return
            
            # Sort characters by criteria
            sorted_waifus = self.sort_characters(waifus, sort_by.lower())
            
            if not sorted_waifus:
                embed = self.embed_builder.error_embed(
                    "Invalid Sort Criteria",
                    "Valid options: potential, level, hp, atk, def, power"
                )
                await ctx.send(embed=embed)
                return
            
            # Create top characters embed
            embed = self.create_top_characters_embed(sorted_waifus, sort_by)
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = self.embed_builder.error_embed(
                "Top Characters Error",
                "Unable to load top characters. Please try again later."
            )
            await ctx.send(embed=error_embed)
            print(f"Top characters command error: {e}")
    
    def find_similar_names(self, waifus: List[Dict], search_name: str) -> List[str]:
        """Find similar character names for suggestions"""
        from difflib import SequenceMatcher
        
        suggestions = []
        search_name = search_name.lower()
        
        for waifu in waifus:
            char_name = waifu.get("name", "").lower()
            similarity = SequenceMatcher(None, search_name, char_name).ratio()
            
            if similarity > 0.3:  # 30% similarity threshold
                suggestions.append((waifu.get("name", "Unknown"), similarity))
        
        # Sort by similarity and return names
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in suggestions[:5]]
    
    def sort_characters(self, waifus: List[Dict], sort_by: str) -> Optional[List[Dict]]:
        """Sort characters by specified criteria"""
        sort_functions = {
            "potential": lambda w: w.get("potential", 0),
            "level": lambda w: w.get("level", 1),
            "hp": lambda w: w.get("hp", 0),
            "atk": lambda w: w.get("atk", 0),
            "def": lambda w: w.get("def", 0),
            "power": lambda w: calculate_battle_power(
                w.get("hp", 0), w.get("atk", 0), w.get("def", 0), w.get("level", 1)
            )
        }
        
        if sort_by not in sort_functions:
            return None
        
        return sorted(waifus, key=sort_functions[sort_by], reverse=True)
    
    def create_comparison_embed(self, char1: Dict, char2: Dict) -> discord.Embed:
        """Create a character comparison embed"""
        name1 = char1.get("name", "Unknown")
        name2 = char2.get("name", "Unknown")
        
        embed = self.embed_builder.create_embed(
            title=f"⚔️ Character Comparison",
            description=f"**{name1}** vs **{name2}**",
            color=0xFF4500
        )
        
        # Basic stats comparison
        stats1 = {
            "Level": char1.get("level", 1),
            "HP": char1.get("hp", 0),
            "ATK": char1.get("atk", 0), 
            "DEF": char1.get("def", 0),
            "Potential": char1.get("potential", 0)
        }
        
        stats2 = {
            "Level": char2.get("level", 1),
            "HP": char2.get("hp", 0),
            "ATK": char2.get("atk", 0),
            "DEF": char2.get("def", 0),
            "Potential": char2.get("potential", 0)
        }
        
        # Character 1 stats
        char1_text = ""
        for stat, value in stats1.items():
            char1_text += f"{stat}: **{format_number(value)}**\n"
        
        embed.add_field(
            name=f"📊 {name1}",
            value=char1_text,
            inline=True
        )
        
        # Comparison indicators
        comparison_text = ""
        for stat in stats1.keys():
            val1, val2 = stats1[stat], stats2[stat]
            if val1 > val2:
                comparison_text += "🟩\n"  # Green for char1 wins
            elif val1 < val2:
                comparison_text += "🟥\n"  # Red for char2 wins
            else:
                comparison_text += "🟨\n"  # Yellow for tie
        
        embed.add_field(
            name="📈 Winner",
            value=comparison_text,
            inline=True
        )
        
        # Character 2 stats
        char2_text = ""
        for stat, value in stats2.items():
            char2_text += f"{stat}: **{format_number(value)}**\n"
        
        embed.add_field(
            name=f"📊 {name2}",
            value=char2_text,
            inline=True
        )
        
        # Battle power comparison
        power1 = calculate_battle_power(
            char1.get("hp", 0), char1.get("atk", 0), char1.get("def", 0), char1.get("level", 1)
        )
        power2 = calculate_battle_power(
            char2.get("hp", 0), char2.get("atk", 0), char2.get("def", 0), char2.get("level", 1)
        )
        
        if power1 > power2:
            winner = f"**{name1}** is stronger!"
            power_diff = power1 - power2
        elif power2 > power1:
            winner = f"**{name2}** is stronger!"
            power_diff = power2 - power1
        else:
            winner = "Both characters are equally powerful!"
            power_diff = 0
        
        embed.add_field(
            name="⚔️ Overall Battle Power",
            value=f"{name1}: {format_number(power1)}\n"
                  f"{name2}: {format_number(power2)}\n\n"
                  f"{winner}"
                  f"{f' (by {format_number(power_diff)} points)' if power_diff > 0 else ''}",
            inline=False
        )
        
        return embed
    
    def create_top_characters_embed(self, sorted_waifus: List[Dict], sort_by: str) -> discord.Embed:
        """Create top characters embed"""
        embed = self.embed_builder.create_embed(
            title=f"🏆 Top Characters by {sort_by.title()}",
            color=0xFFD700
        )
        
        # Show top 10
        top_waifus = sorted_waifus[:10]
        
        rankings_text = ""
        for i, waifu in enumerate(top_waifus, 1):
            name = waifu.get("name", "Unknown")
            rarity = waifu.get("rarity", "N").split()[0]
            
            if sort_by == "power":
                value = calculate_battle_power(
                    waifu.get("hp", 0), waifu.get("atk", 0), 
                    waifu.get("def", 0), waifu.get("level", 1)
                )
            else:
                value = waifu.get(sort_by, 0)
            
            # Add rank emoji
            rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
            
            rankings_text += f"{rank_emoji} **{name}** ({rarity})\n"
            rankings_text += f"    {sort_by.title()}: {format_number(value)}\n\n"
        
        embed.add_field(
            name=f"🎯 Rankings (Top {len(top_waifus)})",
            value=rankings_text or "No characters found",
            inline=False
        )
        
        # Add summary stats
        total_chars = len(sorted_waifus)
        if total_chars > 0:
            avg_value = sum(waifu.get(sort_by, 0) for waifu in sorted_waifus) / total_chars
            embed.add_field(
                name="📈 Collection Stats",
                value=f"Total Characters: {total_chars}\n"
                      f"Average {sort_by.title()}: {format_number(int(avg_value))}",
                inline=True
            )
        
        return embed


class CharacterInspectView(discord.ui.View):
    """Interactive character inspection view"""
    
    def __init__(self, character: Dict, user_id: str):
        super().__init__(timeout=300.0)
        self.character = character
        self.user_id = user_id
        self.current_view = "main"
    
    def create_main_embed(self) -> discord.Embed:
        """Create main character information embed"""
        name = self.character.get("name", "Unknown")
        rarity = self.character.get("rarity", "N")
        level = self.character.get("level", 1)
        
        embed = EmbedBuilder.create_embed(
            title=f"✨ {name}",
            description=f"**{rarity}** • Level {level}",
            color=0xFF69B4
        )
        
        # Basic stats
        hp = self.character.get("hp", 0)
        atk = self.character.get("atk", 0)
        defense = self.character.get("def", 0)
        potential = self.character.get("potential", 0)
        
        embed.add_field(
            name="📊 Combat Stats",
            value=f"❤️ HP: **{format_number(hp)}**\n"
                  f"⚔️ ATK: **{format_number(atk)}**\n"
                  f"🛡️ DEF: **{format_number(defense)}**",
            inline=True
        )
        
        # Additional info
        element = self.character.get("element", "Neutral")
        xp = self.character.get("exp", 0)
        max_xp = self.character.get("max_exp", 100)
        
        embed.add_field(
            name="✨ Character Info",
            value=f"🔮 Potential: **{format_number(potential)}**\n"
                  f"🌟 Element: **{element}**\n"
                  f"📈 XP: {format_number(xp)}/{format_number(max_xp)}",
            inline=True
        )
        
        # Battle power
        battle_power = calculate_battle_power(hp, atk, defense, level)
        embed.add_field(
            name="⚔️ Battle Power",
            value=f"**{format_number(battle_power)}**",
            inline=True
        )
        
        # Equipment/Relic
        relic = self.character.get("relic")
        if relic:
            embed.add_field(
                name="💎 Equipped Relic",
                value=f"**{relic}**",
                inline=False
            )
        
        return embed
    
    def create_skills_embed(self) -> discord.Embed:
        """Create skills information embed"""
        name = self.character.get("name", "Unknown")
        
        embed = EmbedBuilder.create_embed(
            title=f"🎯 {name}'s Skills",
            color=0x4169E1
        )
        
        skills = self.character.get("skills", [])
        if skills:
            skills_text = ""
            for i, skill in enumerate(skills, 1):
                if isinstance(skill, dict):
                    skill_name = skill.get("name", f"Skill {i}")
                    skill_desc = skill.get("description", "No description")
                    skills_text += f"**{skill_name}**\n{skill_desc}\n\n"
                else:
                    skills_text += f"**Skill {i}**\n{skill}\n\n"
            
            embed.add_field(
                name="⚔️ Active Skills",
                value=skills_text,
                inline=False
            )
        else:
            embed.add_field(
                name="⚔️ Skills",
                value="No special skills learned yet.",
                inline=False
            )
        
        # Fate/Passive abilities
        fate = self.character.get("fate", [])
        if fate:
            fate_text = ""
            for ability in fate:
                fate_text += f"• {ability}\n"
            
            embed.add_field(
                name="🌟 Fate Abilities",
                value=fate_text,
                inline=False
            )
        
        return embed
    
    def create_stats_embed(self) -> discord.Embed:
        """Create detailed statistics embed"""
        name = self.character.get("name", "Unknown")
        
        embed = EmbedBuilder.create_embed(
            title=f"📈 {name}'s Detailed Stats",
            color=0x32CD32
        )
        
        # Growth stats
        level = self.character.get("level", 1)
        xp = self.character.get("exp", 0)
        max_xp = self.character.get("max_exp", 100)
        affection = self.character.get("affection", 0)
        
        embed.add_field(
            name="📊 Growth",
            value=f"Level: **{level}**\n"
                  f"Experience: {format_number(xp)}/{format_number(max_xp)}\n"
                  f"Affection: **{affection}**",
            inline=True
        )
        
        # Combat effectiveness
        hp = self.character.get("hp", 0)
        atk = self.character.get("atk", 0)
        defense = self.character.get("def", 0)
        crit = self.character.get("crit", 5)
        
        embed.add_field(
            name="⚔️ Combat",
            value=f"HP: **{format_number(hp)}**\n"
                  f"ATK: **{format_number(atk)}**\n"
                  f"DEF: **{format_number(defense)}**\n"
                  f"CRIT: **{crit}%**",
            inline=True
        )
        
        # Special stats
        potential = self.character.get("potential", 0)
        element = self.character.get("element", "Neutral")
        summoned_at = self.character.get("summoned_at", "Unknown")
        
        embed.add_field(
            name="✨ Special",
            value=f"Potential: **{format_number(potential)}**\n"
                  f"Element: **{element}**\n"
                  f"Summoned: {summoned_at[:10] if summoned_at != 'Unknown' else 'Unknown'}",
            inline=True
        )
        
        return embed
    
    @discord.ui.button(label="🎯 Skills", style=discord.ButtonStyle.primary)
    async def view_skills(self, interaction: discord.Interaction, button: discord.ui.Button):
        """View character skills"""
        embed = self.create_skills_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="📈 Detailed Stats", style=discord.ButtonStyle.secondary)
    async def view_detailed_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        """View detailed statistics"""
        embed = self.create_stats_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="🏠 Main View", style=discord.ButtonStyle.success)
    async def main_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Return to main character view"""
        embed = self.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=self)


async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(InspectCommands(bot))