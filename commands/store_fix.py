import discord
from discord.ext import commands
import json
import os

USERS_FILE = "data/users.json"

class StoreFix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def load_users(self):
        if not os.path.exists(USERS_FILE):
            return {}
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_users(self, users):
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2)
    
    def format_currency(self, amount):
        """Format currency for display (K/M notation)"""
        if amount >= 1_000_000:
            return f"{amount / 1_000_000:.1f}M"
        elif amount >= 1_000:
            return f"{amount / 1_000:.1f}K"
        else:
            return str(int(amount))
    
    def parse_currency(self, amount_str):
        """Parse currency from K/M notation back to integer"""
        if isinstance(amount_str, (int, float)):
            return int(amount_str)
        
        amount_str = str(amount_str).upper().replace(',', '')
        
        if 'K' in amount_str:
            return int(float(amount_str.replace('K', '')) * 1_000)
        elif 'M' in amount_str:
            return int(float(amount_str.replace('M', '')) * 1_000_000)
        else:
            return int(float(amount_str))

async def setup(bot):
    await bot.add_cog(StoreFix(bot))