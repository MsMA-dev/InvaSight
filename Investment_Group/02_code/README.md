# InvaSight - Investment Analytics Data Pipeline

InvaSight is an end-to-end data pipeline for an investment firm. It ingests a near-real-time
internal transaction ledger and daily market data (stock prices, exchange rates, precious-metal
prices), lands the raw files in Azure, loads them into Snowflake, transforms them with dbt into a
galaxy schema (3 fact tables sharing 5 dimensions), and serves a live Power BI dashboard.

```
APIs + synthetic ledger ──► Airflow (validate) ──► Azure Blob (landing)
    ──► Snowflake RAW (COPY INTO) ──► dbt: STAGING ──► ANALYTICS (galaxy schema) ──► Power BI
```

## Team and contributions
Taken from the repository's commit history.

| Member | Contributions |
|---|---|
| **Fayha'a Alharbi** | Airflow orchestration: both DAGs, the synthetic ledger generator, API ingestion with validation, Azure landing zone, Snowflake `COPY INTO` loading and the dbt trigger · Docker image and Compose setup · CI/CD (GitHub Actions) with the DAG integrity test · Power BI dashboard · recovery of the deployed dbt models from Snowflake's query history · assembling this submission |
| **Maryam Alotaibi** | dbt project configuration (`dbt_project.yml`, `packages.yml`, schema macro) · staging sources and tests · equity-price and exchange-rate staging models · FX-to-SAR conversion · moving the API keys to AWS Secrets Manager |
| **Rawan Alaklabi** | Galaxy Schema analytics layer (5 dimensions shared by 3 facts) with tests and documentation · end-to-end Internal Ledger contribution · 50,000-record ledger preparation · Snowflake RAW & STAGING and staging transformations · data-quality tests · source-to-target and SAR valuation validation · portfolio valuation, P&L, daily returns and currency exposure · analytics fact and dimension models · submission structure and documentation |
| **Hanoof Alassiri** | dbt project setup and environment-setup documentation · precious-metals staging model and tests · Snowflake Azure-stage setup SQL · precious-metals sample data |

## Folder contents (`02_code/`)

| Path | Contents |
|---|---|
| `01_data/` | Sample raw files as they land in Azure, one folder per source |
| `02_src/airflow/` | DAGs and pipeline code, `dockerfile`, `docker-compose.yaml`, DAG test, CI/CD workflow |
| `02_src/dbt/invasight_transform/` | dbt project: staging and analytics models, tests, `profiles.yml` |
| `02_src/snowflake/` | Snowflake layers: `raw/` (table samples, stage setup), `staging/`, `analytics/` (models as deployed) |
| `02_src/powerbi/` | Power BI project (`.pbip`) |
| `03_assets/` | Dashboard screenshots, lineage graph |

