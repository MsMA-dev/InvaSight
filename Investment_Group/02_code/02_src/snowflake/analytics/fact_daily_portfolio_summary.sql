-- Recovered from Snowflake query history: the version Worker01 built on 2026-09-28 (not pushed to GitHub)
WITH daily_positions AS (
    SELECT
        client_key,
        date_key,
        asset_key,
        SUM(quantity) AS total_quantity,
        SUM(value_sar) AS total_investment,
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
),

position_prices AS (
    SELECT
        p.client_key,
        p.date_key,
        p.asset_key,
        p.total_quantity,
        p.total_investment,
        p.total_fees,
        COALESCE(m.price_sar, 0) AS price_sar
    FROM daily_positions p
    LEFT JOIN daily_market_prices m
        ON p.asset_key = m.asset_key
       AND m.date_key <= p.date_key
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY p.client_key, p.date_key, p.asset_key
        ORDER BY m.date_key DESC
    ) = 1
),

portfolio_aggregated AS (
    SELECT
        p.client_key,
        p.date_key,
        SUM(p.total_investment) AS total_investment,
        SUM(p.total_quantity * p.price_sar) AS portfolio_value_sar,
        SUM(p.total_fees) AS total_fees
    FROM position_prices p
    GROUP BY p.client_key, p.date_key
),

with_pnl AS (
    SELECT
        client_key,
        date_key,

        CAST(total_investment AS NUMBER(38,4)) AS total_investment,

        CAST(portfolio_value_sar AS NUMBER(38,4)) AS portfolio_value_sar,

        CAST(total_fees AS NUMBER(38,4)) AS total_fees,

        -- PnL = Current Portfolio Value - Total Investment
        CAST(
            portfolio_value_sar - total_investment
            AS NUMBER(38,4)
        ) AS pnl_sar,

        -- Daily Return = (Current Value - Previous Value) / Previous Value
        CAST(
            COALESCE(
                (
                    portfolio_value_sar
                    - LAG(portfolio_value_sar)
                      OVER (
                          PARTITION BY client_key
                          ORDER BY date_key
                      )
                )
                /
                NULLIF(
                    LAG(portfolio_value_sar)
                    OVER (
                        PARTITION BY client_key
                        ORDER BY date_key
                    ),
                    0
                ),
                0
            )
            AS NUMBER(38,6)
        ) AS daily_return,

        -- Current portfolio exposure in SAR
        CAST(
            portfolio_value_sar
            AS NUMBER(38,4)
        ) AS currency_exposure_sar

    FROM portfolio_aggregated
)

SELECT
    ABS(HASH(client_key, date_key)) AS portfolio_summary_key,

    CAST(date_key AS NUMBER(38,0)) AS date_key,

    -- Keep CLIENT_KEY compatible with DIM_CLIENT
    client_key,

    total_investment,
    portfolio_value_sar,
    total_fees,
    daily_return,
    pnl_sar,
    currency_exposure_sar

FROM with_pnl
