import time

import requests

from pipelines.blob_utils import upload_json_to_blob


EXCHANGE_BASE_URL = "http://api.exchangeratesapi.io/v1/latest"
EXCHANGE_SYMBOLS = ["USD", "SAR", "GBP", "CHF"]
TICKERS = ["AAPL", "MSFT", "SPY", "GLD", "GOOGL", "IBM", "SAP", "VOD"]
BASE_URL = "https://www.alphavantage.co/query"
METAL_BASE_URL = "https://api.metalpriceapi.com/v1/latest"

API_ENDPOINTS = {
    "exchange_rates": EXCHANGE_BASE_URL,
    "metal_prices": METAL_BASE_URL,
    "equity_prices": BASE_URL,
}


def check_api_availability(**kwargs):
    """Fail fast if any upstream market data API is unreachable."""
    unavailable = []

    for name, url in API_ENDPOINTS.items():
        try:
            response = requests.get(url, timeout=10)
            print(f"{name} ({url}) responded with status {response.status_code}")
        except requests.exceptions.RequestException as exc:
            print(f"{name} ({url}) is unavailable: {exc}")
            unavailable.append(name)

    if unavailable:
        raise RuntimeError(f"Unavailable APIs: {', '.join(unavailable)}")


def validate_exchange_rates(data, symbols):
    if not data.get("success"):
        raise ValueError(f"Exchange rates API returned an error: {data}")

    rates = data.get("rates", {})
    invalid = [
        s for s in symbols
        if not isinstance(rates.get(s), (int, float)) or rates.get(s) <= 0
    ]
    if invalid:
        raise ValueError(f"Missing or invalid exchange rates for {invalid}: {rates}")


def validate_metal_prices(data, metals):
    if not data.get("success"):
        raise ValueError(f"Metal prices API returned an error: {data}")

    rates = data.get("rates", {})
    invalid = [
        m for m in metals
        if not isinstance(rates.get(m), (int, float)) or rates.get(m) <= 0
    ]
    if invalid:
        raise ValueError(f"Missing or invalid metal rates for {invalid}: {rates}")


def validate_equity_prices(raw_results, tickers):
    missing = [t for t in tickers if t not in raw_results]
    if missing:
        raise ValueError(f"Missing tickers in equity response: {missing}")

    for symbol, payload in raw_results.items():
        series = payload.get("Time Series (Daily)")
        if not series:
            raise ValueError(f"No daily time series for {symbol}: {payload}")

        for date, values in series.items():
            missing_fields = [
                f for f in ("1. open", "2. high", "3. low", "4. close", "5. volume")
                if f not in values
            ]
            if missing_fields:
                raise ValueError(f"Missing {missing_fields} for {symbol} on {date}")


def fetch_exchange_rates(**kwargs):
    params = {
        "access_key": "9f4c589d5963842ccaf9e8d7db8aaad3",
        "symbols": ",".join(EXCHANGE_SYMBOLS)
    }

    response = requests.get(EXCHANGE_BASE_URL, params=params)
    response.raise_for_status()

    raw_data = response.json()
    print("Exchange rates fetched successfully.")

    validate_exchange_rates(raw_data, EXCHANGE_SYMBOLS)
    upload_json_to_blob(raw_data, f"exchange_rates/exchange_rates/{kwargs['ds']}.json")


def fetch_metal_prices(**kwargs):
    metals = {"XAU": "Gold", "XAG": "Silver", "XPT": "Platinum", "XPD": "Palladium"}
    params = {
        "api_key": "113af9100ddadc638fa89a91e9a46663",
        "base": "USD",
        "currencies": ",".join(metals.keys())
    }

    response = requests.get(METAL_BASE_URL, params=params)
    response.raise_for_status()
    raw_data = response.json()

    validate_metal_prices(raw_data, metals.keys())
    upload_json_to_blob(raw_data, f"metal_prices/metal_prices/{kwargs['ds']}.json")


def fetch_daily_equity_prices(**kwargs):
    raw_results = {}

    for symbol in TICKERS:
        print(f"Fetching {symbol}...")
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": "compact",
            "apikey": "EFIRKT1KRYJCYC3D",
        }

        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()

        raw_results[symbol] = response.json()

        time.sleep(15)

    if raw_results:
        validate_equity_prices(raw_results, TICKERS)
        upload_json_to_blob(raw_results, f"equity_prices/equity_prices/{kwargs['ds']}.json")
    else:
        print("No data retrieved.")
