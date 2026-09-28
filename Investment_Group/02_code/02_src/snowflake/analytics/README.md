# Analytics models as deployed in Snowflake

These are the versions of the analytics models that built the `INVASIGHT.ANALYTICS`
tables the Power BI dashboard reads. They are newer than the copies in
`02_src/dbt/invasight_transform/models/analytics/`, which don't produce the columns the
dashboard uses (`TOTAL_INVESTMENT`, `DAILY_RETURN`, `PNL_SAR`, `CURRENCY_EXPOSURE_SAR`,
`SECTOR`, `ASSET_NAME`, `SIGNED_QUANTITY`, `FX_RATE_DATE`).

This folder holds the complete analytics layer (5 dimensions + 3 facts). `dim_client`,
`dim_currency`, `dim_date` and `dim_source` are the same as in `02_src/dbt/`; `dim_asset`
and the three fact models are the newer deployed versions.

## Credits
- **Analytics models:** Rawan Alaklabi
- **FX-to-SAR conversion** (`int_fx_rates_to_sar`, included as a CTE in
  `fact_holdings` and `fact_market_prices`): Maryam Alotaibi
- **Recovered from Snowflake's query history:** Fayha'a Alharbi

## Why "recovered"
When the server had to be shut down, they were rebuilt from the SQL that dbt had executed,
which Snowflake keeps in `INFORMATION_SCHEMA.QUERY_HISTORY`. With these files in the
dbt project, `dbt build` passes all 61 tests.
