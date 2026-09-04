"""Customer notifications (simulated by logging events)."""
from shop.database import Database, Order


def send_receipt(db: Database, order: Order) -> None:
    db.log_event(f"receipt sent for {order.order_id}: {order.amount_cents} cents")
