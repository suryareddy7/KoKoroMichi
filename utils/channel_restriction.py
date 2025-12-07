"""Channel restriction utilities"""
import discord
from discord.ext import commands
from typing import List


async def check_channel_restriction(ctx: commands.Context, allowed_channels: List[str] = None) -> bool:
    """Check if command is being used in allowed channel.
    
    Args:
        ctx: Discord command context
        allowed_channels: List of allowed channel names
    
    Returns:
        True if command is in allowed channel or no restriction set
    """
    if not allowed_channels:
        return True
    
    if not ctx.channel:
        return False
    
    channel_name = ctx.channel.name.lower()
    return any(allowed.lower() in channel_name for allowed in allowed_channels)
