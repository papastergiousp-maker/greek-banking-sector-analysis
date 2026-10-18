"""
app.py — Overview page (entry point for the Streamlit multi-page app).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.data import (
    load_kpis, BANKS, YEARS, COLORS, LAYOUT, fmt_eur, pct
)
import pandas as pd

st.set_page_config(
    page_title="Greek Banking Sector Analysis",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏦 Greek Banking 2022–2024")
    st.caption("Eurobank · Alpha Bank · Piraeus Bank · NBG")
    st.divider()
    st.caption("Consolidated figures of the four listed groups, from their "
               "audited annual reports. Every number is traced to a PDF page.\n"
               "All figures in € millions unless stated.")
    st.divider()
    st.caption("**Analyst:** Spyros Papastergiou\n\n"
               "papastergiousp@gmail.com")


@st.cache_data
def get_kpis():
    return load_kpis()


kpis = get_kpis()
k24  = kpis[kpis.year == 2024].set_index("bank")
k23  = kpis[kpis.year == 2023].set_index("bank")
nii_by_year = kpis.groupby("year")["nii"].sum()
nii_growth = (nii_by_year[2024] / nii_by_year[2022] - 1) * 100

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("Greek Banking Sector Analysis 2022–2024")
st.markdown(
    "The four listed Greek banking groups (Alpha Services and Holdings, Eurobank Holdings, "
    "National Bank of Greece, Piraeus Financial Holdings), analysed from their annual reports. "
    f"Sector net interest income grew **{nii_growth:+.0f}%** from 2022 to 2024, almost all of it in 2023 "
    "with the ECB rate hikes."
)
st.divider()

# ── Sector headline cards ───────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
sector_assets  = k24["total_assets"].sum()
sector_nii     = k24["nii"].sum()
best_roe_bank  = k24["roe"].idxmax()
best_cet1_bank = k24["cet1"].idxmax()

c1.metric("Sector Total Assets", fmt_eur(sector_assets))
c2.metric("Sector NII (2024)", fmt_eur(sector_nii),
          delta=f"{nii_growth:+.0f}% vs 2022", delta_color="normal")
c3.metric(f"Highest ROE: {best_roe_bank}",
          pct(k24.loc[best_roe_bank, "roe"]))
c4.metric(f"Strongest Capital: {best_cet1_bank}",
          pct(k24.loc[best_cet1_bank, "cet1"]) + " CET1")

st.divider()

# ── FY2024 Peer Scorecard ───────────────────────────────────────────────────────
st.subheader("FY2024 Peer Scorecard")

scorecard_cols = ["rote", "roe", "roa", "nim", "cost_to_income", "cet1",
                  "loan_to_deposit", "npe_ratio", "net_profit"]
labels         = ["RoTE (%)", "ROE (%)", "ROA (%)", "NIM (%)", "C/I (%)",
                  "CET1 (%)", "L/D (%)", "NPE (%)", "Net Profit (€m)"]
lower_better   = {"cost_to_income", "loan_to_deposit", "npe_ratio"}

rows = []
for bank in BANKS:
    row = {"Bank": bank}
    for col, lbl in zip(scorecard_cols, labels):
        val = k24.loc[bank, col] if col in k24.columns else None
        if val is None or (hasattr(val, "isna") and val.isna()):
            row[lbl] = "—"
        elif col == "net_profit":
            row[lbl] = f"€{val:,.0f}m"
        else:
            row[lbl] = f"{val:.1f}%"
    rows.append(row)

import pandas as pd
scorecard_df = pd.DataFrame(rows).set_index("Bank")

# Highlight best-in-class per column
def highlight_best(df):
    styled = pd.DataFrame("", index=df.index, columns=df.columns)
    for col_lbl, col_key in zip(labels, scorecard_cols):
        if col_lbl not in df.columns:
            continue
        raw = k24[col_key] if col_key in k24.columns else None
        if raw is None:
            continue
        best_bank = raw.idxmin() if col_key in lower_better else raw.idxmax()
        styled.loc[best_bank, col_lbl] = "background-color: #14532d; color: #86efac; font-weight: bold"
    return styled

st.dataframe(
    scorecard_df.style.apply(highlight_best, axis=None),
    use_container_width=True,
    height=215,
)
st.caption("★ Green = best in class for that metric.")

st.divider()

# ── Trend charts ───────────────────────────────────────────────────────────────
st.subheader("Key Sector Trends")

col_l, col_r = st.columns(2)

# ── NII trend ──────────────────────────────────────────────────────────────────
with col_l:
    fig_nii = go.Figure()
    for bank in BANKS:
        bdf = kpis[kpis.bank == bank].sort_values("year")
        fig_nii.add_trace(go.Scatter(
            x=bdf["year"], y=bdf["nii"], name=bank,
            mode="lines+markers",
            line=dict(color=COLORS[bank], width=2.5),
            marker=dict(size=7),
            hovertemplate=f"<b>{bank}</b><br>NII: €%{{y:,.0f}}m<extra></extra>",
        ))
    fig_nii.update_layout(**LAYOUT, title="Net Interest Income (€m)")
    fig_nii.update_xaxes(tickvals=YEARS)
    st.plotly_chart(fig_nii, use_container_width=True)

# ── ROE trend ──────────────────────────────────────────────────────────────────
with col_r:
    fig_roe = go.Figure()
    for bank in BANKS:
        bdf = kpis[kpis.bank == bank].sort_values("year")
        fig_roe.add_trace(go.Scatter(
            x=bdf["year"], y=bdf["roe"], name=bank,
            mode="lines+markers",
            line=dict(color=COLORS[bank], width=2.5),
            marker=dict(size=7),
            hovertemplate=f"<b>{bank}</b><br>ROE: %{{y:.1f}}%<extra></extra>",
        ))
    fig_roe.add_hline(y=10.0, line_dash="dot", line_color="#475569",
                      annotation_text="Cost of equity assumption 10%",
                      annotation_font_color="#94a3b8")
    fig_roe.update_layout(**LAYOUT, title="Return on Equity (%)")
    fig_roe.update_yaxes(ticksuffix="%")
    fig_roe.update_xaxes(tickvals=YEARS)
    st.plotly_chart(fig_roe, use_container_width=True)

col_l2, col_r2 = st.columns(2)

# ── C/I trend ──────────────────────────────────────────────────────────────────
with col_l2:
    fig_ci = go.Figure()
    for bank in BANKS:
        bdf = kpis[kpis.bank == bank].sort_values("year")
        fig_ci.add_trace(go.Scatter(
            x=bdf["year"], y=bdf["cost_to_income"], name=bank,
            mode="lines+markers",
            line=dict(color=COLORS[bank], width=2.5),
            marker=dict(size=7),
            hovertemplate=f"<b>{bank}</b><br>C/I: %{{y:.1f}}%<extra></extra>",
        ))
    fig_ci.update_layout(**LAYOUT, title="Cost-to-Income Ratio (%)")
    fig_ci.update_yaxes(ticksuffix="%", autorange="reversed")
    fig_ci.update_xaxes(tickvals=YEARS)
    st.plotly_chart(fig_ci, use_container_width=True)

# ── NPE trend ──────────────────────────────────────────────────────────────────
with col_r2:
    fig_npe = go.Figure()
    for bank in BANKS:
        bdf = kpis[kpis.bank == bank].sort_values("year")
        if "npe_ratio" not in bdf.columns:
            continue
        fig_npe.add_trace(go.Scatter(
            x=bdf["year"], y=bdf["npe_ratio"], name=bank,
            mode="lines+markers",
            line=dict(color=COLORS[bank], width=2.5, dash="dot"),
            marker=dict(size=7),
            hovertemplate=f"<b>{bank}</b><br>NPE: %{{y:.1f}}%<extra></extra>",
        ))
    fig_npe.update_layout(**LAYOUT, title="NPE Ratio (%), lower is better")
    fig_npe.update_yaxes(ticksuffix="%", autorange="reversed")
    fig_npe.update_xaxes(tickvals=YEARS)
    st.plotly_chart(fig_npe, use_container_width=True)

st.divider()

# ── Key insight callout ────────────────────────────────────────────────────────
st.subheader("Key Takeaways")
cols = st.columns(3)
nbg, eb, pb = k24.loc["NBG"], k24.loc["Eurobank"], k24.loc["Piraeus Bank"]
pb_np_at_2023_cor = pb["net_profit"] - (k23.loc["Piraeus Bank", "cost_of_risk"] / 100 * pb["avg_loans"]
                                        + pb["impairment"]) * (1 - 0.29)
cols[0].info(
    "**Highest margin and capital: NBG**\n\n"
    f"NIM {nbg['nim']:.2f}% of average assets and CET1 {nbg['cet1']:.1f}%, both the highest of the four, "
    f"with the lowest loan-to-deposit ratio ({nbg['loan_to_deposit']:.1f}%). "
    "A cheap deposit base drives the margin, which also makes NBG the most exposed to ECB cuts."
)
cols[1].success(
    "**Best returns: Eurobank**\n\n"
    f"ROE {eb['roe']:.1f}% and RoTE {eb['rote']:.1f}%, the highest in 2024. "
    f"Hellenic Bank lifted total assets by {eb['assets_yoy']:.0f}% in 2024. "
    f"DTCs are {eb['dtc_to_cet1']:.0f}% of its CET1 capital, the lowest share of the four."
)
cols[2].warning(
    "**Watch: Piraeus provisions**\n\n"
    f"Net profit rose {pb['profit_yoy']:.0f}% in 2024 as cost of risk fell to {pb['cost_of_risk']:.2f}% "
    f"from {k23.loc['Piraeus Bank', 'cost_of_risk']:.2f}%. At the 2023 cost of risk, 2024 net profit would be about "
    f"€{pb_np_at_2023_cor:,.0f}m. CET1 {pb['cet1']:.1f}% is the lowest of the four."
)
