# Phase 6 - Data Quality Record

## dbt Test Results

Initial test run:
- Total tests: 40
- Passed: 39
- Failed: 1
- Failed test: FACT_MARKET_PRICES.DATE_KEY relationship to DIM_DATE.DATE_KEY

Final test run after correction:
- Total tests: 40
- Passed: 40
- Warnings: 0
- Errors: 0
- Skipped: 0

## Issues Detected

### FACT_MARKET_PRICES
- Invalid foreign-key rows detected: 800
- Affected source: Equity Market Data
- Affected tickers: 8
- Rows per ticker: 100
- Root cause: Equity DATE_KEY values were generated using MD5(PRICE_DATE::VARCHAR) instead of DIM_DATE.DATE_KEY in YYYYMMDD format.

### DIM_DATE
- Incomplete date records detected: 3
- Affected dates:
  - 2026-09-22
  - 2026-09-23
  - 2026-09-24
- Missing attributes included DAY, MONTH, QUARTER, YEAR, and DAY_OF_WEEK.
- Missing date detected: 2026-09-25

## Corrections Applied

- Updated 3 incomplete DIM_DATE records.
- Added/confirmed complete DIM_DATE record for 2026-09-25.
- Corrected DATE_KEY for 800 Equity Market Data rows in FACT_MARKET_PRICES.
- Rows deleted: 0
- Duplicates removed: 0

## Final Validation

- Unmatched FACT_MARKET_PRICES DATE_KEY rows: 0
- Incomplete DIM_DATE rows: 0
- FACT_MARKET_PRICES row count: 1262
- Distinct MARKET_PRICE_KEY count: 1262
- Downstream portfolio groups before correction: 120
- Downstream portfolio groups after correction: 120
- Missing portfolio groups: 0
- Changed portfolio values: 0
