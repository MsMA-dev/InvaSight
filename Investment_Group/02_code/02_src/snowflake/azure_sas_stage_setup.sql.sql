/* ============================================================
   InvaSight - Azure ADLS to Snowflake SAS Stage
   ============================================================ */

USE DATABASE INVASIGHT;
USE SCHEMA RAW;


/* ------------------------------------------------------------
   1. Create Azure External Stage using SAS Token
   ------------------------------------------------------------ */

CREATE STAGE INVASIGHT.RAW.INVASIGHT_AZURE_SAS_STAGE
    URL = 'azure://invasighttarget2026.blob.core.windows.net/invasight-data/'
    CREDENTIALS = (
        AZURE_SAS_TOKEN = '<2026-02-06&ss=bfqt&srt=sco&sp=rwdlacupiytfx&se=2028-09-20T21:00:00Z&st=2026-09-21T08:15:30Z&spr=https&sig=UjNlaAJAYwDmAAOMhd8wwULnPGtGAjqE96voE6YwTqE%3D>'
    );


/* ------------------------------------------------------------
   2. Verify Precious Metals Files
   ------------------------------------------------------------ */

LIST @INVASIGHT.RAW.INVASIGHT_AZURE_SAS_STAGE/metal_prices/metal_prices/;