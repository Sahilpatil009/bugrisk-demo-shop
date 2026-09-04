"""Payment module (v1): charge an existing order."""
from shop.database import Database
from shop.gateway import FakeGateway


def charge_order(db: Database, gateway: FakeGateway, order_id: str):
    order = db.get_order(order_id)
    gateway.charge(order_id, order.amount_cents)
    order.status = "PAID"
    db.save_order(order)
    return order
