-- Recovered from Snowflake query history: the version Worker01 built on 2026-09-28 (not pushed to GitHub)
{{ config(materialized='view') }}

WITH raw_parsed AS (

    SELECT
        RAW:base::STRING AS base_currency,
        TO_DATE(RAW:date::STRING) AS rate_date,
        TO_TIMESTAMP_NTZ(TRY_TO_NUMBER(RAW:timestamp::STRING)) AS rate_timestamp,

        -- Flatten key-value pairs inside the rates JSON object
        f.key::STRING AS target_currency,
        TRY_CAST(f.value::STRING AS NUMBER(38, 6)) AS exchange_rate,

        FILE_NAME,
        LOADED_AT

    FROM {{ source('raw', 'fx_rates_raw') }},
    LATERAL FLATTEN(input => RAW:rates) f
    WHERE TRY_TO_BOOLEAN(RAW:success::STRING) = TRUE

),

deduplicated AS (

    SELECT
        rate_date,
        rate_timestamp,
        base_currency,
        target_currency,
        exchange_rate,
        FILE_NAME,
        LOADED_AT
    FROM raw_parsed
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY rate_date, base_currency, target_currency
        ORDER BY LOADED_AT DESC, FILE_NAME DESC
    ) = 1

)

SELECT * FROM deduplicated
