"""
5_Investment_Thesis.py — What FY2024 returns would justify (justified P/TBV), and each bank's
strengths and weak points computed from the data. No market prices and no ratings.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from utils.data import load_kpis, BANKS, YEARS, COLORS, LAYOUT

st.set_page_config(page_title="Investment Thesis", page_icon="💡", layout="wide")

with st.sidebar:
    st.markdown("### 💡 Investment Thesis")
    st.markdown("**Assumptions**")
    coe = st.slider("Cost of equity, CoE (%)", 8.0, 14.0, 10.0, 0.25,
                    help="Your assumption: risk-free rate + beta × equity risk premium + country premium.")
    g = st.slider("Long-run growth, g (%)", 0.0, 4.0, 2.0, 0.25,
                  help="Long-run nominal growth of profits.")
    st.divider()
    st.caption(
        "Justified P/TBV = (RoTE − g) / (CoE − g): the multiple of tangible book value that a bank's "
        "return would justify if it lasted. No market prices are used and nothing here is a recommendation."
    )


@st.cache_data
def get_kpis():
    return load_kpis()


kpis = get_kpis()
k24 = kpis[kpis.year == 2024].set_index("bank").loc[BANKS]
k22 = kpis[kpis.year == 2022].set_index("bank").loc[BANKS]


def justified_ptbv(rote: float) -> float:
    return (rote - g) / (coe - g) if coe > g else np.nan


# ── Header ────────────────────────────────────────────────────────────────────
st.title("Investment Thesis")
st.caption(
    "FY2024 returns against an assumed cost of equity, and each bank's strengths and weak points "
    "computed from the data. Not investment advice."
)
st.divider()

# ── RoTE vs cost of equity ────────────────────────────────────────────────────
st.subheader("Return on tangible equity vs cost of equity")

fig_rote = go.Figure()
for bank in BANKS:
    b = kpis[kpis.bank == bank].sort_values("year")
    fig_rote.add_trace(go.Scatter(
        x=b["year"], y=b["rote"], mode="lines+markers+text", name=bank,
        line=dict(color=COLORS[bank], width=2.5), marker=dict(size=9),
        text=[f"{v:.1f}%" for v in b["rote"]], textposition="top center",
        textfont=dict(color=COLORS[bank], size=10),
        hovertemplate=f"<b>{bank}</b><br>%{{x}}: RoTE %{{y:.1f}}%<extra></extra>",
    ))
fig_rote.add_hline(y=coe, line_dash="dash", line_color="#f59e0b",
                   annotation_text=f"Cost of equity {coe:.2f}%", annotation_font_color="#f59e0b")
fig_rote.update_layout(**LAYOUT, height=400, title="RoTE (%), 2022–2024")
fig_rote.update_xaxes(tickvals=YEARS)
fig_rote.update_yaxes(ticksuffix="%", range=[0, kpis["rote"].max() * 1.15])
st.plotly_chart(fig_rote, use_container_width=True)

above = [b for b in BANKS if k24.loc[b, "rote"] > coe]
below = [b for b in BANKS if k24.loc[b, "rote"] <= coe]
if above and below:
    st.markdown(f"At a {coe:.2f}% cost of equity, **{', '.join(above)}** earned more than the cost of "
                f"equity in 2024 and **{', '.join(below)}** earned less.")
elif above:
    st.markdown(f"At a {coe:.2f}% cost of equity, all four banks earned more than the cost of equity in 2024.")
else:
    st.markdown(f"At a {coe:.2f}% cost of equity, no bank earned more than the cost of equity in 2024.")
st.caption("RoTE = net profit attributable / average tangible equity (equity attributable − AT1 − goodwill "
           "and intangibles). AT1 coupons are not deducted from profit.")

st.divider()

# ── Justified P/TBV ───────────────────────────────────────────────────────────
st.subheader("Justified P/TBV, FY2024")

rows = []
for bank in BANKS:
    r = k24.loc[bank]
    rows.append({
        "Bank": bank,
        "Net profit (€m)": f"{r['net_profit']:,.0f}",
        "Equity attributable (€m)": f"{r['equity']:,.0f}",
        "AT1 (€m)": f"{r['at1']:,.0f}",
        "Goodwill & intangibles (€m)": f"{r['intangibles']:,.0f}",
        "Tangible equity (€m)": f"{r['tangible_equity']:,.0f}",
        "RoTE": f"{r['rote']:.1f}%",
        "RoTE − CoE": f"{r['rote'] - coe:+.1f}pp",
        "Justified P/TBV": f"{justified_ptbv(r['rote']):.2f}x",
    })
st.dataframe(pd.DataFrame(rows).set_index("Bank"), use_container_width=True, height=215)

ptbv = [justified_ptbv(k24.loc[b, "rote"]) for b in BANKS]
fig_pb = go.Figure(go.Bar(
    x=BANKS, y=ptbv, marker_color=[COLORS[b] for b in BANKS],
    text=[f"{v:.2f}x" for v in ptbv], textposition="outside",
    hovertemplate="%{x}<br>Justified P/TBV: %{y:.2f}x<extra></extra>",
))
fig_pb.add_hline(y=1.0, line_dash="dot", line_color="#475569",
                 annotation_text="1.0x = tangible book value", annotation_font_color="#64748b")
fig_pb.update_layout(**LAYOUT, height=360, showlegend=False,
                     title=f"Justified P/TBV at CoE {coe:.2f}% and g {g:.2f}%")
fig_pb.update_yaxes(ticksuffix="x", rangemode="tozero")
st.plotly_chart(fig_pb, use_container_width=True)
st.caption("A bank that earns exactly its cost of equity is worth 1.0x tangible book value in this model.")

st.markdown("**Sensitivity to the cost of equity** (at the chosen growth rate)")
coe_grid = [9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0]
sens = pd.DataFrame(
    {f"CoE {c:.1f}%": [(k24.loc[b, "rote"] - g) / (c - g) if c > g else np.nan for b in BANKS]
     for c in coe_grid},
    index=BANKS,
)
st.dataframe(sens.style.format("{:.2f}x"), use_container_width=True)

st.divider()

# ── Strengths and weak points, computed ───────────────────────────────────────
st.subheader("Strengths and weak points, computed from the data")
st.caption("Ranks the four banks on eight measures: the 2024 level and the change since 2022. "
           "Shows the three points where each bank stands out most from the average.")

METRICS = [
    # column, label, higher is better, format
    ("rote", "RoTE", True, "{:.1f}%"),
    ("nim", "net interest margin", True, "{:.2f}%"),
    ("cost_to_income", "cost-to-income ratio", False, "{:.1f}%"),
    ("cost_of_risk", "cost of risk", False, "{:.2f}%"),
    ("npe_ratio", "NPE ratio", False, "{:.1f}%"),
    ("cet1", "CET1 ratio", True, "{:.1f}%"),
    ("dtc_to_cet1", "DTC share of CET1", False, "{:.0f}%"),
    ("fee_share", "fee share of operating income", True, "{:.1f}%"),
]

NOTES = {
    "Eurobank": [
        "Hellenic Bank (Cyprus) is consolidated from 30 June 2024. It added €295m to 2024 NII; "
        "without it NII grew 1.8% (FY2024 report p.4–5).",
    ],
}


def points(bank: str):
    strengths, weak = [], []
    for col, label, higher_better, fmt in METRICS:
        lvl = k24[col].round(2)
        avg, sd = k24[col].mean(), k24[col].std() or 1.0
        z = abs(k24.loc[bank, col] - avg) / sd
        best = lvl.max() if higher_better else lvl.min()
        worst = lvl.min() if higher_better else lvl.max()
        same = [b for b in BANKS if b != bank and lvl[b] == lvl[bank]]
        tie = f", level with {' and '.join(same)}" if same else ""
        value = fmt.format(k24.loc[bank, col])
        if lvl[bank] == best:
            word = "Highest" if higher_better else "Lowest"
            strengths.append((z, f"{word} {label} of the four: {value}{tie} (average {fmt.format(avg)})"))
        elif lvl[bank] == worst:
            word = "Lowest" if higher_better else "Highest"
            weak.append((z, f"{word} {label} of the four: {value} (average {fmt.format(avg)})"))

        sign = 1 if higher_better else -1
        better = (k24[col] - k22[col]) * sign            # > 0 means it improved
        sd_c = better.std() or 1.0
        z_c = abs(better[bank] - better.mean()) / sd_c
        move = f"{fmt.format(k22.loc[bank, col])} → {fmt.format(k24.loc[bank, col])}"
        if better.idxmax() == bank and better[bank] > 0:
            word = "rise" if higher_better else "fall"
            strengths.append((z_c, f"Largest {word} in {label} since 2022: {move}"))
        if better.idxmin() == bank and better[bank] < 0:
            word = "fall" if higher_better else "rise"
            weak.append((z_c, f"Largest {word} in {label} since 2022: {move}"))
    top = lambda items: [t for _, t in sorted(items, key=lambda x: -x[0])[:3]]
    return top(strengths), top(weak)


for bank in BANKS:
    s, w = points(bank)
    with st.expander(f"**{bank}**  |  RoTE {k24.loc[bank, 'rote']:.1f}%  |  "
                     f"justified P/TBV {justified_ptbv(k24.loc[bank, 'rote']):.2f}x", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Strengths**")
            st.markdown("\n".join(f"- {t}" for t in s) if s else "- None stands out among the four")
        with c2:
            st.markdown("**Weak points**")
            st.markdown("\n".join(f"- {t}" for t in w) if w else "- None stands out among the four")
        for note in NOTES.get(bank, []):
            st.caption(note)

st.divider()
st.caption(
    "Greek Banking Sector Analysis 2022–2024 | Analyst: Spyros Papastergiou | papastergiousp@gmail.com  \n"
    "Justified P/TBV is a simple Gordon growth model: a way to read returns, not a price target."
)
