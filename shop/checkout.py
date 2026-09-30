"""Checkout flow (v3): loyalty discounts and order cancellation with refunds."""
from typing import List, Optional, Tuple

from shop import notifications, payment
from shop.database import Database, Order
from shop.gateway import FakeGateway

PRICES = {"book": 1500, "pen": 250, "bag": 4900}   # cents
DISCOUNTS = {"SAVE10": 10, "SAVE20": 20}           # percent


def loyalty_percent(past_orders: int) -> int:
    """Extra discount for returning customers."""
    if past_orders >= 20:
        return 10
    if past_orders >= 10:
        return 5
    if past_orders >= 3:
        return 2
    return 0


def calculate_total(items: List[Tuple[str, int]], discount_code: Optional[str] = None,
                    past_orders: int = 0) -> int:
    total = 0
    for name, qty in items:
        if name not in PRICES:
            raise ValueError(f"unknown item: {name}")
        if qty <= 0:
            raise ValueError("quantity must be positive")
        total += PRICES[name] * qty
    percent = DISCOUNTS.get(discount_code, 0) if discount_code else 0
    percent += loyalty_percent(past_orders)
    if percent > 25:
        percent = 25                      # never discount more than 25%
    return total * (100 - percent) // 100


def checkout(db: Database, gateway: FakeGateway, user_id: str,
             items: List[Tuple[str, int]], order_id: str,
             discount_code: Optional[str] = None) -> Order:
    past_orders = len(db.orders_for_user(user_id))
    total = calculate_total(items, discount_code, past_orders)
    db.save_order(Order(order_id=order_id, user_id=user_id, amount_cents=total))
    paid = payment.charge_order(db, gateway, order_id)
    if paid.status == "PAID":
        notifications.send_receipt(db, paid)
    return paid


def cancel_order(db: Database, gateway: FakeGateway, order_id: str,
                 reason: str = "customer_request") -> Order:
    """Cancel a paid order and refund whatever is still refundable."""
    order = db.get_order(order_id)
    if order.status == "PENDING":
        order.status = "CANCELLED"
        db.save_order(order)
        return order
    refunded = payment.refund_order(db, gateway, order_id, reason=reason)
    notifications.send_refund_notice(db, refunded, refunded.refunded_cents)
    return refunded
