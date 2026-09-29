# InvaSight - Investment Analytics Data Pipeline

End-to-end pipeline: a synthetic trading ledger and daily market data are ingested by Airflow,
landed in Azure, loaded into Snowflake, transformed by dbt into a galaxy schema, and served live in Power BI.

## Architecture

```
 [1] Sources            [2] Airflow (Docker on EC2)      [3] Azure Blob        [4] Snowflake RAW
 Ledger generator  ─┐   generate / fetch                  invasight-data/       FX_RATES_RAW
 exchangeratesapi  ─┼─► validate ──────────────────────►  <source>/<date>  ──►  METAL_PRICES_RAW
 metalpriceapi     ─┤                                     (landing zone)        EQUITY_PRICES_RAW
 Alpha Vantage     ─┘                                          COPY INTO ▲      LEDGER_TRANSACTIONS_RAW
                                                                                      │ dbt (EC2, via SSH)
 [7] Power BI (DirectQuery) ◄── [6] ANALYTICS: galaxy schema ◄── [5] STAGING: 4 views ◄┘
```

| Layer | What | Numbers |
|---|---|---|
| 1. Sources | Synthetic ledger + 3 APIs | 8 stock tickers · 4 metals · 4 currencies |
| 2. Orchestration | Airflow 3.3.2, 2 DAGs | Ledger: 50,000 rows every 45 min (~1.6M/day) · Market: daily 23:00 UTC · 11 tasks |
| 3. Landing | Azure Blob, one folder per source | 4 validation gates before upload |
| 4. RAW | Snowflake, 4 tables, loaded by `COPY INTO` | Each run loads exactly the file it uploaded |
| 5. STAGING | dbt views | 4 models |
| 6. ANALYTICS | dbt tables, galaxy schema | 5 dimensions · 3 facts · 61 data tests |
| 7. Dashboard | Power BI, DirectQuery | 3 pages · 26 measures · 36 visuals |

## Team and contributions

| Member | Contributions |
|---|---|
| **Fayha'a Alharbi** | Airflow orchestration: both DAGs, the synthetic ledger generator, API ingestion with validation, Azure landing zone, Snowflake `COPY INTO` loading and the dbt trigger · Docker image and Compose setup · CI/CD (GitHub Actions) with the DAG integrity test · Power BI dashboard · recovery of the deployed dbt models from Snowflake's query history · assembling this submission |
| **Maryam Alotaibi** | dbt project configuration (`dbt_project.yml`, `packages.yml`, schema macro) · staging sources and tests · equity-price and exchange-rate staging models · FX-to-SAR conversion · moving the API keys to AWS Secrets Manager |
| **Rawan Alaklabi** | Galaxy Schema analytics layer (5 dimensions shared by 3 facts) with tests and documentation · end-to-end Internal Ledger contribution · 50,000-record ledger preparation · Snowflake RAW & STAGING and staging transformations · data-quality tests · source-to-target and SAR valuation validation · portfolio valuation, P&L, daily returns and currency exposure · analytics fact and dimension models · submission structure and documentation |
| **Hanoof Alassiri** | dbt installation and environment setup on the dedicated Worker01 EC2 server · Precious Metals dbt staging model for Gold, Silver, Platinum and Palladium · Azure ADLS-to-Snowflake external-stage setup and verification · dbt lineage graph documenting RAW → STAGING → ANALYTICS dependencies · Precious Metals sample data |

## How to run each part

Requirements: Docker, Snowflake, Azure Storage, AWS account, Power BI Desktop, Python packages in
`requirements.txt` (dbt in its own virtualenv).

### Part 1 - Snowflake (once)
1. Create database `INVASIGHT` with schemas `RAW`, `STAGING`, `ANALYTICS` and warehouse `INVASIGHT_WH`.
2. Create the 4 RAW tables: `FX_RATES_RAW`, `METAL_PRICES_RAW`, `EQUITY_PRICES_RAW` (`RAW VARIANT`,
   `FILE_NAME`, `LOADED_AT`) and `LEDGER_TRANSACTIONS_RAW` (samples in `02_src/snowflake/raw/`).
3. Create the Azure stage with `02_src/snowflake/raw/stage/azure_sas_stage_setup.sql.sql`.

### Part 2 - API keys (once)
1. In AWS Secrets Manager (`eu-north-1`) create `APIs-credentials` with
   `EXCHANGE_RATES_API`, `METAL_PRICE_API`, `ALPHA_VANTAGE_API`.
2. Give the Airflow EC2 an IAM role that can read it.

### Part 3 - Airflow (`02_src/airflow/`)
1. `docker compose up -d --build`
2. Open `http://<host>:30000`, user `admin`, password in `airflow/simple_auth_manager_passwords.json.generated`.
3. Add connections: `wasb_default` (Azure SAS token), `snowflake_default` (account, user, password,
   warehouse `INVASIGHT_WH`, database `INVASIGHT`, role), `dbt_ec2_ssh` (dbt host, user, private key).
4. Add pool `dbt_ssh_pool` with 1 slot.
5. Unpause and trigger `internal_ledger_dag` and `daily_multi_resource_dag`.
6. Check: `dbt_build` ends with `PASS=… ERROR=0`.

Test the DAGs without running them:
```bash
docker build -t invasight-airflow -f dockerfile .
docker run --rm -v "$PWD/airflow/dags:/opt/airflow/dags" -v "$PWD/tests:/tests"   -e PYTHONPATH=/opt/airflow/dags --entrypoint python invasight-airflow /tests/test_dag_integrity.py
```

### Part 4 - dbt (`02_src/dbt/invasight_transform/`)
1. `pip install dbt-core==1.12.4 dbt-snowflake==1.12.0`
2. `export SNOWFLAKE_ACCOUNT=... SNOWFLAKE_USER=... SNOWFLAKE_PASSWORD=... SNOWFLAKE_ROLE=... DBT_PROFILES_DIR=.`
3. `dbt deps`
4. `dbt build` → builds 12 models (4 staging, 8 analytics) and runs 61 tests.

In the pipeline, Airflow runs this step on the dbt EC2 (`/home/ubuntu/invasight_pipeline`) over SSH.

### Part 5 - Power BI (`02_src/powerbi/`)
1. Open `InvaSight dashboard pbip.pbip` in Power BI Desktop.
2. Sign in to Snowflake (`INVASIGHT_WH`), then **Refresh**. DirectQuery keeps it live.

### Part 6 - CI/CD (`02_src/airflow/ci_cd/airflow-cicd.yml`)
1. Place the file in `.github/workflows/` at the repository root.
2. Add repository secrets: `USERNAME_TEAM`, `DOCKERHUB_TOKEN`, `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY`, `EC2_APP_DIR`.
3. Each push that changes the Airflow code then runs: build → DAG test → push to Docker Hub → deploy to EC2.

## Limitations
- Alpha Vantage free tier: 25 requests/day, 8 per market run.
- Exchange-rate history starts 2026-09-07; older stock prices have no SAR value.
- The ledger is synthetic: every ticker is priced at random 66-494 USD, so returns are illustrative.
