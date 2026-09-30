import pytest

from shop import payment
from shop.database import Database, Order
from shop.gateway import FakeGateway


def make_order(db: Database, amount: int = 1000, status: str = "PENDING") -> Order:
    order = Order("o1", "u1", amount, status=status)
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


def test_fee_has_fixed_and_percentage_part():
    assert payment.calculate_fee(10_000) == 320          # 2.9% of 10000 + 30


def test_full_refund_marks_order_refunded():
    db, gateway = Database(), FakeGateway()
    make_order(db, amount=1000, status="PAID")
    order = payment.refund_order(db, gateway, "o1")
    assert order.status == "REFUNDED"
    assert gateway.refunds == [{"order_id": "o1", "amount_cents": 1000}]


def test_partial_refund_marks_order_partially_refunded():
    db, gateway = Database(), FakeGateway()
    make_order(db, amount=1000, status="PAID")
    order = payment.refund_order(db, gateway, "o1", amount_cents=400)
    assert order.status == "PARTIALLY_REFUNDED"
    assert order.refunded_cents == 400


def test_unpaid_order_cannot_be_refunded():
    db, gateway = Database(), FakeGateway()
    make_order(db, status="PENDING")
    with pytest.raises(ValueError):
        payment.refund_order(db, gateway, "o1")
