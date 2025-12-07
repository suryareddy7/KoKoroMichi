from __future__ import annotations

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from enum import Enum
from uuid import uuid4
from datetime import datetime


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    COMMITTED = "COMMITTED"
    FAILED = "FAILED"
    PENDING_OFFLINE = "PENDING_OFFLINE"


class InventoryEntry(BaseModel):
    item_id: str
    quantity: int = 0
    last_purchased_at: Optional[datetime] = None


class VipTierSpec(BaseModel):
    tier_name: str
    discount_pct: float = 0.0  # 0.10 == 10%
    categories: List[str] = Field(default_factory=list)


class Item(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    categories: List[str] = Field(default_factory=list)
    base_price: Dict[str, int] = Field(default_factory=lambda: {"gold": 0, "gems": 0})
    stock: Optional[int] = None  # None = infinite
    max_per_user: Optional[int] = None
    cooldown_seconds: Optional[int] = None
    inflation_rate: float = 0.0  # e.g., 0.01 per purchase
    total_sold: int = 0
    version: int = 1  # optimistic locking
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @validator("base_price")
    def ensure_price_keys(cls, v):
        if not isinstance(v, dict):
            raise ValueError("base_price must be a dict of currency->amount")
        # ensure numeric ints
        for k, amt in v.items():
            if not isinstance(amt, int) or amt < 0:
                raise ValueError("base_price values must be non-negative ints")
        return v


class PriceSnapshot(BaseModel):
    item_id: str
    currency: str
    base_price: int
    inflation_multiplier: float = 1.0
    vip_discount: float = 0.0
    exchange_rate: float = 1.0
    final_price: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PurchaseTransaction(BaseModel):
    tx_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    item_id: str
    quantity: int = 1
    currency: str = "gold"
    price_snapshot: Optional[PriceSnapshot] = None
    pre_balances: Dict[str, int] = Field(default_factory=dict)
    post_balances: Dict[str, int] = Field(default_factory=dict)
    status: TransactionStatus = TransactionStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    committed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    provider_synced: bool = False


class PendingOfflineTransaction(PurchaseTransaction):
    local_file_path: Optional[str] = None
    retry_count: int = 0


class StorePage(BaseModel):
    items: List[Item]
    page: int
    per_page: int
    total: int


class PurchaseResult(BaseModel):
    success: bool
    tx_id: Optional[str] = None
    message: Optional[str] = None
    new_balances: Optional[Dict[str, int]] = None


class StoreCatalog(BaseModel):
    items: Dict[str, Item] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    def get_item(self, item_id: str) -> Optional[Item]:
        return self.items.get(item_id)
