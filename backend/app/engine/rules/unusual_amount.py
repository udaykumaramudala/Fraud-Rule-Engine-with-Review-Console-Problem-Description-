import math
from typing import Dict, Any, List, Optional
from app.engine.base import BaseRule, RuleResult
from app.engine.registry import register_rule

@register_rule
class UnusualAmountRule(BaseRule):
    rule_id = "unusual_transaction_amount"
    rule_name = "Unusual Transaction Amount"
    description = "Detects transactions with amounts substantially exceeding typical spending patterns or absolute risk thresholds"
    enabled = True
    weight = 1.0
    parameters = {
        "absolute_medium_threshold": 3000.0,
        "absolute_high_threshold": 7500.0,
        "absolute_critical_threshold": 15000.0,
        "multiplier_warning_threshold": 3.0,
        "multiplier_critical_threshold": 5.0,
        "min_history_count_for_stats": 2
    }

    def evaluate(
        self,
        transaction: Dict[str, Any],
        user_history: List[Dict[str, Any]],
        system_context: Optional[Dict[str, Any]] = None
    ) -> RuleResult:
        amount = float(transaction.get("amount", 0.0))
        currency = transaction.get("currency", "USD")

        # Collect past amounts
        past_amounts = [float(tx.get("amount", 0.0)) for tx in user_history if tx.get("amount")]

        avg_amount = sum(past_amounts) / len(past_amounts) if past_amounts else amount
        multiplier = (amount / avg_amount) if avg_amount > 0 else 1.0

        # Calculate standard deviation if sufficient history
        std_dev = 0.0
        z_score = 0.0
        if len(past_amounts) >= self.parameters["min_history_count_for_stats"]:
            variance = sum((x - avg_amount) ** 2 for x in past_amounts) / len(past_amounts)
            std_dev = math.sqrt(variance)
            if std_dev > 0:
                z_score = (amount - avg_amount) / std_dev

        metadata = {
            "current_amount": round(amount, 2),
            "currency": currency,
            "historical_avg": round(avg_amount, 2),
            "historical_count": len(past_amounts),
            "amount_multiplier": round(multiplier, 2),
            "z_score": round(z_score, 2),
            "std_dev": round(std_dev, 2)
        }

        # Check conditions
        is_critical_abs = amount >= self.parameters["absolute_critical_threshold"]
        is_high_abs = amount >= self.parameters["absolute_high_threshold"]
        is_medium_abs = amount >= self.parameters["absolute_medium_threshold"]

        has_history = len(past_amounts) >= self.parameters["min_history_count_for_stats"]
        is_critical_multiplier = has_history and (multiplier >= self.parameters["multiplier_critical_threshold"])
        is_warning_multiplier = has_history and (multiplier >= self.parameters["multiplier_warning_threshold"])

        # Severe: Both absolute high and severe historical deviation, or massive absolute amount
        if is_critical_abs or (is_high_abs and is_critical_multiplier):
            return RuleResult(
                is_flagged=True,
                risk_score=90.0,
                severity="CRITICAL",
                reason=(
                    f"Severe amount anomaly: {currency} {amount:,.2f} is {multiplier:.1f}x higher than user's "
                    f"average ({currency} {avg_amount:,.2f}) and exceeds critical threshold ({currency} {self.parameters['absolute_critical_threshold']:,.2f})."
                ),
                metadata=metadata
            )

        if is_high_abs or is_critical_multiplier or (z_score >= 3.5):
            return RuleResult(
                is_flagged=True,
                risk_score=70.0,
                severity="HIGH",
                reason=(
                    f"High transaction amount: {currency} {amount:,.2f} is {multiplier:.1f}x typical spend "
                    f"({currency} {avg_amount:,.2f}) across {len(past_amounts)} prior transactions."
                ),
                metadata=metadata
            )

        if is_medium_abs or is_warning_multiplier or (z_score >= 2.5):
            return RuleResult(
                is_flagged=True,
                risk_score=45.0,
                severity="MEDIUM",
                reason=(
                    f"Elevated amount: {currency} {amount:,.2f} noticeably exceeds typical baseline "
                    f"({currency} {avg_amount:,.2f}, multiplier {multiplier:.1f}x)."
                ),
                metadata=metadata
            )

        return RuleResult(
            is_flagged=False,
            risk_score=0.0,
            severity="LOW",
            reason=f"Amount {currency} {amount:,.2f} is consistent with user's spending profile (avg: {currency} {avg_amount:,.2f}).",
            metadata=metadata
        )
