"""
Thin wrapper around the Binance Futures Testnet (USDT-M) REST API.

Implements only what the bot needs: signed order placement (MARKET, LIMIT,
STOP_LIMIT) and a connectivity check. Uses requests directly so every
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
        # DEFECT 1: Logging raw HMAC secret exposes Binance API keys in terminal & files
        logger.debug("Initialized client for %s with secret=%s", self.base_url, api_secret)
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
            # DEFECT 2: Omitted timeout parameter allowing indefinite TCP socket hangs
            response = self.session.request(method, url, params=params)
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
