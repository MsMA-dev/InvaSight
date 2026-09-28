{{ config(materialized='table') }}

WITH equity_assets AS (
    SELECT DISTINCT ticker, 'EQUITY' AS asset_type, 1 AS priority
    FROM {{ ref('stg_equity_prices') }}
),
metal_assets AS (
    SELECT ticker, 'METAL' AS asset_type, 0 AS priority
    FROM (VALUES ('XAU'), ('XAG'), ('XPT'), ('XPD')) AS t(ticker)
),
ledger_assets AS (
    SELECT DISTINCT ticker, 'EQUITY' AS asset_type, 2 AS priority
    FROM {{ ref('stg_ledger_transactions') }}
    WHERE ticker IS NOT NULL
),
combined_assets AS (
    SELECT * FROM equity_assets
    UNION ALL
    SELECT * FROM metal_assets
    UNION ALL
    SELECT * FROM ledger_assets
),
deduped AS (
    SELECT
        ticker,
        asset_type,
        ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY priority) AS rn
    FROM combined_assets
    WHERE ticker IS NOT NULL
)

SELECT
    MD5(ticker) AS asset_key,
    ticker,
    asset_type
FROM deduped
WHERE rn = 1
