from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import pytest
from app.engine.base import BaseRule, RuleResult
from app.engine.registry import register_rule, rule_registry
from app.engine.evaluator import fraud_engine


def test_custom_rule_plugged_without_modifying_core_engine():
    """
    Demonstrates the Open-Closed Principle requirement:
    New rules are added by extending BaseRule and registering with rule_registry,
    without touching RuleEngine or core evaluator logic.
    """
    # 1. Define a brand-new custom fraud rule at runtime
    @register_rule
    class DeviceIpMismatchRule(BaseRule):
        rule_id = "device_ip_mismatch_test"
        rule_name = "Device IP Mismatch Test"
        description = "Flags transactions using unexpected Tor or proxy devices"
        enabled = True
        weight = 1.0
        parameters = {"suspicious_device": "tor_browser_test"}

        def evaluate(
            self,
            transaction: Dict[str, Any],
            user_history: List[Dict[str, Any]],
            system_context: Optional[Dict[str, Any]] = None
        ) -> RuleResult:
            if transaction.get("device_id") == self.parameters["suspicious_device"]:
                return RuleResult(
                    is_flagged=True,
                    risk_score=85.0,
                    severity="HIGH",
                    reason="Transaction originated from monitored Tor gateway.",
                    metadata={"device": transaction.get("device_id")}
                )
            return RuleResult(
                is_flagged=False,
                risk_score=0.0,
                severity="LOW",
                reason="Standard verified device signature."
            )

    # 2. Verify registry has the new rule
    registered = rule_registry.get_rule("device_ip_mismatch_test")
    assert registered is not None
    assert registered.rule_name == "Device IP Mismatch Test"

    # 3. Verify core fraud_engine evaluates the new rule automatically
    txn_benign = {
        "transaction_id": "TXN-TEST-1",
        "user_id": "USR-TEST",
        "amount": 20.0,
        "device_id": "trusted_chrome",
        "timestamp": datetime.now(timezone.utc)
    }
    report_benign = fraud_engine.evaluate_transaction(txn_benign, user_history=[])
    rule_evals = {r.rule_id: r for r in report_benign.rule_evaluations}
    assert "device_ip_mismatch_test" in rule_evals
    assert not rule_evals["device_ip_mismatch_test"].is_flagged

    txn_suspicious = {
        "transaction_id": "TXN-TEST-2",
        "user_id": "USR-TEST",
        "amount": 20.0,
        "device_id": "tor_browser_test",
        "timestamp": datetime.now(timezone.utc)
    }
    report_suspicious = fraud_engine.evaluate_transaction(txn_suspicious, user_history=[])
    rule_evals_suspicious = {r.rule_id: r for r in report_suspicious.rule_evaluations}
    assert "device_ip_mismatch_test" in rule_evals_suspicious
    assert rule_evals_suspicious["device_ip_mismatch_test"].is_flagged
    assert report_suspicious.risk_score >= 85.0
    assert report_suspicious.is_high_risk

    # 4. Verify rule can be disabled dynamically via registry
    rule_registry.update_rule("device_ip_mismatch_test", enabled=False)
    report_disabled = fraud_engine.evaluate_transaction(txn_suspicious, user_history=[])
    rule_evals_disabled = {r.rule_id: r for r in report_disabled.rule_evaluations}
    assert "device_ip_mismatch_test" not in rule_evals_disabled

    # Clean up test rule
    if "device_ip_mismatch_test" in rule_registry._rules:
        del rule_registry._rules["device_ip_mismatch_test"]
