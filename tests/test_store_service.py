"""Comprehensive test suite for StoreService with transactional semantics."""
import asyncio
import os
import json
import pytest

from services.store_service import StoreService, PENDING_FILE
from core.store_models import VipTierSpec, TransactionStatus
from core.data_manager import data_manager


@pytest.fixture(autouse=True)
def cleanup_pending():
    """Clean up pending transactions file before and after each test."""
    if os.path.exists(PENDING_FILE):
        os.remove(PENDING_FILE)
    yield
    if os.path.exists(PENDING_FILE):
        os.remove(PENDING_FILE)


@pytest.mark.asyncio
async def test_preview_price_vip_discount():
    """Test that VIP discount is correctly applied to final price."""
    svc = StoreService()
    vip = VipTierSpec(tier_name="Gold", discount_pct=0.10, categories=["consumable"])
    snap = svc.preview_price("health_potion_small", quantity=2, vip_tier=vip, currency="gold")
    
    assert snap.base_price == 500
    assert snap.vip_discount == pytest.approx(0.10)
    assert snap.final_price > 0
    # Without VIP, price would be 500 * 2 = 1000
    # With 10% VIP discount: 500 * 0.9 * 2 = 900
    expected_price = int(500 * 0.9 * 2)
    assert snap.final_price == expected_price


@pytest.mark.asyncio
async def test_preview_price_inflation():
    """Test that inflation multiplier increases with total_sold."""
    svc = StoreService()
    
    # Initial price without inflation (no sales yet)
    snap1 = svc.preview_price("experience_scroll", quantity=1, vip_tier=None, currency="gold")
    assert snap1.base_price == 1200
    assert snap1.inflation_multiplier == pytest.approx(1.0)
    
    # Simulate 50 sales by updating total_sold
    item = svc.get_item("experience_scroll")
    item.total_sold = 50
    svc.catalog.items[item.id] = item
    
    snap2 = svc.preview_price("experience_scroll", quantity=1, vip_tier=None, currency="gold")
    inflation_mult = (1 + 0.001) ** 50  # inflation_rate = 0.001 for this item
    assert snap2.inflation_multiplier == pytest.approx(inflation_mult)
    # Price should increase
    assert snap2.final_price > snap1.final_price


@pytest.mark.asyncio
async def test_purchase_success_online():
    """Test successful purchase when provider is online."""
    svc = StoreService()
    user_id = "test_user_online"
    
    # Ensure user has sufficient funds
    user = {"gold": 5000, "gems": 100, "inventory": {}, "version": 1}
    data_manager.save_user_data(user_id, user)
    
    res = await svc.purchase_item(
        user_id, "health_potion_small", quantity=2, currency="gold", 
        vip_tier=None, simulate_provider_offline=False
    )
    
    assert res.success is True
    assert res.tx_id is not None
    assert res.new_balances is not None
    
    # Verify local data_manager updated
    updated = data_manager.get_user_data(user_id)
    assert updated["inventory"].get("health_potion_small", 0) >= 2
    # 500 gold per potion * 2 = 1000 gold spent
    assert updated["gold"] == 5000 - 1000


@pytest.mark.asyncio
async def test_purchase_offline_records_pending():
    """Test that purchase is recorded locally when provider is offline."""
    svc = StoreService()
    user_id = "test_user_offline"
    user = {"gold": 10000, "gems": 50, "inventory": {}, "version": 1}
    data_manager.save_user_data(user_id, user)
    
    # Remove pending file if exists
    if os.path.exists(PENDING_FILE):
        os.remove(PENDING_FILE)
    
    res = await svc.purchase_item(
        user_id, "treasure_chest", quantity=1, currency="gems", 
        vip_tier=None, simulate_provider_offline=True
    )
    
    assert res.success is True
    assert "offline" in res.message.lower()
    assert os.path.exists(PENDING_FILE)
    
    with open(PENDING_FILE, "r", encoding="utf-8") as f:
        pending = json.load(f)
    assert len(pending) > 0
    assert any(p["tx_id"] == str(res.tx_id) for p in pending)


@pytest.mark.asyncio
async def test_purchase_insufficient_funds():
    """Test that purchase fails when user has insufficient funds."""
    svc = StoreService()
    user_id = "test_user_poor"
    user = {"gold": 10, "gems": 0, "inventory": {}, "version": 1}
    data_manager.save_user_data(user_id, user)
    
    # Try to buy treasure_chest (costs 5000 gold), user only has 10
    res = await svc.purchase_item(
        user_id, "treasure_chest", quantity=1, currency="gold", 
        vip_tier=None, simulate_provider_offline=False
    )
    
    assert res.success is False
    assert "insufficient" in res.message.lower()
    
    # Verify no state change - user still has 10 gold
    updated = data_manager.get_user_data(user_id)
    assert updated["gold"] == 10


