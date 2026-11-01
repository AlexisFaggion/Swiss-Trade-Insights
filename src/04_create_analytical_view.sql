/* ============================================================
   SWISS TRADE & SUPPLY CHAIN ANALYTICS
   04_create_analytical_view.sql

   Purpose:
   Create a Power BI-ready analytical view by harmonizing the
   VZ classification and aggregating trade measures to a
   consistent monthly analytical grain.

   Grain:
   Monthly trade observations grouped by partner country,
   trade flow, VZ hierarchy and publication status.

   VZ5 is excluded from the grouping.
   ============================================================ */


-- ============================================================
-- 1. CREATE ANALYTICS SCHEMA
-- ============================================================
IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = 'analytics'
)
BEGIN
    EXEC('CREATE SCHEMA analytics');
END;
GO


-- ============================================================
-- 2. CREATE HARMONIZED TRADE VIEW
--
-- VZ harmonization rule:
--
-- Use VZ4 when available.
-- Otherwise use the most detailed available higher level:
--
-- VZ4 → VZ3 → VZ2 → VZ1
--
-- VZ5 is intentionally excluded from the analytical grain
-- because its level of detail is not consistently comparable
-- across the full 1988–2025 period.
-- ============================================================
CREATE OR ALTER VIEW analytics.vw_trade_harmonized AS
WITH normalized AS
(
    SELECT
        trade_flow,

        [year],
        [quarter],
        [month],

        partner_country_num,
        partner_country_iso2,
        partner_country_name,

        vz1,
        vz2,
        vz3,

        -- Assumes missing VZ classifications are stored as NULL.
        -- Empty strings are not treated as missing by COALESCE.
        COALESCE(vz4, vz3, vz2, vz1) AS vz_harmonized,

        -- Only "oui" and "yes" are treated as true.
        -- Missing or unrecognized values are mapped to 0.
        CASE
            WHEN LOWER(LTRIM(RTRIM(total_business_cycle)))
                 IN ('oui', 'yes')
            THEN 1
            ELSE 0
        END AS is_total_business_cycle,

        status,

        net_mass_kg,
        value_chf,
        value_eur,
        value_usd

    FROM staging.trade_raw
)

SELECT
    trade_flow,

    [year],
    [quarter],
    [month],

    partner_country_num,
    partner_country_iso2,

    -- Country name is descriptive information and is not part
    -- of the analytical grain.
    MAX(partner_country_name) AS partner_country_name,

    vz1,
    vz2,
    vz3,
    vz_harmonized,

    -- Returns 1 if at least one source record in the group is flagged.
    MAX(is_total_business_cycle) AS is_total_business_cycle,

    status,

    SUM(net_mass_kg) AS net_mass_kg,

    SUM(CAST(value_chf AS DECIMAL(38,0))) AS value_chf,

    SUM(value_eur) AS value_eur,
    SUM(value_usd) AS value_usd
FROM normalized
GROUP BY
    trade_flow,

    [year],
    [quarter],
    [month],

    partner_country_num,
    partner_country_iso2,

    vz1,
    vz2,
    vz3,
    vz_harmonized,

    status;
GO


-- ============================================================
-- 3. VALIDATION
-- ============================================================
-- Raw staging rows
SELECT
    COUNT(*) AS staging_rows
FROM staging.trade_raw;


-- Harmonized analytical rows
-- This number should be lower than the staging row count.

SELECT
    COUNT(*) AS analytical_rows
FROM analytics.vw_trade_harmonized;


-- ============================================================
-- 4. VERIFY THAT THE ANALYTICAL GRAIN IS UNIQUE
--
-- Expected result:
-- 0 rows
-- ============================================================
SELECT
    trade_flow,
    [year],
    [month],
    partner_country_num,
    vz_harmonized,
    COUNT(*) AS occurrences

FROM analytics.vw_trade_harmonized

GROUP BY
    trade_flow,
    [year],
    [month],
    partner_country_num,
    vz_harmonized

HAVING COUNT(*) > 1;
GO


-- ============================================================
-- 5. VERIFY THE HISTORICAL VZ EXAMPLE
--
-- The three historical records identified during the VZ
-- investigation should now appear as one aggregated row.
-- ============================================================
SELECT
    trade_flow,
    [year],
    [quarter],
    [month],

    partner_country_iso2,
    partner_country_name,

    vz_harmonized,

    net_mass_kg,
    value_chf,
    value_eur,
    value_usd

FROM analytics.vw_trade_harmonized

WHERE trade_flow = 'IMP'
  AND [year] = 2002
  AND [month] = 6
  AND partner_country_iso2 = 'US'
  AND vz_harmonized = '03.1.5.01';
GO