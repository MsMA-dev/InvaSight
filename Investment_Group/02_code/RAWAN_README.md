InvaSight

Data Engineering \& Analytics

Author: Rawan Alaklabi: Data engineering, Snowflake RAW and STAGING, Galaxy Schema analytics modeling, dbt transformations and data validation.

Highlights

\- 50,000 Internal Ledger transaction records prepared and processed through the data pipeline.

\- End-to-end Internal Ledger flow implemented across source data, AWS S3, Azure Blob Storage, Snowflake RAW, STAGING and ANALYTICS layers.

\- Galaxy Schema implemented with 5 dimensions and 3 core fact tables for financial analytics.

\- 8 dbt Analytics models developed for dimensions and facts supporting portfolio analysis.

\- FACT\_HOLDINGS processes 6.5M+ financial records across the analytical layer.

\- Portfolio analytics models support holdings, portfolio valuation, investment values, fees, P\&L, daily returns and SAR currency exposure.

\- 61 dbt data tests validated as a quality gate, covering not-null, uniqueness, accepted values and relationship integrity.

\- Source-to-target reconciliation and SAR valuation checks performed, with validated SAR calculations showing zero reconciliation difference.

What it does

The project integrates financial transaction data with market and reference data to build a cloud-based financial analytics platform.

My contribution focused on the Internal Ledger data flow and the shared analytical layer, from source preparation through Snowflake RAW and STAGING into Analytics.

\- Internal Ledger: source → S3 → Azure Blob → Snowflake RAW → STAGING → dbt → ANALYTICS

\- Analytics: Galaxy Schema → holdings → portfolio valuation → P\&L → daily returns → SAR exposure

Code: 02\_src/snowflake/ · dbt: 02\_src/dbt/ · Data: 01\_data/internal\_ledger/

Requirements

Python 3.x, Snowflake, dbt Core and the dbt Snowflake adapter.

Setup

\- Snowflake: database, schema, warehouse and appropriate role permissions.

\- dbt: configured Snowflake connection and project environment.

\- Cloud storage: access to the configured AWS S3 and Azure Blob Storage resources.

\- Security: credentials, private keys, API keys and sensitive configuration must not be committed to GitHub.

How to run

cd 02\_src/dbt/invasight\_transform

dbt debug dbt run dbt test

Limitations

\- The Internal Ledger data is synthetic.

\- The pipeline uses batch-oriented financial data rather than real-time transaction processing.

\- Market prices and exchange rates depend on the availability of the configured data sources.

\- Historical valuation may use the latest available market price when an exact-date market price is unavailable.

\- Snowflake and dbt execution require valid credentials and appropriate permissions.

Contribution

\- Internal Ledger source data preparation and ingestion.

\- Snowflake RAW and STAGING organization and transformation.

\- Galaxy Schema design and implementation.

\- Development of dimensional and fact analytics models.

\- dbt analytical transformations.

\- Portfolio valuation and SAR exposure calculations.

\- Data quality, relationship and source-to-target validation.

