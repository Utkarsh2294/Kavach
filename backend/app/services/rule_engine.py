from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime

@dataclass
class RuleResult:
    passed: bool
    denied_by: Optional[Any] = None  # The Policy object that denied
    evaluation_trace: list[dict] = field(default_factory=list)

def evaluate_condition(condition: dict, transaction: dict) -> bool:
    """
    Evaluate a single condition against a transaction.
    
    Supports:
    - Simple: {"field": "amount", "op": "<=", "value": 500}
    - Compound: {"all": [...conditions]} or {"any": [...conditions]}
    """
    # Handle compound conditions
    if 'all' in condition:
        return all(evaluate_condition(c, transaction) for c in condition['all'])
    if 'any' in condition:
        return any(evaluate_condition(c, transaction) for c in condition['any'])
    
    # Simple condition
    field_name = condition['field']
    op = condition['op']
    expected = condition['value']
    
    # Get the actual value from the transaction dict
    actual = transaction.get(field_name)
    if actual is None:
        return False  # Missing field fails the condition
    
    # Evaluate the operator
    if op == '==':
        return actual == expected
    elif op == '!=':
        return actual != expected
    elif op == '<':
        return float(actual) < float(expected)
    elif op == '>':
        return float(actual) > float(expected)
    elif op == '<=':
        return float(actual) <= float(expected)
    elif op == '>=':
        return float(actual) >= float(expected)
    elif op == 'in':
        return actual in expected
    elif op == 'not_in':
        return actual not in expected
    else:
        raise ValueError(f"Unknown operator: {op}")

def evaluate_rules(transaction: dict, policies: list) -> RuleResult:
    """
    Evaluate all active policies against a transaction.
    
    Deny-by-default: every ACTIVE policy, sorted by priority ascending,
    is a condition the transaction must satisfy. First failure -> immediate deny.
    
    Args:
        transaction: dict with keys matching supported fields:
            - amount (float)
            - merchant_category (str)
            - delegation_depth (int)
            - agent_type (str)
            - time_of_day_hour (int, 0-23)
        policies: list of Policy ORM objects with .rule_json, .priority, .active, .name, .id
    
    Returns:
        RuleResult with passed, denied_by, and evaluation_trace
    """
    trace = []
    
    # Sort by priority ascending (lower number = higher priority = checked first)
    sorted_policies = sorted(
        [p for p in policies if p.active],
        key=lambda p: p.priority
    )
    
    for policy in sorted_policies:
        condition = policy.rule_json
        satisfied = evaluate_condition(condition, transaction)
        
        trace_entry = {
            'policy_id': str(policy.id),
            'policy_name': policy.name,
            'priority': policy.priority,
            'condition': condition,
            'satisfied': satisfied,
        }
        trace.append(trace_entry)
        
        if not satisfied:
            return RuleResult(
                passed=False,
                denied_by=policy,
                evaluation_trace=trace,
            )
    
    return RuleResult(
        passed=True,
        denied_by=None,
        evaluation_trace=trace,
    )
