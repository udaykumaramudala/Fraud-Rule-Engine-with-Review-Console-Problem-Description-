from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import json

@dataclass
class RuleResult:
    is_flagged: bool
    risk_score: float
    severity: str # LOW, MEDIUM, HIGH, CRITICAL
    reason: str
    rule_id: str = "unknown_rule"
    rule_name: str = "Unknown Rule"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "is_flagged": self.is_flagged,
            "risk_score": round(self.risk_score, 2),
            "severity": self.severity,
            "reason": self.reason,
            "metadata_json": json.dumps(self.metadata, default=str)
        }

class BaseRule(ABC):
    """
    Abstract Base Rule for the Fraud Rule Engine.
    All new rules inherit from this class and register with the RuleRegistry.
    This fulfills the Open-Closed Principle: Core engine evaluates rules dynamically
    without modification.
    """
    rule_id: str = "base_rule"
    rule_name: str = "Base Rule"
    description: str = "Base fraud detection rule"
    enabled: bool = True
    weight: float = 1.0
    parameters: Dict[str, Any] = {}

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)

    @abstractmethod
    def evaluate(
        self,
        transaction: Dict[str, Any],
        user_history: List[Dict[str, Any]],
        system_context: Optional[Dict[str, Any]] = None
    ) -> RuleResult:
        """
        Evaluate transaction against fraud risk criteria.
        :param transaction: Dictionary containing current transaction details.
        :param user_history: Chronological list of past transactions for this user.
        :param system_context: Optional additional context (e.g. global platform metrics).
        :return: RuleResult with is_flagged, risk_score, severity, reason, and metadata.
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "description": self.description,
            "enabled": self.enabled,
            "weight": self.weight,
            "parameters": self.parameters
        }

    def update_config(self, enabled: Optional[bool] = None, weight: Optional[float] = None, parameters: Optional[Dict[str, Any]] = None):
        if enabled is not None:
            self.enabled = enabled
        if weight is not None:
            self.weight = weight
        if parameters is not None:
            self.parameters.update(parameters)
