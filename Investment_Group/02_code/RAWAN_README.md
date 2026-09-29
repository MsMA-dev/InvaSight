\# InvaSight



\## Data Engineering \& Analytics



\*\*Author: Rawan Alaklabi:\*\* Data engineering, Snowflake RAW and STAGING, Galaxy Schema analytics modeling, dbt transformations and data validation.



\### Highlights



\- \*\*50,000 Internal Ledger records\*\* prepared and processed through the data pipeline.

\- \*\*End-to-end Internal Ledger flow\*\* implemented across AWS S3, Azure Blob Storage, Snowflake RAW, STAGING and ANALYTICS layers.

\- \*\*Galaxy Schema implemented\*\* with \*\*5 dimensions and 3 core fact tables\*\* for financial analytics.

\- \*\*8 dbt Analytics models\*\* developed for dimensions and facts supporting portfolio analysis.

\- \*\*6.5M+ financial records\*\* processed in `FACT\_HOLDINGS` across the analytical layer.

\- Portfolio analytics support \*\*holdings, portfolio valuation, investment values, fees, P\&L, daily returns and SAR currency exposure\*\*.

\- \*\*61 dbt data tests\*\* validated as a quality gate, covering not-null, uniqueness, accepted values and relationship integrity.

\- \*\*Source-to-target reconciliation\*\* and \*\*SAR valuation checks\*\* performed, with validated SAR calculations showing zero reconciliation difference.



\### What it does



The project integrates financial transaction data with market and reference data to build a cloud-based financial analytics platform.



My contribution focused on the \*\*Internal Ledger data flow\*\* and the shared analytical layer, from source preparation through Snowflake RAW and STAGING into Analytics.



\- \*\*Internal Ledger:\*\* Source → AWS S3 → Azure Blob → Snowflake RAW → STAGING → dbt → ANALYTICS

\- \*\*Analytics:\*\* Galaxy Schema → Holdings → Portfolio Valuation → P\&L → Daily Returns → SAR Exposure



\### Requirements



\- Python 3.x

\- Snowflake

\- dbt Core

\- dbt Snowflake adapter



\### Setup



\- Configure the required Snowflake database, schema, warehouse and permissions.

\- Configure the dbt Snowflake connection.

\- Configure access to the required AWS S3 and Azure Blob Storage resources.

\- Keep credentials, private keys, API keys and sensitive configuration outside the repository.



\### How to run



```bash

cd 02\_src/dbt/invasight\_transform



dbt debug

dbt run

dbt test

```



\### Limitations



\- The Internal Ledger data is synthetic.

\- The pipeline uses batch-oriented financial data rather than real-time transaction processing.

\- Market prices and exchange rates depend on the availability of the configured data sources.

\- Historical valuation may use the latest available market price when an exact-date market price is unavailable.

\- Snowflake and dbt execution require valid credentials and appropriate permissions.



\### Lessons learned



\- \*\*Data quality must be validated across every layer\*\*, not only after reaching the analytics layer.

\- \*\*Source-to-target reconciliation\*\* helps verify that transformations preserve the expected financial values.

\- \*\*Galaxy Schema design\*\* requires clear definitions of dimensions, facts and their business grain before building analytical models.

\- \*\*Cloud data pipelines require dependency awareness\*\* across storage, Snowflake and transformation layers.

\- \*\*Financial calculations\*\*, especially SAR valuation and exchange-rate conversions, must be validated before exposing results to analytics and dashboards.



\### Contribution



\- Internal Ledger source data preparation and ingestion.

\- Snowflake RAW and STAGING organization and transformation.

\- Galaxy Schema design and implementation.

\- Development of dimensional and fact analytics models.

\- dbt analytical transformations.

\- Portfolio valuation and SAR exposure calculations.

\- Data quality, relationship and source-to-target validation.

