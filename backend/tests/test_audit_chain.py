"""Phase 10/13 unit coverage for deterministic, tamper-evident audit hashes."""

from app.services.audit import GENESIS_HASH, calculate_hash, canonical_payload


def test_canonical_payload_is_order_independent():
    left = {"decision": "deny", "amount": 42, "nested": {"b": 2, "a": 1}}
    right = {"nested": {"a": 1, "b": 2}, "amount": 42, "decision": "deny"}
    assert canonical_payload(left) == canonical_payload(right)
    assert calculate_hash(GENESIS_HASH, left) == calculate_hash(GENESIS_HASH, right)


def test_chain_detects_payload_tampering():
    original = {"transaction_id": "tx-1", "decision": "deny"}
    original_hash = calculate_hash(GENESIS_HASH, original)
    tampered = {"transaction_id": "tx-1", "decision": "approve"}
    assert calculate_hash(GENESIS_HASH, tampered) != original_hash


def test_chain_links_each_entry_to_the_previous_hash():
    first_hash = calculate_hash(GENESIS_HASH, {"event": "grant"})
    second_hash = calculate_hash(first_hash, {"event": "deny"})
    assert first_hash != second_hash
    assert len(first_hash) == 64
    assert len(second_hash) == 64
