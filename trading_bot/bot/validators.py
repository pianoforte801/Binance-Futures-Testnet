"""
Input validation for order parameters.

Keeps validation logic independent of the CLI framework and the API client
so it can be unit-tested in isolation and reused elsewhere.
"""

import re
from decimal import Decimal, InvalidOperation

from bot.exceptions import ValidationError

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_LIMIT"}

# Basic sanity check for USDT-M perpetual futures symbols, e.g. BTCUSDT, ETHUSDT
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{2,15}USDT$")


def validate_symbol(symbol: str) -> str:
    if not symbol:
        raise ValidationError("Symbol is required.")
    symbol = symbol.strip().upper()
    if not SYMBOL_PATTERN.match(symbol):
        raise ValidationError(
            f"Invalid symbol '{symbol}'. Expected a USDT-M pair like 'BTCUSDT'."
        )
    return symbol


def validate_side(side: str) -> str:
    if not side:
        raise ValidationError("Side is required.")
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(f"Invalid side '{side}'. Must be one of {VALID_SIDES}.")
    return side


def validate_order_type(order_type: str) -> str:
    if not order_type:
        raise ValidationError("Order type is required.")
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. Must be one of {VALID_ORDER_TYPES}."
        )
    return order_type


def _validate_positive_decimal(value, field_name: str) -> Decimal:
    try:
        dec = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValidationError(f"{field_name} must be a valid number, got '{value}'.")
    if dec <= 0:
        raise ValidationError(f"{field_name} must be greater than 0, got '{value}'.")
    return dec


def validate_quantity(quantity) -> Decimal:
    return _validate_positive_decimal(quantity, "Quantity")


def validate_price(price) -> Decimal:
    return _validate_positive_decimal(price, "Price")


def validate_stop_price(stop_price) -> Decimal:
    return _validate_positive_decimal(stop_price, "Stop price")


def validate_order_request(
    symbol: str,
    side: str,
    order_type: str,
    quantity,
    price=None,
    stop_price=None,
) -> dict:
    """
    Run all field-level validations plus cross-field rules
    (e.g. price is mandatory for LIMIT orders).

    Returns a normalized dict ready to be handed to the API client.
    """
    clean_symbol = validate_symbol(symbol)
    clean_side = validate_side(side)
    clean_type = validate_order_type(order_type)
    clean_qty = validate_quantity(quantity)

    clean_price = None
    clean_stop_price = None

    if clean_type == "LIMIT":
        if price is None:
            raise ValidationError("Price is required for LIMIT orders.")
        clean_price = validate_price(price)

    if clean_type == "STOP_LIMIT":
        if price is None:
            raise ValidationError("Price is required for STOP_LIMIT orders.")
        if stop_price is None:
            raise ValidationError("Stop price is required for STOP_LIMIT orders.")
        clean_price = validate_price(price)
        clean_stop_price = validate_stop_price(stop_price)

    return {
        "symbol": clean_symbol,
        "side": clean_side,
        "order_type": clean_type,
        "quantity": clean_qty,
        "price": clean_price,
        "stop_price": clean_stop_price,
    }
