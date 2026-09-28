/* ============================================================
   InvaSight - Azure ADLS to Snowflake SAS Stage
   ============================================================ */

USE DATABASE INVASIGHT;
USE SCHEMA RAW;


/* ------------------------------------------------------------
   1. Create Azure External Stage using SAS Token
   ------------------------------------------------------------ */

CREATE STAGE INVASIGHT.RAW.INVASIGHT_AZURE_SAS_STAGE
    URL = 'azure://<storage_account>.blob.core.windows.net/<container>/'
    CREDENTIALS = (
        AZURE_SAS_TOKEN = '<AZURE_SAS_TOKEN>'
    );


/* ------------------------------------------------------------
   2. Verify Precious Metals Files
   ------------------------------------------------------------ */

LIST @INVASIGHT.RAW.INVASIGHT_AZURE_SAS_STAGE/metal_prices/metal_prices/;