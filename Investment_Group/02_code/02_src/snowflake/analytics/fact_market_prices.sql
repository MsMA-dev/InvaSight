WITH staging_prices AS (
    SELECT
        ticker,
        date,
        close_price AS price,
        'USD' AS currency_code,
        loaded_at
    FROM {{ ref('stg_equity_prices') }}
),

dim_source AS (
    SELECT source_key, source_name FROM {{ ref('dim_source') }}
),

dim_asset AS (
    SELECT asset_key, ticker FROM {{ ref('dim_asset') }}
),

dim_date AS (
    SELECT date_key, full_date FROM {{ ref('dim_date') }}
),

dim_currency AS (
    SELECT currency_key, currency_code FROM {{ ref('dim_currency') }}
),

fx AS (
    SELECT * FROM {{ ref('stg_exchange_rates') }}
    WHERE base_currency = 'USD'
),

joined AS (
    SELECT
        a.asset_key,
        d.date_key,
        curr.currency_key,
        COALESCE(s.source_key, md5('EQUITY_API')) AS source_key,
        p.price,
        COALESCE(fx.exchange_rate, 1.0) AS exchange_rate,
        (p.price * COALESCE(fx.exchange_rate, 1.0)) AS price_sar,
        p.loaded_at
    FROM staging_prices p
    INNER JOIN dim_asset a ON p.ticker = a.ticker
    INNER JOIN dim_date d ON p.date = d.full_date
    LEFT JOIN dim_currency curr ON p.currency_code = curr.currency_code
    LEFT JOIN fx ON p.date = fx.rate_date AND p.currency_code = fx.target_currency
    LEFT JOIN dim_source s ON LOWER(s.source_name) LIKE '%equity%' OR LOWER(s.source_name) LIKE '%external%'
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['asset_key', 'date_key', 'source_key']) }} AS market_price_key,
    asset_key,
    date_key,
    currency_key,
    source_key,
    price,
    exchange_rate,
    price_sar,
    loaded_at
FROM joined
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY asset_key, date_key, source_key
    ORDER BY loaded_at DESC
) = 1
