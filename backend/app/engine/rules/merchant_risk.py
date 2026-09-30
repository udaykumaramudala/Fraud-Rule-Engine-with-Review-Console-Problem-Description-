from typing import Dict, Any, List, Optional
from app.engine.base import BaseRule, RuleResult
from app.engine.registry import register_rule

@register_rule
class MerchantRiskRule(BaseRule):
    rule_id = "high_risk_merchant_category"
    rule_name = "High-Risk Merchant & Category"
    description = "Detects transactions associated with elevated risk categories, unregulated digital assets, or suspicious merchants"
    enabled = True
    weight = 0.8
    parameters = {
        "high_risk_categories": [
            "crypto_exchange",
            "online_gambling",
            "wire_transfer",
            "prepaid_giftcards",
            "adult_entertainment",
            "darkweb_services"
        ],
        "suspicious_keywords": [
            "crypto",
            "casino",
            "binance",
            "poker",
            "offshore",
            "anonymous",
            "escrow",
            "tumbler"
        ]
    }

    def evaluate(
        self,
        transaction: Dict[str, Any],
        user_history: List[Dict[str, Any]],
        system_context: Optional[Dict[str, Any]] = None
    ) -> RuleResult:
        category = str(transaction.get("category", "")).lower().strip()
        merchant = str(transaction.get("merchant", "")).lower().strip()

        matched_categories = [
            cat for cat in self.parameters.get("high_risk_categories", [])
            if cat in category
        ]

        matched_keywords = [
            kw for kw in self.parameters.get("suspicious_keywords", [])
            if kw in merchant
        ]

        metadata = {
            "category": transaction.get("category"),
            "merchant": transaction.get("merchant"),
            "matched_categories": matched_categories,
            "matched_keywords": matched_keywords
        }

        if matched_categories and matched_keywords:
            return RuleResult(
                is_flagged=True,
                risk_score=75.0,
                severity="HIGH",
                reason=f"High-risk merchant profile: Category '{category}' and merchant keyword matches [{', '.join(matched_keywords)}].",
                metadata=metadata
            )
        elif matched_categories:
            return RuleResult(
                is_flagged=True,
                risk_score=50.0,
                severity="MEDIUM",
                reason=f"Elevated risk sector: Transaction category '{category}' is classified as high-risk.",
                metadata=metadata
            )
        elif matched_keywords:
            return RuleResult(
                is_flagged=True,
                risk_score=40.0,
                severity="MEDIUM",
                reason=f"Merchant name flag: '{transaction.get('merchant')}' contains monitored keywords [{', '.join(matched_keywords)}].",
                metadata=metadata
            )

        return RuleResult(
            is_flagged=False,
            risk_score=0.0,
            severity="LOW",
            reason="Merchant and category are standard retail/service entities.",
            metadata=metadata
        )
