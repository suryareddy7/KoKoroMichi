"""Advanced combat engine for KoKoroMichi battles"""
from typing import Dict, List, Optional, Tuple
import random


class BattleEngine:
    """Advanced battle calculation engine"""
    
    def __init__(self):
        self.element_advantage = {
            "fire": {"grass", "bug", "steel"},
            "water": {"fire", "ground", "rock"},
            "grass": {"water", "ground", "rock"},
            "electric": {"water", "flying"},
            "ice": {"grass", "flying", "ground", "dragon"},
            "fighting": {"normal", "ice", "rock", "dark", "steel"},
            "poison": {"grass", "fairy"},
            "ground": {"fire", "electric", "poison", "rock", "steel"},
            "flying": {"grass", "fighting", "bug"},
            "psychic": {"fighting", "poison"},
            "bug": {"grass", "psychic", "dark"},
            "rock": {"fire", "ice", "flying", "bug"},
            "ghost": {"psychic", "ghost"},
            "dragon": {"dragon"},
            "dark": {"psychic", "ghost"},
            "steel": {"ice", "rock", "fairy"},
            "fairy": {"fighting", "dragon", "dark"}
        }
    
    def calculate_damage(self, attacker: Dict, defender: Dict) -> int:
        """Calculate damage from attacker to defender.
        
        Args:
            attacker: Attacker character data
            defender: Defender character data
        
        Returns:
            Damage value
        """
        base_damage = attacker.get("atk", 10) * random.uniform(0.8, 1.2)
        defense_reduction = defender.get("def", 5) * 0.5
        
        # Elemental advantage
        attacker_element = attacker.get("element", "normal").lower()
        defender_element = defender.get("element", "normal").lower()
        element_multiplier = 1.0
        
        if attacker_element in self.element_advantage:
            if defender_element in self.element_advantage[attacker_element]:
                element_multiplier = 1.5
        
        damage = max(1, int((base_damage - defense_reduction) * element_multiplier))
        return damage
    
    def simulate_battle(self, team1: List[Dict], team2: List[Dict]) -> Dict:
        """Simulate a full battle between two teams.
        
        Args:
            team1: First team (list of character data)
            team2: Second team (list of character data)
        
        Returns:
            Battle result with winner and statistics
        """
        team1_hp = [char.get("hp", 100) for char in team1]
        team2_hp = [char.get("hp", 100) for char in team2]
        
        rounds = 0
        max_rounds = 50
        
        while sum(team1_hp) > 0 and sum(team2_hp) > 0 and rounds < max_rounds:
            # Team 1 attacks
            if sum(team1_hp) > 0:
                attacker_idx = next(i for i in range(len(team1_hp)) if team1_hp[i] > 0)
                defender_idx = next(i for i in range(len(team2_hp)) if team2_hp[i] > 0)
                
                damage = self.calculate_damage(team1[attacker_idx], team2[defender_idx])
                team2_hp[defender_idx] -= damage
            
            # Team 2 attacks
            if sum(team2_hp) > 0:
                attacker_idx = next(i for i in range(len(team2_hp)) if team2_hp[i] > 0)
                defender_idx = next(i for i in range(len(team1_hp)) if team1_hp[i] > 0)
                
                damage = self.calculate_damage(team2[attacker_idx], team1[defender_idx])
                team1_hp[defender_idx] -= damage
            
            rounds += 1
        
        winner = 1 if sum(team1_hp) > sum(team2_hp) else 2
        
        return {
            "winner": winner,
            "rounds": rounds,
            "team1_remaining_hp": max(0, sum(team1_hp)),
            "team2_remaining_hp": max(0, sum(team2_hp))
        }
