"""
7_Macro_Funding.py — How the 2022–2024 ECB rate cycle reached the banks: margins, ECB funding
and deposits. Every bank figure comes from the annual reports (report and page in the tables).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from utils.data import (load_kpis, load_ecb_funding, forecast_nii, BANKS, YEARS, COLORS, LAYOUT,
                        ECB_HIST, ECB_YEAR_END)

st.set_page_config(page_title="Macro & Funding", page_icon="📡", layout="wide")

# Deposits that Hellenic Bank added when Eurobank consolidated it (Eurobank FY2024 report p.262)
HELLENIC_BANK_DEPOSITS = 15_800

with st.sidebar:
    st.markdown("### 📡 Macro & Funding")
    st.caption(
        "How the 2022–2024 ECB rate cycle reached the four banks: margins, ECB funding and deposits. "
        "ECB deposit facility rate: yearly average of the daily rate, from the ECB."
    )


@st.cache_data
def get_data():
    return load_kpis(), load_ecb_funding()


kpis, ecb = get_data()
k = kpis.set_index(["bank", "year"])

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Macro & Funding Context")
st.caption("ECB rates, net interest margins, ECB funding and deposits, FY2022–2024")
st.divider()

# ── 1. NIM vs ECB rate ────────────────────────────────────────────────────────
st.subheader("1. Net interest margin vs the ECB deposit rate")

nim_moves = ", ".join(
    f"{b} {k.loc[(b, 2022), 'nim']:.2f}% → {k.loc[(b, 2024), 'nim']:.2f}%" for b in BANKS
)
st.markdown(
    f"The ECB deposit facility rate averaged {ECB_HIST[2022]:.2f}% in 2022, {ECB_HIST[2023]:.2f}% in 2023 "
    f"and {ECB_HIST[2024]:.2f}% in 2024 (year end {ECB_YEAR_END[2024]:.2f}%, after the first cuts in "
    f"June 2024). Net interest margins rose at every bank between 2022 and 2024: {nim_moves}."
)

fig_nim = go.Figure()
fig_nim.add_trace(go.Bar(
    x=YEARS, y=[ECB_HIST[y] for y in YEARS], name="ECB deposit rate, yearly average (%)",
    marker_color="rgba(71,85,105,0.5)", yaxis="y2",
    hovertemplate="ECB deposit rate: %{y:.2f}%<extra></extra>",
))
for bank in BANKS:
    b = kpis[kpis.bank == bank].sort_values("year")
    fig_nim.add_trace(go.Scatter(
        x=b["year"], y=b["nim"], mode="lines+markers", name=bank,
        line=dict(color=COLORS[bank], width=2.5), marker=dict(size=9),
        hovertemplate=f"<b>{bank}</b><br>NIM: %{{y:.2f}}%<extra></extra>",
    ))
top = max(kpis["nim"].max(), max(ECB_HIST.values())) * 1.15
fig_nim.update_layout(
    **{key: v for key, v in LAYOUT.items() if key not in ("xaxis", "yaxis")},
    title="Net interest margin (%) vs ECB deposit facility rate (%)",
    height=400,
    xaxis=dict(tickvals=YEARS, gridcolor="#1e293b", tickfont=dict(color="#94a3b8")),
    yaxis=dict(title="NIM (%)", ticksuffix="%", gridcolor="#1e293b",
               tickfont=dict(color="#94a3b8"), range=[0, top]),
    yaxis2=dict(title="ECB rate (%)", ticksuffix="%", overlaying="y", side="right",
                tickfont=dict(color="#64748b"), range=[0, top], showgrid=False),
)
st.plotly_chart(fig_nim, use_container_width=True)
st.caption("NIM = net interest income / average total assets (opening + closing / 2).")

st.divider()

# ── 2. NIM sensitivity ────────────────────────────────────────────────────────
st.subheader("2. How much of the rate rise reached the margin")
st.markdown(
    "A simple measure: the change in NIM divided by the change in the average ECB rate. "
    "A higher figure means more of the rate rise ended up in the margin."
)

d_ecb_23 = (ECB_HIST[2023] - ECB_HIST[2022]) * 100   # bps
d_ecb_24 = (ECB_HIST[2024] - ECB_HIST[2023]) * 100

beta_rows = []
for bank in BANKS:
    d_nim_23 = (k.loc[(bank, 2023), "nim"] - k.loc[(bank, 2022), "nim"]) * 100
    d_nim_24 = (k.loc[(bank, 2024), "nim"] - k.loc[(bank, 2023), "nim"]) * 100
    beta_rows.append({
        "Bank": bank,
        "ECB rate change 2022→23": f"{d_ecb_23:+.0f}bp",
        "NIM change 2022→23": f"{d_nim_23:+.0f}bp",
        "Share reaching the margin 2022→23": f"{d_nim_23 / d_ecb_23 * 100:.0f}%",
        "ECB rate change 2023→24": f"{d_ecb_24:+.0f}bp",
        "NIM change 2023→24": f"{d_nim_24:+.0f}bp",
        "_share": d_nim_23 / d_ecb_23 * 100,
    })
beta_df = pd.DataFrame(beta_rows).set_index("Bank")

fig_beta = go.Figure(go.Bar(
    x=BANKS, y=beta_df["_share"], marker_color=[COLORS[b] for b in BANKS],
    text=[f"{v:.0f}%" for v in beta_df["_share"]], textposition="outside",
    hovertemplate="%{x}<br>%{y:.0f}% of the rate rise reached the NIM<extra></extra>",
))
fig_beta.update_layout(**LAYOUT, height=320, showlegend=False,
                       title=f"NIM change / ECB rate change, 2022→2023 (ECB average {d_ecb_23:+.0f}bp)")
fig_beta.update_yaxes(ticksuffix="%", rangemode="tozero")
st.plotly_chart(fig_beta, use_container_width=True)
st.dataframe(beta_df.drop(columns="_share"), use_container_width=True, height=215)

hi_b, lo_b = beta_df["_share"].idxmax(), beta_df["_share"].idxmin()
st.caption(
    f"{hi_b} passed {beta_df.loc[hi_b, '_share']:.0f}% of the 2022→23 rate rise into its margin and "
    f"{lo_b} {beta_df.loc[lo_b, '_share']:.0f}%. This is not a deposit beta: it also reflects the share of "
    "floating-rate loans, cash held at the central bank, bond portfolios and hedging. In 2023→24 the average "
    "rate moved little, so that column says little about sensitivity."
)

st.divider()

# ── 3. ECB funding ────────────────────────────────────────────────────────────
st.subheader("3. ECB funding paid back")

tot = ecb.groupby("year")["value"].sum()
st.markdown(
    f"The four banks owed the ECB and other central banks €{tot[2022]/1000:.1f}bn at the end of 2022, "
    f"€{tot[2023]/1000:.1f}bn at the end of 2023 and €{tot[2024]/1000:.1f}bn at the end of 2024. "
    "Most of it was TLTRO-III funding. The ECB made TLTRO-III more expensive from 23 November 2022, "
    "and the last operation matured in December 2024. By then only Alpha still had ECB funding."
)

fig_ecb = go.Figure()
for bank in BANKS:
    b = ecb[ecb.bank == bank].sort_values("year")
    fig_ecb.add_trace(go.Bar(
        x=b["year"], y=b["value"], name=bank, marker_color=COLORS[bank],
        text=[f"€{v/1000:.1f}bn" if v > 0 else "0" for v in b["value"]], textposition="outside",
        hovertemplate=f"<b>{bank}</b><br>%{{x}}: €%{{y:,.0f}}m<extra></extra>",
    ))
fig_ecb.update_layout(**LAYOUT, barmode="group", height=380,
                      title="Amounts due to the ECB and central banks at year end (€m)")
fig_ecb.update_xaxes(tickvals=YEARS)
fig_ecb.update_yaxes(tickprefix="€", ticksuffix="m", range=[0, ecb["value"].max() * 1.2])
st.plotly_chart(fig_ecb, use_container_width=True)

ecb_tbl = ecb.pivot(index="bank", columns="year", values="value").loc[BANKS]
ecb_tbl.columns = [f"{c} (€m)" for c in ecb_tbl.columns]
ecb_tbl = ecb_tbl.map(lambda v: f"{v:,.0f}")
ecb_tbl["Sources"] = [
    "; ".join(f"{r.source_file} p.{r.source_page}"
              for r in ecb[ecb.bank == b].drop_duplicates(["source_file", "source_page"]).itertuples())
    for b in BANKS
]
st.dataframe(ecb_tbl, use_container_width=True, height=215)
st.caption(
    "Cross-check: Piraeus's reports put total ECB funding to the whole Greek banking system at €35.4bn at "
    "end-2022 and €14.3bn at end-2023 (FY2023 and FY2024 reports, p.12), so these four banks account for "
    "almost all of it."
)

st.divider()

# ── 4. Deposits ───────────────────────────────────────────────────────────────
st.subheader("4. Customer deposits")

dep = kpis.pivot(index="bank", columns="year", values="deposits").loc[BANKS]
eb_organic = dep.loc["Eurobank", 2024] - HELLENIC_BANK_DEPOSITS
sector_22, sector_24 = dep[2022].sum(), dep[2024].sum()
st.markdown(
    f"Deposits at the four banks grew from €{sector_22/1000:.1f}bn in 2022 to €{sector_24/1000:.1f}bn in 2024 "
    f"({(sector_24/sector_22-1)*100:+.1f}%). Most of the rise is Eurobank's: its deposits went from "
    f"€{dep.loc['Eurobank', 2023]/1000:.1f}bn to €{dep.loc['Eurobank', 2024]/1000:.1f}bn in 2024, of which "
    f"€{HELLENIC_BANK_DEPOSITS/1000:.1f}bn came with Hellenic Bank (Eurobank FY2024 report p.262). Without it the "
    f"four banks grew deposits by {((sector_24 - HELLENIC_BANK_DEPOSITS)/sector_22-1)*100:+.1f}% over the two years, "
    "even while they were paying back the ECB."
)

fig_dep = make_subplots(rows=1, cols=2, subplot_titles=("Customer deposits (€bn)", "Yearly change (%)"))
for bank in BANKS:
    b = kpis[kpis.bank == bank].sort_values("year")
    fig_dep.add_trace(go.Bar(
        x=b["year"], y=b["deposits"] / 1000, name=bank, marker_color=COLORS[bank],
        hovertemplate=f"<b>{bank}</b><br>Deposits: €%{{y:.1f}}bn<extra></extra>",
    ), row=1, col=1)
    yoy = b["deposits"].pct_change() * 100
    fig_dep.add_trace(go.Scatter(
        x=b["year"].values[1:], y=yoy.values[1:], mode="lines+markers", name=bank, showlegend=False,
        line=dict(color=COLORS[bank], width=2), marker=dict(size=8),
        hovertemplate=f"<b>{bank}</b><br>Change: %{{y:+.1f}}%<extra></extra>",
    ), row=1, col=2)
fig_dep.add_hline(y=0, line_color="#475569", row=1, col=2)
fig_dep.add_annotation(
    x=2024, y=dep.loc["Eurobank", 2024] / 1000, text="Hellenic Bank<br>consolidated",
    showarrow=True, arrowhead=2, arrowcolor="#94a3b8", ax=40, ay=-40,
    font=dict(color="#94a3b8", size=10), row=1, col=1,
)
fig_dep.update_layout(
    **{key: v for key, v in LAYOUT.items() if key not in ("xaxis", "yaxis")},
    title="Customer deposits and yearly change", height=400, barmode="group",
)
for c in (1, 2):
    fig_dep.update_xaxes(tickvals=YEARS, gridcolor="#1e293b", tickfont=dict(color="#94a3b8"), row=1, col=c)
    fig_dep.update_yaxes(gridcolor="#1e293b", tickfont=dict(color="#94a3b8"), row=1, col=c)
fig_dep.update_yaxes(tickprefix="€", ticksuffix="bn", row=1, col=1)
fig_dep.update_yaxes(ticksuffix="%", row=1, col=2)
st.plotly_chart(fig_dep, use_container_width=True)

chg = pd.DataFrame({
    "2022 (€m)": dep[2022].map("{:,.0f}".format),
    "2023 (€m)": dep[2023].map("{:,.0f}".format),
    "2024 (€m)": dep[2024].map("{:,.0f}".format),
    "Change 2022→24": ((dep[2024] / dep[2022] - 1) * 100).map("{:+.1f}%".format),
})
chg.loc["Eurobank", "Change 2022→24"] += f" ({(eb_organic / dep.loc['Eurobank', 2022] - 1) * 100:+.1f}% without Hellenic Bank)"
st.dataframe(chg, use_container_width=True, height=215)

st.divider()

# ── Takeaways (computed) ──────────────────────────────────────────────────────
st.subheader("Takeaways for 2025–2026")

nii = kpis.groupby("year")["nii"].sum()
fc = forecast_nii(kpis, "Base (gradual cuts)").groupby("year")["nii"].sum()
st.markdown(f"""
| Factor | 2022–2024 | What it means for 2025–2026 |
|--------|-----------|-----------------------------|
| **Rates and NII** | Sector NII {nii[2022]:,.0f} → {nii[2024]:,.0f} €m ({(nii[2024]/nii[2022]-1)*100:+.0f}%) as the average ECB rate rose from {ECB_HIST[2022]:.2f}% to {ECB_HIST[2024]:.2f}% | The ECB cut its deposit rate to 2.00% by June 2025; in the base scenario on the Forecast page sector NII is {fc[2026]:,.0f} €m in 2026 ({(fc[2026]/nii[2024]-1)*100:+.0f}% vs 2024) |
| **ECB funding** | Down from €{tot[2022]/1000:.1f}bn to €{tot[2024]/1000:.1f}bn | TLTRO-III is over; the banks fund themselves with deposits, bonds and repos |
| **Deposits** | {((sector_24 - HELLENIC_BANK_DEPOSITS)/sector_22-1)*100:+.1f}% without Hellenic Bank | Deposit pricing decides how much margin the banks keep as rates fall |
""")
st.caption(
    "The base scenario assumes margins fall with rates as fast as they rose in 2022–2024. Banks hedge part "
    "of their rate risk, so the real fall can be smaller. FY2025 results are now published and can be used "
    "to test the scenario."
)

st.divider()
st.caption(
    "Greek Banking Sector Analysis 2022–2024 | Analyst: Spyros Papastergiou | papastergiousp@gmail.com"
)
