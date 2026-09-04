"""Fake payment gateway that can simulate real-world failures."""
from __future__ import annotations

from typing import Dict, List, Optional


class GatewayTimeout(Exception):
    """The response was lost, but the gateway may already have processed the request."""


class GatewayError(Exception):
    """The gateway rejected the request."""


class FakeGateway:
    def __init__(self, timeout_first_n_charges: int = 0, fail_refunds: bool = False) -> None:
        self.timeout_first_n_charges = timeout_first_n_charges
        self.fail_refunds = fail_refunds
        self.charges: List[Dict] = []
        self.refunds: List[Dict] = []
        self._charge_calls = 0

    def charge(self, order_id: str, amount_cents: int, idempotency_key: Optional[str] = None) -> str:
        self._charge_calls += 1
        # A repeated idempotency key is safely ignored, like real gateways do.
        if idempotency_key and any(c["key"] == idempotency_key for c in self.charges):
            return f"ch_{order_id}"
        self.charges.append({"order_id": order_id, "amount_cents": amount_cents, "key": idempotency_key})
        if self._charge_calls <= self.timeout_first_n_charges:
            raise GatewayTimeout("response lost after processing")
        return f"ch_{order_id}"

    def refund(self, order_id: str, amount_cents: int) -> str:
        if self.fail_refunds:
            raise GatewayError("refund rejected by gateway")
        self.refunds.append({"order_id": order_id, "amount_cents": amount_cents})
        return f"re_{order_id}"
