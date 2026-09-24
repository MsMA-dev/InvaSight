from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from datetime import datetime, timedelta

from pipelines.market_data import (
    check_api_availability,
    fetch_exchange_rates,
    fetch_metal_prices,
    fetch_daily_equity_prices,
)
from pipelines.config import SNOWFLAKE_CONN, DBT_SSH_CONN, DBT_POOL, dbt_build_cmd


with DAG(
    "daily_multi_resource_dag",
    default_args={
        "start_date": datetime(2026, 9, 5),
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    schedule="0 23 * * *",
    catchup=False,
    max_active_runs=1,
) as dag:

    check_api_availability_task = PythonOperator(
        task_id="check_api_availability",
        python_callable=check_api_availability,
    )

    fetch_exchange_rates_task = PythonOperator(
        task_id="fetch_exchange_rates",
        python_callable=fetch_exchange_rates,
    )
    fetch_metal_prices_task = PythonOperator(
        task_id="fetch_metal_prices",
        python_callable=fetch_metal_prices,
    )
    fetch_daily_equity_prices_task = PythonOperator(
        task_id="fetch_daily_equity_prices",
        python_callable=fetch_daily_equity_prices,
    )

    load_exchange_rates = SQLExecuteQueryOperator(
        task_id="load_exchange_rates",
        conn_id=SNOWFLAKE_CONN,
        sql="CALL raw.market_data.load_exchange_rates();",
    )
    load_metal_prices = SQLExecuteQueryOperator(
        task_id="load_metal_prices",
        conn_id=SNOWFLAKE_CONN,
        sql="CALL raw.market_data.load_metal_prices();",
    )
    load_equity_prices = SQLExecuteQueryOperator(
        task_id="load_equity_prices",
        conn_id=SNOWFLAKE_CONN,
        sql="CALL raw.market_data.load_equity_prices();",
    )

    dbt_build = SSHOperator(
        task_id="dbt_build",
        ssh_conn_id=DBT_SSH_CONN,
        cmd_timeout=3600,  # default is 10s, which would kill dbt mid-run
        command=dbt_build_cmd(
            "source:market_data.exchange_rates+",
            "source:market_data.metal_prices+",
            "source:market_data.equity_prices+",
        ),
        pool=DBT_POOL,
    )

    check_api_availability_task >> [
        fetch_exchange_rates_task,
        fetch_metal_prices_task,
        fetch_daily_equity_prices_task,
    ]

    fetch_exchange_rates_task >> load_exchange_rates
    fetch_metal_prices_task >> load_metal_prices
    fetch_daily_equity_prices_task >> load_equity_prices

    [load_exchange_rates, load_metal_prices, load_equity_prices] >> dbt_build