# KoKoroMichi Bot - Complete Commands Reference

This document provides a comprehensive list of all available commands organized by category.

---

## 📊 Achievements
**Cog:** `achievements.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `achievements` | `badges`, `trophies` | View earned achievements and badges | `!achievements` |
| `achievement_details` | `badge_info` | View specific achievement details | `!achievement_details "First Summon"` |
| `achievement_stats` | `badge_stats` | View achievement progress statistics | `!achievement_stats` |

---

## 🛍️ Store & Economy
**Cog:** `store.py`, `inventory.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `store` | `shop`, `catalog` | Browse the item store | `!store` |
| `store_inventory` | `store_inv`, `store_items` | View store inventory and special items | `!store_inventory` |
| `buy` | `purchase`, `shop_buy` | Buy items from the store | `!buy "Summon Ticket" 5` |
| `inventory` | `inv`, `items` | View your personal inventory | `!inventory` |
| `use_item` | `consume`, `use` | Use/consume items from inventory | `!use_item "Potion" 1` |
| `sell_item` | `sell` | Sell items for gold | `!sell_item "Common Relic" 3` |
| `gift` | `give` | Gift items to other players | `!gift @user "Summon Ticket" 1` |

---

## 💰 Economy & Transactions
**Cog:** `economy.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `balance` | `gold`, `money` | Check your gold balance | `!balance` |
| `transfer` | `send`, `pay` | Transfer gold to another player | `!transfer @user 1000` |
| `transactions` | `history`, `ledger` | View transaction history | `!transactions` |
| `rich_list` | `leaderboard`, `top_gold` | View richest players | `!rich_list` |
| `daily_reward` | `claim_daily`, `daily` | Claim daily gold reward | `!daily_reward` |

---

## 👯 Profile & Characters
**Cog:** `profile.py`, `summon.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `profile` | `myprofile`, `stats` | View your profile and statistics | `!profile` |
| `summon` | `pull`, `draw`, `gacha` | Summon new characters | `!summon` |
| `favorite` | `fav`, `set_favorite` | Set a favorite character | `!favorite "Amaterasu"` |
| `character` | `waifu`, `char` | View character details | `!character "Amaterasu"` |
| `collection` | `waifus`, `chars` | View your character collection | `!collection` |
| `ascend` | `promote` | Ascend a character to higher rarity | `!ascend "Amaterasu"` |

---

## ⚔️ Battle & Combat
**Cog:** `battle.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `battle` | `fight`, `combat` | Start a battle against an enemy | `!battle` |
| `boss_battle` | `raid`, `world_boss` | Fight a world boss | `!boss_battle` |
| `battle_history` | `fight_log` | View your battle history | `!battle_history` |
| `battle_stats` | `combat_stats` | View battle statistics | `!battle_stats` |

---

## 🏆 PvP & Bosses
**Cog:** `pvp_bosses.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `pvp_duel` | `pvp`, `challenge` | Challenge another player to a duel | `!pvp_duel @user` |
| `bosses` | `world_boss`, `raid` | View active world bosses | `!bosses` |
| `join_raid` | `attack_boss` | Join a world boss raid | `!join_raid boss_id` |

---

## 🎮 Arena
**Cog:** `arena.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `arena` | `coliseum`, `tournament` | Enter the arena tournament | `!arena` |
| `arena_stats` | `arena_info` | View arena statistics | `!arena_stats` |
| `arena_leaderboard` | `arena_top`, `rankings` | View arena rankings | `!arena_leaderboard` |
| `arena_join` | `join_tournament` | Join arena tournament | `!arena_join` |

---

## 🎪 Contests & Events
**Cog:** `contests.py`, `events.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `contests` | `competitions` | View available contests | `!contests` |
| `join_contest` | `participate` | Join a contest | `!join_contest "Beauty Contest"` |
| `events` | `special_events` | View active events | `!events` |
| `event_status` | `event_info` | Check event progress | `!event_status "Valentine Event"` |

---

