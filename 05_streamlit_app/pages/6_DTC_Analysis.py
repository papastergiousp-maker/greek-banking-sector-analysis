"""
6_DTC_Analysis.py — Deferred tax credits (DTCs) in the CET1 capital of the four Greek banks.
Every DTC figure comes from the annual reports; the PDF pages are listed at the bottom.
"""

import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from utils.data import load_kpis, load_sources, BANKS, YEARS, COLORS, LAYOUT

st.set_page_config(page_title="DTC Analysis", page_icon="🏦", layout="wide")


@st.cache_data
def get_data():
    return load_kpis(), load_sources()


kpis, sources = get_data()
k = kpis.set_index(["bank", "year"])

with st.sidebar:
    st.markdown("### 🏦 DTC Analysis")
    st.caption(
        "DTC = deferred tax assets that can be converted into a claim on the Greek State "
        "(article 27A of Law 4172/2013), as included in regulatory capital. "
        "Figures as reported in each annual report; pages in the table at the bottom."
    )

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Deferred Tax Credits (DTCs)")
st.caption("How much of each bank's CET1 capital is made of DTCs, FY2022–2024")
st.divider()

# ── Context ───────────────────────────────────────────────────────────────────
st.subheader("What DTCs are and why they matter")
st.markdown("""
Greek banks still carry deferred tax assets (DTAs) from the crisis years: losses on the 2012 PSI bond
exchange and loan loss provisions. Under **article 27A of Law 4172/2013**, most of these DTAs can be
converted into a claim on the Greek State if the bank reports an accounting loss. Because of that
guarantee they do not depend on future profits, so under **article 39 of the CRR** they are not deducted
from CET1 capital; they carry a 100% risk weight instead.

**Why analysts watch them:** a DTC counts as CET1 capital, but it is a tax claim on the Greek State,
not capital paid in by shareholders or kept from profits. The higher the DTC share of CET1, the lower
the quality of the capital.

**What the banks plan:** two banks describe in their FY2024 reports how they will deduct DTCs from
capital faster than the tax schedule from 2025. Eurobank aims to eliminate its DTC by 2033
(FY2024 report p.6). Alpha will accelerate DTC amortisation by an amount equal to 29% of its planned
dividends (FY2024 report p.23).
""")
st.divider()

# ── DTC stock ─────────────────────────────────────────────────────────────────
st.subheader("DTC stock (€m)")

fig_stock = go.Figure()
for bank in BANKS:
    b = kpis[kpis.bank == bank].sort_values("year")
    fig_stock.add_trace(go.Bar(
        x=b["year"], y=b["dtc"], name=bank, marker_color=COLORS[bank],
        text=[f"€{v/1000:.2f}bn" for v in b["dtc"]], textposition="outside",
        hovertemplate=f"<b>{bank}</b><br>%{{x}}: €%{{y:,.0f}}m<extra></extra>",
    ))
sector_dtc = kpis.groupby("year")["dtc"].sum()
for year in YEARS:
    fig_stock.add_annotation(
        x=year, y=kpis["dtc"].max() * 1.2, showarrow=False,
        text=f"Total €{sector_dtc[year]/1000:.1f}bn", font=dict(color="#94a3b8", size=11),
    )
fig_stock.update_layout(**LAYOUT, barmode="group", title="DTC per bank (€m)", height=420)
fig_stock.update_xaxes(tickvals=YEARS)
fig_stock.update_yaxes(tickprefix="€", ticksuffix="m", range=[0, kpis["dtc"].max() * 1.3])
st.plotly_chart(fig_stock, use_container_width=True)
st.caption(
    "Alpha and NBG report the DTC rounded to €0.1bn. Piraeus 2024 is the DTC included in regulatory "
    "capital: €3,248m eligible DTA less a €128m prudential amortisation adjustment (FY2024 report p.567–568)."
)

st.divider()

# ── DTC share of CET1 ─────────────────────────────────────────────────────────
st.subheader("DTC as a share of CET1 capital")

fig_pct = go.Figure()
for bank in BANKS:
    b = kpis[kpis.bank == bank].sort_values("year")
    fig_pct.add_trace(go.Scatter(
        x=b["year"], y=b["dtc_to_cet1"], mode="lines+markers+text", name=bank,
        line=dict(color=COLORS[bank], width=2.5), marker=dict(size=9),
        text=[f"{v:.0f}%" for v in b["dtc_to_cet1"]], textposition="top center",
        textfont=dict(color=COLORS[bank], size=11),
        hovertemplate=f"<b>{bank}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>",
    ))
