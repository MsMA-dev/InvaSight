{{ config(materialized='table') }}

SELECT
    DATE_KEY,
    FULL_DATE,
    YEAR,
    MONTH,
    MONTH_NAME,
    DAY,
    DAY_NAME,
    WEEK_OF_YEAR,
    QUARTER
FROM INVASIGHT.ANALYTICS.DIM_DATE
