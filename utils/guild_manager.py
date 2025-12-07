"""Guild management utilities"""
from typing import Dict, List, Optional, Any


class GuildManager:
    """Manage guild-related functionality"""
    
    def __init__(self):
        self.guilds = {}
    
    def create_guild(self, guild_name: str, founder_id: str) -> Dict:
        """Create a new guild.
        
        Args:
            guild_name: Name of the guild
            founder_id: Discord ID of guild founder
        
        Returns:
            Guild data
        """
        return {
            "name": guild_name,
            "founder": founder_id,
            "members": [founder_id],
            "level": 1,
            "treasury": 0,
            "established": None
        }
    
    def add_member(self, guild_data: Dict, member_id: str) -> bool:
        """Add a member to a guild.
        
        Args:
            guild_data: Guild data dictionary
            member_id: Discord ID of member
        
        Returns:
            True if added, False if already member
        """
        if member_id not in guild_data["members"]:
            guild_data["members"].append(member_id)
            return True
        return False
    
    def remove_member(self, guild_data: Dict, member_id: str) -> bool:
        """Remove a member from a guild.
        
        Args:
            guild_data: Guild data dictionary
            member_id: Discord ID of member
        
        Returns:
            True if removed, False if not a member
        """
        if member_id in guild_data["members"]:
            guild_data["members"].remove(member_id)
            return True
        return False
