"""
4_Methodology.py — Data sources, metric definitions, and known limitations.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

import streamlit as st
import pandas as pd

from utils.data import load_kpis, load_sources, MANUAL

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

# ── Same perimeter ─────────────────────────────────────────────────────────────
st.subheader("Same perimeter for income and balances")
st.markdown("""
When a bank sells, or is selling, a business, it shows that business as a **discontinued operation**:
the income statement leaves it out, while the balance sheet may still hold it, inside its lines or as
assets held for sale. A margin that divides one by the other then mixes two different groups.

| Bank | Business | What the reports show | How NIM and cost of risk treat it |
|------|----------|-----------------------|-----------------------------------|
| Alpha | Alpha Bank Romania (sold to UniCredit, 4.11.2024), Alpha Life (51% to UniCredit, 2025), Alpha Leasing Romania | Income left out in 2022–2024; balances inside the lines at end-2021 and end-2022, held for sale at end-2023 and end-2024 | 2022–2023: their net interest income and loan impairments added back (FY2023 report p.417, FY2024 report p.395), loans held for sale added back at end-2023 (FY2023 p.403). 2024: their assets held for sale taken out (FY2024 p.390) |
| Eurobank | Eurobank Direktna, Serbia (sold 2.11.2023) | Income left out in 2022–2023; balances inside the lines at end-2021 and end-2022 | Eurobank's own continuing-operations balances (FY2023 report p.73) |
| NBG | Ethniki Insurance (sold 31.3.2022), CAC Coral | Income left out in 2022; held for sale at end-2021 | Their net interest income added back (FY2022 report p.286) |
| Piraeus | Small disposal group | Assets from discontinued operations at end-2021 | Taken out (FY2022 report p.119) |

The printed statement lines are not changed: NII, profit and total assets are as published. Without this,
Alpha's NIM came out about 0.2pp too low, and its loans and deposits seemed to fall in 2023 (−6.7% and
−4.6%) when they rose (+1.6% and +3.5% with the Romanian bank and Alpha Life; the report itself gives +3%
for deposits). The amounts and pages are in `data/manual/perimeter_adjustments.csv`.
""")

st.divider()

# ── Metric definitions ─────────────────────────────────────────────────────────
st.subheader("Metric Definitions")

defs = [
    ("NII", "Net interest income", "Interest income minus interest expense, as printed."),
    ("Operating income", "Total operating income", "Each bank's own total income line (e.g. 'Total income from banking operations' for Alpha, 'Total net income' for Piraeus)."),
    ("Operating expenses", "Operating expenses", "Each bank's total operating expenses line, as printed (NBG: personnel, administrative and depreciation lines added up)."),
    ("Impairments", "Impairment losses on loans", "Each bank's credit impairment line for loans (Alpha's line also includes provisions for other credit risk)."),
    ("NIM", "Net interest margin", "NII / average total assets (opening + closing / 2), with income and assets covering the same businesses (see above)."),
    ("ROE", "Return on equity", "Net profit attributable to shareholders / average equity attributable to shareholders."),
    ("RoTE", "Return on tangible equity", "(Net profit attributable − AT1 coupons) / average (equity attributable − AT1 − goodwill and intangibles). Coupons: Alpha €24m (2023) and €48m (2024), Piraeus €53m a year."),
    ("ROA", "Return on assets", "Net profit attributable / average total assets."),
    ("C/I", "Cost-to-income ratio", "Operating expenses / operating income."),
    ("CoR", "Cost of risk", "Loan impairments / average net loans, same perimeter as NIM."),
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
        |  data/manual/perimeter_adjustments.csv, at1_coupons.csv (with PDF page)
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
- ROE, RoTE, ROA, NIM, cost of risk, cost-to-income and loan-to-deposit re-computed from the statement lines (and the perimeter and AT1 coupon files) match `kpis_final.csv`
- Total assets = total liabilities + total equity for every bank and year
- Every statement line and ratio has a report and page reference
- Key figures match the annual reports (e.g. Alpha 2024 net profit €654m, NBG 2024 CET1 18.3%)
- The DTC share of CET1 matches the banks' own disclosures
- Ratios match the banks' own figures where they use the same definition: Piraeus RoTE 12.3% (2023) and 15.0% (2024), Alpha ROA 0.91% and loans to deposits 75% and 77%, Eurobank 2022 cost of risk 0.71%
""")

