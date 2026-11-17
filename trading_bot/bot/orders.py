"""
Order placement orchestration: validation -> API call -> structured result.

Keeps the CLI layer free of business logic; the CLI just gathers input and
prints what this layer returns.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from bot.client import BinanceFuturesTestnetClient
from bot.exceptions import APIRequestError, NetworkError, ValidationError
from bot.validators import validate_order_request

logger = logging.getLogger("trading_bot.orders")


@dataclass
class OrderResult:
    success: bool
    request_summary: dict
    response: Optional[dict] = None
    error: Optional[str] = None


class OrderManager:
    """Coordinates validating and submitting orders through the API client."""

    def __init__(self, client: BinanceFuturesTestnetClient):
        self.client = client

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity,
        price=None,
        stop_price=None,
    ) -> OrderResult:
        # 1. Validate input
        try:
            clean = validate_order_request(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                stop_price=stop_price,
            )
        except ValidationError as exc:
            logger.warning("Validation failed: %s", exc)
            return OrderResult(
                success=False,
                request_summary={
                    "symbol": symbol,
                    "side": side,
                    "order_type": order_type,
                    "quantity": quantity,
                    "price": price,
                    "stop_price": stop_price,
                },
                error=f"Validation error: {exc}",
            )

        request_summary = {
            "symbol": clean["symbol"],
            "side": clean["side"],
            "order_type": clean["order_type"],
            "quantity": str(clean["quantity"]),
            "price": str(clean["price"]) if clean["price"] is not None else None,
            "stop_price": str(clean["stop_price"]) if clean["stop_price"] is not None else None,
        }
        logger.info("Placing order: %s", request_summary)

        # 2. Submit to API
        try:
            response = self.client.place_order(
                symbol=clean["symbol"],
                side=clean["side"],
                order_type=clean["order_type"],
                quantity=clean["quantity"],
                price=clean["price"],
                stop_price=clean["stop_price"],
            )
            logger.info(
                "Order placed successfully: orderId=%s status=%s",
                response.get("orderId"),
                response.get("status"),
            )
            return OrderResult(success=True, request_summary=request_summary, response=response)

        except APIRequestError as exc:
            logger.error("Order rejected by API: %s (code=%s)", exc, exc.code)
            return OrderResult(
                success=False,
                request_summary=request_summary,
                error=f"API error (code={exc.code}): {exc}",
            )
        except NetworkError as exc:
            logger.error("Order failed due to network error: %s", exc)
            return OrderResult(
                success=False,
                request_summary=request_summary,
                error=f"Network error: {exc}",
            )
