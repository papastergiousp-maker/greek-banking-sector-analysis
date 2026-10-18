-- 05_npe_cleanup_progress.sql
-- Measure each bank's NPE ratio improvement from 2022 to 2024 using
-- conditional aggregation (no self-join needed).
-- Shows: SUM(CASE WHEN), conditional aggregation, ROUND, ORDER BY alias.

SELECT
    bank,
    ROUND(SUM(CASE WHEN year = 2022 THEN npe_ratio END), 1) AS npe_2022,
    ROUND(SUM(CASE WHEN year = 2023 THEN npe_ratio END), 1) AS npe_2023,
    ROUND(SUM(CASE WHEN year = 2024 THEN npe_ratio END), 1) AS npe_2024,
    ROUND(
        SUM(CASE WHEN year = 2022 THEN npe_ratio END)
        - SUM(CASE WHEN year = 2024 THEN npe_ratio END),
        1
    )                                                       AS improvement_pp,
    ROUND(
        (SUM(CASE WHEN year = 2022 THEN npe_ratio END)
         - SUM(CASE WHEN year = 2024 THEN npe_ratio END))
        * 100.0
        / NULLIF(SUM(CASE WHEN year = 2022 THEN npe_ratio END), 0),
        1
    )                                                       AS improvement_pct
FROM kpis
GROUP BY bank
ORDER BY improvement_pp DESC;

-- Piraeus: 6.8 → 2.6 = -4.2 pp (-62 %), most dramatic cleanup in the sector
