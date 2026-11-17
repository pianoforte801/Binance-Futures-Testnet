"""
Thin wrapper around the Binance Futures Testnet (USDT-M) REST API.

Implements only what the bot needs: signed order placement (MARKET, LIMIT,
STOP_LIMIT) and a connectivity check. Uses `requests` directly so every
request/response can be logged explicitly.

Binance Futures Testnet docs: https://binance-docs.github.io/apidocs/testnet/en/
"""

import hashlib
import hmac
import logging
import time
from urllib.parse import urlencode

import requests

from bot.exceptions import APIRequestError, NetworkError

logger = logging.getLogger("trading_bot.client")

BASE_URL = "https://testnet.binancefuture.com"


class BinanceFuturesTestnetClient:
    """Minimal signed REST client for Binance USDT-M Futures Testnet."""

    def __init__(self, api_key: str, api_secret: str, base_url: str = BASE_URL, timeout: int = 10):
        if not api_key or not api_secret:
            raise ValueError("API key and secret must be provided.")
        self.api_key = api_key
        self.api_secret = api_secret.encode()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _sign(self, params: dict) -> str:
        query_string = urlencode(params)
        signature = hmac.new(self.api_secret, query_string.encode(), hashlib.sha256).hexdigest()
        return signature

    def _signed_request(self, method: str, path: str, params: dict) -> dict:
        params = dict(params)
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = 5000
        params["signature"] = self._sign(params)

        url = f"{self.base_url}{path}"
        logger.debug("Request -> %s %s | params=%s", method, url, {k: v for k, v in params.items() if k != "signature"})

        try:
            response = self.session.request(method, url, params=params, timeout=self.timeout)
        except requests.exceptions.Timeout as exc:
            logger.error("Network timeout calling %s: %s", url, exc)
            raise NetworkError(f"Request to {path} timed out after {self.timeout}s.") from exc
        except requests.exceptions.ConnectionError as exc:
            logger.error("Connection error calling %s: %s", url, exc)
            raise NetworkError(f"Could not connect to {self.base_url}. Check your internet connection.") from exc
        except requests.exceptions.RequestException as exc:
            logger.error("Unexpected network error calling %s: %s", url, exc)
            raise NetworkError(f"Unexpected network error: {exc}") from exc

        logger.debug("Response <- status=%s body=%s", response.status_code, response.text)

        try:
            body = response.json()
        except ValueError:
            body = {"raw": response.text}

        if response.status_code != 200:
            code = body.get("code") if isinstance(body, dict) else None
            msg = body.get("msg") if isinstance(body, dict) else str(body)
            logger.error("API error: status=%s code=%s msg=%s", response.status_code, code, msg)
            raise APIRequestError(
                message=msg or "Unknown API error",
                code=code,
                status_code=response.status_code,
            )

        return body

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def ping(self) -> bool:
        """Check connectivity to the testnet server (unsigned endpoint)."""
        url = f"{self.base_url}/fapi/v1/ping"
        logger.debug("Ping -> %s", url)
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as exc:
            logger.error("Ping failed: %s", exc)
            raise NetworkError(f"Could not reach {self.base_url}: {exc}") from exc

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity,
        price=None,
        stop_price=None,
        time_in_force: str = "GTC",
    ) -> dict:
        """
        Place an order on the USDT-M futures testnet.

        order_type: "MARKET", "LIMIT", or "STOP_LIMIT" (mapped to Binance's
        native "STOP" order type, which is a stop-limit order in the
        futures API).
        """
        params = {
            "symbol": symbol,
            "side": side,
            "quantity": str(quantity),
        }

        if order_type == "MARKET":
            params["type"] = "MARKET"
        elif order_type == "LIMIT":
            params["type"] = "LIMIT"
            params["price"] = str(price)
            params["timeInForce"] = time_in_force
        elif order_type == "STOP_LIMIT":
            # Binance futures native type for a stop-limit order is "STOP"
            params["type"] = "STOP"
            params["price"] = str(price)
            params["stopPrice"] = str(stop_price)
            params["timeInForce"] = time_in_force
        else:
            raise ValueError(f"Unsupported order_type: {order_type}")

        return self._signed_request("POST", "/fapi/v1/order", params)

    def get_order_status(self, symbol: str, order_id: int) -> dict:
        """Query a previously placed order's current status."""
        params = {"symbol": symbol, "orderId": order_id}
        return self._signed_request("GET", "/fapi/v1/order", params)
