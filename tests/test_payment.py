import pytest

from shop import payment
from shop.database import Database, Order
from shop.gateway import FakeGateway


def make_order(db: Database, amount: int = 1000) -> Order:
    order = Order("o1", "u1", amount)
    db.save_order(order)
    return order


def test_charge_marks_order_paid():
    db, gateway = Database(), FakeGateway()
    make_order(db)
    order = payment.charge_order(db, gateway, "o1")
    assert order.status == "PAID"
    assert len(gateway.charges) == 1


def test_charge_rejects_non_positive_amount():
    db, gateway = Database(), FakeGateway()
    make_order(db, amount=0)
    with pytest.raises(ValueError):
        payment.charge_order(db, gateway, "o1")


def test_charging_twice_only_charges_once():
    db, gateway = Database(), FakeGateway()
    make_order(db)
    payment.charge_order(db, gateway, "o1")
    payment.charge_order(db, gateway, "o1")
    assert len(gateway.charges) == 1


def test_receipt_format():
    order = Order("o1", "u1", 1999, status="PAID")
    assert payment.format_receipt(order) == "Receipt o1 | user u1 | $19.99 | PAID"
