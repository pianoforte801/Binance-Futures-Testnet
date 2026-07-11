#!/usr/bin/env python3
"""
CLI entry point for the Simplified Trading Bot (Binance Futures Testnet).

Examples:
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

    python cli.py --symbol BTCUSDT --side SELL --type LIMIT \\
        --quantity 0.01 --price 60000

    python cli.py --symbol ETHUSDT --side BUY --type STOP_LIMIT \\
        --quantity 0.05 --price 3200 --stop-price 3180

Credentials are read from environment variables (or a local .env file):
    BINANCE_TESTNET_API_KEY
    BINANCE_TESTNET_API_SECRET
"""

import argparse
import os
import sys

from bot.client import BinanceFuturesTestnetClient
from bot.exceptions import NetworkError, TradingBotError
from bot.logging_config import setup_logging
from bot.orders import OrderManager

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv is optional; env vars can be exported directly instead.
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Place MARKET / LIMIT / STOP_LIMIT orders on Binance Futures Testnet (USDT-M).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, choices=["BUY", "SELL", "buy", "sell"], help="Order side")
    parser.add_argument(
        "--type",
        dest="order_type",
        required=True,
        choices=["MARKET", "LIMIT", "STOP_LIMIT", "market", "limit", "stop_limit"],
        help="Order type",
    )
    parser.add_argument("--quantity", required=True, help="Order quantity")
    parser.add_argument("--price", required=False, default=None, help="Limit price (required for LIMIT / STOP_LIMIT)")
    parser.add_argument(
        "--stop-price", required=False, default=None, dest="stop_price",
        help="Stop trigger price (required for STOP_LIMIT)",
    )
    parser.add_argument(
        "--log-level", default="DEBUG",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Minimum level written to the log file (default: DEBUG)",
    )
    return parser


def print_summary(order_summary: dict) -> None:
    print("\n--- Order Request Summary ---")
    for key, value in order_summary.items():
        if value is not None:
            print(f"  {key:12s}: {value}")


def print_response(response: dict) -> None:
    print("\n--- Order Response ---")
    fields = ["orderId", "symbol", "status", "side", "type", "origQty", "executedQty", "avgPrice", "price"]
    for f in fields:
        if f in response:
            print(f"  {f:12s}: {response[f]}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    logger = setup_logging(args.log_level)

    api_key = os.environ.get("BINANCE_TESTNET_API_KEY")
    api_secret = os.environ.get("BINANCE_TESTNET_API_SECRET")

    if not api_key or not api_secret:
        print(
            "ERROR: Missing API credentials.\n"
            "Set BINANCE_TESTNET_API_KEY and BINANCE_TESTNET_API_SECRET as environment "
            "variables, or place them in a .env file in the project root.",
            file=sys.stderr,
        )
        return 1

    try:
        client = BinanceFuturesTestnetClient(api_key=api_key, api_secret=api_secret)
        manager = OrderManager(client)

        # Optional connectivity check before attempting the order
        try:
            client.ping()
        except NetworkError as exc:
            logger.error("Connectivity check failed: %s", exc)
            print(f"FAILED: Could not reach Binance Futures Testnet - {exc}", file=sys.stderr)
            return 1

        result = manager.place_order(
            symbol=args.symbol,
            side=args.side.upper(),
            order_type=args.order_type.upper(),
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )

        print_summary(result.request_summary)

        if result.success:
            print_response(result.response)
            print("\nSUCCESS: Order placed successfully.")
            return 0
        else:
            print(f"\nFAILED: {result.error}", file=sys.stderr)
            return 1

    except TradingBotError as exc:
        logger.exception("Unhandled trading bot error")
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - top-level safety net
        logger.exception("Unexpected error")
        print(f"FAILED: Unexpected error - {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