st.divider()

# ── Comparing with the banks' own returns ──────────────────────────────────────
st.subheader("Why Alpha's published return is higher than the ROE here")
_k = load_kpis().set_index(["bank", "year"])
_a = _k.loc[("Alpha Bank", 2024)]
_pub = pd.read_csv(MANUAL / "published_returns.csv").set_index(["bank", "year", "metric"])["value"]
_norm = _pub[("Alpha Bank", 2024, "Normalised profit after tax")]
_rotbv = _pub[("Alpha Bank", 2024, "Normalised RoTBV")]
_rote_norm = (_norm - _a["at1_coupons"]) / _a["avg_tangible_equity"] * 100
st.markdown(f"""
Alpha's headline 2024 return, **{_rotbv:.1f}% normalised RoTBV**, uses three choices that the
reported ROE here does not:

| Step | Profit (€m) | Equity base | 2024 |
|------|------------:|-------------|-----:|
| ROE, as reported | {_a['net_profit']:,.0f} | Average equity attributable (incl. AT1) | {_a['roe']:.1f}% |
| RoTE: less AT1 coupons, tangible equity without AT1 | {_a['net_profit'] - _a['at1_coupons']:,.0f} | Average tangible equity {_a['avg_tangible_equity']:,.0f} | {_a['rote']:.1f}% |
| Excluding one-offs (NPE sales, voluntary exit scheme, transformation costs) | {_norm - _a['at1_coupons']:,.0f} | Same | {_rote_norm:.1f}% |
| Alpha's own measure: also removes capital above its target and accrued dividends from the equity base | {_norm - _a['at1_coupons']:,.0f} | Adjusted TBV | {_rotbv:.1f}% |

Sources: reported profit and AT1 coupons, FY2024 report p.246 and p.290; normalised profit €{_norm:,.0f}m,
FY2024 report p.441 (APM appendix); {_rotbv:.1f}% from Alpha's FY2024 results press release. There is no
missing company or balance sheet: the listed holding's consolidated statements include Alpha Bank S.A.
Piraeus defines its RoaTBV the way RoTE is defined here, and the two match.
""")

st.subheader("Alpha's other headline ratios and the ones here")
_a23 = _k.loc[("Alpha Bank", 2023)]
_nim_mixed = _a["nii"] / ((_a23["total_assets"] + _a["total_assets"]) / 2) * 100
_crm = _pub[("Alpha Bank", 2024, "Credit risk management expenses")]
_npe_imp = _pub[("Alpha Bank", 2024, "NPE transaction impairments")]
_cor_under = (-_a["impairment"] + _crm - _npe_imp) / _a["avg_loans"] * 100
st.markdown(f"""
| 2024 | Alpha reports | Here | Why they differ |
|------|--------------:|-----:|-----------------|
| Net interest margin | {_pub[("Alpha Bank", 2024, "NIM")]:.1f}% | {_a['nim']:.2f}% | Alpha divides NII, which leaves out the Romanian bank and Alpha Life, by total assets that still include them as held for sale. Here both cover the same businesses. On Alpha's basis the year-end balances give {_nim_mixed:.2f}%. |
| Cost of risk | {_pub[("Alpha Bank", 2024, "Underlying cost of risk")]:.2f}% (underlying) | {_a['cost_of_risk']:.2f}% | Here: the loan impairment line as printed (€{-_a['impairment']:,.0f}m). Alpha adds €{_crm:,.0f}m of credit risk management expenses and leaves out €{_npe_imp:,.0f}m of impairments from NPE sales: (€{-_a['impairment']:,.0f}m + €{_crm:,.0f}m − €{_npe_imp:,.0f}m) / average loans €{_a['avg_loans']:,.0f}m = {_cor_under:.2f}%. |
| Loans to deposits | {_pub[("Alpha Bank", 2024, "Loans to deposits")]:.0f}% | {_a['loan_to_deposit']:.1f}% | Same definition. |

Sources: Alpha's FY2024 results press release (NIM, underlying cost of risk); FY2024 report p.246 (credit risk
management expenses), p.440 (NPE transaction impairments, loans to deposits). Both ways of
measuring are correct; the one here keeps the four banks comparable.
""")

st.divider()
st.caption("Greek Banking Sector Analysis 2022–2024 | Analyst: Spyros Papastergiou | papastergiousp@gmail.com")
