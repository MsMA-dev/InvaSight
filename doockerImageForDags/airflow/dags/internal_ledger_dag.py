from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
from datetime import datetime, timedelta

from pipelines.ledger import generate_internal_ledger
from pipelines.config import DBT_SSH_CONN, DBT_POOL, dbt_build_cmd


with DAG(
    "internal_ledger_dag",
    default_args={
        "start_date": datetime(2026, 9, 5),
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    schedule=timedelta(minutes=45),
    catchup=False,
    max_active_runs=1,
) as dag:

    generate_internal_ledger_task = PythonOperator(
        task_id="generate_internal_ledger",
        python_callable=generate_internal_ledger,
    )

    dbt_build = SSHOperator(
        task_id="dbt_build",
        ssh_conn_id=DBT_SSH_CONN,
        cmd_timeout=3600,  # default is 10s, which would kill dbt mid-run
        command=dbt_build_cmd("source:ledger.internal_ledger+"),
        pool=DBT_POOL,
    )

    generate_internal_ledger_task >> dbt_build