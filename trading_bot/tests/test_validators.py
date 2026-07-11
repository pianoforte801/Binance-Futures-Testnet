"""
Unit tests for bot.validators.

Run with:  python -m pytest tests/ -v
(or:       python -m unittest discover tests)
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.exceptions import ValidationError
from bot.validators import validate_order_request


class TestValidateOrderRequest(unittest.TestCase):
    def test_valid_market_order(self):
        result = validate_order_request("btcusdt", "buy", "market", "0.01")
        self.assertEqual(result["symbol"], "BTCUSDT")
        self.assertEqual(result["side"], "BUY")
        self.assertEqual(result["order_type"], "MARKET")
        self.assertIsNone(result["price"])

    def test_valid_limit_order(self):
        result = validate_order_request("ETHUSDT", "SELL", "LIMIT", "1.5", price="3000")
        self.assertEqual(str(result["price"]), "3000")

    def test_limit_order_missing_price_raises(self):
        with self.assertRaises(ValidationError):
            validate_order_request("ETHUSDT", "SELL", "LIMIT", "1.5")

    def test_invalid_symbol_raises(self):
        with self.assertRaises(ValidationError):
            validate_order_request("BTC", "BUY", "MARKET", "0.01")

    def test_invalid_side_raises(self):
        with self.assertRaises(ValidationError):
            validate_order_request("BTCUSDT", "HOLD", "MARKET", "0.01")

    def test_invalid_order_type_raises(self):
        with self.assertRaises(ValidationError):
            validate_order_request("BTCUSDT", "BUY", "ICEBERG", "0.01")

    def test_negative_quantity_raises(self):
        with self.assertRaises(ValidationError):
            validate_order_request("BTCUSDT", "BUY", "MARKET", "-1")

    def test_zero_quantity_raises(self):
        with self.assertRaises(ValidationError):
            validate_order_request("BTCUSDT", "BUY", "MARKET", "0")

    def test_non_numeric_quantity_raises(self):
        with self.assertRaises(ValidationError):
            validate_order_request("BTCUSDT", "BUY", "MARKET", "abc")

    def test_stop_limit_requires_both_prices(self):
        with self.assertRaises(ValidationError):
            validate_order_request("BTCUSDT", "BUY", "STOP_LIMIT", "0.01", price="60000")

        result = validate_order_request(
            "BTCUSDT", "BUY", "STOP_LIMIT", "0.01", price="60000", stop_price="59500"
        )
        self.assertEqual(str(result["stop_price"]), "59500")


if __name__ == "__main__":
    unittest.main()
