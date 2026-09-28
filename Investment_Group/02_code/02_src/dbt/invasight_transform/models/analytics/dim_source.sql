{{ config(materialized='table') }}
WITH source_data AS (
SELECT 'Internal Ledger' AS source_name, 'Internal' AS source_type

UNION ALL

SELECT 'EQUITY_API' AS source_name, 'External' AS source_type

UNION ALL

SELECT 'Metal Market Data' AS source_name, 'External' AS source_type
)
SELECT MD5(source_name) AS source_key, source_name, source_type FROM source_data
