"""Pet management and companion system"""
from typing import Dict, List, Optional


class PetManager:
    """Manage pet companions and pet-related features"""
    
    def __init__(self):
        self.pet_types = ["cat", "dog", "rabbit", "bird", "fox", "wolf"]
        self.pet_stats = {
            "cat": {"friendliness": 7, "energy": 6, "intelligence": 8},
            "dog": {"friendliness": 9, "energy": 8, "intelligence": 6},
            "rabbit": {"friendliness": 6, "energy": 7, "intelligence": 5},
            "bird": {"friendliness": 5, "energy": 9, "intelligence": 7},
            "fox": {"friendliness": 4, "energy": 8, "intelligence": 9},
            "wolf": {"friendliness": 3, "energy": 9, "intelligence": 8}
        }
    
    def create_pet(self, pet_type: str, name: str) -> Optional[Dict]:
        """Create a new pet.
        
        Args:
            pet_type: Type of pet
            name: Pet name
        
        Returns:
            Pet data dictionary or None if invalid type
        """
        if pet_type not in self.pet_types:
            return None
        
        return {
            "type": pet_type,
            "name": name,
            "level": 1,
            "happiness": 50,
            "hunger": 50,
            "energy": 100,
            "stats": self.pet_stats[pet_type].copy(),
            "experience": 0
        }
    
    def feed_pet(self, pet: Dict) -> bool:
        """Feed a pet to reduce hunger.
        
        Args:
            pet: Pet data
        
        Returns:
            True if fed successfully
        """
        if pet.get("hunger", 0) > 0:
            pet["hunger"] = max(0, pet["hunger"] - 30)
            pet["happiness"] = min(100, pet["happiness"] + 10)
            return True
        return False
    
    def pet_adventure(self, pet: Dict) -> Dict:
        """Send pet on an adventure.
        
        Args:
            pet: Pet data
        
        Returns:
            Adventure result with rewards
        """
        import random
        
        if pet.get("energy", 0) < 20:
            return {"success": False, "message": "Pet is too tired"}
        
        pet["energy"] -= 20
        pet["hunger"] += 10
        
        reward = random.randint(50, 200)
        
        return {
            "success": True,
            "gold": reward,
            "experience": random.randint(10, 50)
        }
