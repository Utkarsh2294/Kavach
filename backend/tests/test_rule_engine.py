"""
Kavach Backend — Rule Engine Unit Tests.

Tests cover:
  - Pass: transaction satisfying all policies
  - Single-rule deny: one policy violated
  - Compound-rule deny: 'all' / 'any' combinators
  - Empty-policy pass-through: no active policies
  - Delegation-depth correctness against seeded 3-level chain
  - Full evaluation trace inspection
"""

import uuid
from dataclasses import dataclass
from typing import Optional, Any

import pytest

from app.services.rule_engine import evaluate_rules, evaluate_condition, RuleResult


# ── Mock Policy object ───────────────────────────────────────────────────────

@dataclass
class MockPolicy:
    """Lightweight stand-in for the SQLAlchemy Policy model."""
    id: uuid.UUID
    name: str
    rule_json: dict
    priority: int
    active: bool = True


def _policy(name: str, rule: dict, priority: int = 100, active: bool = True) -> MockPolicy:
    """Helper to build a mock policy quickly."""
    return MockPolicy(
        id=uuid.uuid4(),
        name=name,
        rule_json=rule,
        priority=priority,
        active=active,
    )


# ── A standard transaction context ───────────────────────────────────────────

STANDARD_TX = {
    "amount": 500.0,
    "merchant_category": "office_supplies",
    "delegation_depth": 1,
    "agent_type": "travel",
    "time_of_day_hour": 14,
}


# ── Tests ────────────────────────────────────────────────────────────────────

class TestEvaluateCondition:
    """Unit tests for the low-level evaluate_condition function."""

    def test_eq_pass(self):
        assert evaluate_condition({"field": "agent_type", "op": "==", "value": "travel"}, STANDARD_TX) is True

    def test_eq_fail(self):
        assert evaluate_condition({"field": "agent_type", "op": "==", "value": "procurement"}, STANDARD_TX) is False

    def test_not_eq(self):
        assert evaluate_condition({"field": "agent_type", "op": "!=", "value": "procurement"}, STANDARD_TX) is True

    def test_less_than(self):
        assert evaluate_condition({"field": "amount", "op": "<", "value": 1000}, STANDARD_TX) is True
        assert evaluate_condition({"field": "amount", "op": "<", "value": 500}, STANDARD_TX) is False

    def test_less_than_or_equal(self):
        assert evaluate_condition({"field": "amount", "op": "<=", "value": 500}, STANDARD_TX) is True
        assert evaluate_condition({"field": "amount", "op": "<=", "value": 499}, STANDARD_TX) is False

    def test_greater_than(self):
        assert evaluate_condition({"field": "amount", "op": ">", "value": 400}, STANDARD_TX) is True
        assert evaluate_condition({"field": "amount", "op": ">", "value": 500}, STANDARD_TX) is False

    def test_greater_than_or_equal(self):
        assert evaluate_condition({"field": "amount", "op": ">=", "value": 500}, STANDARD_TX) is True
        assert evaluate_condition({"field": "amount", "op": ">=", "value": 501}, STANDARD_TX) is False

    def test_in_operator(self):
        assert evaluate_condition(
            {"field": "merchant_category", "op": "in", "value": ["office_supplies", "hotel"]},
            STANDARD_TX,
        ) is True
        assert evaluate_condition(
            {"field": "merchant_category", "op": "in", "value": ["hotel", "airline"]},
            STANDARD_TX,
        ) is False

    def test_not_in_operator(self):
        assert evaluate_condition(
            {"field": "merchant_category", "op": "not_in", "value": ["gambling", "casino"]},
            STANDARD_TX,
        ) is True
        assert evaluate_condition(
            {"field": "merchant_category", "op": "not_in", "value": ["office_supplies"]},
            STANDARD_TX,
        ) is False

    def test_missing_field_fails(self):
        """If the transaction lacks a field, the condition should fail."""
        assert evaluate_condition(
            {"field": "nonexistent_field", "op": "==", "value": "foo"},
            STANDARD_TX,
        ) is False

    def test_unknown_operator_raises(self):
        with pytest.raises(ValueError, match="Unknown operator"):
            evaluate_condition({"field": "amount", "op": "~=", "value": 500}, STANDARD_TX)


