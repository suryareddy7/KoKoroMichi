"""Dream event and dream-buff manager

Provides a minimal DreamManager with an in-memory store for active dream buffs.
This is intentionally lightweight — expand later to persist via `core.data_manager` if needed.
"""
from typing import Dict, Any
from datetime import datetime, timedelta


class DreamManager:
    """Manage dream events and temporary dream buffs for users."""

    def __init__(self):
        # Structure: {"dream_buffs": {user_id: {buff_id: {effects: {...}, expires_at: iso}}}}
        self.user_dreams: Dict[str, Dict[str, Any]] = {"dream_buffs": {}}

    def add_dream_buff(self, user_id: str, buff_id: str, effects: Dict[str, float], duration_seconds: int = 3600):
        """Add a temporary dream buff for a user.

        Args:
            user_id: Discord user id string
            buff_id: unique id for this buff
            effects: mapping of effect key -> multiplier/amount
            duration_seconds: seconds until expiry
        """
        expires_at = (datetime.utcnow() + timedelta(seconds=duration_seconds)).isoformat()
        buffs = self.user_dreams.setdefault("dream_buffs", {})
        user_buffs = buffs.setdefault(user_id, {})
        user_buffs[buff_id] = {"effects": effects, "expires_at": expires_at}

    def remove_dream_buff(self, user_id: str, buff_id: str):
        buffs = self.user_dreams.get("dream_buffs", {})
        user_buffs = buffs.get(user_id, {})
        if buff_id in user_buffs:
            del user_buffs[buff_id]

    def get_user_buffs(self, user_id: str) -> Dict[str, Any]:
        """Return active buffs for a user, skipping expired ones."""
        active: Dict[str, Any] = {}
        buffs = self.user_dreams.get("dream_buffs", {}).get(user_id, {})
        now = datetime.utcnow()
        for buff_id, buff_data in list(buffs.items()):
            expires_at = buff_data.get("expires_at")
            if not expires_at:
                continue
            try:
                expire_time = datetime.fromisoformat(expires_at)
            except Exception:
                continue
            if now <= expire_time:
                active[buff_id] = buff_data
            else:
                # expired, remove
                try:
                    del buffs[buff_id]
                except KeyError:
                    pass

        return active

    def cleanup_expired(self) -> int:
        """Remove expired buffs across all users. Returns number removed."""
        removed = 0
        dreams = self.user_dreams.get("dream_buffs", {})
        now = datetime.utcnow()
        for user_id, user_buffs in list(dreams.items()):
            for buff_id, buff_data in list(user_buffs.items()):
                expires_at = buff_data.get("expires_at")
                try:
                    expire_time = datetime.fromisoformat(expires_at)
                except Exception:
                    continue
                if now > expire_time:
                    del user_buffs[buff_id]
                    removed += 1

            if not user_buffs:
                try:
                    del dreams[user_id]
                except KeyError:
                    pass

        return removed
