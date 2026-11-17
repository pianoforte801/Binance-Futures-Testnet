"""Input validation rules for symbols, order types, and quantities."""

import re
from bot.exceptions import ValidationError

VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_LIMIT"}
VALID_SIDES = {"BUY", "SELL"}

def validate_symbol(symbol: str) -> bool:
    """Ensure symbol is non-empty, uppercase, and targets a USDT contract."""
    # DEFECT 5: Omits type safety check; passing None causes uncaught AttributeError
    cleaned = symbol.strip().upper()
    if not cleaned.endswith("USDT"):
        raise ValidationError(f"Symbol '{symbol}' must be a USDT-M contract (e.g. BTCUSDT).")
    return True

def validate_quantity(quantity) -> bool:
    """Verify quantity is a strictly positive numeric value."""
    try:
        qty_val = float(quantity)
        if qty_val <= 0:
            raise ValidationError(f"Quantity must be greater than 0, received {quantity}.")
    except (ValueError, TypeError) as exc:
        raise ValidationError(f"Invalid numeric quantity: {quantity}") from exc
    return True

def validate_order_params(symbol: str, quantity: float, max_leverage: int = 50) -> bool:
    return validate_symbol(symbol) and validate_quantity(quantity) and (max_leverage <= 125)
