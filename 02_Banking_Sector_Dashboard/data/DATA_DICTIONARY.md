# Data Dictionary

Greek Banking Sector Analysis 2022–2024. All money amounts are in € million.

The database `02_Banking_Sector_Dashboard/data/greek_banking_final.db` (SQLite) is built by `rebuild_db.py` from the CSV files below and copied to `docs/data/` for the browser dashboard.

---

## Entities and basis

| Short name | Entity (listed on the Athens Exchange in 2022–2024) |
|------------|------------------------------------------------------|
| Alpha Bank | Alpha Services and Holdings S.A. (group) |
| Eurobank | Eurobank Ergasias Services and Holdings S.A. (group) |
| NBG | National Bank of Greece S.A. (group) |
| Piraeus Bank | Piraeus Financial Holdings S.A. (group) |

In 2025 each holding company merged with its bank, so the listed company is now the bank itself. The 2022–2024 figures are those of the listed groups.

**Which report each year comes from.** Each year is taken from the latest annual report that contains it, so every year-on-year change compares figures prepared the same way:

- 2024 and 2023: FY2024 annual reports (2023 is the restated comparative column)
- 2022: FY2023 annual reports (2022 is the restated comparative column)
- End-2021 balances, used only for 2022 averages: FY2022 annual reports

Regulatory ratios (CET1, total capital ratio, NPE ratio, DTC, RWAs) are taken as reported at each year end.

---

## Files

| File | Rows | Content |
|------|-----:|---------|
| `processed/extracted_statements.csv` | 232 | Every statement line read from the PDFs, with file, page and the printed line (`source_label`) |
| `processed/income_statement_final.csv` | 96 | 8 lines × 4 banks × 3 years, long format |
| `processed/balance_sheet_final.csv` | 159 | 13 lines × 12 bank-years, plus Eurobank's "Due to central banks" (3 rows) |
| `processed/kpis_final.csv` | 12 | One row per bank and year, 39 columns |
| `processed/sources.csv` | 335 | Every number with its report file and PDF page |
| `manual/regulatory_ratios.csv` | 60 | CET1 ratio, total capital ratio, NPE ratio, DTC and RWAs, with page |
| `manual/opening_balances_2021.csv` | 20 | End-2021 total assets, equity, loans, intangibles and AT1 |
| `manual/eba_stress_test_2023.csv` | 4 | Official EBA 2023 stress test results (fully loaded CET1) |
| `manual/ecb_funding.csv` | 12 | Amounts due to the ECB and central banks at each year end, with page |
| `manual/ecb_deposit_rate.csv` | 3 | ECB deposit facility rate, yearly average and year end |

Long files (`income_statement_final.csv`, `balance_sheet_final.csv`) have the columns `bank`, `year`, `metric`, `value`, `unit`, `source_ref` (for example `alpha_holdings_2024.pdf p.248`).

---

## Income statement lines

| Metric | Definition |
|--------|------------|
| Net interest income | As printed |
| Net banking fee and commission income | As printed |
| Operating income | Each bank's own total income line, as printed (the label is in `extracted_statements.csv`) |
| Operating expenses | Each bank's total operating expenses line, as printed (Alpha "Total expenses", Eurobank "Operating expenses", Piraeus "Total operating expenses"). NBG prints personnel, administrative and depreciation costs on separate lines, which are added up. Negative. |
| Profit from operations before impairments | Operating income + operating expenses (derived) |
| Impairment losses on loans | Each bank's credit impairment line for loans (Alpha "Impairment losses and provisions to cover credit risk", NBG "Credit provisions", Eurobank and Piraeus impairment losses on loans and advances to customers). Negative = charge. |
| Profit before tax | As printed |
| Net profit attributable to shareholders | Profit attributable to the equity holders of the parent; for Piraeus the continuing and discontinued lines are added |

## Balance sheet lines

| Metric | Definition |
|--------|------------|
| Cash and balances with central banks | As printed |
| Due from credit institutions | As printed |
| Loans and advances to customers | Net of allowances; for Piraeus the loans at amortised cost and at fair value through profit or loss are added |
| Investment securities | As printed; for Alpha three lines are added |
| Goodwill and intangible assets | Goodwill plus other intangible assets |
| Total assets | As printed |
| Due to central banks | Eurobank only (separate line in its balance sheet) |
| Due to credit institutions | Amounts due to banks, including the ECB. For Eurobank = due to central banks + due to credit institutions |
| Deposits from customers | As printed |
| Total liabilities | As printed |
| Additional Tier 1 instruments | AT1 notes inside equity (Alpha from 2023, Piraeus); 0 where there are none |
| Equity attributable to shareholders | The printed line where one exists; otherwise total equity − non-controlling interests. Includes AT1. |
| Non-controlling interests | As printed |
| Total equity | As printed |

