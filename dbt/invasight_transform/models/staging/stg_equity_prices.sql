-- models/staging/stg_equity_prices.sql

with source as (
    select
        raw,
        file_name,
        loaded_at
    from {{ source('raw', 'equity_prices_raw') }}
),

-- Step 1: flatten to per-ticker level (outer JSON keys)
tickers as (
    select
        source.file_name,
        source.loaded_at,
        ticker_flat.key as ticker,
        ticker_flat.value as ticker_data
    from source,
    lateral flatten(input => parse_json(source.raw)) as ticker_flat
    where ticker_flat.key != 'Meta Data'  -- some Alpha Vantage payloads include a top-level Meta Data too
),

-- Step 2: flatten to per-date level (nested inside "Time Series (Daily)")
dates_flat as (
    select
        tickers.file_name,
        tickers.loaded_at,
        tickers.ticker,
        date_flat.key as trade_date,
        date_flat.value as ohlcv
    from tickers,
    lateral flatten(input => tickers.ticker_data:"Time Series (Daily)") as date_flat
),

-- Step 3: extract and cast fields
cleaned as (
    select
        ticker,
        try_to_date(trade_date) as trade_date,
        try_to_double(ohlcv:"1. open"::string) as open_price,
        try_to_double(ohlcv:"2. high"::string) as high_price,
        try_to_double(ohlcv:"3. low"::string) as low_price,
        try_to_double(ohlcv:"4. close"::string) as close_price,
        try_to_number(ohlcv:"5. volume"::string) as volume,
        file_name,
        loaded_at,
        'alpha_vantage_live' as source
    from dates_flat
),

-- Step 4: deduplicate — same ticker+date can appear across multiple pulls;
-- keep the most recently loaded version
deduped as (
    select
        *,
        row_number() over (
            partition by ticker, trade_date
            order by loaded_at desc
        ) as rn
    from cleaned
)

select
    ticker,
    trade_date as date,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    source,
    loaded_at
from deduped
where rn = 1
