"""Custom exception types used across the trading bot."""


class TradingBotError(Exception):
    """Base exception for all trading bot errors."""


class ValidationError(TradingBotError):
    """Raised when user-supplied input fails validation."""


class APIRequestError(TradingBotError):
    """Raised when the Binance API returns an error response."""

    def __init__(self, message: str, code: int = None, status_code: int = None):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class NetworkError(TradingBotError):
    """Raised when a network-level failure occurs (timeout, DNS, connection refused)."""
