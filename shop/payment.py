"""Payment module (v4): retries, processing fees, multi-currency and refunds.

This is the risky pull request the BugRisk AI demo analyzes:
large diff, many branches, and the money-handling logic of the shop.
"""
from __future__ import annotations

from typing import Optional

from shop.database import Database, Order
from shop.gateway import FakeGateway, GatewayTimeout

MAX_RETRIES = 3
FEE_RATE = 0.029                 # 2.9% processing fee
FIXED_FEE_CENTS = 30
REFUND_WINDOW_DAYS = 30
USD_RATES = {"USD": 1.0, "EUR": 1.08, "INR": 0.012}
REFUND_REASONS = {"customer_request", "duplicate", "fraud", "damaged"}


def calculate_fee(amount_cents: int, currency: str = "USD") -> int:
    """Processing fee in cents, with volume discounts on big payments."""
    if currency not in USD_RATES:
        raise ValueError(f"unsupported currency: {currency}")
    usd_cents = amount_cents * USD_RATES[currency]
    fee = usd_cents * FEE_RATE + FIXED_FEE_CENTS
    if usd_cents > 100_000:
        fee = fee * 0.8
    elif usd_cents > 50_000:
        fee = fee * 0.9
    elif usd_cents < 500:
        fee = min(fee, 50)
    return int(fee)


def charge_order(db: Database, gateway: FakeGateway, order_id: str,
                 retry: bool = True):
    """Charge an order, retrying when the gateway times out."""
    order = db.get_order(order_id)
    if order.amount_cents <= 0:
        raise ValueError("order amount must be positive")
    if order.status == "PAID":
        return order
    if order.status in ("REFUNDED", "PARTIALLY_REFUNDED"):
        raise ValueError("cannot charge a refunded order")

    attempts = 0
    while attempts <= MAX_RETRIES:
        try:
            gateway.charge(order_id, order.amount_cents)
            order.status = "PAID"
            order.fee_cents = calculate_fee(order.amount_cents, order.currency)
            break
        except GatewayTimeout:
            attempts += 1
            db.log_event(f"charge timeout for {order_id}, attempt {attempts}")
            if not retry:
                break

    if order.status != "PAID":
        order.status = "FAILED"
        db.log_event(f"charge failed for {order_id}")
    else:
        db.log_event(f"charged {order_id}: {order.amount_cents} cents")
    db.save_order(order)
    return order


def refund_order(db: Database, gateway: FakeGateway, order_id: str,
                 amount_cents: Optional[int] = None,
                 reason: str = "customer_request",
                 days_since_purchase: int = 0):
    """Refund all or part of a paid order."""
    order = db.get_order(order_id)
    if order.status not in ("PAID", "PARTIALLY_REFUNDED"):
        raise ValueError(f"order {order_id} is not refundable ({order.status})")
    if reason not in REFUND_REASONS:
        raise ValueError(f"unknown refund reason: {reason}")

    if days_since_purchase > REFUND_WINDOW_DAYS and reason not in ("fraud", "damaged"):
        raise ValueError("refund window has expired")

    if amount_cents is None:
        amount_cents = order.amount_cents - order.refunded_cents
    if amount_cents <= 0:
        raise ValueError("refund amount must be positive")
    if amount_cents > order.amount_cents:
        raise ValueError("refund exceeds the original order amount")

    order.refunded_cents += amount_cents
    if order.refunded_cents >= order.amount_cents:
        order.status = "REFUNDED"
    else:
        order.status = "PARTIALLY_REFUNDED"
    db.save_order(order)

    gateway.refund(order_id, amount_cents)
    if reason == "fraud":
        db.log_event(f"FRAUD refund for {order_id}: {amount_cents} cents")
    elif reason == "duplicate":
        db.log_event(f"duplicate-charge refund for {order_id}: {amount_cents} cents")
    else:
        db.log_event(f"refund for {order_id}: {amount_cents} cents ({reason})")
    return order


def format_receipt(order: Order) -> str:
    dollars = order.amount_cents / 100
    return f"Receipt {order.order_id} | user {order.user_id} | ${dollars:.2f} | {order.status}"
