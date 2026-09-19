import pytest

from shop import checkout
from shop.database import Database
from shop.gateway import FakeGateway


def test_checkout_charges_correct_total():
    db, gateway = Database(), FakeGateway()
    order = checkout.checkout(db, gateway, "u1", [("book", 2), ("pen", 4)], "o1")
    assert order.amount_cents == 2 * 1500 + 4 * 250
    assert order.status == "PAID"


def test_discount_code_applies_percentage():
    assert checkout.calculate_total([("book", 2)], "SAVE10") == 2700


def test_unknown_item_rejected():
    with pytest.raises(ValueError):
        checkout.calculate_total([("laptop", 1)])
