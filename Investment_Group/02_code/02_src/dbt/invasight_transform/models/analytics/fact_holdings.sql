{{ config(materialized='table') }}

WITH ledger AS (

    SELECT * FROM {{ ref('stg_ledger_transactions') }}

),

fx AS (

    SELECT * FROM {{ ref('stg_exchange_rates') }}
    WHERE base_currency = 'USD'

),

joined AS (

    SELECT
        MD5(l.transaction_id) AS holding_key,
        d.date_key,
        a.asset_key,
        c.client_key,
        curr.currency_key,
        l.transaction_type,
        l.quantity,
        l.price,
        COALESCE(fx.exchange_rate, 1.0) AS exchange_rate,
        l.fees,
        (l.quantity * l.price) AS transaction_value,
        ((l.quantity * l.price) * COALESCE(fx.exchange_rate, 1.0)) AS value_sar

    FROM ledger l
    LEFT JOIN {{ ref('dim_date') }} d
        ON l.transaction_date = d.full_date
    LEFT JOIN {{ ref('dim_asset') }} a
        ON l.ticker = a.ticker
    LEFT JOIN {{ ref('dim_client') }} c
        ON l.client_id = c.client_id
    LEFT JOIN {{ ref('dim_currency') }} curr
        ON l.currency_code = curr.currency_code
    LEFT JOIN fx
        ON l.transaction_date = fx.rate_date
       AND l.currency_code = fx.target_currency

)

SELECT
    holding_key,
    date_key,
    asset_key,
    client_key,
    currency_key,
    transaction_type,
    quantity,
    price,
    exchange_rate,
    fees,
    transaction_value,
    value_sar
FROM joined
