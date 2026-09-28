# dbt models recovered from Snowflake

These are the dbt models that were running on the **Worker01** EC2 instance on 2026-09-28
but were **never pushed to GitHub**. Worker01 was compromised (root SSH brute-forced) and has
been stopped, so the code was recovered from Snowflake instead.

The versions in `dbt/invasight_transform/models/` on GitHub are **older**: they don't produce
the columns the Power BI dashboard uses, so running them breaks the dashboard.

| Model | What GitHub's version is missing |
|---|---|
| `fact_daily_portfolio_summary` | `TOTAL_INVESTMENT`, `DAILY_RETURN`, `PNL_SAR`, `CURRENCY_EXPOSURE_SAR` |
| `dim_asset` | `ASSET_NAME`, `SECTOR` |
| `fact_holdings` | `SIGNED_QUANTITY`, `FX_RATE_DATE` |
| `fact_market_prices` | `FX_RATE_DATE` |
| `stg_*` (all four staging models) | `FILE_NAME`, which the staging tests in `schema.yml` expect |

## How they were recovered

dbt compiles each model to plain SQL and sends it to Snowflake as a `CREATE TABLE ... AS SELECT`
(or `CREATE VIEW`). Snowflake keeps the full text of every query, so the last successful
builds by Worker01's dbt user (`MSMA`) were read back with:

```sql
SELECT start_time, query_text
FROM TABLE(INVASIGHT.INFORMATION_SCHEMA.QUERY_HISTORY(
       END_TIME_RANGE_START => DATEADD('day', -3, CURRENT_TIMESTAMP()), RESULT_LIMIT => 10000))
WHERE user_name = 'MSMA' AND execution_status = 'SUCCESS'
  AND query_type IN ('CREATE_TABLE_AS_SELECT', 'CREATE_VIEW')
ORDER BY start_time DESC;
```

- Analytics models: last built at 06:45 Snowflake time (16:45 Riyadh). Worker01's final build of any model; none failed.
- Market staging views: last built at 01:07 by the daily market DAG.

## Folders

- `compiled_sql_from_query_history/` - the exact SQL Snowflake executed, untouched.
- `models/` - the same SQL turned back into dbt models:
  - the `create or replace ... as (` wrapper and dbt's trailing comment removed
  - fully qualified names turned back into `{{ ref(...) }}` / `{{ source('raw', ...) }}`
  - the ephemeral model `int_fx_rates_to_sar`, which dbt inlines, kept as a normal CTE

## Verified

Dropped into `dbt/invasight_transform/models/` in place of the GitHub versions, a full
`dbt build` passes **73/73** (12 models, 61 tests), and every column the Power BI model
expects exists in Snowflake again.

## Limits

- Only code that **ran** is in the log: edits saved on Worker01 after 06:45 but never run are not here.
- Macros come back already expanded (e.g. `dbt_utils.generate_surrogate_key` appears as the `md5(...)` it produces).
- YAML (`schema.yml` tests and docs) is never sent as a query, so it isn't recoverable this way.
  The existing `schema.yml` files on GitHub still pass against these models.
- `INFORMATION_SCHEMA.QUERY_HISTORY` only keeps 7 days (until about 2026-10-05).