fig_pct.update_layout(**LAYOUT, title="DTC / CET1 capital (%), lower is better", height=400)
fig_pct.update_xaxes(tickvals=YEARS)
fig_pct.update_yaxes(ticksuffix="%", range=[0, kpis["dtc_to_cet1"].max() * 1.15])
st.plotly_chart(fig_pct, use_container_width=True)
st.caption(
    "CET1 capital = CET1 ratio × RWAs. The banks' own figures for end-2024 are Alpha 49.2% "
    "(FY2024 report p.23) and Eurobank 36% (p.6); the small gaps come from rounding in the reported figures."
)

st.divider()

# ── CET1 with and without DTCs ────────────────────────────────────────────────
st.subheader("CET1 ratio with and without DTCs")
st.markdown(
    "An illustrative test: the CET1 ratio if all DTCs were deducted at once. DTCs carry a 100% risk "
    "weight, so the deduction also removes them from RWAs. No bank has to do this; DTCs run off over time."
)
year_sel = st.radio("Year", YEARS[::-1], horizontal=True)
ks = kpis[kpis.year == year_sel].set_index("bank").loc[BANKS]

fig_ex = go.Figure()
fig_ex.add_trace(go.Bar(
    x=BANKS, y=ks["cet1"], name="CET1 ratio as reported",
    marker_color=[COLORS[b] for b in BANKS],
    text=[f"{v:.1f}%" for v in ks["cet1"]], textposition="outside",
    hovertemplate="%{x}<br>Reported: %{y:.1f}%<extra></extra>",
))
fig_ex.add_trace(go.Bar(
    x=BANKS, y=ks["cet1_ex_dtc"], name="CET1 ratio without DTCs",
    marker_color="#64748b",
    text=[f"{v:.1f}%" for v in ks["cet1_ex_dtc"]], textposition="outside",
    hovertemplate="%{x}<br>Without DTCs: %{y:.1f}%<extra></extra>",
))
fig_ex.update_layout(**LAYOUT, barmode="group", height=380,
                     title=f"CET1 ratio, reported vs without DTCs ({year_sel})")
fig_ex.update_yaxes(ticksuffix="%", range=[0, ks["cet1"].max() * 1.2])
st.plotly_chart(fig_ex, use_container_width=True)
st.caption("Without DTCs = (CET1 capital − DTC) / (RWAs − DTC).")

st.divider()

# ── Run-off at the 2022–24 pace ───────────────────────────────────────────────
st.subheader("Run-off at the 2022–24 pace")

pace = {b: (k.loc[(b, 2022), "dtc"] - k.loc[(b, 2024), "dtc"]) / 2 for b in BANKS}
years_left = {b: k.loc[(b, 2024), "dtc"] / pace[b] for b in BANKS}
zero_year = {b: 2024 + math.ceil(years_left[b]) for b in BANKS}

proj_years = list(range(2024, max(zero_year.values()) + 1))
fig_proj = go.Figure()
for bank in BANKS:
    b = kpis[kpis.bank == bank].sort_values("year")
    fig_proj.add_trace(go.Scatter(
        x=b["year"], y=b["dtc"], mode="lines+markers", name=bank,
        line=dict(color=COLORS[bank], width=2.5), marker=dict(size=8), legendgroup=bank,
        hovertemplate=f"<b>{bank}</b><br>%{{x}}: €%{{y:,.0f}}m (reported)<extra></extra>",
    ))
    start = k.loc[(bank, 2024), "dtc"]
    fig_proj.add_trace(go.Scatter(
        x=proj_years, y=[max(0.0, start - pace[bank] * (y - 2024)) for y in proj_years],
        mode="lines", name=f"{bank} (extrapolated)", showlegend=False, legendgroup=bank,
        line=dict(color=COLORS[bank], width=1.5, dash="dot"),
        hovertemplate=f"<b>{bank}</b><br>%{{x}}: €%{{y:,.0f}}m (extrapolated)<extra></extra>",
    ))
fig_proj.add_trace(go.Scatter(
    x=[2033], y=[0], mode="markers+text", name="Eurobank target (2033)",
    marker=dict(symbol="x", size=12, color=COLORS["Eurobank"]),
    text=["Eurobank target"], textposition="top center", textfont=dict(color="#94a3b8", size=10),
    hovertemplate="Eurobank: DTC eliminated by 2033 (FY2024 report p.6)<extra></extra>",
))
fig_proj.add_vline(x=2024.5, line_dash="dot", line_color="#475569")
fig_proj.update_layout(**LAYOUT, height=420,
                       title="DTC (€m): reported 2022–2024, straight line at the 2022–24 pace after that")
