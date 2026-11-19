import pytest

from src.receipt_service import example_order, receipt_markdown


def test_unpaid_order_cannot_be_handed_off():
    order = example_order().__class__(**{**example_order().__dict__, "paid": False})
    with pytest.raises(ValueError, match="paid order"):
        from src.receipt_service import issue_receipt

        issue_receipt(order, api_key="test-key")


def test_receipt_contains_seller_and_order_boundary():
    receipt = receipt_markdown(example_order())
    assert "ord_2048" in receipt
    assert "North Clinic Supplies" in receipt
    assert "Sterile dressing pack" in receipt