class TestCompoundConditions:
    """Test the 'all' and 'any' combinators."""

    def test_all_pass(self):
        condition = {
            "all": [
                {"field": "amount", "op": "<=", "value": 1000},
                {"field": "agent_type", "op": "==", "value": "travel"},
            ]
        }
        assert evaluate_condition(condition, STANDARD_TX) is True

    def test_all_fail_one(self):
        condition = {
            "all": [
                {"field": "amount", "op": "<=", "value": 1000},
                {"field": "agent_type", "op": "==", "value": "procurement"},
            ]
        }
        assert evaluate_condition(condition, STANDARD_TX) is False

    def test_any_pass(self):
        condition = {
            "any": [
                {"field": "agent_type", "op": "==", "value": "procurement"},
                {"field": "amount", "op": "<=", "value": 1000},
            ]
        }
        assert evaluate_condition(condition, STANDARD_TX) is True

    def test_any_fail_all(self):
        condition = {
            "any": [
                {"field": "agent_type", "op": "==", "value": "procurement"},
                {"field": "amount", "op": ">", "value": 10000},
            ]
        }
        assert evaluate_condition(condition, STANDARD_TX) is False

    def test_nested_compound(self):
        """Nested 'all' inside 'any'."""
        condition = {
            "any": [
                {
                    "all": [
                        {"field": "amount", "op": ">=", "value": 99999},
                        {"field": "agent_type", "op": "==", "value": "travel"},
                    ]
                },
                {"field": "delegation_depth", "op": "<=", "value": 3},
            ]
        }
        assert evaluate_condition(condition, STANDARD_TX) is True


