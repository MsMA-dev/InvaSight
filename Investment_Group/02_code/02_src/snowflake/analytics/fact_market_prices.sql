-- Recovered from Snowflake query history: the version Worker01 built on 2026-09-28 (not pushed to GitHub)
WITH int_fx_rates_to_sar AS (
with rates as (

    select
        rate_date,
        base_currency,
        target_currency,
        exchange_rate
    from {{ ref('stg_exchange_rates') }}
    where exchange_rate > 0

),

-- Loads that already arrived USD-based (preferred when both exist)
usd_native as (

    select
        rate_date,
        target_currency,
        exchange_rate as usd_to_currency,
        0 as priority
    from rates
    where base_currency = 'USD'

),

eur_to_usd as (

    select
        rate_date,
        exchange_rate as eur_to_usd
    from rates
    where base_currency = 'EUR'
      and target_currency = 'USD'

),

-- Legacy EUR-based loads converted to a USD base
usd_rebased as (

    select
        r.rate_date,
        r.target_currency,
        r.exchange_rate / e.eur_to_usd as usd_to_currency,
        1 as priority
    from rates r
    inner join eur_to_usd e
        on r.rate_date = e.rate_date
    where r.base_currency = 'EUR'

    union all

    -- EUR is the base of those loads, so it never appears in their rates
    select
        rate_date,
        'EUR' as target_currency,
        1 / eur_to_usd as usd_to_currency,
        1 as priority
    from eur_to_usd

),

-- One USD-based rate per date and currency
usd_rates as (

    select
        rate_date,
        target_currency,
        usd_to_currency
    from (
        select * from usd_native
        union all
        select * from usd_rebased
    )
    qualify row_number() over (
        partition by rate_date, target_currency
        order by priority
    ) = 1

),

usd_to_sar as (

    select
        rate_date,
        usd_to_currency as usd_to_sar
    from usd_rates
    where target_currency = 'SAR'

)

-- SAR per 1 unit of currency = usd_to_sar / usd_to_currency
select
    r.rate_date,
    r.target_currency as currency_code,
    s.usd_to_sar / r.usd_to_currency as rate_to_sar
from usd_rates r
inner join usd_to_sar s
    on r.rate_date = s.rate_date
), equity_prices AS (
    SELECT
        ticker,
        date,
        close_price AS price,
        'USD' AS currency_code,
        'EQUITY_API' AS source_name,
        loaded_at
    FROM {{ ref('stg_equity_prices') }}
),

-- One row per metal per day (USD per troy ounce), so metal holdings get a market price
metals AS (
    SELECT * FROM {{ ref('stg_precious_metals') }} WHERE success
),

metal_prices AS (
    SELECT 'XAU' AS ticker, api_timestamp::DATE AS date, gold_usd AS price, 'USD' AS currency_code, 'Metal Market Data' AS source_name, loaded_at FROM metals WHERE gold_usd IS NOT NULL
    UNION ALL
    SELECT 'XAG', api_timestamp::DATE, silver_usd, 'USD', 'Metal Market Data', loaded_at FROM metals WHERE silver_usd IS NOT NULL
    UNION ALL
    SELECT 'XPT', api_timestamp::DATE, platinum_usd, 'USD', 'Metal Market Data', loaded_at FROM metals WHERE platinum_usd IS NOT NULL
    UNION ALL
    SELECT 'XPD', api_timestamp::DATE, palladium_usd, 'USD', 'Metal Market Data', loaded_at FROM metals WHERE palladium_usd IS NOT NULL
),

staging_prices AS (
    SELECT * FROM equity_prices
    UNION ALL
    SELECT * FROM metal_prices
),

-- Most recent SAR rate on or before each price date (see fact_holdings).
-- No fallback: a missing rate leaves exchange_rate / price_sar NULL.
prices_with_fx AS (
    SELECT
        p.*,
        fx.rate_date   AS fx_rate_date,
        fx.rate_to_sar
    FROM staging_prices p
    ASOF JOIN int_fx_rates_to_sar fx
        MATCH_CONDITION (p.date >= fx.rate_date)
        ON p.currency_code = fx.currency_code
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

joined AS (
    SELECT
        a.asset_key,
        d.date_key,
        curr.currency_key,
        COALESCE(s.source_key, md5('EQUITY_API')) AS source_key,
        p.price,
        p.rate_to_sar AS exchange_rate,
        p.fx_rate_date,
        p.price * p.rate_to_sar AS price_sar,
        p.loaded_at
    FROM prices_with_fx p
    INNER JOIN dim_asset a ON p.ticker = a.ticker
    INNER JOIN dim_date d ON p.date = d.full_date
    LEFT JOIN dim_currency curr ON p.currency_code = curr.currency_code
    LEFT JOIN dim_source s ON s.source_name = p.source_name
)

SELECT
    md5(cast(coalesce(cast(asset_key as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(date_key as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(source_key as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) AS market_price_key,
    asset_key,
    date_key,
    currency_key,
    source_key,
    price,
    exchange_rate,
    fx_rate_date,
    price_sar,
    loaded_at
FROM joined
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY asset_key, date_key, source_key
    ORDER BY loaded_at DESC
) = 1
