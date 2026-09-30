import importlib
import os
import pkgutil
import logging
from typing import Dict, Type, List, Optional
from app.engine.base import BaseRule

logger = logging.getLogger(__name__)

class RuleRegistry:
    """
    Singleton Registry that holds all available fraud detection rules.
    Allows registering rules declaratively or dynamically discovering them.
    Enables new rules to be added without touching the core engine.
    """
    _instance: Optional["RuleRegistry"] = None
    _rules: Dict[str, BaseRule] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RuleRegistry, cls).__new__(cls)
            cls._instance._rules = {}
        return cls._instance

    def register(self, rule_instance_or_cls):
        if isinstance(rule_instance_or_cls, type) and issubclass(rule_instance_or_cls, BaseRule):
            instance = rule_instance_or_cls()
        elif isinstance(rule_instance_or_cls, BaseRule):
            instance = rule_instance_or_cls
        else:
            raise ValueError(f"Rule must inherit from BaseRule, got {type(rule_instance_or_cls)}")

        self._rules[instance.rule_id] = instance
        logger.info(f"Registered fraud rule: [{instance.rule_id}] {instance.rule_name}")
        return rule_instance_or_cls

    def get_rule(self, rule_id: str) -> Optional[BaseRule]:
        return self._rules.get(rule_id)

    def get_all_rules(self) -> List[BaseRule]:
        return list(self._rules.values())

    def get_active_rules(self) -> List[BaseRule]:
        return [r for r in self._rules.values() if r.enabled]

    def update_rule(self, rule_id: str, enabled: Optional[bool] = None, weight: Optional[float] = None, parameters: Optional[dict] = None) -> Optional[BaseRule]:
        rule = self.get_rule(rule_id)
        if rule:
            rule.update_config(enabled=enabled, weight=weight, parameters=parameters)
            return rule
        return None

    def auto_discover_rules(self, package_name: str = "app.engine.rules"):
        """
        Dynamically imports all modules inside the specified rules package directory.
        Any module decorated with @register_rule or defining a BaseRule subclass will be loaded.
        """
        try:
            package = importlib.import_module(package_name)
            for _, module_name, _ in pkgutil.iter_modules(package.__path__):
                full_module_name = f"{package_name}.{module_name}"
                importlib.import_module(full_module_name)
                logger.info(f"Discovered and imported rule module: {full_module_name}")
        except Exception as e:
            logger.error(f"Error auto-discovering rules from {package_name}: {e}")

rule_registry = RuleRegistry()

def register_rule(cls_or_instance):
    """
    Decorator to register a fraud rule with the RuleRegistry.
    Example:
        @register_rule
        class MyCustomRule(BaseRule):
            ...
    """
    return rule_registry.register(cls_or_instance)
