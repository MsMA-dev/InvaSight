import time

import requests

from pipelines.s3_utils import upload_json_to_s3


EXCHANGE_BASE_URL = "http://api.exchangeratesapi.io/v1/latest"
TICKERS = ["AAPL", "MSFT", "SPY", "GLD"]
BASE_URL = "https://www.alphavantage.co/query"


def fetch_exchange_rates(**kwargs):
    params = {
        "access_key": "9f4c589d5963842ccaf9e8d7db8aaad3",
        "symbols": "USD"
    }

    response = requests.get(EXCHANGE_BASE_URL, params=params)
    response.raise_for_status()

    raw_data = response.json()
    print("Exchange rates fetched successfully.")

    if raw_data.get("success"):
        upload_json_to_s3(raw_data, f"exchange_rates/{kwargs['ds']}.json")
    else:
        print(f"API Error: {raw_data}")


def fetch_metal_prices(**kwargs):
    base_url = "https://api.metalpriceapi.com/v1/latest"
    metals = {"XAU": "Gold", "XAG": "Silver", "XPT": "Platinum", "XPD": "Palladium"}
    params = {
        "api_key": "113af9100ddadc638fa89a91e9a46663",
        "base": "USD",
        "currencies": ",".join(metals.keys())
    }

    response = requests.get(base_url, params=params)
    response.raise_for_status()
    raw_data = response.json()

    upload_json_to_s3(raw_data, f"metal_prices/{kwargs['ds']}.json")


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
        upload_json_to_s3(raw_results, f"equity_prices/{kwargs['ds']}.json")
    else:
        print("No data retrieved.")
