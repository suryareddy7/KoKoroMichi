"""Pydantic models for core domain objects.

These are minimal skeletons used during the refactor. They will be expanded
as services and features are migrated.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class Item(BaseModel):
    item_id: str = Field(..., description="Unique item identifier")
    name: str
    description: Optional[str] = None
    price: int = 0


class Waifu(BaseModel):
    waifu_id: str
    name: str
    rarity: Optional[str] = None


class UserProfile(BaseModel):
    user_id: str
    name: Optional[str] = None
    gold: int = 0
    inventory: dict = Field(default_factory=dict)


class Transaction(BaseModel):
    tx_id: str
    user_id: str
    amount: int
    description: Optional[str] = None