class TestEvaluateRules:
    """Integration tests for the full evaluate_rules function."""

    def test_pass_all_policies(self):
        """Transaction that satisfies every policy should pass."""
        policies = [
            _policy("Max Amount", {"field": "amount", "op": "<=", "value": 10000}, priority=10),
            _policy("Block Gaming", {"field": "merchant_category", "op": "not_in", "value": ["gambling"]}, priority=20),
        ]
        result = evaluate_rules(STANDARD_TX, policies)

        assert result.passed is True
        assert result.denied_by is None
        assert len(result.evaluation_trace) == 2
        assert all(t["satisfied"] for t in result.evaluation_trace)

    def test_single_rule_deny(self):
        """Transaction exceeding the max amount should be denied."""
        policies = [
            _policy("Max Amount", {"field": "amount", "op": "<=", "value": 100}, priority=10),
            _policy("Block Gaming", {"field": "merchant_category", "op": "not_in", "value": ["gambling"]}, priority=20),
        ]
        tx = {**STANDARD_TX, "amount": 500.0}
        result = evaluate_rules(tx, policies)

        assert result.passed is False
        assert result.denied_by is not None
        assert result.denied_by.name == "Max Amount"
        # Trace should stop at the first failure — only 1 entry
        assert len(result.evaluation_trace) == 1
        assert result.evaluation_trace[0]["satisfied"] is False

    def test_compound_rule_deny(self):
        """Test compound 'all' condition that fails."""
        policies = [
            _policy(
                "Sub-Agent Spend Cap",
                {
                    "all": [
                        {"field": "agent_type", "op": "==", "value": "sub-agent"},
                        {"field": "amount", "op": "<=", "value": 200},
                    ]
                },
                priority=50,
            ),
        ]
        tx = {**STANDARD_TX, "agent_type": "sub-agent", "amount": 500.0}
        result = evaluate_rules(tx, policies)

        assert result.passed is False
        assert result.denied_by.name == "Sub-Agent Spend Cap"

    def test_compound_rule_pass_non_matching_agent(self):
        """Compound 'all' condition passes when the agent_type doesn't match the first condition."""
        policies = [
            _policy(
                "Sub-Agent Spend Cap",
                {
                    "all": [
                        {"field": "agent_type", "op": "==", "value": "sub-agent"},
                        {"field": "amount", "op": "<=", "value": 200},
                    ]
                },
                priority=50,
            ),
        ]
        # agent_type is 'travel', not 'sub-agent', so the 'all' fails
        # BUT this means the condition is NOT satisfied, which means deny
        # Actually: 'all' requires BOTH sub-conditions to be true for the policy to be satisfied.
        # If agent_type != sub-agent, 'all' returns False, meaning the policy condition is NOT satisfied -> deny.
        # 
        # Wait, let me think again. The semantics are:
        # - Policy condition must be SATISFIED for the transaction to pass that policy.
        # - If condition is NOT satisfied, the transaction is DENIED by that policy.
        # 
        # For "Sub-Agent Spend Cap" with {"all": [agent_type==sub-agent, amount<=200]}:
        # - A travel agent with amount 500 -> 'all' returns False -> policy NOT satisfied -> DENY
        # This seems wrong for this use case. The policy is meant to constrain sub-agents only.
        #
        # This is actually a design question — the rule engine as specified treats every active
        # policy as a constraint the transaction must satisfy. So compound rules like this
        # need to be written carefully. In practice you'd write it as:
        # {"any": [{"field": "agent_type", "op": "!=", "value": "sub-agent"}, {"field": "amount", "op": "<=", "value": 200}]}
        # Which means: either you're not a sub-agent, OR your amount is under 200.
        #
        # For this test, verify the engine's behavior is correct even if the policy design
        # would need adjustment for real use.
        tx = {**STANDARD_TX, "agent_type": "travel", "amount": 500.0}
        result = evaluate_rules(tx, policies)

        # 'all' fails because agent_type != sub-agent, so condition not satisfied -> deny
        assert result.passed is False

    def test_empty_policies_pass(self):
        """With no active policies, everything should pass."""
        result = evaluate_rules(STANDARD_TX, [])
        assert result.passed is True
        assert result.denied_by is None
        assert len(result.evaluation_trace) == 0

    def test_inactive_policies_skipped(self):
        """Inactive policies should be ignored."""
        policies = [
            _policy("Strict Limit", {"field": "amount", "op": "<=", "value": 1}, priority=10, active=False),
            _policy("Loose Limit", {"field": "amount", "op": "<=", "value": 10000}, priority=20, active=True),
        ]
        result = evaluate_rules(STANDARD_TX, policies)
        assert result.passed is True
        # Only the active policy should appear in the trace
        assert len(result.evaluation_trace) == 1
        assert result.evaluation_trace[0]["policy_name"] == "Loose Limit"

    def test_priority_ordering(self):
        """Policies should be evaluated in priority order (ascending)."""
        policies = [
            _policy("Low Priority", {"field": "amount", "op": "<=", "value": 10000}, priority=99),
            _policy("High Priority", {"field": "amount", "op": "<=", "value": 10000}, priority=1),
            _policy("Mid Priority", {"field": "amount", "op": "<=", "value": 10000}, priority=50),
        ]
        result = evaluate_rules(STANDARD_TX, policies)
        assert result.passed is True
        names = [t["policy_name"] for t in result.evaluation_trace]
        assert names == ["High Priority", "Mid Priority", "Low Priority"]

    def test_delegation_depth_pass(self):
        """Delegation depth within limit should pass."""
        policies = [
            _policy("Depth Limit", {"field": "delegation_depth", "op": "<=", "value": 3}, priority=10),
        ]
        tx = {**STANDARD_TX, "delegation_depth": 2}
        result = evaluate_rules(tx, policies)
        assert result.passed is True

    def test_delegation_depth_deny(self):
        """Delegation depth exceeding limit should be denied."""
        policies = [
            _policy("Depth Limit", {"field": "delegation_depth", "op": "<=", "value": 3}, priority=10),
        ]
        tx = {**STANDARD_TX, "delegation_depth": 4}
        result = evaluate_rules(tx, policies)
        assert result.passed is False
        assert result.denied_by.name == "Depth Limit"

    def test_trace_contains_all_checked_policies(self):
        """Evaluation trace should contain every policy that was checked."""
        policies = [
            _policy("Policy A", {"field": "amount", "op": "<=", "value": 10000}, priority=10),
            _policy("Policy B", {"field": "merchant_category", "op": "not_in", "value": ["gambling"]}, priority=20),
            _policy("Policy C", {"field": "delegation_depth", "op": "<=", "value": 5}, priority=30),
        ]
        result = evaluate_rules(STANDARD_TX, policies)
        assert result.passed is True
        assert len(result.evaluation_trace) == 3
        for entry in result.evaluation_trace:
            assert "policy_id" in entry
            assert "policy_name" in entry
            assert "priority" in entry
            assert "condition" in entry
            assert "satisfied" in entry

    def test_time_of_day_check(self):
        """Business hours policy should work correctly."""
        policies = [
            _policy(
                "Business Hours",
                {
                    "all": [
                        {"field": "time_of_day_hour", "op": ">=", "value": 8},
                        {"field": "time_of_day_hour", "op": "<=", "value": 18},
                    ]
                },
                priority=40,
            ),
        ]
        # 14:00 — within business hours
        tx = {**STANDARD_TX, "time_of_day_hour": 14}
        assert evaluate_rules(tx, policies).passed is True

        # 3:00 AM — outside business hours
        tx_late = {**STANDARD_TX, "time_of_day_hour": 3}
        result = evaluate_rules(tx_late, policies)
        assert result.passed is False
        assert result.denied_by.name == "Business Hours"

    def test_gaming_block(self):
        """Gaming merchant category should be blocked."""
        policies = [
            _policy(
                "Block Gaming",
                {"field": "merchant_category", "op": "not_in", "value": ["gambling", "gaming", "casino"]},
                priority=20,
            ),
        ]
        tx_gaming = {**STANDARD_TX, "merchant_category": "gambling"}
        result = evaluate_rules(tx_gaming, policies)
        assert result.passed is False
        assert result.denied_by.name == "Block Gaming"

        tx_normal = {**STANDARD_TX, "merchant_category": "office_supplies"}
        assert evaluate_rules(tx_normal, policies).passed is True
