"""
2_Peer_Comparison.py — Radar chart, score table and ranked bar charts across the four banks.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from utils.data import load_kpis, BANKS, YEARS, COLORS, LAYOUT

st.set_page_config(page_title="Peer Comparison", page_icon="📊", layout="wide")

with st.sidebar:
    st.markdown("### 📊 Peer Comparison")
    year = st.radio("Select year", YEARS, index=2)
    st.divider()
    st.caption("Scores are scaled between the weakest (0) and the strongest (1) of the four banks "
               "on each measure (min-max), so they show position within this peer group only.")


@st.cache_data
def get_kpis():
    return load_kpis()


kpis = get_kpis()
ky = kpis[kpis.year == year].set_index("bank")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Peer Comparison")
st.caption(f"FY{year}: Eurobank, Alpha Bank, Piraeus Bank and NBG on the same definitions")
st.divider()

# Measures where better and worse are clear. Size (assets, profit in €) and the
# loan-to-deposit ratio are left out of the scores on purpose.
SCORED = {
    # label: (column, higher is better)
    "RoTE": ("rote", True),
    "ROE": ("roe", True),
    "ROA": ("roa", True),
    "NIM": ("nim", True),
    "C/I": ("cost_to_income", False),
    "Cost of risk": ("cost_of_risk", False),
    "NPE": ("npe_ratio", False),
    "CET1": ("cet1", True),
    "DTC/CET1": ("dtc_to_cet1", False),
}


def normalise(series: pd.Series, higher_better: bool) -> pd.Series:
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(0.5, index=series.index)
    norm = (series - mn) / (mx - mn)
    return norm if higher_better else 1 - norm


scores = pd.DataFrame({label: normalise(ky[col], hb) for label, (col, hb) in SCORED.items()})

# ── Radar chart ───────────────────────────────────────────────────────────────
st.subheader(f"Radar chart, FY{year} (1 = strongest of the four)")

theta = list(scores.columns) + [scores.columns[0]]   # close the polygon


def _hex_rgba(hex_color: str, alpha: float) -> str:
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    return f"rgba({r},{g},{b},{alpha})"


fig_radar = go.Figure()
for bank in BANKS:
    r_vals = list(scores.loc[bank]) + [scores.loc[bank].iloc[0]]
    fig_radar.add_trace(go.Scatterpolar(
        r=r_vals, theta=theta, name=bank, fill="toself",
        line=dict(color=COLORS[bank], width=2.5),
        fillcolor=_hex_rgba(COLORS[bank], 0.15),
        hovertemplate=f"<b>{bank}</b><br>%{{theta}}: %{{r:.2f}}<extra></extra>",
    ))

fig_radar.update_layout(
    **{k: v for k, v in LAYOUT.items() if k not in ("xaxis", "yaxis", "legend", "margin", "title_font")},
    polar=dict(
        bgcolor="rgba(0,0,0,0)",
        radialaxis=dict(visible=True, range=[0, 1], tickfont=dict(color="#64748b"), gridcolor="#1e293b"),
        angularaxis=dict(tickfont=dict(color="#94a3b8"), gridcolor="#1e293b"),
    ),
    height=480,
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8")),
    margin=dict(l=60, r=60, t=40, b=40),
    title=f"FY{year} scores on nine measures",
    title_font=dict(color="#f1f5f9"),
)
st.plotly_chart(fig_radar, use_container_width=True)

st.divider()

# ── Score table ───────────────────────────────────────────────────────────────
st.subheader(f"Scores and values, FY{year}")

FMT = {"RoTE": "{:.1f}%", "ROE": "{:.1f}%", "ROA": "{:.2f}%", "NIM": "{:.2f}%", "C/I": "{:.1f}%",
       "Cost of risk": "{:.2f}%", "NPE": "{:.1f}%", "CET1": "{:.1f}%", "DTC/CET1": "{:.0f}%"}

score_tbl = (scores * 100).round(0).astype(int).loc[BANKS]
value_tbl = pd.DataFrame({label: [FMT[label].format(ky.loc[b, col]) for b in BANKS]
                          for label, (col, _) in SCORED.items()}, index=BANKS)


def style_score(val):
    if val >= 75:
        return "background-color: #14532d; color: #86efac"
    if val >= 50:
        return "background-color: #1e3a1e; color: #4ade80"
    if val >= 25:
        return "background-color: #422006; color: #fb923c"
    return "background-color: #450a0a; color: #fca5a5"


st.markdown("**Score** (0 = weakest of the four, 100 = strongest)")
st.dataframe(score_tbl.style.map(style_score), use_container_width=True, height=215)
st.markdown("**Values**")
st.dataframe(value_tbl, use_container_width=True, height=215)
st.caption("Lower is better for C/I, cost of risk, NPE and DTC/CET1; the score already takes that into account.")

st.divider()

# ── Ranked bar charts ─────────────────────────────────────────────────────────
st.subheader(f"Ranked bar charts, FY{year}")

BAR_METRICS = [
    # column, label, higher is better, text format
    ("rote", "RoTE (%)", True, "{:.1f}%"),
    ("roe", "ROE (%)", True, "{:.1f}%"),
    ("nim", "NIM (%)", True, "{:.2f}%"),
    ("cost_to_income", "Cost-to-income (%)", False, "{:.1f}%"),
    ("cet1", "CET1 (%)", True, "{:.1f}%"),
    ("npe_ratio", "NPE ratio (%)", False, "{:.1f}%"),
    ("net_profit", "Net profit (€m)", True, "€{:,.0f}m"),
]

cols_per_row = 3
for start in range(0, len(BAR_METRICS), cols_per_row):
    cols = st.columns(cols_per_row)
    for i, (col_key, label, higher_better, fmt) in enumerate(BAR_METRICS[start:start + cols_per_row]):
        sorted_df = ky[[col_key]].dropna().sort_values(col_key, ascending=not higher_better)
        fig_bar = go.Figure(go.Bar(
            x=sorted_df.index, y=sorted_df[col_key],
            marker_color=[COLORS[b] for b in sorted_df.index],
            text=[fmt.format(v) for v in sorted_df[col_key]], textposition="outside",
            hovertemplate="%{x}<br>" + label + ": %{y:,.2f}<extra></extra>",
        ))
        note = "lower is better" if not higher_better else "higher is better"
        fig_bar.update_layout(
            **{k: v for k, v in LAYOUT.items() if k != "margin"},
            title=f"{label}, {note}", height=300, showlegend=False,
            margin=dict(l=30, r=10, t=50, b=40),
        )
        fig_bar.update_yaxes(rangemode="tozero", range=[0, sorted_df[col_key].max() * 1.2])
        cols[i].plotly_chart(fig_bar, use_container_width=True)

st.divider()
st.caption("Greek Banking Sector Analysis 2022–2024 | Analyst: Spyros Papastergiou | papastergiousp@gmail.com")
