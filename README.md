# InvaSight

A data pipeline that pulls market and internal transaction data, lands it in Azure Blob Storage, loads it into Snowflake, and transforms it with dbt — orchestrated end-to-end by Airflow.

## Items
[Source Inventory and selection reasoning](#data-sources)

[Extraction scripts(ledger)](https://github.com/MsMA-dev/InvaSight/blob/main/doockerImageForDags/airflow/dags/pipelines/ledger.py)

[Extraction scripts(market)](https://github.com/MsMA-dev/InvaSight/blob/main/doockerImageForDags/airflow/dags/pipelines/market_data.py)

[dbt project (models, tests, docs)](dbt/invasight_transform/models)

[dbt project (tests, docs)](dbt/invasight_transform/tests)

[dbt project (docs)]()


[grain](#grain)

[schema](schema.pdf)

[how to run](#how-to-run)


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


## Grain

 FACT_HOLDINGS: one row per transaction. Each row represents a single BUY or SELL transaction by a client for an asset, in one currency, on one date. A client can have multiple transactions for the same asset on the same day. Current positions are derived by netting BUY and SELL quantities.

FACT_MARKET_PRICES: one row per asset, date, and source. Each row represents the closing market price reported by a source for an asset on a specific date, together with the exchange rate and SAR-converted price.

FACT_DAILY_PORTFOLIO_SUMMARY: one row per client and date. Each row represents a client’s daily portfolio summary, including investment, portfolio value, fees, return, P&L, and currency exposure in SAR.

Dimension tables: one row per business entity: DIM_DATE (one per calendar date), DIM_ASSET (one per asset), DIM_CLIENT (one per client), DIM_CURRENCY (one per currency), and DIM_SOURCE (one per data source). Fact tables reference these dimensions through their respective keys.


## Storage — Azure Blob Storage

Container `invasight-data`, accessed via `WasbHook`/`wasb_default` connection, authenticated with a SAS token (account-key signing) rather than Azure AD/a service principal, to keep credential setup simple. (Originally planned around S3; switched to Azure Blob instead.)

## Transformation — dbt

Project `dbt/invasight_transform`, layered `staging` (views) → `intermediate` (ephemeral) → `marts` (tables). dbt runs on a separate EC2 instance rather than inside the Airflow container; Airflow triggers it over SSH after each DAG's fetch/upload step completes, using dbt's `--select` graph operator (e.g. `source:ledger.internal_ledger+`) so only the models actually downstream of the data that just landed get rebuilt, not the whole project every run.

## Orchestration — Airflow

Two DAGs, both docker-composed with `apache/airflow`:

- **`internal_ledger_dag`** — every 45 minutes: generate the synthetic ledger → upload to Blob → dbt build (ledger models).
- **`daily_multi_resource_dag`** — daily at 23:00 UTC: check all upstream APIs are reachable → fetch exchange rates/metal prices/equity prices in parallel → upload each to Blob → dbt build (market data models).

Required Airflow connections/pools for the dbt step: `dbt_ec2_ssh` (SSH connection to the dbt EC2 host), `snowflake_default` (used elsewhere for direct Snowflake access), and the `dbt_ssh_pool` pool (caps concurrent SSH sessions to the dbt box at 1).

## How to run

### Prerequisites

- Docker Desktop (with Docker Compose v2)
- Access to the Azure Blob container `invasight-data` (storage account name + SAS token)
- SSH access to the dbt EC2 worker (set up per [environment_setup/dbt](environment_setup/dbt/README.md))
- Optional, for local dbt checks: Python 3.10+ with `dbt-core` and `dbt-snowflake`

### 1. Start Airflow

```bash
git clone https://github.com/MsMA-dev/InvaSight.git
cd InvaSight/doockerImageForDags
docker compose up -d --build
```

This builds the image from `dockerfile` (Airflow 3.3.2 + Azure and SSH providers) and runs `airflow standalone`. The `airflow/` folder is mounted into the container, so the database, logs and generated data persist between restarts (all gitignored).

Wait ~30 seconds, then open **http://localhost:30000**.

- Username: `admin`
- Password: generated on first start, in `doockerImageForDags/airflow/simple_auth_manager_passwords.json.generated`

Health check: `curl http://localhost:30000/api/v2/monitor/health` should report `metadatabase`, `scheduler` and `dag_processor` as `healthy`.

### 2. Configure connections and the pool

In the UI under **Admin → Connections**, add:

| Connection ID | Type | Fields |
|---|---|---|
| `wasb_default` | Azure Blob Storage | Login: storage account name; SAS token: your SAS token |
| `dbt_ec2_ssh` | SSH | Host: EC2 public DNS/IP; Username: `ubuntu`; Extra: `{"key_file": "/opt/airflow/<your-key>.pem"}` (place the key inside `doockerImageForDags/airflow/` so the container can see it — it is not gitignored, so don't commit it) |

Then create the pool that limits dbt runs to one SSH session at a time:

```bash
docker compose exec test airflow pools set dbt_ssh_pool 1 "Limit concurrent SSH sessions to the dbt EC2 host"
```

### 3. Check the DAGs loaded

```bash
docker compose exec test airflow dags list-import-errors   # expect: No data found
docker compose exec test airflow dags list                 # expect internal_ledger_dag and daily_multi_resource_dag
```

### 4. Run the pipeline

Both DAGs are scheduled (`internal_ledger_dag` every 45 minutes, `daily_multi_resource_dag` daily at 23:00 UTC). To run one now, click **Trigger** on the DAG in the UI, or:

```bash
docker compose exec test airflow dags trigger internal_ledger_dag
```

Note: a triggered or scheduled run uploads to the shared Blob container and runs dbt on the shared EC2 host. Pause the DAGs in the UI if you only want to explore.

### 5. Smoke tests (no uploads, no Snowflake)

Generate one ledger batch inside the container with the Blob upload stubbed out:

```bash
docker compose exec -T test python - <<'EOF'
import sys, tempfile
sys.path.insert(0, "/opt/airflow/dags")
import pipelines.ledger as L
L.upload_file_to_blob = lambda *a, **k: print("upload skipped")
L.STAGING_DIR = tempfile.mkdtemp()
L.generate_internal_ledger()
EOF
# expect: "Validated 50000 rows." and "Created 50000 transactions at ..."
```

Check the dbt project compiles (uses a dummy profile; `dbt parse` does not connect to Snowflake):

```bash
cd dbt/invasight_transform
mkdir -p /tmp/dbt_ci && cat > /tmp/dbt_ci/profiles.yml <<'EOF'
invasight_transform:
  target: ci
  outputs:
    ci: {type: snowflake, account: x, user: x, password: x, role: x, database: INVASIGHT, warehouse: x, schema: ANALYTICS, threads: 1}
EOF
dbt deps --profiles-dir /tmp/dbt_ci
dbt parse --profiles-dir /tmp/dbt_ci
```

### 6. Stop

```bash
docker compose down
```

### Known issues (found while testing, 2026-09-27)

- `dbt parse` currently fails: source `raw.metal_prices_raw` is defined in both `models/sources/sources.yml` and `models/staging/schema.yml`. Removing either definition fixes it.
- The DAGs' dbt selectors (`source:ledger.internal_ledger+`, `source:market_data.*+`) match no nodes in this repo's dbt project — its only source is `raw` — so the `dbt_build` tasks succeed without building anything.
- `.github/workflows/deploy.yml` runs `docker build` without a build context path, and the Dockerfile lives in `doockerImageForDags/`, so the CI build step fails.

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
