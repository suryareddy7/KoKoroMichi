"""Basic tests for DataProvider interface and pydantic models.

These tests are a scaffold to verify test runner setup and will be expanded
as adapters and services are implemented.
"""
import os
import sys

# Ensure repository root is on sys.path so `core` is importable during tests
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.models import UserProfile, Item


def test_user_profile_model():
    u = UserProfile(user_id="123", name="Tester", gold=100)
    assert u.user_id == "123"
    assert u.gold == 100


def test_item_model():
    it = Item(item_id="sword_01", name="Short Sword", price=150)
    assert it.item_id == "sword_01"
    assert it.price == 150
