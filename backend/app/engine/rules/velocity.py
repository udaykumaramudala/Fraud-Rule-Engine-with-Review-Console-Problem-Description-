from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from app.engine.base import BaseRule, RuleResult
from app.engine.registry import register_rule

@register_rule
class VelocityRule(BaseRule):
    rule_id = "transaction_velocity"
    rule_name = "Transaction Velocity Spike"
    description = "Detects rapid burst of transactions from the same account within a short timeframe"
    enabled = True
    weight = 1.0
    parameters = {
        "short_window_minutes": 5,
        "short_window_limit": 3,
        "long_window_minutes": 60,
        "long_window_limit": 8,
        "critical_burst_limit": 5
    }

    def evaluate(
        self,
        transaction: Dict[str, Any],
        user_history: List[Dict[str, Any]],
        system_context: Optional[Dict[str, Any]] = None
    ) -> RuleResult:
        if not user_history:
            return RuleResult(
                is_flagged=False,
                risk_score=0.0,
                severity="LOW",
                reason="No prior transaction history found. Velocity normal.",
                metadata={"recent_tx_count_5m": 1, "recent_tx_count_60m": 1}
            )

        current_time = transaction.get("timestamp")
        if isinstance(current_time, str):
            current_time = datetime.fromisoformat(current_time.replace("Z", "+00:00"))
        if not current_time:
            current_time = datetime.now(timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        short_window = timedelta(minutes=self.parameters["short_window_minutes"])
        long_window = timedelta(minutes=self.parameters["long_window_minutes"])

        short_window_txs = []
        long_window_txs = []

        for tx in user_history:
            tx_time = tx.get("timestamp")
            if isinstance(tx_time, str):
                tx_time = datetime.fromisoformat(tx_time.replace("Z", "+00:00"))
            if tx_time:
                if tx_time.tzinfo is None:
                    tx_time = tx_time.replace(tzinfo=timezone.utc)
                diff = abs(current_time - tx_time)
                if diff <= short_window:
                    short_window_txs.append(tx)
                if diff <= long_window:
                    long_window_txs.append(tx)

        # Include current transaction in count
        short_count = len(short_window_txs) + 1
        long_count = len(long_window_txs) + 1

        metadata = {
            "short_window_minutes": self.parameters["short_window_minutes"],
            "short_window_count": short_count,
            "short_window_limit": self.parameters["short_window_limit"],
            "long_window_minutes": self.parameters["long_window_minutes"],
            "long_window_count": long_count,
            "long_window_limit": self.parameters["long_window_limit"],
        }

        # Check burst / critical velocity
        if short_count >= self.parameters["critical_burst_limit"]:
            score = min(95.0, 60.0 + (short_count - self.parameters["short_window_limit"]) * 10)
            return RuleResult(
                is_flagged=True,
                risk_score=score,
                severity="CRITICAL",
                reason=f"Extreme velocity burst: {short_count} transactions within {self.parameters['short_window_minutes']} minutes (burst threshold: {self.parameters['critical_burst_limit']}).",
                metadata=metadata
            )
        elif short_count >= self.parameters["short_window_limit"]:
            score = 50.0 + (short_count - self.parameters["short_window_limit"]) * 8
            return RuleResult(
                is_flagged=True,
                risk_score=min(80.0, score),
                severity="HIGH",
                reason=f"High transaction velocity: {short_count} transactions within {self.parameters['short_window_minutes']} minutes (limit: {self.parameters['short_window_limit']}).",
                metadata=metadata
            )
        elif long_count >= self.parameters["long_window_limit"]:
            return RuleResult(
                is_flagged=True,
                risk_score=40.0,
                severity="MEDIUM",
                reason=f"Elevated hourly activity: {long_count} transactions within {self.parameters['long_window_minutes']} minutes (limit: {self.parameters['long_window_limit']}).",
                metadata=metadata
            )

        return RuleResult(
            is_flagged=False,
            risk_score=0.0,
            severity="LOW",
            reason=f"Normal velocity ({short_count} txs in {self.parameters['short_window_minutes']}m, {long_count} txs in {self.parameters['long_window_minutes']}m).",
            metadata=metadata
        )
