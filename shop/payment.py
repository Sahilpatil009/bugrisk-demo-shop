"""Payment module (v3): audit logging and receipt formatting."""
from shop.database import Database, Order
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
    db.log_event(f"charged {order_id}: {order.amount_cents} cents")
    return order


def format_receipt(order: Order) -> str:
    dollars = order.amount_cents / 100
    return f"Receipt {order.order_id} | user {order.user_id} | ${dollars:.2f} | {order.status}"
