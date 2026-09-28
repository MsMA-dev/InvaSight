-- Recovered from Snowflake query history: the version Worker01 built on 2026-09-28 (not pushed to GitHub)
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
        ROW_NUMBER() OVER (
            PARTITION BY ticker
            ORDER BY priority
        ) AS rn
    FROM combined_assets
    WHERE ticker IS NOT NULL
),
classified AS (
    SELECT
        ticker,
        asset_type,
        CASE
            WHEN ticker IN ('XAU', 'XAG', 'XPT', 'XPD') THEN 'METALS'
            WHEN ticker IN ('AAPL', 'MSFT', 'GOOGL', 'IBM', 'SAP') THEN 'TECHNOLOGY'
            WHEN ticker = 'VOD' THEN 'TELECOMMUNICATIONS'
            WHEN ticker = 'NESN.SW' THEN 'CONSUMER'
            WHEN ticker = '2222.SR' THEN 'ENERGY'
            WHEN ticker IN ('GLD', 'SPY') THEN 'ETF'
            ELSE 'OTHER'
        END AS sector
    FROM deduped
    WHERE rn = 1
)

SELECT
    MD5(ticker) AS asset_key,
    ticker,
    ticker AS asset_name,
    asset_type,
    sector
FROM classified
