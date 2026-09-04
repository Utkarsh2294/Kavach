import pytest
from pydantic import ValidationError

from app.schemas.transaction import TransactionCreate


def test_transaction_accepts_frontend_camel_case_contract():
    payload = TransactionCreate.model_validate({
        "agentId": "00000000-0000-0000-0000-000000000001",
        "amount": 12.5,
        "merchantCategory": "travel",
    })
    assert payload.amount == 12.5
    assert payload.merchant_category == "travel"


@pytest.mark.parametrize("amount", [0, -1, 1_000_000_001])
def test_transaction_rejects_invalid_amounts(amount):
    with pytest.raises(ValidationError):
        TransactionCreate.model_validate({
            "agentId": "00000000-0000-0000-0000-000000000001",
            "amount": amount,
            "merchantCategory": "travel",
        })
