Samples of the Snowflake `INVASIGHT.RAW` tables, one subfolder per source, exported as CSV the way
Snowflake shows them: same columns and order as each table, values formatted by Snowflake. In the
FX, metals and equity tables the `RAW` column is a VARIANT holding one full API response per row.
They show the data after Airflow's `COPY INTO` load; `02_code/01_data/` holds it as it landed in Azure.
