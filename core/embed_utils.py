# Embed utilities for KoKoroMichi Advanced Bot
import discord
from datetime import datetime
from typing import Dict, List, Any, Optional
import random

from .config import EMBED_COLOR, ENCOURAGING_EMOJIS, RARITY_EMOJIS
from .data_manager import data_manager

class EmbedBuilder:
    """Advanced embed builder with consistent styling and utilities"""
    
    @staticmethod
    def get_random_easter_egg():
        """Get a random easter egg tip"""
        try:
            easter_data = data_manager.get_game_data("easter_egg_tips")
            if easter_data and "tips" in easter_data:
                return random.choice(easter_data["tips"])
        except:
            pass
        return "Your journey in KoKoroMichi continues to unfold mysteries..."
    
    @staticmethod
    def create_embed(title: Optional[str] = None, description: Optional[str] = None, color: int = EMBED_COLOR, 
                    add_timestamp: bool = True, thumbnail_url: Optional[str] = None, 
                    image_url: Optional[str] = None, dramatic: bool = False) -> discord.Embed:
        """Create a standardized embed with optional dramatic effects"""
        embed = discord.Embed(color=color)
        
        if title:
            embed.title = EmbedBuilder.add_dramatic_effects(title) if dramatic else title
        if description:
            embed.description = EmbedBuilder.add_visual_border(description) if dramatic else description
        if add_timestamp:
            embed.timestamp = datetime.now()
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)
        if image_url:
            embed.set_image(url=image_url)
        
        # Add easter egg footer to all embeds
        easter_tip = EmbedBuilder.get_random_easter_egg()
        embed.set_footer(text=f"💡 {easter_tip}")
        
        return embed
    
    @staticmethod
    def add_dramatic_effects(text: str) -> str:
        """Add dramatic visual effects to text"""
        if not text:
            return text
        
        effects = [
            f"✨ {text} ✨",
            f"🌟 {text} 🌟", 
            f"⚡ {text} ⚡",
            f"💫 {text} 💫",
            f"🔥 {text} 🔥",
            f"🌙 {text} 🌙",
            f"⭐ {text} ⭐"
        ]
        return random.choice(effects)
    
    @staticmethod
    def add_visual_border(text: str) -> str:
        """Add visual border effects to description text"""
        if not text:
            return text
            
        borders = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "✦ ─────────────────────────────── ✦",
            "⋆｡‧˚ʚ♡ɞ˚‧｡⋆ ─────── ⋆｡‧˚ʚ♡ɞ˚‧｡⋆",
            "•°○●○°• ─────────────── •°○●○°•",
            "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓",
            "◦•●◉✿ ─────────────── ✿◉●•◦"
        ]
        
        border = random.choice(borders)
        return f"{border}\n{text}\n{border}"
    
    @staticmethod
    def success_embed(title: str, description: Optional[str] = None, **kwargs) -> discord.Embed:
        """Create a success embed (green)"""
        return EmbedBuilder.create_embed(title=f"✅ {title}", description=description, 
                                       color=0x00FF00, **kwargs)
    
    @staticmethod
    def error_embed(title: str, description: Optional[str] = None, **kwargs) -> discord.Embed:
        """Create an error embed (red)"""
        return EmbedBuilder.create_embed(title=f"❌ {title}", description=description, 
                                       color=0xFF0000, **kwargs)
    
    @staticmethod
    def warning_embed(title: str, description: Optional[str] = None, **kwargs) -> discord.Embed:
        """Create a warning embed (yellow)"""
        return EmbedBuilder.create_embed(title=f"⚠️ {title}", description=description, 
                                       color=0xFFFF00, **kwargs)
    
    @staticmethod
    def info_embed(title: str, description: Optional[str] = None, **kwargs) -> discord.Embed:
        """Create an info embed (blue)"""
        return EmbedBuilder.create_embed(title=f"ℹ️ {title}", description=description, 
                                       color=0x0099FF, **kwargs)
    
    @staticmethod
    def profile_embed(user_data: Dict[str, Any], user_name: str) -> discord.Embed:
        """Create a user profile embed"""
        embed = EmbedBuilder.create_embed(
            title=f"📊 {user_name}'s Profile",
            color=0xFF69B4
        )
        
        # Basic stats
        embed.add_field(
            name="💰 Resources", 
            value=f"Gold: {user_data.get('gold', 0):,}\nGems: {user_data.get('gems', 0):,}",
            inline=True
        )
        
        embed.add_field(
            name="⭐ Level & XP",
            value=f"Level: {user_data.get('level', 1)}\nXP: {user_data.get('xp', 0):,}",
            inline=True
        )
        
        # Collection stats
        waifus_count = len(user_data.get('claimed_waifus', []))
        embed.add_field(
            name="👥 Collection",
            value=f"Characters: {waifus_count}",
            inline=True
        )
        
        # Battle stats
        battle_stats = user_data.get('battle_stats', {})
        wins = battle_stats.get('battles_won', 0)
        losses = battle_stats.get('battles_lost', 0)
        total = wins + losses
        winrate = (wins / total * 100) if total > 0 else 0
        
        embed.add_field(
            name="⚔️ Battle Record",
            value=f"Wins: {wins} | Losses: {losses}\nWin Rate: {winrate:.1f}%",
            inline=True
        )
        
        return embed
    
    @staticmethod
    def waifu_embed(waifu_data: Dict[str, Any], show_detailed: bool = False) -> discord.Embed:
        """Create a waifu/character embed"""
        name = waifu_data.get('name', 'Unknown')
        rarity = waifu_data.get('rarity', 'N')
        level = waifu_data.get('level', 1)
        
        # Extract rarity tier for emoji
        rarity_tier = rarity.split()[0] if ' ' in rarity else rarity
        rarity_emoji = RARITY_EMOJIS.get(rarity_tier, "❓")
        
        embed = EmbedBuilder.create_embed(
            title=f"{rarity_emoji} {name}",
            description=f"**{rarity}** • Level {level}",
            color=0xFF69B4
        )
        
        # Basic stats
        hp = waifu_data.get('hp', 0)
        atk = waifu_data.get('atk', 0)
        defense = waifu_data.get('def', 0)
        
        embed.add_field(
            name="📊 Stats",
            value=f"❤️ HP: {hp}\n⚔️ ATK: {atk}\n🛡️ DEF: {defense}",
            inline=True
        )
        
        # Potential and element
        potential = waifu_data.get('potential', 0)
        element = waifu_data.get('element', 'Neutral')
        
        embed.add_field(
            name="✨ Details",
            value=f"🔮 Potential: {potential:,}\n🌟 Element: {element}",
            inline=True
        )
        
        if show_detailed:
            # Skills
            skills = waifu_data.get('skills', [])
            if skills:
                skills_text = "\n".join([f"• {skill}" for skill in skills[:3]])
                embed.add_field(name="🎯 Skills", value=skills_text, inline=False)
            
            # Relic
            relic = waifu_data.get('relic')
            if relic:
                embed.add_field(name="💎 Equipped Relic", value=relic, inline=False)
        
        return embed
    
    @staticmethod
    def battle_result_embed(result_data: Dict[str, Any]) -> discord.Embed:
        """Create a battle result embed"""
        winner = result_data.get('winner')
        player_name = result_data.get('player_name', 'Player')
        opponent_name = result_data.get('opponent_name', 'Opponent')
        
        if winner == 'player':
            title = f"🎉 Victory!"
            description = f"{player_name} defeated {opponent_name}!"
            color = 0x00FF00
        else:
            title = f"💔 Defeat"
            description = f"{opponent_name} defeated {player_name}!"
            color = 0xFF0000
        
        embed = EmbedBuilder.create_embed(title=title, description=description, color=color)
        
        # Rewards
        rewards = result_data.get('rewards', {})
        if rewards:
            reward_text = ""
            if rewards.get('gold', 0) > 0:
                reward_text += f"💰 Gold: +{rewards['gold']:,}\n"
            if rewards.get('xp', 0) > 0:
                reward_text += f"⭐ XP: +{rewards['xp']:,}\n"
            if rewards.get('items'):
                reward_text += f"🎁 Items: {', '.join(rewards['items'])}\n"
            
            if reward_text:
                embed.add_field(name="🎁 Rewards", value=reward_text.strip(), inline=False)
        
        return embed
    
    @staticmethod
    def summon_result_embed(summon_data: Dict[str, Any]) -> discord.Embed:
        """Create a summon result embed"""
        character = summon_data.get('character', {})
        name = character.get('name', 'Unknown')
        rarity = character.get('rarity', 'N')
        
        # Get rarity emoji
        rarity_tier = rarity.split()[0] if ' ' in rarity else rarity
        rarity_emoji = RARITY_EMOJIS.get(rarity_tier, "❓")
        
        embed = EmbedBuilder.create_embed(
            title=f"✨ Summoning Results",
            description=f"You summoned **{name}**!",
            color=0xFF69B4
        )
        
        embed.add_field(
            name="🎭 Character Details",
            value=f"{rarity_emoji} **{rarity}**\n🌟 Level 1\n⚔️ ATK: {character.get('atk', 0)}\n❤️ HP: {character.get('hp', 0)}",
            inline=True
        )
        
        # Special message for rare summons
        if rarity_tier in ['UR', 'LR', 'Mythic']:
            embed.add_field(
                name="🎉 Rare Summon!",
                value="Congratulations on this exceptional summon!",
                inline=False
            )
        
        return embed
    
    @staticmethod
    def paginated_embed(title: str, items: List[str], page: int = 0, 
                       items_per_page: int = 10) -> discord.Embed:
        """Create a paginated embed"""
        total_pages = (len(items) - 1) // items_per_page + 1
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        
        page_items = items[start_idx:end_idx]
        
        embed = EmbedBuilder.create_embed(
            title=title,
            description="\n".join(page_items) if page_items else "No items found."
        )
        
        embed.set_footer(text=f"Page {page + 1}/{total_pages}")
        
        return embed
    
    @staticmethod
    def add_random_encouragement(embed: discord.Embed):
        """Add a random encouraging footer to an embed"""
        emoji = random.choice(ENCOURAGING_EMOJIS)
        encouragements = [
            "Keep going, adventurer!",
            "Your journey continues!",
            "Every step makes you stronger!",
            "The waifus believe in you!",
            "Adventure awaits!"
        ]
        message = random.choice(encouragements)
        
        existing_footer = embed.footer.text if embed.footer else ""
        new_footer = f"{existing_footer} | {emoji} {message}" if existing_footer else f"{emoji} {message}"
        embed.set_footer(text=new_footer)
        
        return embed

# Create global instance
embed_builder = EmbedBuilder()