SNOWFLAKE_CONN = "snowflake_default"

# Points at the container root, so FILES takes the full blob path as uploaded
STAGE = "@INVASIGHT.RAW.INVASIGHT_AZURE_SAS_STAGE"

RAW_LEDGER = "INVASIGHT.RAW.LEDGER_TRANSACTIONS_RAW"
RAW_FX = "INVASIGHT.RAW.FX_RATES_RAW"
RAW_METALS = "INVASIGHT.RAW.METAL_PRICES_RAW"
RAW_EQUITY = "INVASIGHT.RAW.EQUITY_PRICES_RAW"


def _uploaded_blob(upload_task_id):
    # The upload task returns the blob path it wrote; Airflow renders this at run time
    return f"{{{{ ti.xcom_pull(task_ids='{upload_task_id}') }}}}"


# No ON_ERROR = CONTINUE: a bad file must fail the task so dbt doesn't run on
# missing data. Retries are safe because COPY's load history skips files it
# already loaded. LOADED_AT/_LOADED_AT are filled by their column defaults.

def copy_json_sql(table, upload_task_id):
    return f"""
COPY INTO {table} (RAW, FILE_NAME)
FROM (SELECT $1, METADATA$FILENAME FROM {STAGE})
FILES = ('{_uploaded_blob(upload_task_id)}')
FILE_FORMAT = (TYPE = JSON);
"""


def copy_ledger_sql(upload_task_id):
    # CSV columns in ledger.LEDGER_COLUMNS order; the trailing TOTAL column has
    # no RAW counterpart and is dropped. BATCH_ID is the file stem (run timestamp).
    return f"""
COPY INTO {RAW_LEDGER} (
    TRANSACTION_ID, CLIENT_ID, CLIENT_NAME, PORTFOLIO_ID, TICKER, TRANSACTION_TYPE,
    QUANTITY, PRICE, CURRENCY, FEE_AMOUNT, TRANSACTION_DATE, TRANSACTION_TS,
    BATCH_ID, FILE_NAME
)
FROM (
    SELECT $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
           SPLIT_PART(SPLIT_PART(METADATA$FILENAME, '/', -1), '.', 1),
           METADATA$FILENAME
    FROM {STAGE}
)
FILES = ('{_uploaded_blob(upload_task_id)}')
FILE_FORMAT = (TYPE = CSV SKIP_HEADER = 1 FIELD_OPTIONALLY_ENCLOSED_BY = '"');
"""