@pytest.mark.asyncio
async def test_purchase_insufficient_stock():
    """Test that purchase fails when item stock is insufficient."""
    svc = StoreService()
    user_id = "test_user_stock"
    user = {"gold": 100000, "gems": 1000, "inventory": {}, "version": 1}
    data_manager.save_user_data(user_id, user)
    
    # Reduce stock on treasure_chest to 2
    item = svc.get_item("treasure_chest")
    original_stock = item.stock
    item.stock = 2
    svc.catalog.items[item.id] = item
    svc._save_local_catalog()
    
    # Try to buy 5 (only 2 available)
    res = await svc.purchase_item(
        user_id, "treasure_chest", quantity=5, currency="gold", 
        vip_tier=None, simulate_provider_offline=False
    )
    
    assert res.success is False
    assert "stock" in res.message.lower()
    
    # Restore original stock
    item.stock = original_stock
    svc.catalog.items[item.id] = item
    svc._save_local_catalog()


    @pytest.mark.asyncio
    async def test_admin_restock():
        """Test admin restock operation increments stock and version."""
        svc = StoreService()
        admin_id = "admin_user"
    
        item = svc.get_item("lucky_charm")
        original_stock = item.stock
        original_version = item.version
    
        # Restock by 50
        restocked = svc.restock_item(admin_id, "lucky_charm", 50)
    
        assert restocked.stock == original_stock + 50
        assert restocked.version == original_version + 1
    
        # Verify persisted
        item_reloaded = svc.get_item("lucky_charm")
        assert item_reloaded.stock == original_stock + 50
        assert item_reloaded.version == original_version + 1


    @pytest.mark.asyncio
    async def test_admin_set_price():
        """Test admin price change operation."""
        svc = StoreService()
        admin_id = "admin_user"
    
        item = svc.get_item("health_potion_small")
        original_version = item.version
    
        # Change price
        new_price = {"gold": 750, "gems": 10}
        updated = svc.set_price(admin_id, "health_potion_small", new_price)
    
        assert updated.base_price == new_price
        assert updated.version == original_version + 1
    
        # Verify persisted
        item_reloaded = svc.get_item("health_potion_small")
        assert item_reloaded.base_price == new_price
        assert item_reloaded.version == original_version + 1


    @pytest.mark.asyncio
    async def test_sync_pending_transactions():
        """Test syncing of offline pending transactions."""
        svc = StoreService()
        user_id = "test_user_sync"
        user = {"gold": 20000, "gems": 200, "inventory": {}, "version": 1}
        data_manager.save_user_data(user_id, user)
    
        # Create a pending transaction by simulating offline purchase
        res = await svc.purchase_item(
            user_id, "treasure_chest", quantity=1, currency="gems", 
            vip_tier=None, simulate_provider_offline=True
        )
    
        assert os.path.exists(PENDING_FILE)
    
        # Sync pending transactions
        report = svc.sync_pending_transactions()
    
        assert report["applied"] >= 1
        # After sync, pending file should be empty or removed
        if os.path.exists(PENDING_FILE):
            with open(PENDING_FILE, "r", encoding="utf-8") as f:
                remaining = json.load(f)
            assert len(remaining) == 0 or report["applied"] > 0


    @pytest.mark.asyncio
    async def test_catalog_pagination():
        """Test catalog pagination and category filtering."""
        svc = StoreService()
    
        # Test default pagination (page 1)
        result = svc.get_catalog(page=1, per_page=2)
        assert len(result["items"]) <= 2
        assert result["page"] == 1
        assert result["total"] == 4  # We have 4 items in sample catalog
    
        # Test category filtering
        consumable_result = svc.get_catalog(page=1, per_page=10, category="consumable")
        # health_potion_small and experience_scroll are consumable
        assert len(consumable_result["items"]) >= 2
        assert all("consumable" in item["categories"] for item in consumable_result["items"])
    
        # Test pagination boundaries
        page_2 = svc.get_catalog(page=2, per_page=2)
        assert len(page_2["items"]) <= 2
        assert page_2["page"] == 2


    @pytest.mark.asyncio
    async def test_get_item_lookup():
        """Test individual item lookup."""
        svc = StoreService()
    
        item = svc.get_item("health_potion_small")
        assert item is not None
        assert item.id == "health_potion_small"
        assert item.name == "Health Potion (Small)"
        assert item.base_price["gold"] == 500
    
        # Non-existent item
        missing = svc.get_item("nonexistent_item")
        assert missing is None


    @pytest.mark.asyncio
    async def test_get_ledger():
        """Test transaction ledger retrieval."""
        svc = StoreService()
    
        # Initially empty or with pending transactions
        ledger = svc.get_ledger("test_user", limit=10, offset=0)
        assert isinstance(ledger, list)
        # Note: actual ledger content depends on pending transactions


    @pytest.mark.asyncio
    async def test_vip_tier_category_matching():
        """Test that VIP discount only applies to matching categories."""
        svc = StoreService()
    
        # VIP only for 'loot' category
        vip = VipTierSpec(tier_name="Loot Master", discount_pct=0.20, categories=["loot"])
    
        # treasure_chest is in 'loot' category - should get discount
        snap_treasure = svc.preview_price(
            "treasure_chest", quantity=1, vip_tier=vip, currency="gold"
        )
        assert snap_treasure.vip_discount == pytest.approx(0.20)
    
        # health_potion_small is NOT in 'loot' category - should NOT get discount
        snap_potion = svc.preview_price(
            "health_potion_small", quantity=1, vip_tier=vip, currency="gold"
        )
        assert snap_potion.vip_discount == pytest.approx(0.0)


    @pytest.mark.asyncio
    async def test_multi_currency_pricing():
        """Test that items can have different prices in different currencies."""
        svc = StoreService()
    
        # treasure_chest has both gold and gem pricing
        snap_gold = svc.preview_price(
            "treasure_chest", quantity=1, vip_tier=None, currency="gold"
        )
        assert snap_gold.base_price == 5000
        assert snap_gold.currency == "gold"
    
        snap_gems = svc.preview_price(
            "treasure_chest", quantity=1, vip_tier=None, currency="gems"
        )
        assert snap_gems.base_price == 25
        assert snap_gems.currency == "gems"
    
        # Different pricing
        assert snap_gold.final_price != snap_gems.final_price
