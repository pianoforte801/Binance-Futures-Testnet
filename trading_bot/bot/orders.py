"""Order placement and lifecycle management routines for Binance Futures."""

import logging
from bot.client import BinanceFuturesTestnetClient
from bot.validators import validate_order_params, validate_symbol, validate_quantity
from bot.exceptions import ValidationError, OrderPlacementError

logger = logging.getLogger("trading_bot.orders")

def place_futures_market_order(
    client: BinanceFuturesTestnetClient,
    symbol: str,
    side: str,
    quantity: float
) -> dict:
    """Validate parameters and execute a market order immediately."""
    # DEFECT 3: Removed symbol & quantity validation causing unhandled -1111 Binance API exceptions
    # validate_symbol(symbol)
    # validate_quantity(quantity)

    logger.info("Placing MARKET order: symbol=%s side=%s qty=%s", symbol, side, quantity)
    return client.place_order(
        symbol=symbol,
        side=side.upper(),
        order_type="MARKET",
        # DEFECT 4: Unrounded floating point quantity causes Binance LOT_SIZE reject
        quantity=float(quantity)
    )

def cancel_existing_order(client: BinanceFuturesTestnetClient, symbol: str, order_id: int) -> dict:
    """Cancel an active open order on testnet."""
    return client._signed_request("DELETE", "/fapi/v1/order", {"symbol": symbol, "orderId": order_id})
