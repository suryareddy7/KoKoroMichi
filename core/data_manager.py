# Advanced Data Manager for KoKoroMichi Bot
import json
import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from .config import DATA_DIR, CHARACTERS_DIR, DEFAULT_GOLD, DEFAULT_GEMS

class DataManager:
    """Advanced data manager with error handling, backups, and optimization"""
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.characters_dir = CHARACTERS_DIR
        self.users_file = self.data_dir / "users.json"
        self.game_data_file = self.data_dir / "game_data.json"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Cache for frequently accessed data
        self._cache = {}
        self._cache_expiry = {}
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        for directory in [self.data_dir, self.characters_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Create default files if they don't exist
        if not self.users_file.exists():
            self._save_json(self.users_file, {})
    
    def _create_backup(self, file_path: Path) -> bool:
        """Create a backup of a file before modifying it"""
        try:
            if file_path.exists():
                backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
                shutil.copy2(file_path, backup_path)
                return True
        except Exception as e:
            self.logger.error(f"Failed to create backup for {file_path}: {e}")
        return False
    
    def _save_json(self, file_path: Path, data: Dict[str, Any]) -> bool:
        """Save JSON data safely with backup"""
        try:
            # Create backup first
            self._create_backup(file_path)
            
            # Save new data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Clear cache for this file
            cache_key = str(file_path)
            if cache_key in self._cache:
                del self._cache[cache_key]
            
            return True
        except Exception as e:
            self.logger.error(f"Error saving {file_path}: {e}")
            # Try to restore from backup
            self._restore_from_backup(file_path)
            return False
    
    def _load_json(self, file_path: Path, use_cache: bool = True) -> Dict[str, Any]:
        """Load JSON data safely with caching"""
        cache_key = str(file_path)
        
        # Check cache first
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Cache the data
                if use_cache:
                    self._cache[cache_key] = data.copy()
                
                return data
        except Exception as e:
            self.logger.error(f"Error loading {file_path}: {e}")
            # Try to restore from backup
            if self._restore_from_backup(file_path):
                return self._load_json(file_path, use_cache=False)
        
        return {}
    
    def _restore_from_backup(self, file_path: Path) -> bool:
        """Restore file from backup"""
        try:
            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
            if backup_path.exists():
                shutil.copy2(backup_path, file_path)
                self.logger.info(f"Restored {file_path} from backup")
                return True
        except Exception as e:
            self.logger.error(f"Failed to restore {file_path} from backup: {e}")
        return False
    
    def get_user_data(self, user_id: str) -> Dict[str, Any]:
        """Get user data with automatic profile creation"""
        users_data = self._load_json(self.users_file)
        
        if user_id not in users_data:
            # Create new user profile
            new_profile = self._create_default_profile()
            users_data[user_id] = new_profile
            self._save_json(self.users_file, users_data)
            self.logger.info(f"Created new profile for user {user_id}")
        
        return users_data[user_id].copy()
    
    def save_user_data(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """Save user data with validation"""
        try:
            users_data = self._load_json(self.users_file)
            
            # Update last active timestamp
            user_data["last_active"] = datetime.now().isoformat()
            
            users_data[user_id] = user_data
            return self._save_json(self.users_file, users_data)
        except Exception as e:
            self.logger.error(f"Error saving user data for {user_id}: {e}")
            return False
    
    def _create_default_profile(self) -> Dict[str, Any]:
        """Create a default user profile"""
        return {
            "name": "",
            "gold": DEFAULT_GOLD,
            "gems": DEFAULT_GEMS,
            "level": 1,
            "xp": 0,
            "hp": 100,
            "claimed_waifus": [],
            "waifu_stats": {},
            "inventory": {},
            "investments": {},
            "guild_id": None,
            "achievements": [],
            "battle_stats": {
                "battles_won": 0,
                "battles_lost": 0,
                "total_damage_dealt": 0,
                "total_damage_taken": 0
            },
            "crafting_stats": {
                "items_crafted": 0,
                "materials_gathered": 0,
                "successful_crafts": 0
            },
            "settings": {
                "auto_collect": False,
                "notifications": True,
                "display_mode": "detailed"
            },
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat()
        }
    
    def get_character_data(self, character_name: str) -> Optional[Dict[str, Any]]:
        """Get character data by name"""
        try:
            char_file = self.characters_dir / f"{character_name.lower()}.json"
            if char_file.exists():
                return self._load_json(char_file)
        except Exception as e:
            self.logger.error(f"Error loading character {character_name}: {e}")
        return None
    
    def get_all_characters(self) -> List[Dict[str, Any]]:
        """Get all available characters"""
        characters = []
        try:
            for char_file in self.characters_dir.glob("*.json"):
                char_data = self._load_json(char_file)
                if char_data:
                    characters.append(char_data)
        except Exception as e:
            self.logger.error(f"Error loading characters: {e}")
        return characters
    
    def get_game_data(self, section: Optional[str] = None) -> Dict[str, Any]:
        """Get game configuration data"""
        if section:
            # Try to load from specific file first
            section_file = self.data_dir / f"{section}.json"
            if section_file.exists():
                return self._load_json(section_file)
        
        # Fallback to main game data file
        game_data = self._load_json(self.game_data_file)
        if section and section in game_data:
            return game_data[section]
        return game_data
    
    def add_waifu_to_user(self, user_id: str, waifu_data: Dict[str, Any]) -> bool:
        """Add a waifu to user's collection"""
        try:
            user_data = self.get_user_data(user_id)
            user_data["claimed_waifus"].append(waifu_data)
            return self.save_user_data(user_id, user_data)
        except Exception as e:
            self.logger.error(f"Error adding waifu to user {user_id}: {e}")
            return False
    
    def update_user_stats(self, user_id: str, stats_update: Dict[str, Any]) -> bool:
        """Update specific user stats"""
        try:
            user_data = self.get_user_data(user_id)
            
            # Update stats
            for key, value in stats_update.items():
                if key in user_data:
                    if isinstance(value, (int, float)) and isinstance(user_data[key], (int, float)):
                        user_data[key] += value  # Add to existing value
                    else:
                        user_data[key] = value  # Replace value
                else:
                    user_data[key] = value
            
            return self.save_user_data(user_id, user_data)
        except Exception as e:
            self.logger.error(f"Error updating stats for user {user_id}: {e}")
            return False
    
    def get_users_count(self) -> int:
        """Get total number of registered users"""
        try:
            users_data = self._load_json(self.users_file)
            return len(users_data)
        except:
            return 0
    
    def cleanup_old_backups(self, days_old: int = 7):
        """Clean up backup files older than specified days"""
        try:
            import time
            current_time = time.time()
            
            for backup_file in self.data_dir.glob("*.backup"):
                file_age = current_time - backup_file.stat().st_mtime
                if file_age > (days_old * 24 * 3600):  # Convert days to seconds
                    backup_file.unlink()
                    self.logger.info(f"Deleted old backup: {backup_file}")
        except Exception as e:
            self.logger.error(f"Error cleaning up backups: {e}")

# Global instance
data_manager = DataManager()