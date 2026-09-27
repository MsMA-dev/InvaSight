from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime, timedelta

from pipelines.ledger import generate_internal_ledger
from pipelines.config import DBT_SSH_CONN, DBT_POOL, dbt_build_cmd
from pipelines.snowflake_load import SNOWFLAKE_CONN, copy_ledger_sql


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

    load_ledger = SQLExecuteQueryOperator(
        task_id="load_ledger",
        conn_id=SNOWFLAKE_CONN,
        sql=copy_ledger_sql("generate_internal_ledger"),
        show_return_value_in_logs=True,
    )

    dbt_build = SSHOperator(
        task_id="dbt_build",
        ssh_conn_id=DBT_SSH_CONN,
        cmd_timeout=3600,  # default is 10s, which would kill dbt mid-run
        command=dbt_build_cmd("source:raw.ledger_transactions_raw+"),
        pool=DBT_POOL,
    )

    generate_internal_ledger_task >> load_ledger >> dbt_build