## Requirements
- Docker with Docker Compose (Airflow host with about 4 GB RAM)
- Azure Storage account with a container `invasight-data`
- Snowflake account: database `INVASIGHT` (schemas `RAW`, `STAGING`, `ANALYTICS`), warehouse `INVASIGHT_WH`
- AWS account (Secrets Manager for the API keys)
- API keys: exchangeratesapi.io, metalpriceapi.com, Alpha Vantage
- Power BI Desktop
- Python packages: see `requirements.txt` (Airflow's are installed by the dockerfile; install dbt in its own virtualenv)

## Setup
1. **Snowflake:** create the RAW tables and the external stage
   `INVASIGHT.RAW.INVASIGHT_AZURE_SAS_STAGE` on the `invasight-data` container
   (see `02_src/snowflake/raw/stage/`).
2. **API keys:** AWS Secrets Manager secret `APIs-credentials` (`eu-north-1`) with
   `EXCHANGE_RATES_API`, `METAL_PRICE_API`, `ALPHA_VANTAGE_API`. The Airflow host needs an IAM role
   that can read it.
3. **dbt host:** the dbt project in `/home/ubuntu/invasight_pipeline` with a virtualenv
   (`dbt-core`, `dbt-snowflake`) and a `dev_env.sh` that activates it and exports the Snowflake
   credentials (see "Run dbt on its own" for the variables).
4. **Airflow** (`02_src/airflow/`): `docker compose up -d --build`, then in the UI create:
   - connections `wasb_default` (Azure SAS token), `snowflake_default` (account, user, password,
     warehouse `INVASIGHT_WH`, database `INVASIGHT`, role), `dbt_ec2_ssh` (dbt host, user, private key)
   - pool `dbt_ssh_pool` with 1 slot

## How to run
- **Pipeline:** open `http://<host>:30000` (user `admin`, password in
  `airflow/simple_auth_manager_passwords.json.generated`), then unpause and trigger
  `internal_ledger_dag` (every 45 min) and `daily_multi_resource_dag` (daily 23:00 UTC).
  A good run ends with `dbt_build` reporting `PASS=… ERROR=0`.
- **Run dbt on its own:**
  ```bash
  cd 02_src/dbt/invasight_transform
  export SNOWFLAKE_ACCOUNT=... SNOWFLAKE_USER=... SNOWFLAKE_PASSWORD=... SNOWFLAKE_ROLE=...
  export DBT_PROFILES_DIR=.
  dbt deps && dbt build
  ```
- **Dashboard:** open `02_src/powerbi/InvaSight dashboard pbip.pbip` in Power BI Desktop and sign
  in to Snowflake (DirectQuery, always live).
- **CI/CD:** `02_src/airflow/ci_cd/airflow-cicd.yml` defines the pipeline: build the image → check
  that every DAG imports → push to Docker Hub → deploy to the EC2 over SSH. It ran on the team
  repository during development; to enable it, place it in `.github/workflows/` at the repository root.

## Orchestration, Ingestion & Dashboard

**Author: Fayha'a Alharbi**: Airflow orchestration, Azure landing zone, Snowflake loading,
CI/CD and the Power BI dashboard.

### Highlights
- **~1.6M transactions a day** ingested (50,000 every 45 minutes), plus daily market data
  from 3 APIs: 8 tickers, 4 metals and 4 currencies.
- **4 sources validated before landing:** a bad batch never reaches the warehouse.
- **Fresh data reaches the gold layer in the same run.** Before, it lagged one cycle
  behind: up to 45 minutes for the ledger and about 24 hours for market data.
- **Every build runs the team's 61 automated data tests as a quality gate**, protecting a
  3-page, 26-measure DirectQuery dashboard.
- **2 silent failures found and eliminated:** stages that reported success while doing nothing.

### Lessons learned
- **Check what a green task actually did.** dbt reported "Nothing to do" with exit code 0
  (its selectors matched nothing), and Snowflake loads reported success with 0 rows.
  Steps now fail loudly instead.
- **Chain the stages; don't line up schedules.** Three separate schedulers only worked when
  their timing happened to line up. Each stage now triggers the next one.
- **Code that only lives on a server isn't safe.** When a server went down, unpushed dbt
  models were recovered from Snowflake's query history (the SQL dbt had executed).
  Git is the only source of truth.
- **Treat the gold layer as a contract.** Renamed columns upstream broke the DirectQuery
  dashboard; the columns the dashboard depends on must not change silently.
- **Secure by default.** SSH open to the internet with password login was brute-forced;
  hosts must use key-only SSH and restricted security groups, and secrets stay out of code.

## Limitations and known issues
- Alpha Vantage free tier: 25 requests/day, 8 per market run; retries can hit the limit.
- No stock prices on weekends and holidays, while the synthetic ledger trades every day.
- The ledger is synthetic, so portfolio values and returns are illustrative.
- dbt runs on a separate EC2 reached over SSH.
- `dim_asset` and the three fact models in `02_src/dbt/` are older than the deployed versions in
  `02_src/snowflake/analytics/`; building from `02_src/dbt/` produces tables without some dashboard
  columns (e.g. `TOTAL_INVESTMENT`, `SECTOR`).
