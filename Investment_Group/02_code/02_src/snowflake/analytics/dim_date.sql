{{ config(materialized='table') }}

WITH all_dates AS (

    SELECT transaction_date AS full_date FROM {{ ref('stg_ledger_transactions') }}
    UNION
    SELECT date AS full_date FROM {{ ref('stg_equity_prices') }}
    UNION
    SELECT api_timestamp::DATE AS full_date FROM {{ ref('stg_precious_metals') }}
    UNION
    SELECT rate_date AS full_date FROM {{ ref('stg_exchange_rates') }}

)

SELECT DISTINCT
    CAST(TO_CHAR(full_date, 'YYYYMMDD') AS INT) AS date_key,
    full_date,
    EXTRACT(YEAR FROM full_date) AS year,
    EXTRACT(MONTH FROM full_date) AS month,
    EXTRACT(DAY FROM full_date) AS day
FROM all_dates
WHERE full_date IS NOT NULL
