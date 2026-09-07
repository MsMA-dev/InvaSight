from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import requests
import json
import time


def fetch_exchange_rates():
    params = {
        "access_key": "9f4c589d5963842ccaf9e8d7db8aaad3",
        "symbols": "USD" 
    }

    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()

    raw_data = response.json()
    print("Exchange rates fetched successfully.")

    if raw_data.get("success"):
        # Dump raw JSON payload directly to staging for Snowflake loading
        output_path = "/tmp/raw_exchange_rates.json"
        with open(output_path, "w") as f:
            json.dump(raw_data, f)
        print(f"Raw API payload saved successfully to {output_path}")
    else:
        print(f"API Error: {raw_data}")

def fetch_metal_prices():
    base_url = "https://api.metalpriceapi.com/v1/latest"
    metals = {"XAU": "Gold", "XAG": "Silver", "XPT": "Platinum", "XPD": "Palladium"}
    params = {
        "api_key": "113af9100ddadc638fa89a91e9a46663",
        "base": "USD",
        "currencies": ",".join(metals.keys())
    }
    
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    raw_data = response.json()  # 1. Parse JSON from response
    
    # 2. Open file in write mode ('w') and save it
    output_path = "/tmp/raw_metal_prices.json"
    with open(output_path, "w") as f:
        json.dump(raw_data, f)
        
    print("Metal prices fetched and saved successfully.")



TICKERS = ["AAPL", "MSFT", "SPY", "GLD"]
BASE_URL = "https://www.alphavantage.co/query"


def fetch_daily_equity_prices():
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
        output_path = "/tmp/raw_equity_prices.json"
        with open(output_path, "w") as f:
            json.dump(raw_results, f)
        print(f"Raw API payload saved successfully to {output_path}")
    else:
        print("No data retrieved.")


with DAG(
    'daily_multi_resource_dag',
    default_args={'start_date': datetime(2026, 9, 5)},
    schedule='0 23 * * *',
    catchup=False
) as dag:


    fetch_exchange_rates_task = PythonOperator(
        task_id='fetch_exchange_rates',
        python_callable=fetch_exchange_rates
    )

    fetch_metal_prices_task = PythonOperator(
        task_id='fetch_metal_prices',
        python_callable=fetch_metal_prices
    )

    fetch_daily_equity_prices_task = PythonOperator(
        task_id='fetch_daily_equity_prices',
        python_callable=fetch_daily_equity_prices
    )

    # All tasks run in parallel (no dependencies between them)
    [
        fetch_exchange_rates_task,
        fetch_metal_prices_task,
        fetch_daily_equity_prices_task
    ]