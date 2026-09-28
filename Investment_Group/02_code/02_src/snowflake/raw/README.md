Samples of the Snowflake `INVASIGHT.RAW` tables, one subfolder per source. The `*_raw.jsonl`
and `ledger_transactions_raw.csv` files have the same columns and order as their tables
(JSON Lines = one row per line); they show the data after Airflow's `COPY INTO` load.
`02_code/01_data/` holds the same data as it landed in Azure.
