-- 06_income_decomposition.sql
-- Break operating income into NII vs non-NII for each bank-year, where non-NII is
-- operating income minus NII (fees, trading and other income). Then compute NII mix %
-- and rank banks by NII dependency in each year.
-- Joins kpis (NII) against income_statement (operating income line) to avoid
-- double-counting; shows multi-CTE pipeline and cross-table JOIN.
-- Shows: multi-CTE, JOIN across two tables, window function on CTE result.

WITH nii_base AS (
    SELECT bank, year, nii
    FROM kpis
),
opincome_base AS (
    SELECT bank, year, value AS operating_income
    FROM income_statement
    WHERE metric = 'Operating income'
),
decomposed AS (
    SELECT
        n.bank,
        n.year,
        ROUND(n.nii, 1)                                AS nii_eur_m,
        ROUND(o.operating_income, 1)                   AS opincome_eur_m,
        ROUND(o.operating_income - n.nii, 1)           AS non_nii_eur_m,
        ROUND(n.nii * 100.0 / NULLIF(o.operating_income, 0), 1) AS nii_mix_pct
    FROM nii_base n
    JOIN opincome_base o ON n.bank = o.bank AND n.year = o.year
)
SELECT
    bank,
    year,
    nii_eur_m,
    opincome_eur_m,
    non_nii_eur_m,
    nii_mix_pct,
    RANK() OVER (PARTITION BY year ORDER BY nii_mix_pct DESC) AS nii_dependency_rank
FROM decomposed
ORDER BY year, nii_dependency_rank;

-- A higher NII share means income depends more on the interest margin, so it moves more
-- with interest rates. In 2024 the NII share ranges from 74.0% (Alpha) to 81.7% (NBG).