---

## KPIs (`kpis_final.csv`, table `kpis`)

Averages are (opening + closing) / 2. Ratios are in %.

| Column | Definition |
|--------|------------|
| `nii`, `fees`, `operating_income`, `operating_expenses`, `net_profit`, `pbt`, `impairment` | Income statement lines above |
| `loans`, `deposits`, `total_assets` | Balance sheet lines above, year end |
| `equity` | Equity attributable to shareholders (including AT1), year end |
| `at1` | Additional Tier 1 instruments |
| `intangibles` | Goodwill and intangible assets |
| `tangible_equity` | equity − at1 − intangibles |
| `roe` | net_profit / average equity |
| `rote` | net_profit / average tangible equity. AT1 coupons are not deducted. |
| `roa` | net_profit / average total assets |
| `nim` | nii / average total assets |
| `cost_of_risk` | −impairment / average loans |
| `cost_to_income` | −operating_expenses / operating_income |
| `loan_to_deposit` | loans / deposits, year end |
| `fee_share` | fees / operating_income |
| `equity_to_assets` | equity / total_assets, year end |
| `nii_yoy`, `profit_yoy`, `assets_yoy`, `opincome_yoy` | Year-on-year change; empty for 2022 |
| `cet1`, `total_capital_ratio`, `npe_ratio` | As reported at year end |
| `dtc` | Deferred tax credits included in regulatory capital (DTAs that can be converted into a claim on the Greek State under article 27A of Law 4172/2013) |
| `rwa` | Risk-weighted assets |
| `dtc_to_cet1` | dtc / (cet1 × rwa) |
| `avg_equity`, `avg_tangible_equity`, `avg_total_assets`, `avg_loans` | The averages used above |

## Other tables

| Table | Columns |
|-------|---------|
| `sources` | bank, year, metric, value, source (report file and page), how (note) |
| `eba_stress_test` | bank, cet1_fl_start_2022, cet1_fl_adverse_2025, cet1_fl_baseline_2025, source_file, source_page, note |
| `ecb_funding` | bank, year, value, unit, source_file, source_page, line_in_report |
| `ecb_rates` | year, dfr_avg, dfr_year_end, source, note |

---

## Comparability notes

- **Eurobank 2024** includes Hellenic Bank (Cyprus), consolidated from 30 June 2024. It added €15.8bn of deposits and €295m of 2024 NII (Eurobank FY2024 report, p.4 and p.262).
- **CET1 ratios** are as reported, and the banks treat FY2024 profit and dividends differently. NBG's 18.3% includes FY2024 profit with a 50% payout accrual (FY2024 report p.40); its statutory note shows 18.0% with the accrual approved by the ECB (p.445). Alpha's 16.3% includes profit after the dividend provision (p.387). Piraeus' 14.47% includes FY2024 profit (p.566). Eurobank's 16.8% is before the accrual for its FY2024 dividend; pro forma for that accrual and for projects Solar, Leon and Wave VI it is 15.7% (p.6).
- **Piraeus DTC 2024** is the amount included in regulatory capital: €3,248m eligible DTAs less a €128m prudential amortisation adjustment (FY2024 report p.567–568).
- **NPE ratios** follow each bank's own definition.
- **Operating income and expenses** follow each bank's own presentation, so cost-to-income ratios are close but not perfectly comparable.

---

## Corrections log

| Date | Change |
|------|--------|
| October 2026 | Dataset rebuilt from the annual reports of the four listed groups with an automated extractor (`pipeline/`), every number traced to a PDF page. Earlier versions mixed bank-level and holding-level reports, mixed first-published and restated years, used year-end instead of average balances, and contained some estimated ratios. All of those values were replaced. |
| October 2026 | Added amounts due to the ECB and central banks (`ecb_funding`) and the ECB deposit rate (`ecb_rates`) as sourced tables. |

---

*Project: Greek Banking Sector Analysis 2022–2024 · Spyros Papastergiou*
