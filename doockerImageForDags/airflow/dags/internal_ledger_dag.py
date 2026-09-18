from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

from pipelines.ledger import generate_internal_ledger


with DAG(
    "internal_ledger_dag",
    default_args={"start_date": datetime(2026, 9, 5), "retries": 2},
    schedule=timedelta(minutes=45),
    catchup=False,
    max_active_runs=1,
) as dag:

    generate_internal_ledger_task = PythonOperator(
        task_id="generate_internal_ledger",
        python_callable=generate_internal_ledger,
    )
