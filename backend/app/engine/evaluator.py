from typing import Dict, Any, List
from app.engine.registry import rule_registry
from app.engine.base import RuleResult
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class EvaluationReport:
    def __init__(
        self,
        risk_score: float,
        risk_level: str,
        status: str,
        is_high_risk: bool,
        rule_evaluations: List[RuleResult]
    ):
        self.risk_score = risk_score
        self.risk_level = risk_level
        self.status = status
        self.is_high_risk = is_high_risk
        self.rule_evaluations = rule_evaluations
        self.flagged_count = sum(1 for r in rule_evaluations if r.is_flagged)

class RuleEngine:
    """
    Core Fraud Evaluation Engine.
    Executes all active rules registered in the RuleRegistry.
    The core engine remains completely closed for modification, while
    allowing infinite new rules via the RuleRegistry.
    """
    def __init__(self):
        # Auto discover any rules in app.engine.rules
        rule_registry.auto_discover_rules()

    def evaluate_transaction(
        self,
        transaction: Dict[str, Any],
        user_history: List[Dict[str, Any]],
        system_context: Dict[str, Any] = None
    ) -> EvaluationReport:
        active_rules = rule_registry.get_active_rules()
        logger.info(f"Evaluating transaction {transaction.get('transaction_id')} across {len(active_rules)} active rules")

        results: List[RuleResult] = []
        flagged_scores: List[float] = []

        for rule in active_rules:
            try:
                res = rule.evaluate(transaction, user_history, system_context)
                res.rule_id = rule.rule_id
                res.rule_name = rule.rule_name
                results.append(res)
                if res.is_flagged:
                    # Apply rule weight to score
                    weighted_score = res.risk_score * rule.weight
                    flagged_scores.append(weighted_score)
            except Exception as e:
                logger.error(f"Error evaluating rule [{rule.rule_id}]: {e}", exc_info=True)
                results.append(RuleResult(
                    rule_id=rule.rule_id,
                    rule_name=rule.rule_name,
                    is_flagged=False,
                    risk_score=0.0,
                    severity="LOW",
                    reason=f"Evaluation error on rule {rule.rule_id}: {str(e)}",
                    metadata={"error": str(e)}
                ))

        # Composite Risk Score Calculation
        if not flagged_scores:
            overall_score = 0.0
        else:
            flagged_scores.sort(reverse=True)
            max_score = flagged_scores[0]
            # Compound risk if multiple rules trigger
            additional_compound = sum(s * 0.25 for s in flagged_scores[1:])
            overall_score = min(100.0, max_score + additional_compound)

        overall_score = round(overall_score, 1)

        # Determine Risk Level
        if overall_score >= settings.CRITICAL_RISK_THRESHOLD:
            risk_level = "CRITICAL"
        elif overall_score >= settings.HIGH_RISK_THRESHOLD:
            risk_level = "HIGH"
        elif overall_score >= 30.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Determine Initial Status
        # If any rule flags or risk score >= 30, it requires review
        if overall_score >= 30.0 or any(r.is_flagged for r in results):
            status = "FLAGGED"
        else:
            status = "CLEARED"

        is_high_risk = (overall_score >= settings.HIGH_RISK_THRESHOLD) or (risk_level in ["HIGH", "CRITICAL"])

        return EvaluationReport(
            risk_score=overall_score,
            risk_level=risk_level,
            status=status,
            is_high_risk=is_high_risk,
            rule_evaluations=results
        )

# Global singleton
fraud_engine = RuleEngine()
