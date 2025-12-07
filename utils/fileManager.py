"""File management utilities for user data"""
import json
import os
from pathlib import Path
from typing import Dict, Any


def load_users(users_file: str = "data/users.json") -> Dict[str, Any]:
    """Load all user data from JSON file.
    
    Args:
        users_file: Path to users.json file
    
    Returns:
        Dictionary of user data
    """
    file_path = Path(users_file)
    
    if not file_path.exists():
        return {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_users(users_data: Dict[str, Any], users_file: str = "data/users.json") -> bool:
    """Save user data to JSON file.
    
    Args:
        users_data: Dictionary of user data to save
        users_file: Path to users.json file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        file_path = Path(users_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, indent=2, ensure_ascii=False)
        return True
    except IOError:
        return False


def load_json(filepath: str) -> Dict[str, Any]:
    """Load JSON data from file.
    
    Args:
        filepath: Path to JSON file
    
    Returns:
        Loaded data or empty dict if error
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, FileNotFoundError):
        return {}


def save_json(filepath: str, data: Dict[str, Any]) -> bool:
    """Save JSON data to file.
    
    Args:
        filepath: Path to JSON file
        data: Data to save
    
    Returns:
        True if successful
    """
    try:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except IOError:
        return False
