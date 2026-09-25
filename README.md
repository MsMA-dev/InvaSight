# InvaSight

A data pipeline that pulls market and internal transaction data, lands it in Azure Blob Storage, loads it into Snowflake, and transforms it with dbt — orchestrated end-to-end by Airflow.

## Architecture

```
Airflow (Docker)
  ├── fetch/generate data  ──►  Azure Blob Storage
  └── (after upload)       ──►  dbt build over SSH, on a separate EC2 host
                                     │
                                     ▼
                          Snowflake (raw tables ← Snowflake Task ← Blob stage)
                                     │
                                     ▼
                        dbt: staging → intermediate → marts
```

Airflow's job stops at landing data in Blob and then kicking off the matching dbt models — it does not load data into Snowflake itself. A Snowflake Task, running on its own schedule, pulls from an external stage over the Blob container into the raw tables. (Airflow used to also call that load step directly via a SQL `CALL`, but that was redundant once the Snowflake Task existed, so it was removed.)

## Data sources

| Source | Provider | Notes / why |
|---|---|---|
| Internal ledger | generated in-house | No real ledger data available, so a synthetic 50,000-row ledger is generated per run, seeded from the run's timestamp so it's reproducible on retry. |
| Exchange rates | exchangeratesapi.io | Using the free tier, since this is a no-budget project and the free plan covers everything needed except one thing: it rejects a custom `base` currency (`base_currency_access_restricted`) and only ever returns EUR-based rates — a paid plan would lift that restriction. Rather than pay for it, the pipeline re-derives USD-based rates itself (triangulating through the EUR→USD rate) after fetching, to stay consistent with the other USD-based sources. |
| Metal prices | metalpriceapi.com | This API's plan does honor `base=USD` directly, so no conversion needed. Covers gold, silver, platinum, palladium (XAU/XAG/XPT/XPD). |
| Equity prices | Alpha Vantage (`TIME_SERIES_DAILY`) | Only supports US-listed tickers/ADRs — confirmed by testing that Tadawul (`.SR`) and Swiss (`.SW`) listings aren't supported at all on this endpoint. Tickers are US-listed companies/ETFs (AAPL, MSFT, SPY, GLD, GOOGL, IBM) plus the NYSE/NASDAQ ADR listings for Vodafone (`VOD`) and SAP (`SAP`) — both confirmed USD-denominated, not their home-exchange currencies. |

Every fetch validates its own data (all fields present, values positive/well-formed, expected symbols/tickers present) before uploading — failing fast rather than uploading partial or malformed data.

## Storage — Azure Blob Storage

Container `invasight-data`, accessed via `WasbHook`/`wasb_default` connection, authenticated with a SAS token (account-key signing) rather than Azure AD/a service principal, to keep credential setup simple. (Originally planned around S3; switched to Azure Blob instead.)

## Transformation — dbt

Project `dbt/invasight_transform`, layered `staging` (views) → `intermediate` (ephemeral) → `marts` (tables). dbt runs on a separate EC2 instance rather than inside the Airflow container; Airflow triggers it over SSH after each DAG's fetch/upload step completes, using dbt's `--select` graph operator (e.g. `source:ledger.internal_ledger+`) so only the models actually downstream of the data that just landed get rebuilt, not the whole project every run.

## Orchestration — Airflow

Two DAGs, both docker-composed with `apache/airflow`:

- **`internal_ledger_dag`** — every 45 minutes: generate the synthetic ledger → upload to Blob → dbt build (ledger models).
- **`daily_multi_resource_dag`** — daily at 23:00 UTC: check all upstream APIs are reachable → fetch exchange rates/metal prices/equity prices in parallel → upload each to Blob → dbt build (market data models).

Required Airflow connections/pools for the dbt step: `dbt_ec2_ssh` (SSH connection to the dbt EC2 host), `snowflake_default` (used elsewhere for direct Snowflake access), and the `dbt_ssh_pool` pool (caps concurrent SSH sessions to the dbt box at 1).

## Repo layout

```
doockerImageForDags/        Airflow (Dockerfile, docker-compose, DAGs, pipeline code)
  airflow/dags/
    pipelines/               fetch/generate + validation logic per source
    *.py                     the two DAGs
dbt/invasight_transform/    dbt project (staging/intermediate/marts models)
environment_setup/dbt/      docs for how dbt was installed/configured on the EC2 worker
SNOWFLAKE/                  placeholder folders mirroring the Snowflake schema layout
data_source/raw/            early local sample data snapshots (pre-Blob-storage)
.github/workflows/          CI/CD
```
