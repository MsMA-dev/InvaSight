create or replace   view INVASIGHT.STAGING.stg_precious_metals
  
  
  
  
  as (
    

WITH parsed AS (

    SELECT
        TRY_TO_BOOLEAN(RAW:success::STRING) AS success,
        RAW:base::STRING AS base_currency,

        TO_TIMESTAMP_NTZ(
            TRY_TO_NUMBER(RAW:timestamp::STRING)
        ) AS api_timestamp,

        TRY_TO_NUMBER(RAW:rates:USDXAU::STRING, 38, 12) AS gold_usd,
        TRY_TO_NUMBER(RAW:rates:USDXAG::STRING, 38, 12) AS silver_usd,
        TRY_TO_NUMBER(RAW:rates:USDXPT::STRING, 38, 12) AS platinum_usd,
        TRY_TO_NUMBER(RAW:rates:USDXPD::STRING, 38, 12) AS palladium_usd,

        FILE_NAME,
        LOADED_AT

    FROM INVASIGHT.RAW.METAL_PRICES_RAW

),

deduplicated AS (

    SELECT *
    FROM parsed

    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY api_timestamp
        ORDER BY loaded_at DESC, file_name DESC
    ) = 1

)

SELECT *
FROM deduplicated
  )
/* {"app": "dbt", "dbt_version": "1.12.4", "profile_name": "invasight_pipeline", "target_name": "prod", "node_id": "model.invasight_pipeline.stg_precious_metals"} */;