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
), ledger AS (

    SELECT * FROM {{ ref('stg_ledger_transactions') }}

),

-- Attach the most recent SAR rate on or before each transaction date.
-- FX is fetched once a day (23:00 UTC), so same-day transactions earlier in
-- the day, and weekend/holiday dates, use the latest published rate.
-- ASOF JOIN behaves like a LEFT JOIN: if no rate exists yet, the FX columns
-- stay NULL instead of silently defaulting to 1.0.
ledger_with_fx AS (

    SELECT
        l.*,
        fx.rate_date   AS fx_rate_date,
        fx.rate_to_sar
    FROM ledger l
    ASOF JOIN int_fx_rates_to_sar fx
        MATCH_CONDITION (l.transaction_date >= fx.rate_date)
        ON l.currency_code = fx.currency_code

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
        CASE l.transaction_type
            WHEN 'BUY'  THEN l.quantity
            WHEN 'SELL' THEN -l.quantity
        END AS signed_quantity,
        l.price,
        l.rate_to_sar AS exchange_rate,
        l.fx_rate_date,
        l.fees,
        (l.quantity * l.price) AS transaction_value,
        (l.quantity * l.price) * l.rate_to_sar AS value_sar

    FROM ledger_with_fx l
    LEFT JOIN {{ ref('dim_date') }} d
        ON l.transaction_date = d.full_date
    LEFT JOIN {{ ref('dim_asset') }} a
        ON l.ticker = a.ticker
    LEFT JOIN {{ ref('dim_client') }} c
        ON l.client_id = c.client_id
    LEFT JOIN {{ ref('dim_currency') }} curr
        ON l.currency_code = curr.currency_code

)

SELECT
    holding_key,
    date_key,
    asset_key,
    client_key,
    currency_key,
    transaction_type,
    quantity,
    signed_quantity,
    price,
    exchange_rate,
    fx_rate_date,
    fees,
    transaction_value,
    value_sar
FROM joined
