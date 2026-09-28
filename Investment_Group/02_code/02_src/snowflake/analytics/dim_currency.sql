{{ config(materialized='table') }}

SELECT DISTINCT
    MD5(currency_code) AS currency_key,
    currency_code
FROM (
    SELECT currency_code FROM {{ ref('stg_ledger_transactions') }}
    UNION
    SELECT target_currency AS currency_code FROM {{ ref('stg_exchange_rates') }}
)
WHERE currency_code IS NOT NULL
