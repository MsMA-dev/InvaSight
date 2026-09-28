Staging models (dbt views over `INVASIGHT.RAW`), one subfolder per source.

- **Written by the dbt team:** Maryam Alotaibi, Hanoof Alassiri, Rawan Alaklabi
- `equity_prices/` and `exchange_rates/`: the versions deployed in Snowflake, recovered from Snowflake's
  query history by Fayha'a Alharbi (they include `file_name`, which the staging tests expect)
