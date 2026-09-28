# InvaSight

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
