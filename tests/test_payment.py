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
