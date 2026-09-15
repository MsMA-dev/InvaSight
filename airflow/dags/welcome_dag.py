from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

from pipelines.market_data import (
    check_api_availability,
    fetch_exchange_rates,
    fetch_metal_prices,
    fetch_daily_equity_prices,
)


with DAG(
    'daily_multi_resource_dag',
    default_args={
        'start_date': datetime(2026, 9, 5),
        'retries': 2,
        'retry_delay': timedelta(minutes=5),
    },
    schedule='0 23 * * *',
    catchup=False
) as dag:

    check_api_availability_task = PythonOperator(
        task_id='check_api_availability',
        python_callable=check_api_availability
    )

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

    # Fetch tasks run in parallel, but only after API availability is confirmed
    check_api_availability_task >> [
        fetch_exchange_rates_task,
        fetch_metal_prices_task,
        fetch_daily_equity_prices_task
    ]
