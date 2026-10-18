-- 04_capital_headroom.sql
-- CET1 headroom and capital quality for each bank and year.
-- 10.5% is a round reference level, not a regulatory minimum. Each bank's CET1
-- requirement is set by the ECB and differs by bank (at end-2024: NBG 9.64%,
-- Eurobank 10.41%, or 12.45% while it had no AT1 capital).
-- Shows: CASE WHEN tiers, arithmetic on a column, ORDER BY.

SELECT
    bank,
    year,
    cet1,
    ROUND(cet1 - 10.5, 2)                   AS buffer_vs_reference_pp,
    dtc_to_cet1,
    CASE
        WHEN cet1 >= 17 THEN 'High'
        WHEN cet1 >= 14 THEN 'Medium'
        ELSE 'Low'
    END                                     AS capital_tier
FROM kpis
ORDER BY year, cet1 DESC;

-- 2024 CET1: NBG 18.3, Eurobank 16.8, Alpha 16.3, Piraeus 14.47.
-- 2024 DTC share of CET1: Eurobank 36.0, Alpha 48.6, NBG 51.1, Piraeus 63.2.
