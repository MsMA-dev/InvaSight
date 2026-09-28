with usd_rates as (

    select
        rate_date,
        target_currency,
        exchange_rate
    from {{ ref('stg_exchange_rates') }}
    where base_currency = 'USD'
      and exchange_rate > 0

),

usd_to_sar as (

    select
        rate_date,
        exchange_rate as usd_to_sar
    from usd_rates
    where target_currency = 'SAR'

)

select
    r.rate_date,
    r.target_currency as currency_code,
    s.usd_to_sar / r.exchange_rate as rate_to_sar
from usd_rates r
inner join usd_to_sar s
    on r.rate_date = s.rate_date
