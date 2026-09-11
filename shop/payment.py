"""Payment module (v2): validate the order before charging."""
from shop.database import Database
from shop.gateway import FakeGateway


def charge_order(db: Database, gateway: FakeGateway, order_id: str):
    order = db.get_order(order_id)
    if order.amount_cents <= 0:
        raise ValueError("order amount must be positive")
    if order.status == "PAID":          # already charged: do nothing
        return order
    gateway.charge(order_id, order.amount_cents)
    order.status = "PAID"
    db.save_order(order)
    return order
