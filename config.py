#!/usr/bin/env python3
"""
KoKoroMichi Bot Configuration
Secure token management and bot settings
"""

import os
from pathlib import Path

# Bot Configuration
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN', '')

def get_bot_token():
    """Securely retrieve bot token from environment variables"""
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("⚠️  DISCORD_BOT_TOKEN not found in environment variables")
        print("📝 Please set your Discord bot token using Replit Secrets:")
        print("   1. Go to Secrets tab in Replit")
        print("   2. Add key: DISCORD_BOT_TOKEN")
        print("   3. Add your bot token as the value")
        return None
    return token

def validate_token(token):
    """Basic token validation"""
    if not token:
        return False
    # Discord bot tokens start with specific patterns
    if len(token) < 50:
        return False
    return True