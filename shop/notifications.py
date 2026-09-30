"""Customer notifications (simulated by logging events)."""
from shop.database import Database, Order


def send_receipt(db: Database, order: Order) -> None:
    db.log_event(f"receipt sent for {order.order_id}: {order.amount_cents} cents")


def send_refund_notice(db: Database, order: Order, amount_cents: int) -> None:
    db.log_event(f"refund notice for {order.order_id}: {amount_cents} cents")
