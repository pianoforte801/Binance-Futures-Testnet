# Simplified Trading Bot — Binance Futures Testnet (USDT-M)
credentials/logs aren't included and please use your own testnet API key/secret to run it

A small, well-structured Python CLI application that places MARKET, LIMIT,
and STOP_LIMIT orders on the Binance USDT-M Futures **Testnet**, with
input validation, structured logging, and clean error handling.

## Project Structure

```
trading_bot/
  bot/
    __init__.py
    client.py          # Signed REST client for Binance Futures Testnet
    orders.py           # Validation -> API call -> structured result
    validators.py        # Input validation (symbol, side, type, qty, price)
    exceptions.py        # Custom exception types
    logging_config.py    # Rotating file + console logging setup
  tests/
    test_validators.py   # Unit tests for validation logic
  cli.py                 # CLI entry point (argparse)
  logs/                  # Created at runtime; bot.log lives here
  requirements.txt
  .env.example
  README.md
```

**Design notes:**
- `client.py` is the only module that talks to the network — it signs
  requests (HMAC-SHA256), sends them, and logs every request/response.
- `orders.py` sits between the CLI and the client: it validates input,
  calls the client, and returns a uniform `OrderResult` so the CLI never
  has to know about API internals.
- `validators.py` has no dependency on argparse or requests, so it's
  independently unit-testable (see `tests/test_validators.py`).
- Direct REST calls (`requests`) are used instead of `python-binance` so
  every request/response can be logged explicitly and there's one fewer
  third-party dependency to trust.

## Setup

### 1. Create a Binance Futures Testnet account
1. Go to https://testnet.binancefuture.com
2. Log in with a GitHub account (no separate registration needed).
3. Once logged in, generate an **API Key** and **API Secret** from the
   testnet dashboard (top right, "API Key").
4. Your testnet account is auto-funded with test USDT — no real funds are
   involved anywhere in this project.

### 2. Clone and install dependencies

```bash
git clone <your-repo-url>
cd trading_bot
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure credentials

Copy the example env file and fill in your testnet keys:

```bash
cp .env.example .env
```

Edit `.env`:

```
BINANCE_TESTNET_API_KEY=your_testnet_api_key_here
BINANCE_TESTNET_API_SECRET=your_testnet_api_secret_here
```

The CLI loads `.env` automatically via `python-dotenv`. Alternatively,
export the variables directly in your shell:

```bash
export BINANCE_TESTNET_API_KEY=your_testnet_api_key_here
export BINANCE_TESTNET_API_SECRET=your_testnet_api_secret_here
```

## Usage

### Place a MARKET order

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Place a LIMIT order

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 60000
```

### Place a STOP_LIMIT order (bonus order type)

```bash
python cli.py --symbol ETHUSDT --side BUY --type STOP_LIMIT \
    --quantity 0.05 --price 3200 --stop-price 3180
```

### Sample output

```
--- Order Request Summary ---
  symbol      : BTCUSDT
  side        : BUY
  order_type  : MARKET
  quantity    : 0.01

--- Order Response ---
  orderId     : 3123456789
  symbol      : BTCUSDT
  status      : FILLED
  side        : BUY
  type        : MARKET
  origQty     : 0.01
  executedQty : 0.01
  avgPrice    : 60123.4

SUCCESS: Order placed successfully.
```

On failure (validation error, rejected order, or network issue), the CLI
prints `FAILED: <reason>` and exits with a non-zero status code — the
process never crashes with a raw traceback.

### Adjusting log verbosity

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01 --log-level INFO
```

## Logging

All requests, responses, and errors are written to `logs/bot.log`
(rotating, 5 MB per file, 3 backups kept). The console only shows
`INFO`+ messages so normal runs aren't noisy; the file captures full
`DEBUG` detail (exact request params minus the signature, and full raw
response bodies) for troubleshooting.

Example log line:

```
2026-07-11 10:02:14 | INFO     | trading_bot.orders | Placing order: {'symbol': 'BTCUSDT', 'side': 'BUY', 'order_type': 'MARKET', 'quantity': '0.01', 'price': None, 'stop_price': None}
2026-07-11 10:02:14 | DEBUG    | trading_bot.client | Request -> POST https://testnet.binancefuture.com/fapi/v1/order | params={'symbol': 'BTCUSDT', 'side': 'BUY', 'quantity': '0.01', 'type': 'MARKET', 'timestamp': 1752224534000, 'recvWindow': 5000}
2026-07-11 10:02:14 | DEBUG    | trading_bot.client | Response <- status=200 body={"orderId": 3123456789, "status": "FILLED", ...}
2026-07-11 10:02:14 | INFO     | trading_bot.orders | Order placed successfully: orderId=3123456789 status=FILLED
```

Two sample log files demonstrating a successful MARKET order and a
successful LIMIT order should be placed in `logs/` as part of the
deliverable (`logs/market_order_sample.log`, `logs/limit_order_sample.log`),
generated by actually running the commands above against your own testnet
API keys.

## Running tests

```bash
pip install pytest
python -m pytest tests/ -v
```

10 unit tests cover symbol/side/type/quantity/price validation, including
edge cases (negative/zero quantity, missing price for LIMIT, missing
prices for STOP_LIMIT).

## Assumptions

- **Testnet only.** `BASE_URL` is hardcoded to
  `https://testnet.binancefuture.com`; there is no mainnet switch, since
  the task explicitly scopes this to testnet.
- **USDT-M perpetual futures only.** Symbol validation assumes pairs end
  in `USDT` (e.g. `BTCUSDT`), matching the task's "USDT-M" requirement.
  COIN-M contracts are out of scope.
- **`GTC` time-in-force** is used by default for LIMIT and STOP_LIMIT
  orders (not user-configurable via CLI, to keep the required argument
  surface minimal per the spec).
- **STOP_LIMIT** maps to Binance's native `STOP` order type (a stop-limit
  order on the futures API) rather than `STOP_MARKET`, since the bonus
  requirement asked for "Stop-Limit" specifically.
- **No order cancellation / position management** is implemented — the
  spec only requires placing orders, not managing them afterward.
- Quantities and prices are validated as positive decimals but are **not**
  checked against exchange-specific `LOT_SIZE` / `PRICE_FILTER` step
  sizes (would require an extra `/fapi/v1/exchangeInfo` call); Binance
  itself will reject orders that violate these filters, and that
  rejection is surfaced cleanly as an `APIRequestError`.

## Bonus implemented

- **Third order type:** STOP_LIMIT (mapped to Binance's `STOP` type).
- Structured `client` / `orders` / `validators` separation for
  readability and reuse.
- Rotating file logs + concise console output.