## 🌙 Seasonal & Story Events
**Cog:** `seasonal_events.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `seasonal` | `season_info` | View seasonal bonuses and story events | `!seasonal` |
| `startevent` | `begin_event` | Start a story event with waifus | `!startevent "The First Summon" "Amaterasu"` |
| `eventchoice` | `event_choice` | Make choices in story events | `!eventchoice event_id 1` |
| `eventprogress` | `check_event` | Check active event progress | `!eventprogress` |

---

## 💭 Dreams & Vision System
**Cog:** `dreams.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `dreams` | `visions`, `dreamquest` | Enter the dream realm | `!dreams` |
| `dream_buffs` | `buffs`, `effects` | View active dream buffs | `!dream_buffs` |
| `invoke_dream` | `cast_dream` | Invoke a dream buff for combat | `!invoke_dream "Luck Surge"` |

---

## 🔗 Intimate & Relationships
**Cog:** `intimate.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `intimate` | `interact`, `affection` | Increase affection with a character | `!intimate "Amaterasu"` |
| `affinity` | `relationship` | View character affinity/relationship | `!affinity "Amaterasu"` |
| `romance` | `love` | Trigger romantic interactions | `!romance "Amaterasu"` |

---

## 🎁 Daily Activities & Quests
**Cog:** `daily.py`, `quests.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `daily` | `daily_check`, `checkin` | Claim daily rewards | `!daily` |
| `daily_tasks` | `daily_quests` | View daily tasks | `!daily_tasks` |
| `quests` | `missions`, `tasks` | View available quests | `!quests daily` |
| `claim_quest` | `complete_quest` | Claim quest rewards | `!claim_quest "Battle Victory"` |

---

## 🎯 Mini Games & Fun
**Cog:** `mini_games.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `8ball` | `eightball`, `magic_ball` | Ask the magic 8 ball | `!8ball "Will I win?"` |
| `roll` | `dice`, `dice_roll` | Roll dice | `!roll 6` |
| `choose` | `pick`, `decide` | Randomly choose from options | `!choose apple banana cherry` |
| `trivia` | `quiz` | Play trivia game | `!trivia` |
| `lottery` | `lotto` | Try your luck in the lottery | `!lottery 5` |

---

## 🎨 Gallery & Display
**Cog:** `gallery.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `gallery` | `view_art` | View character art gallery | `!gallery` |
| `set_portrait` | `portrait` | Set character portrait | `!set_portrait "Amaterasu" 1` |
| `favorite_art` | `like_art` | Like/favorite art pieces | `!favorite_art id` |

---

## 📜 Lore & Inspect
**Cog:** `lore.py`, `inspect.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `lore` | `story`, `canon` | View character lore and backstory | `!lore "Amaterasu"` |
| `inspect` | `examine`, `info` | Inspect character details | `!inspect "Amaterasu"` |
| `world_lore` | `world_story` | View world lore | `!world_lore` |
| `lore_tree` | `family_tree` | View character relationship trees | `!lore_tree` |

---

## 🏰 Guild & Factions
**Cog:** `guild.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `guild` | `faction`, `organization` | Create or join a guild | `!guild` |
| `guild_info` | `guild_stats` | View guild information | `!guild_info` |
| `guild_members` | `guild_roster` | View guild members | `!guild_members` |
| `guild_upgrade` | `upgrade_guild` | Upgrade guild facilities | `!guild_upgrade` |
| `guild_quest` | `guild_mission` | Start guild quest | `!guild_quest` |

---

## 🐾 Pets & Companions
**Cog:** `pets.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `pet` | `companion`, `pet_stats` | View or manage pets | `!pet` |
| `adopt_pet` | `get_pet` | Adopt a new pet | `!adopt_pet` |
| `feed_pet` | `feed` | Feed your pet | `!feed_pet` |
| `pet_battle` | `pet_fight` | Battle with your pet | `!pet_battle @user` |
| `pet_name` | `rename_pet` | Rename your pet | `!pet_name "Fluffy"` |

---

## 🔨 Crafting & Forging
**Cog:** `crafting.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `craft` | `forge`, `create` | Craft items from materials | `!craft "Iron Sword"` |
| `crafting_recipes` | `recipes` | View available recipes | `!crafting_recipes` |
| `craft_material` | `gather` | Gather crafting materials | `!craft_material` |
| `alchemy` | `potion_craft` | Craft potions and alchemical items | `!alchemy "Health Potion"` |

