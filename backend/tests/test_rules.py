from datetime import datetime, timezone, timedelta
import pytest
from app.engine.rules.velocity import VelocityRule
from app.engine.rules.unusual_amount import UnusualAmountRule
from app.engine.rules.impossible_travel import ImpossibleTravelRule, haversine_distance_km
from app.engine.rules.merchant_risk import MerchantRiskRule


class TestImpossibleTravelRule:
    def setup_method(self):
        self.rule = ImpossibleTravelRule()

    def test_haversine_distance(self):
        # NYC to London is approximately 5,570 km
        dist = haversine_distance_km(40.7128, -74.0060, 51.5074, -0.1278)
        assert 5500 < dist < 5700

        # Same location should be 0 km
        assert haversine_distance_km(40.0, -74.0, 40.0, -74.0) == 0.0

    def test_first_transaction_passes_as_baseline(self):
        txn = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "location_name": "New York, USA",
            "timestamp": datetime.now(timezone.utc)
        }
        res = self.rule.evaluate(txn, user_history=[])
        assert not res.is_flagged
        assert res.risk_score == 0.0

    def test_missing_coordinates_handled_gracefully(self):
        txn = {
            "latitude": None,
            "longitude": None,
            "timestamp": datetime.now(timezone.utc)
        }
        res = self.rule.evaluate(txn, user_history=[])
        assert not res.is_flagged
        assert "no geographical coordinates" in res.reason

    def test_normal_driving_speed_not_flagged(self):
        now = datetime.now(timezone.utc)
        history = [{
            "latitude": 40.7128,
            "longitude": -74.0060,
            "location_name": "New York, USA",
            "timestamp": now - timedelta(hours=2)
        }]
        # Philadelphia is ~130 km from NYC (~65 km/h driving speed)
        txn = {
            "latitude": 39.9526,
            "longitude": -75.1652,
            "location_name": "Philadelphia, USA",
            "timestamp": now
        }
        res = self.rule.evaluate(txn, history)
        assert not res.is_flagged
        assert res.risk_score == 0.0

    def test_instant_teleportation_flagged_critical(self):
        now = datetime.now(timezone.utc)
        # London to Tokyo (~9,560 km) in 10 minutes
        history = [{
            "latitude": 51.5074,
            "longitude": -0.1278,
            "location_name": "London, UK",
            "timestamp": now - timedelta(minutes=10)
        }]
        txn = {
            "latitude": 35.6762,
            "longitude": 139.6503,
            "location_name": "Tokyo, Japan",
            "timestamp": now
        }
        res = self.rule.evaluate(txn, history)
        assert res.is_flagged
        assert res.severity == "CRITICAL"
        assert res.risk_score >= 90.0

    def test_commercial_airline_speed_exceeded_flagged_high(self):
        now = datetime.now(timezone.utc)
        # New York to Los Angeles (~3,940 km) in 2 hours (~1,970 km/h - Mach 1.6 supersonic)
        history = [{
            "latitude": 40.7128,
            "longitude": -74.0060,
            "location_name": "New York, USA",
            "timestamp": now - timedelta(hours=2)
        }]
        txn = {
            "latitude": 34.0522,
            "longitude": -118.2437,
            "location_name": "Los Angeles, USA",
            "timestamp": now
        }
        res = self.rule.evaluate(txn, history)
        assert res.is_flagged
        assert res.severity in ["HIGH", "CRITICAL"]
        assert res.risk_score >= 80.0


class TestVelocityRule:
    def setup_method(self):
        self.rule = VelocityRule()

    def test_normal_velocity_not_flagged(self):
        now = datetime.now(timezone.utc)
        history = [
            {"timestamp": now - timedelta(days=2)},
            {"timestamp": now - timedelta(days=1)}
        ]
        txn = {"timestamp": now}
        res = self.rule.evaluate(txn, history)
        assert not res.is_flagged
        assert res.risk_score == 0.0

    def test_short_window_velocity_spike_flagged_high(self):
        now = datetime.now(timezone.utc)
        # 3 transactions in past 3 minutes + current = 4 txs in 5m
        history = [
            {"timestamp": now - timedelta(minutes=1)},
            {"timestamp": now - timedelta(minutes=2)},
            {"timestamp": now - timedelta(minutes=3)},
        ]
        txn = {"timestamp": now}
        res = self.rule.evaluate(txn, history)
        assert res.is_flagged
        assert res.severity in ["HIGH", "CRITICAL"]
        assert res.risk_score >= 50.0

    def test_critical_burst_velocity_flagged_critical(self):
        now = datetime.now(timezone.utc)
        # 5 transactions in past 2 minutes + current = 6 txs in 5m
        history = [
            {"timestamp": now - timedelta(seconds=20)},
            {"timestamp": now - timedelta(seconds=40)},
            {"timestamp": now - timedelta(seconds=60)},
            {"timestamp": now - timedelta(seconds=80)},
            {"timestamp": now - timedelta(seconds=100)},
        ]
        txn = {"timestamp": now}
        res = self.rule.evaluate(txn, history)
        assert res.is_flagged
        assert res.severity == "CRITICAL"
        assert res.risk_score >= 80.0


class TestUnusualAmountRule:
    def setup_method(self):
        self.rule = UnusualAmountRule()

    def test_normal_amount_not_flagged(self):
        history = [{"amount": 45.0}, {"amount": 50.0}, {"amount": 55.0}]
        txn = {"amount": 52.0, "currency": "USD"}
        res = self.rule.evaluate(txn, history)
        assert not res.is_flagged
        assert res.risk_score == 0.0

    def test_multiplier_spike_flagged(self):
        # Average is $50. Transaction is $300 (6x multiplier)
        history = [{"amount": 50.0}, {"amount": 50.0}, {"amount": 50.0}]
        txn = {"amount": 300.0, "currency": "USD"}
        res = self.rule.evaluate(txn, history)
        assert res.is_flagged
        assert res.severity in ["HIGH", "CRITICAL"]

    def test_absolute_critical_amount_flagged_critical(self):
        history = [{"amount": 100.0}, {"amount": 120.0}]
        txn = {"amount": 25000.0, "currency": "USD"}
        res = self.rule.evaluate(txn, history)
        assert res.is_flagged
        assert res.severity == "CRITICAL"
        assert res.risk_score >= 90.0

    def test_no_history_moderate_amount_not_flagged(self):
        txn = {"amount": 150.0, "currency": "USD"}
        res = self.rule.evaluate(txn, user_history=[])
        assert not res.is_flagged


class TestMerchantRiskRule:
    def setup_method(self):
        self.rule = MerchantRiskRule()

    def test_normal_merchant_not_flagged(self):
        txn = {"merchant": "Target Retail", "category": "groceries"}
        res = self.rule.evaluate(txn, [])
        assert not res.is_flagged

    def test_high_risk_category_flagged(self):
        txn = {"merchant": "Local Trader", "category": "crypto_exchange"}
        res = self.rule.evaluate(txn, [])
        assert res.is_flagged
        assert res.severity == "MEDIUM"

    def test_suspicious_keyword_flagged(self):
        txn = {"merchant": "Atlantic Poker Lounge", "category": "entertainment"}
        res = self.rule.evaluate(txn, [])
        assert res.is_flagged
        assert res.severity == "MEDIUM"

    def test_both_category_and_keyword_flagged_high(self):
        txn = {"merchant": "Binance Crypto Offshore", "category": "crypto_exchange"}
        res = self.rule.evaluate(txn, [])
        assert res.is_flagged
        assert res.severity == "HIGH"
        assert res.risk_score >= 70.0
