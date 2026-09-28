{{ config(materialized='table') }}

WITH daily_positions AS (
    SELECT
        client_key,
        date_key,
        asset_key,
        SUM(quantity) AS total_quantity,
        SUM(fees) AS total_fees
    FROM {{ ref('fact_holdings') }}
    GROUP BY client_key, date_key, asset_key
),

daily_market_prices AS (
    SELECT
        date_key,
        asset_key,
        price_sar
    FROM {{ ref('fact_market_prices') }}
)

SELECT
    MD5(p.client_key || '_' || CAST(p.date_key AS STRING)) AS portfolio_summary_key,
    p.date_key,
    p.client_key,
    SUM(p.total_quantity * COALESCE(m.price_sar, 0)) AS portfolio_value_sar,
    SUM(p.total_fees) AS total_fees
FROM daily_positions p
LEFT JOIN daily_market_prices m
    ON p.date_key = m.date_key
   AND p.asset_key = m.asset_key
GROUP BY p.client_key, p.date_key
