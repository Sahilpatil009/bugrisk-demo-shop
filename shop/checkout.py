"""Checkout flow (v2): discount codes and input validation."""
from typing import List, Optional, Tuple

from shop import notifications, payment
from shop.database import Database, Order
from shop.gateway import FakeGateway

PRICES = {"book": 1500, "pen": 250, "bag": 4900}   # cents
DISCOUNTS = {"SAVE10": 10, "SAVE20": 20}           # percent


def calculate_total(items: List[Tuple[str, int]], discount_code: Optional[str] = None) -> int:
    total = 0
    for name, qty in items:
        if name not in PRICES:
            raise ValueError(f"unknown item: {name}")
        if qty <= 0:
            raise ValueError("quantity must be positive")
        total += PRICES[name] * qty
    if discount_code:
        percent = DISCOUNTS.get(discount_code, 0)
        total = total * (100 - percent) // 100
    return total


def checkout(db: Database, gateway: FakeGateway, user_id: str,
             items: List[Tuple[str, int]], order_id: str,
             discount_code: Optional[str] = None) -> Order:
    total = calculate_total(items, discount_code)
    db.save_order(Order(order_id=order_id, user_id=user_id, amount_cents=total))
    paid = payment.charge_order(db, gateway, order_id)
    notifications.send_receipt(db, paid)
    return paid
