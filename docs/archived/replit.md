# Overview

KoKoroMichi is an advanced Discord RPG bot featuring a comprehensive waifu (anime character) collection and battle system. This is Version 3.0.0 - a complete rebuild that provides 98 commands across 31 modules with a focus on character collection, strategic combat, guild systems, and social interactions. The bot creates an immersive gaming experience where players summon, train, and battle with their favorite anime characters while participating in guilds, seasonal events, and various mini-games.

# User Preferences

Preferred communication style: Simple, everyday language.

# Recent Changes (September 1, 2025)

## Latest Implementation
- **Complete Bot Restoration**: Successfully restored and enhanced KoKoroMichi RPG bot from foundation to full functionality
- **All 33 Command Modules**: Fixed all import errors and conflicts - bot now loads 33/33 modules without errors
- **Enhanced Battle System**: Implemented comprehensive combat engine with all available buffs (guild bonuses, pet abilities, dream buffs, affinity bonuses, trait effects, relic powers)
- **Channel Management**: Smart channel restriction system with flexible matching (e.g., "guild-hall" matches "emoji-guild-hall")
- **Command Restrictions**: Enforced channel-specific restrictions (battles in combat/duel zones, pets in pet channels, guilds in guild-hall)
- **Easter Egg Integration**: Added random easter egg quotes to all bot embeds for enhanced user experience
- **JSON Data Integration**: Created commands for all unused JSON data files (contests, lore achievements, social events, random events)
- **Pet System Enhancement**: Updated pets to use comprehensive JSON data with 5+ species and full stat systems
- **Contest & Social Systems**: Added mood polls, fan contests, pet races, treasure hunts, and achievement tracking
- **Lore & Achievement System**: Implemented rich lore books with reading rewards and comprehensive achievement tracking
- **Welcome System**: Automatic channel creation with welcome embeds and command guides
- **Admin Security**: All admin commands restricted to DM for enhanced security
- **Data Integrity**: All JSON files properly loaded and accessible through data manager

## Website Implementation (September 1, 2025)
- **Complete Full-Stack Website**: Built comprehensive React + Node.js website in dedicated `/website/` folder
- **5-Element Theme System**: Water (blue), Fire (red), Earth (brown), Metal (steel), Wood (green) with animated particle backgrounds
- **Responsive Design**: Mobile-first design with Tailwind CSS, optimized for all screen sizes
- **Dynamic Content Pages**: Home (live stats, invite), Commands (98+ interactive cards), Waifus (character database with rarity system), Features (game mechanics), FAQ (searchable with Discord webhook submission)
- **Discord Integration**: Live server statistics, Discord widget embed, FAQ webhook to #faq-section channel
- **Advanced UI/UX**: Framer Motion animations, particle backgrounds, theme-aware colors, smooth transitions
- **Backend API**: Express server with Discord API integration, character data serving, command statistics
- **Deployment Ready**: Configured for Replit deployment with proper package management and build scripts

# System Architecture

## Core Bot Framework
The application is built on Discord.py with a modular, enterprise-grade architecture:

- **Main Entry Point**: `bot.py` serves as the primary bot runner with proper intents configuration
- **Command System**: 31 command modules in the `/commands` directory, each focusing on specific game systems
- **Channel Management**: Advanced channel restriction system with emoji-aware name matching and automatic channel creation
- **Configuration Management**: Centralized configuration through `core/config.py` with feature flags and game constants
- **Error Handling**: Comprehensive error recovery with user-friendly feedback messages across all modules

## Data Management System
The bot implements a sophisticated JSON-based data storage approach:

- **User Data**: Individual user profiles stored in `data/users.json` with character collections, stats, and progress
- **Game Systems Data**: Multiple specialized JSON files for different game features (guilds, arena, auctions, etc.)
- **Character Database**: Individual character data files with detailed stats, skills, and progression systems
- **Caching Strategy**: Built-in caching system in `core/data_manager.py` for optimized performance
- **Backup Systems**: Automatic backup creation during data operations to prevent data loss

## Game Systems Architecture
The bot features 11+ major interconnected game systems:

- **Summoning System**: Gacha mechanics with rarity tiers (N, R, SR, SSR, UR, LR, Mythic) and pity systems
- **Combat Engine**: Advanced RPG battles with comprehensive buff system incorporating guild bonuses, pet abilities, dream buffs, affinity bonuses, trait effects, relic powers, and elemental advantages
- **Character Progression**: Level-up system, stat enhancement, training, and upgrade mechanics
- **Guild System**: Team-based gameplay with roles, bonuses, and collaborative activities
- **Economy**: Multi-currency system (gold/gems), investment mechanics, auction house, and daily rewards
- **Crafting System**: Item creation and enhancement with recipes and material gathering
- **Social Features**: Character affection system, fan clubs, and intimate interactions
- **Seasonal Events**: Dynamic content with special activities, rewards, and limited-time features

## Discord Integration Architecture
Advanced Discord-specific features:

- **Embed System**: Consistent, professional embed styling through `core/embed_utils.py`
- **Interactive UI**: Discord UI components with buttons, modals, and select menus for complex interactions
- **Channel Management**: Automatic channel creation and restriction systems for organized gameplay
- **Permission Handling**: Role-based access control with admin and moderator systems
- **Server Configuration**: Auto-setup systems for easy bot deployment across multiple servers

## Command Organization
Commands are logically grouped into focused modules:

- **Profile & Collection**: Character management, inspection, and collection viewing
- **Combat & Battles**: Battle systems, arena fights, and PvP duels
- **Economy & Trading**: Store, auction house, investments, and financial management
- **Social Systems**: Guilds, fan clubs, and relationship mechanics
- **Administrative**: Bot management, server setup, and moderation tools

# External Dependencies

## Core Framework
- **Discord.py**: Primary Discord API wrapper for bot functionality and interaction handling
- **Python Standard Library**: JSON for data persistence, datetime for time management, asyncio for asynchronous operations

## Data Storage
- **JSON Files**: All game data stored in human-readable JSON format for easy management and backup
- **File System**: Local file storage for character assets, configuration, and persistent data

## Optional Integrations
- **Flask Web Server**: Optional web dashboard component (`web_server_advanced.py`) for bot monitoring
- **Logging System**: Python logging module for error tracking and debugging
- **Backup Systems**: Automated data backup mechanisms for data integrity

## Asset Management
- **Character Images**: WebP format character portraits organized by rarity and level requirements
- **Static Assets**: Local storage for game-related images and visual content
- **Configuration Files**: JSON-based configuration system for game mechanics and bot settings