fig_proj.update_yaxes(tickprefix="€", ticksuffix="m", rangemode="tozero")
st.plotly_chart(fig_proj, use_container_width=True)
st.caption(
    "A straight-line extrapolation of the average yearly fall in 2022–2024, not a forecast. "
    "Because Alpha and NBG report the DTC rounded to €0.1bn, their pace is approximate. "
    "Piraeus's 2024 fall includes the €128m prudential adjustment."
)

st.divider()

# ── Summary table ─────────────────────────────────────────────────────────────
st.subheader("Summary")

rows = []
for bank in BANKS:
    row = {"Bank": bank}
    for year in YEARS:
        row[f"DTC {year} (€m)"] = f"{k.loc[(bank, year), 'dtc']:,.0f}"
    for year in YEARS:
        row[f"DTC/CET1 {year}"] = f"{k.loc[(bank, year), 'dtc_to_cet1']:.1f}%"
    row["CET1 2024"] = f"{k.loc[(bank, 2024), 'cet1']:.1f}%"
    row["CET1 2024 without DTCs"] = f"{k.loc[(bank, 2024), 'cet1_ex_dtc']:.1f}%"
    row["Yearly fall 2022–24 (€m)"] = f"{pace[bank]:,.0f}"
    row["Zero at that pace"] = str(zero_year[bank])
    rows.append(row)
st.dataframe(pd.DataFrame(rows).set_index("Bank"), use_container_width=True, height=215)

with st.expander("Sources: report and page for every DTC figure"):
    src = sources[sources.metric == "dtc"][["bank", "year", "value", "source", "how"]]
    src = src.rename(columns={"value": "DTC (€m)", "source": "Report and page", "how": "Note"})
    st.dataframe(src.sort_values(["bank", "year"]).set_index(["bank", "year"]),
                 use_container_width=True)

st.divider()

# ── Takeaways (computed) ──────────────────────────────────────────────────────
st.subheader("Takeaways")

cet1_cap = kpis.assign(cap=kpis["cet1"] / 100 * kpis["rwa"]).groupby("year")["cap"].sum()
k24 = kpis[kpis.year == 2024].set_index("bank")
hi, lo = k24["dtc_to_cet1"].idxmax(), k24["dtc_to_cet1"].idxmin()
ex_lo, ex_hi = k24["cet1_ex_dtc"].idxmin(), k24["cet1_ex_dtc"].idxmax()
fell_everywhere = all(k.loc[(b, 2024), "dtc_to_cet1"] < k.loc[(b, 2022), "dtc_to_cet1"] for b in BANKS)

st.markdown(f"""
1. **The DTC stock is shrinking while capital grows.** Across the four banks DTCs fell from
   €{sector_dtc[2022]/1000:.1f}bn in 2022 to €{sector_dtc[2024]/1000:.1f}bn in 2024
   ({(sector_dtc[2024]/sector_dtc[2022]-1)*100:+.0f}%), while CET1 capital rose from
   €{cet1_cap[2022]/1000:.1f}bn to €{cet1_cap[2024]/1000:.1f}bn
   ({(cet1_cap[2024]/cet1_cap[2022]-1)*100:+.0f}%).
   {"So the DTC share of CET1 fell at every bank." if fell_everywhere else ""}

2. **Capital quality differs a lot between the banks.** At end-2024 DTCs were
   {k24.loc[hi, 'dtc_to_cet1']:.0f}% of CET1 capital at {hi} and {k24.loc[lo, 'dtc_to_cet1']:.0f}% at {lo}.
   Without DTCs the CET1 ratios would range from {k24.loc[ex_lo, 'cet1_ex_dtc']:.1f}% ({ex_lo})
   to {k24.loc[ex_hi, 'cet1_ex_dtc']:.1f}% ({ex_hi}).

3. **The run-off needs to speed up.** At the 2022–24 pace the DTCs would last until
   {min(zero_year.values())}–{max(zero_year.values())}. Eurobank's target of 2033 is
   {zero_year['Eurobank'] - 2033} years earlier than its own pace so far ({zero_year['Eurobank']}).
""")

st.divider()
st.caption(
    "Greek Banking Sector Analysis 2022–2024 | Analyst: Spyros Papastergiou | papastergiousp@gmail.com"
)
