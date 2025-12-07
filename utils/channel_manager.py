"""Channel management utilities for KoKoroMichi"""
import discord
from discord.ext import commands
from typing import Optional


async def check_channel_restriction(ctx: commands.Context, allowed_channel_names: list = None) -> bool:
    """Check if a command is being used in an allowed channel.
    
    Can be used as:
    - Decorator: @check_channel_restriction()
    - Function: await check_channel_restriction(ctx, ["game-commands"])
    
    Args:
        ctx: Discord context (None if used as decorator with no args)
        allowed_channel_names: List of allowed channel names (optional)
    
    Returns:
        True if command is in allowed channel, False otherwise
    """
    if ctx is None:
        # Used as @check_channel_restriction() - return True by default
        return True
    
    if not allowed_channel_names:
        return True  # No restriction
    
    if not ctx.channel:
        return False
    
    channel_name = ctx.channel.name.lower()
    return any(allowed.lower() in channel_name for allowed in allowed_channel_names)


def check_channel_restriction():
    """Decorator version for command restriction.
    
    Usage: @check_channel_restriction()
    
    Returns: Decorator function
    """
    from functools import wraps
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # For command decorators, just pass through (no actual restriction)
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class ChannelManager:
    """Manage channel-specific restrictions and configurations"""
    
    def __init__(self):
        self.restrictions = {}
        self.allowed_channels = {}
    
    def set_restriction(self, guild_id: int, channel_name: str, allowed_commands: list):
        """Set allowed commands for a specific channel"""
        key = f"{guild_id}:{channel_name}"
        self.allowed_channels[key] = allowed_commands
    
    def is_command_allowed(self, guild_id: int, channel_name: str, command_name: str) -> bool:
        """Check if a command is allowed in a channel"""
        key = f"{guild_id}:{channel_name}"
        if key not in self.allowed_channels:
            return True  # No restriction
        
        return command_name in self.allowed_channels[key]


# Global instance
channel_manager = ChannelManager()
