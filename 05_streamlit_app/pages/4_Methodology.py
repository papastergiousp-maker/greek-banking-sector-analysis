"""
4_Methodology.py — Data sources, metric definitions, and known limitations.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

import streamlit as st
import pandas as pd

from utils.data import load_sources

st.set_page_config(page_title="Methodology", page_icon="📋", layout="wide")

with st.sidebar:
    st.markdown("### 📋 Methodology")
    st.caption("Every number comes from the banks' annual reports, with its PDF page.")


st.title("Methodology & Data Sources")
st.divider()

# ── Data sources ───────────────────────────────────────────────────────────────
st.subheader("Data Sources")
st.markdown("""
The data covers the **four companies listed on the Athens Exchange in 2022–2024**, using their
consolidated (group) figures from **12 annual reports** (4 groups × FY2022–FY2024):

| Bank | Listed group (2022–2024) | Reports |
|------|--------------------------|---------|
| Alpha Bank | Alpha Services and Holdings S.A. | FY2022, FY2023, FY2024 |
| Eurobank | Eurobank Ergasias Services and Holdings S.A. | FY2022, FY2023, FY2024 |
| NBG | National Bank of Greece S.A. | FY2022, FY2023, FY2024 |
| Piraeus Bank | Piraeus Financial Holdings S.A. | FY2022, FY2023, FY2024 |

In 2025 each holding company merged with its bank, so the listed company is now the bank itself.

**Which column of which report:** each year comes from the latest report that contains it, so every
year-on-year change compares figures prepared the same way. 2024 and 2023 come from the FY2024 report
(2023 restated), 2022 from the FY2023 report (2022 restated). Regulatory ratios (CET1, total capital,
NPE ratio, deferred tax credits, RWAs) are as reported at each year end.

**Extraction:** `pipeline/extract_statements.py` reads the consolidated income statement and balance
sheet pages with `pdfplumber`; the ratios, which sit in the text of the reports, are in
`data/manual/regulatory_ratios.csv`. Every number in the database has its report and PDF page in the
`sources` table (below).

**ECB rates:** ECB deposit facility rate, yearly average and year end, from the ECB key interest rates page.
""")

st.divider()

# ── Metric definitions ─────────────────────────────────────────────────────────
st.subheader("Metric Definitions")

defs = [
    ("NII", "Net interest income", "Interest income minus interest expense, as printed."),
    ("Operating income", "Total operating income", "Each bank's own total income line (e.g. 'Total income from banking operations' for Alpha, 'Total net income' for Piraeus)."),
    ("Operating expenses", "Operating expenses", "Each bank's total operating expenses line, as printed (NBG: personnel, administrative and depreciation lines added up)."),
    ("Impairments", "Impairment losses on loans", "Each bank's credit impairment line for loans (Alpha's line also includes provisions for other credit risk)."),
    ("NIM", "Net interest margin", "NII / average total assets (opening + closing / 2)."),
    ("ROE", "Return on equity", "Net profit attributable to shareholders / average equity attributable to shareholders."),
    ("RoTE", "Return on tangible equity", "Net profit attributable / average (equity attributable − AT1 − goodwill and intangibles). AT1 coupons not deducted."),
    ("ROA", "Return on assets", "Net profit attributable / average total assets."),
    ("C/I", "Cost-to-income ratio", "Operating expenses / operating income."),
    ("CoR", "Cost of risk", "Loan impairments / average net loans."),
    ("L/D", "Loan-to-deposit ratio", "Net loans to customers / customer deposits."),
    ("CET1", "CET1 ratio", "As reported in each annual report's capital adequacy section (regulatory, transitional)."),
    ("NPE ratio", "Non-performing exposure ratio", "As reported by each bank."),
    ("DTC", "Deferred tax credits", "DTAs eligible for conversion into claims on the Greek State (Law 4172/2013), as reported by each bank."),
    ("DTC / CET1", "DTC share of CET1 capital", "DTC / (CET1 ratio × RWAs). Matches the banks' own disclosures (e.g. Alpha 49%, Eurobank 36% at end-2024)."),
    ("Justified P/TBV", "Gordon growth multiple", "(RoTE − g) / (CoE − g). Cost of equity and growth are user assumptions."),
]

def_df = pd.DataFrame(defs, columns=["Metric", "Full name", "Definition"])
st.dataframe(def_df.set_index("Metric"), use_container_width=True, height=560)

st.divider()

# ── ETL pipeline ────────────────────────────────────────────────────────────────
st.subheader("Data Pipeline")
st.markdown("""
```
12 annual report PDFs (4 listed groups x FY2022-FY2024)
        |
        v  pipeline/extract_statements.py   (pdfplumber, 16 statement pages)
        |  data/manual/regulatory_ratios.csv (ratios, with PDF page)
        v
pipeline/build_dataset.py  ->  kpis_final.csv, income_statement_final.csv,
                               balance_sheet_final.csv, sources.csv
        |
        v  rebuild_db.py
greek_banking_final.db (SQLite)
        |
   Streamlit app · Plotly/sql.js dashboard · notebooks · Excel model · deck
```
""")

st.divider()

# ── Source browser ─────────────────────────────────────────────────────────────
st.subheader("Where each number comes from")
src = load_sources()
c1, c2 = st.columns(2)
bank_f = c1.selectbox("Bank", sorted(src["bank"].unique()))
year_f = c2.selectbox("Year", sorted(src["year"].unique(), reverse=True))
st.dataframe(src[(src.bank == bank_f) & (src.year == year_f)][["metric", "value", "source", "how"]]
             .set_index("metric"), use_container_width=True, height=420)

st.divider()

# ── Limitations ────────────────────────────────────────────────────────────────
st.subheader("Known Limitations")
st.markdown("""
| Limitation | Effect |
|---|---|
| Yearly data only | Intra-year rate pass-through cannot be measured |
| Each bank defines operating income and expenses slightly differently | Cost-to-income ratios are close but not perfectly comparable |
| CET1 ratios treat FY2024 profit and dividends differently (e.g. Eurobank's 16.8% is before its FY2024 dividend accrual; 15.7% pro forma for that accrual and other planned transactions) | Small differences in capital comparisons |
| Stress test is one year, static, with RWAs unchanged | Directional only; the official EBA 2023 results are shown for context |
| NII scenarios rest on three yearly points | Rate sensitivity is a rough guide, not a disclosed sensitivity |
| Valuation uses assumed cost of equity and growth | No market prices are used |

**What this analysis is:** a reproducible analysis of the four listed Greek banking groups built from public annual reports.

**What it is not:** investment advice.
""")

st.divider()

# ── Data quality ───────────────────────────────────────────────────────────────
st.subheader("Data Quality")
st.markdown("""
**Automated tests** (`pytest tests/ -v`) check that:
- ROE, ROA, NIM, cost of risk, cost-to-income and loan-to-deposit re-computed from the statement lines match `kpis_final.csv`
- Total assets = total liabilities + total equity for every bank and year
- Every statement line and ratio has a report and page reference
- Key figures match the annual reports (e.g. Alpha 2024 net profit €654m, NBG 2024 CET1 18.3%)
- The DTC share of CET1 matches the banks' own disclosures
""")

st.divider()
st.caption("Greek Banking Sector Analysis 2022–2024 | Analyst: Spyros Papastergiou | papastergiousp@gmail.com")
