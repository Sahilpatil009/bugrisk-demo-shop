"""In-memory 'database' for the demo shop."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Order:
    order_id: str
    user_id: str
    amount_cents: int          # money is stored as integer cents (no float errors)
    status: str = "PENDING"
    refunded_cents: int = 0
    fee_cents: int = 0         # processing fee charged to the merchant
    currency: str = "USD"


class Database:
    def __init__(self) -> None:
        self._orders: Dict[str, Order] = {}
        self._events: List[str] = []

    def save_order(self, order: Order) -> None:
        self._orders[order.order_id] = order

    def get_order(self, order_id: str) -> Order:
        if order_id not in self._orders:
            raise KeyError(f"unknown order: {order_id}")
        return self._orders[order_id]

    def orders_for_user(self, user_id: str) -> List[Order]:
        return [o for o in self._orders.values() if o.user_id == user_id]

    def log_event(self, message: str) -> None:
        self._events.append(message)

    @property
    def events(self) -> List[str]:
        return list(self._events)
