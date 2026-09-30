import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_and_fetch_transaction():
    payload = {
        "user_id": "USR-API-99",
        "amount": 120.0,
        "currency": "USD",
        "merchant": "Best Buy Electronics",
        "category": "electronics",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "location_name": "New York, USA",
        "ip_address": "198.51.100.55",
        "device_id": "desktop_chrome"
    }

    create_res = client.post("/api/transactions", json=payload)
    assert create_res.status_code == 200
    created = create_res.json()
    txn_id = created["transaction_id"]
    assert txn_id.startswith("TXN-")
    assert created["amount"] == 120.0

    # Fetch transaction by ID
    get_res = client.get(f"/api/transactions/{txn_id}")
    assert get_res.status_code == 200
    assert get_res.json()["transaction_id"] == txn_id


def test_review_transaction_workflow():
    payload = {
        "user_id": "USR-REV-1",
        "amount": 8000.0,
        "currency": "USD",
        "merchant": "Offshore Casino",
        "category": "online_gambling",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "location_name": "New York, USA",
        "ip_address": "185.220.101.5",
        "device_id": "proxy_browser"
    }
    create_res = client.post("/api/transactions", json=payload)
    assert create_res.status_code == 200
    txn_id = create_res.json()["transaction_id"]

    # Submit review action
    review_payload = {
        "status": "CONFIRMED_FRAUD",
        "reviewer": "Officer Alex Parker",
        "notes": "Confirmed stolen card credentials used in gambling site."
    }
    rev_res = client.post(f"/api/transactions/{txn_id}/review", json=review_payload)
    assert rev_res.status_code == 200
    updated = rev_res.json()
    assert updated["status"] == "CONFIRMED_FRAUD"
    assert updated["reviewed_by"] == "Officer Alex Parker"
    assert len(updated["audit_logs"]) >= 1


def test_transactions_filtering_and_search():
    # Filter by flagged
    flagged_res = client.get("/api/transactions?flagged_only=true")
    assert flagged_res.status_code == 200
    for txn in flagged_res.json():
        assert txn["status"] in ["FLAGGED", "UNDER_REVIEW", "CONFIRMED_FRAUD"]

    # Search query
    search_res = client.get("/api/transactions?search=electronics")
    assert search_res.status_code == 200
    assert isinstance(search_res.json(), list)


def test_rule_toggle_and_config_update():
    # 1. Toggle rule
    toggle_res = client.post("/api/rules/transaction_velocity/toggle")
    assert toggle_res.status_code == 200
    data = toggle_res.json()
    initial_state = data["enabled"]

    # Toggle back to restore
    restore_res = client.post("/api/rules/transaction_velocity/toggle")
    assert restore_res.status_code == 200
    assert restore_res.json()["enabled"] == (not initial_state)

    # 2. Update config parameters
    config_payload = {
        "weight": 1.2,
        "parameters": {"short_window_limit": 4}
    }
    config_res = client.post("/api/rules/transaction_velocity/config", json=config_payload)
    assert config_res.status_code == 200
    assert config_res.json()["weight"] == 1.2
    assert config_res.json()["parameters"]["short_window_limit"] == 4


def test_analytics_and_notifications_endpoints():
    stats_res = client.get("/api/analytics")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "total_transactions" in stats
    assert "flagged_count" in stats
    assert "rules_trigger_stats" in stats

    notif_res = client.get("/api/notifications")
    assert notif_res.status_code == 200
    assert isinstance(notif_res.json(), list)
