/* ============================================================
   SWISS TRADE & SUPPLY CHAIN ANALYTICS
   03_vz_granularity_investigation.sql

   Purpose:
   Investigate repeated dimensional combinations found
   during staging data-quality checks.
   ============================================================ */


-- ============================================================
-- 1. INSPECT A REPEATED HISTORICAL VZ COMBINATION
-- ============================================================
SELECT
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
    partner_country_name,

    net_mass_kg,
    value_chf,
    value_eur,
    value_usd,

    status,
    updated_at,
    source_file,
    loaded_at

FROM staging.trade_raw

WHERE trade_flow = 'IMP'
  AND [year] = 2002
  AND [quarter] = 2
  AND [month] = 6
  AND vz5 = '03.1.5.01'
  AND partner_country_num = '403'
  AND partner_country_iso2 = 'US'
  AND status = 'def'

ORDER BY value_chf;


-- ============================================================
-- 2. IDENTIFY WHICH VZ CODES HAVE REPEATED COMBINATIONS
-- ============================================================
WITH duplicate_groups AS
(
    SELECT
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
)

SELECT
    vz5,
    occurrences,
    COUNT(*) AS duplicate_groups
FROM duplicate_groups
GROUP BY
    vz5,
    occurrences
ORDER BY duplicate_groups DESC;

-- ============================================================
-- 3. COMPARE HISTORICAL REPEATED ROWS WITH 2025 CHILD CODES
--
-- Goal:
-- Check whether repeated historical rows correspond to the
-- number of detailed VZ5 child codes visible in 2025.
-- ============================================================
WITH current_children AS
(
    SELECT
        vz4 AS parent_code,

        COUNT(DISTINCT vz5) AS child_count_2025

    FROM staging.trade_raw

    WHERE [year] = 2025

      AND vz4 IS NOT NULL
      AND vz5 IS NOT NULL

      -- Keep only genuine child codes
      AND vz5 <> vz4

    GROUP BY
        vz4
),


historical_repeated_groups AS
(
    SELECT
        vz5 AS parent_code,

        COUNT(*) AS historical_occurrences

    FROM staging.trade_raw

    WHERE [year] <= 2024
      AND vz5 IS NOT NULL

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
),


historical_summary AS
(
    SELECT
        parent_code,
        historical_occurrences,

        COUNT(*) AS repeated_groups

    FROM historical_repeated_groups

    GROUP BY
        parent_code,
        historical_occurrences
)


SELECT
    h.parent_code,

    h.historical_occurrences,

    c.child_count_2025,

    h.repeated_groups,

    -- Matching counts suggest comparable classification detail,
    -- but do not establish a one-to-one mapping between records.
    CASE

        WHEN
            h.historical_occurrences = c.child_count_2025

        THEN 'MATCH'

        ELSE 'REVIEW'

    END AS validation_result

FROM historical_summary AS h

LEFT JOIN current_children AS c
    ON h.parent_code = c.parent_code


ORDER BY
    h.parent_code,
    h.historical_occurrences;


/* ============================================================
   INVESTIGATION CONCLUSION

   Repeated historical records are not treated as duplicates.

   The investigation identified differences in VZ classification
   detail between historical and 2025 observations.

   Matching occurrence counts suggest a relationship with
   more detailed 2025 classifications, but do not establish
   an exact correspondence between individual records.

   The finest VZ classification level is therefore not
   consistently comparable across the full 1988–2025 period.

   MODELLING DECISION

   - Preserve all records in staging.trade_raw.
   - Do not deduplicate repeated historical VZ records.
   - Use VZ4 as the common level for longitudinal analysis,
     falling back to VZ3, VZ2 or VZ1 when VZ4 is unavailable.
   - Aggregate trade measures at the harmonized VZ level
     in analytics.vw_trade_harmonized.

   STATUS: INVESTIGATION COMPLETED
   ============================================================ */