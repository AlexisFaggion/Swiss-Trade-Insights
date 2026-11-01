/* ============================================================
   SWISS TRADE & SUPPLY CHAIN ANALYTICS
   02_data_quality_checks.sql

   Purpose:
   Validate completeness, consistency and analytical
   granularity of the staging data.
   ============================================================ */


-- ============================================================
-- 1. TOTAL ROW COUNT
-- Expected: 5,761,429 rows
-- ============================================================
SELECT
    COUNT(*) AS total_rows
FROM staging.trade_raw;


-- ============================================================
-- 2. ROWS BY SOURCE
-- Validate that all four source files were loaded completely.
-- ============================================================
SELECT
    source_file,
    COUNT(*) AS row_count
FROM staging.trade_raw
GROUP BY
    source_file
ORDER BY
    source_file;


-- ============================================================
-- 3. YEAR COVERAGE
-- Expected range: 1988–2025
-- Checks the year boundaries, not the presence of every year.
-- ============================================================
SELECT
    MIN([year]) AS min_year,
    MAX([year]) AS max_year
FROM staging.trade_raw;


-- ============================================================
-- 4. FLOW AND STATUS
--
-- Expected:
-- 1988–2024 → def
-- 2025      → prov
-- ============================================================
SELECT
    trade_flow,
    status,
    MIN([year]) AS min_year,
    MAX([year]) AS max_year,
    COUNT(*) AS row_count
FROM staging.trade_raw
GROUP BY
    trade_flow,
    status
ORDER BY
    trade_flow,
    status;


-- ============================================================
-- 5. MISSING COUNTRY CODES
-- ============================================================
SELECT
    COUNT(*) AS missing_country_iso2
FROM staging.trade_raw
WHERE partner_country_iso2 IS NULL
   OR LTRIM(RTRIM(partner_country_iso2)) = '';


-- ============================================================
-- 5B. INVESTIGATE MISSING COUNTRY ISO2 CODES
--
-- Identify which source country identifiers are associated
-- with missing ISO2 codes.
-- ============================================================
SELECT
    partner_country_num,
    partner_country_name,
    trade_flow,
    MIN([year]) AS min_year,
    MAX([year]) AS max_year,
    COUNT(*) AS row_count
FROM staging.trade_raw
WHERE partner_country_iso2 IS NULL
   OR LTRIM(RTRIM(partner_country_iso2)) = ''
GROUP BY
    partner_country_num,
    partner_country_name,
    trade_flow
ORDER BY
    row_count DESC;


-- ============================================================
-- 5C. MISSING COUNTRY ISO2 BY SOURCE
-- ============================================================
SELECT
    source_file,
    COUNT(*) AS missing_country_iso2
FROM staging.trade_raw
WHERE partner_country_iso2 IS NULL
   OR LTRIM(RTRIM(partner_country_iso2)) = ''
GROUP BY
    source_file
ORDER BY
    source_file;

    
-- ============================================================
-- 6. MISSING VZ CLASSIFICATION
--
-- VZ1 is the highest classification level and should therefore
-- be available for analytical trade records.
-- ============================================================
SELECT
    COUNT(*) AS missing_vz1
FROM staging.trade_raw
WHERE vz1 IS NULL
   OR LTRIM(RTRIM(vz1)) = '';


-- ============================================================
-- 7. INVALID DATE COMPONENTS
--
-- Validate year, month and quarter ranges, as well as
-- consistency between month and quarter.
-- ============================================================
SELECT
    COUNT(*) AS invalid_date_rows
FROM staging.trade_raw
WHERE [month] NOT BETWEEN 1 AND 12
   OR [quarter] NOT BETWEEN 1 AND 4
   OR [year] NOT BETWEEN 1988 AND 2025
   OR [quarter] <> (([month] - 1) / 3 + 1);


-- ============================================================
-- 8. NEGATIVE NUMERIC VALUES
--
-- Trade values and net mass are expected to be non-negative.
-- NULL values are excluded from these negative-value counts.
-- ============================================================
SELECT
    SUM(CASE WHEN net_mass_kg < 0 THEN 1 ELSE 0 END) AS negative_net_mass_rows,
    SUM(CASE WHEN value_chf < 0 THEN 1 ELSE 0 END) AS negative_chf_rows,
    SUM(CASE WHEN value_eur < 0 THEN 1 ELSE 0 END) AS negative_eur_rows,
    SUM(CASE WHEN value_usd < 0 THEN 1 ELSE 0 END) AS negative_usd_rows
FROM staging.trade_raw;


-- ============================================================
-- 9. REPEATED DIMENSIONAL COMBINATIONS
--
-- Repeated combinations were detected during data-quality
-- analysis.
--
-- These records must NOT automatically be treated as duplicate
-- rows because their measures can differ.
--
-- The VZ-specific behaviour is investigated further in:
-- 03_vz_granularity_investigation.sql
-- ============================================================
SELECT TOP 100
    trade_flow,
    [year],
    [quarter],
    [month],

    vz5,
    vz4,
    vz3,
    vz2,
    vz1,

    total_business_cycle,

    partner_country_num,
    partner_country_iso2,

    status,
    COUNT(*) AS occurrences
FROM staging.trade_raw
GROUP BY
    trade_flow,
    [year],
    [quarter],
    [month],

    vz5,
    vz4,
    vz3,
    vz2,
    vz1,

    total_business_cycle,

    partner_country_num,
    partner_country_iso2,

    status
HAVING COUNT(*) > 1
ORDER BY
    occurrences DESC;