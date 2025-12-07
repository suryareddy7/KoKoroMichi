"""Seasonal event management utilities"""
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
import json


class SeasonalManager:
    """Manage seasonal events and rotations"""
    
    def __init__(self, data_file: str = "data/seasonal_events.json"):
        self.data_file = data_file
        self.current_season = self._get_current_season()
        self.events = self._load_events()
    
    def _get_current_season(self) -> str:
        """Determine current season based on month"""
        month = datetime.now().month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:  # 9, 10, 11
            return "autumn"
    
    def _load_events(self) -> Dict[str, Any]:
        """Load seasonal events from file"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def get_current_events(self) -> List[Dict]:
        """Get all active events for current season"""
        return self.events.get(self.current_season, {}).get("events", [])
    
    def is_event_active(self, event_name: str) -> bool:
        """Check if a specific event is active"""
        events = self.get_current_events()
        return any(e.get("name") == event_name for e in events)
    
    def get_event_rewards(self, event_name: str) -> Dict:
        """Get rewards for a specific event"""
        events = self.get_current_events()
        for event in events:
            if event.get("name") == event_name:
                return event.get("rewards", {})
        return {}
    
    def get_season_name(self) -> str:
        """Get human-readable season name"""
        names = {
            "winter": "❄️ Winter",
            "spring": "🌸 Spring",
            "summer": "☀️ Summer",
            "autumn": "🍂 Autumn"
        }
        return names.get(self.current_season, self.current_season.title())
