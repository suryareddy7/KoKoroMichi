"""Affinity and relationship management"""
from typing import Dict, Optional


class AffinityManager:
    """Manage character affinity and relationship systems"""
    
    def __init__(self):
        self.affinity_thresholds = {
            1: 0,
            2: 100,
            3: 250,
            4: 450,
            5: 700,
            "max": 1000
        }
    
    def increase_affinity(self, character: Dict, amount: int) -> int:
        """Increase character affinity.
        
        Args:
            character: Character data
            amount: Amount to increase
        
        Returns:
            New affinity value
        """
        current = character.get("affinity", 0)
        new_affinity = min(current + amount, self.affinity_thresholds["max"])
        character["affinity"] = new_affinity
        return new_affinity
    
    def get_affinity_level(self, affinity: int) -> int:
        """Get affinity level from affinity points.
        
        Args:
            affinity: Affinity points
        
        Returns:
            Affinity level (1-5)
        """
        for level in range(5, 0, -1):
            if affinity >= self.affinity_thresholds[level]:
                return level
        return 1
    
    def get_affinity_percentage(self, affinity: int, current_level: int) -> float:
        """Get percentage progress to next affinity level.
        
        Args:
            affinity: Current affinity points
            current_level: Current affinity level
        
        Returns:
            Percentage to next level (0-100)
        """
        current_threshold = self.affinity_thresholds[current_level]
        next_threshold = self.affinity_thresholds.get(current_level + 1, self.affinity_thresholds["max"])
        
        if current_level >= 5:
            return 100.0
        
        progress = affinity - current_threshold
        required = next_threshold - current_threshold
        
        return (progress / required) * 100
