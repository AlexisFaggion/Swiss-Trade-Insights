/* ============================================================

    Swiss Trade & Supply Chain Analytics
    01_create_staging_schema.sql

    Creates the staging schema and raw trade table in Azure SQL.

   ============================================================ */


/* ============================================================
   1. CREATE STAGING SCHEMA
   ============================================================ */
IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = 'staging'
)
BEGIN
    EXEC('CREATE SCHEMA staging');
END;
GO


/* ============================================================
   2. CREATE RAW TRADE TABLE
   ============================================================ */
IF OBJECT_ID('staging.trade_raw', 'U') IS NULL
BEGIN

    CREATE TABLE staging.trade_raw
    (
        trade_flow VARCHAR(3) NOT NULL,

        [year] SMALLINT NOT NULL,
        [quarter] TINYINT NOT NULL,
        [month] TINYINT NOT NULL,

        vz5 VARCHAR(20) NULL,
        vz4 VARCHAR(20) NULL,
        vz3 VARCHAR(20) NULL,
        vz2 VARCHAR(20) NULL,
        vz1 VARCHAR(20) NULL,

        total_business_cycle VARCHAR(10) NULL,

        partner_country_num VARCHAR(10) NULL,
        partner_country_iso2 VARCHAR(2) NULL,
        partner_country_name NVARCHAR(150) NULL,

        net_mass_kg DECIMAL(38,18) NULL,

        value_chf BIGINT NULL,
        value_eur DECIMAL(28,12) NULL,
        value_usd DECIMAL(28,12) NULL,

        status VARCHAR(10) NULL,

        updated_at DATETIME2 NULL,

        source_file NVARCHAR(255) NULL,

        loaded_at DATETIME2 NOT NULL
            DEFAULT SYSUTCDATETIME()
    );

END;
GO