---

## 💎 Relics & Equipment
**Cog:** `relics.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `relics` | `equipment`, `gear` | View character equipment | `!relics` |
| `equip_relic` | `equip` | Equip a relic to a character | `!equip_relic "Amaterasu" "Celestial Blade"` |
| `unequip_relic` | `remove_gear` | Remove equipment from character | `!unequip_relic "Amaterasu"` |
| `relic_upgrade` | `enhance_gear` | Upgrade relic stats | `!relic_upgrade "Celestial Blade"` |

---

## ⚡ Traits & Abilities
**Cog:** `traits.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `traits` | `trait_list` | View character traits | `!traits` |
| `develop_trait` | `unlock_trait` | Develop a new trait for character | `!develop_trait "Amaterasu" "Divine Protection"` |
| `trait_effects` | `ability_effects` | View trait effects and bonuses | `!trait_effects "Divine Protection"` |

---

## 📈 Upgrades & Enhancement
**Cog:** `upgrade.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `upgrade` | `levelup`, `enhance` | Upgrade character level using XP | `!upgrade "Amaterasu"` |
| `train` | `practice` | Train character by spending gold | `!train "Amaterasu" 10` |
| `evolution` | `transform` | Evolve character to new form | `!evolution "Amaterasu"` |
| `skill_upgrade` | `skill_train` | Upgrade character skills | `!skill_upgrade "Amaterasu" "Divine Strike"` |

---

## 🌍 Mishaps & Random Events
**Cog:** `mishaps.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `mishap` | `incident`, `accident` | Trigger a random mishap event | `!mishap` |
| `mishap_history` | `incident_log` | View past mishaps | `!mishap_history` |

---

## ⚙️ Server Configuration
**Cog:** `server_config.py`, `server_setup.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `server_setup` | `auto_setup`, `configure_server` | Auto-create required channels | `!server_setup` |
| `setup` | N/A | Show current channel setup | `!setup` |
| `link` | N/A | Link feature to channel | `!link arena #arena-channel` |
| `replace` | N/A | Replace channel link | `!replace arena #new-arena` |
| `unlink` | N/A | Remove channel link | `!unlink arena` |

---

## 📋 Admin & Moderation
**Cog:** `admin.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `admin_panel` | `admin` | Access admin control panel | `!admin_panel` |
| `announce` | `broadcast` | Make server announcements | `!announce "Server maintenance at 2 PM"` |
| `reset_user_data` | `wipe_user` | Reset user data (admin) | `!reset_user_data @user` |
| `set_balance` | `set_gold` | Set player gold balance (admin) | `!set_balance @user 10000` |
| `grant_items` | `give_items` | Grant items to players (admin) | `!grant_items @user "Summon Ticket" 5` |

---

## ❓ Help & Information
**Cog:** `help.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `help` | `commands` | Show help and command list | `!help` |
| `help_category` | `help_cog` | Get help on specific category | `!help_category battle` |
| `command_info` | `cmd_info` | Get detailed command info | `!command_info summon` |
| `feature_guide` | `guide` | Get feature guide | `!feature_guide arena` |

---

## 📝 Miscellaneous
**Cog:** `misc.py`

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `ping` | N/A | Check bot ping | `!ping` |
| `status` | `bot_status` | Check bot status | `!status` |
| `info` | `botinfo` | Get bot information | `!info` |
| `uptime` | N/A | Check bot uptime | `!uptime` |

---

## Command Prefix
All commands use the prefix: `!`

## Notes
- Commands are case-insensitive
- Aliases can be used interchangeably with main command names
- Many commands require the user to have claimed at least one character
- Some commands require specific permissions (admin, guild leader, etc.)
- Parameters in angle brackets `<param>` are required
- Parameters in square brackets `[param]` are optional

---

**Last Updated:** December 7, 2025
