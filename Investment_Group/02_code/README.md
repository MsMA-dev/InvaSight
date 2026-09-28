# InvaSight

## Orchestration, Ingestion & Dashboard

### What it does
Airflow ingests a synthetic transaction ledger (50,000 rows every 45 min) and daily
market data (FX rates, metal prices, stock prices), validates each batch, lands it in
Azure Blob Storage, loads it into Snowflake `RAW` with `COPY INTO`, then triggers dbt.
Power BI reads the gold layer live via DirectQuery.

- `internal_ledger_dag` (every 45 min): generate → load → dbt build
- `daily_multi_resource_dag` (daily 23:00 UTC): API check → 3 fetches → 3 loads → dbt build

Code: `02_src/airflow/` · Dashboard: `02_src/powerbi/` · Sample data: `01_data/`

### Requirements
Docker + Docker Compose. Python packages (installed by the dockerfile) are in `requirements.txt`.

### Setup
- **Airflow connections:** `wasb_default` (Azure SAS token), `snowflake_default`
  (account, user, password, warehouse `INVASIGHT_WH`, database `INVASIGHT`, role),
  `dbt_ec2_ssh` (dbt host, user, private key)
- **Airflow pool:** `dbt_ssh_pool` with 1 slot
- **API keys:** AWS Secrets Manager secret `APIs-credentials` (`eu-north-1`) with
  `EXCHANGE_RATES_API`, `METAL_PRICE_API`, `ALPHA_VANTAGE_API`; the host needs an IAM
  role that can read it
- **Snowflake:** RAW tables and the external stage `INVASIGHT.RAW.INVASIGHT_AZURE_SAS_STAGE`
  on the `invasight-data` container

### How to run
```bash
cd 02_src/airflow
docker compose up -d --build
```
Open `http://<host>:30000` (user `admin`, password in
`airflow/simple_auth_manager_passwords.json.generated`), then unpause and trigger the DAGs.
Open `02_src/powerbi/InvaSight dashboard pbip.pbip` in Power BI Desktop and sign in to Snowflake.

**CI/CD:** on push to `main`, GitHub Actions builds the image, checks every DAG imports,
pushes to Docker Hub, and deploys to the EC2 over SSH (`02_src/airflow/ci_cd/`).

### Limitations
- Alpha Vantage free tier: 25 requests/day, 8 per market run.
- No stock prices on weekends and holidays; the ledger is synthetic and trades daily.
- dbt runs on a separate EC2 reached over SSH.
