"""Checkout flow (v1): price the cart, create an order, charge it."""
from typing import List, Tuple

from shop import notifications, payment
from shop.database import Database, Order
from shop.gateway import FakeGateway

PRICES = {"book": 1500, "pen": 250, "bag": 4900}   # cents


def calculate_total(items: List[Tuple[str, int]]) -> int:
    return sum(PRICES[name] * qty for name, qty in items)


def checkout(db: Database, gateway: FakeGateway, user_id: str,
             items: List[Tuple[str, int]], order_id: str) -> Order:
    total = calculate_total(items)
    db.save_order(Order(order_id=order_id, user_id=user_id, amount_cents=total))
    paid = payment.charge_order(db, gateway, order_id)
    notifications.send_receipt(db, paid)
    return paid
