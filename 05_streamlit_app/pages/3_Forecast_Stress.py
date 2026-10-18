"""
3_Forecast_Stress.py — ECB rate scenario NII forecast + interactive EBA-style stress test.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from utils.data import (
    load_kpis, BANKS, YEARS, COLORS, LAYOUT,
    ECB_HIST, ECB_SCENARIOS, CET1_REFERENCE,
    forecast_nii, stress_bank, nim_rate_sensitivity, load_eba, fmt_eur, pct
)


st.set_page_config(page_title="Forecast & Stress", page_icon="📈", layout="wide")

with st.sidebar:
    st.markdown("### 📈 Forecast & Stress")
    st.caption("NII scenarios driven by the ECB deposit rate.\n\n"
               "One-year stress test on FY2024 figures, with the official EBA 2023 results for context.")


@st.cache_data
def get_kpis():
    return load_kpis()


kpis = get_kpis()
k24  = kpis[kpis.year == 2024].set_index("bank")

st.title("Forecast & Stress Testing")
st.divider()

tab1, tab2, tab3 = st.tabs(["NII Scenarios 2025–2026", "Stress Test", "Sensitivity Analysis"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — NII FORECAST
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("NII Scenarios 2025–2026: ECB Deposit Rate")
    _sens = nim_rate_sensitivity(kpis)
    st.markdown(
        "Method: NII = NIM × average assets. **Rate effect** = each bank's historical NIM sensitivity to the "
        "ECB deposit rate over 2022–2024 (" + ", ".join(f"{b} {v:.2f}pp" for b, v in _sens.items()) +
        " of NIM per 1pp of rate), applied to the change from the 2024 average rate. **Volume effect** = total "
        "assets grow 2% a year from the end-2024 balance sheet in every scenario, so the scenarios differ only "
        "in rates. Same method as `04_forecasting/01_forecast_nii_2025_2026.ipynb`. Built on FY2022–2024 data; "
        "FY2025 results are now public and the actual deposit rate reached 2.00% in June 2025."
    )

    col_ctrl, col_ecb = st.columns([1, 2])

    with col_ctrl:
        scenario = st.radio(
            "ECB Rate Scenario",
            list(ECB_SCENARIOS.keys()),
            index=1,
        )
        st.markdown("**ECB deposit rate, yearly average (%): 2022–2024 actual, 2025–2026 scenario**")
        ecb_table = pd.DataFrame({
            "Year": [2022, 2023, 2024, 2025, 2026],
            "Rate": [
                ECB_HIST[2022],
                ECB_HIST[2023],
                ECB_HIST[2024],
                ECB_SCENARIOS[scenario][2025],
                ECB_SCENARIOS[scenario][2026],
            ]
        })
        st.dataframe(ecb_table.set_index("Year"), use_container_width=True, height=220)

    with col_ecb:
        # ECB rate path chart
        all_years = [2022, 2023, 2024, 2025, 2026]
        fig_ecb = go.Figure()
        for sc_name, sc_rates in ECB_SCENARIOS.items():
            rates = [ECB_HIST[2022], ECB_HIST[2023], ECB_HIST[2024],
                     sc_rates[2025], sc_rates[2026]]
            is_selected = sc_name == scenario
            fig_ecb.add_trace(go.Scatter(
                x=all_years, y=rates,
                mode="lines+markers",
                name=sc_name,
                line=dict(
                    width=3 if is_selected else 1.5,
                    dash="solid" if is_selected else "dash",
                    color={"Dovish (faster cuts)": "#60a5fa",
                           "Base (gradual cuts)":  "#10b981",
                           "Hawkish (cuts pause)": "#f59e0b"}[sc_name],
                ),
                marker=dict(size=8 if is_selected else 5),
                opacity=1.0 if is_selected else 0.45,
                hovertemplate=f"<b>{sc_name}</b><br>Year: %{{x}}<br>Rate: %{{y:.2f}}%<extra></extra>",
            ))
        fig_ecb.add_vline(x=2024.5, line_dash="dot", line_color="#475569",
                          annotation_text="forecast →", annotation_font_color="#64748b")
        fig_ecb.update_layout(**LAYOUT, title="ECB Deposit Facility Rate Path (%)",
                              height=280)
        fig_ecb.update_yaxes(ticksuffix="%")
        st.plotly_chart(fig_ecb, use_container_width=True)

    st.divider()

    # ── NII forecast chart ─────────────────────────────────────────────────────
    fc = forecast_nii(kpis, scenario)
    hist = kpis[["bank", "year", "nii"]].copy()
    hist["source"] = "actual"
    fc["source"]   = "forecast"
    combined = pd.concat([hist, fc], ignore_index=True)

    fig_nii = go.Figure()
    for bank in BANKS:
        bdata = combined[combined.bank == bank].sort_values("year")
        actual  = bdata[bdata.source == "actual"]
        fcast   = bdata[bdata.source == "forecast"]

        # Actual line
        fig_nii.add_trace(go.Scatter(
            x=actual["year"], y=actual["nii"], name=bank,
            mode="lines+markers",
            line=dict(color=COLORS[bank], width=2.5),
            marker=dict(size=7),
            hovertemplate=f"<b>{bank}</b> (actual)<br>NII: €%{{y:,.0f}}m<extra></extra>",
        ))
        # Forecast — dashed, connect from last actual
        bridge_x = [actual["year"].iloc[-1]] + list(fcast["year"])
        bridge_y = [actual["nii"].iloc[-1]]  + list(fcast["nii"])
        fig_nii.add_trace(go.Scatter(
            x=bridge_x, y=bridge_y, name=f"{bank} (forecast)",
            mode="lines+markers", showlegend=False,
            line=dict(color=COLORS[bank], width=2, dash="dash"),
            marker=dict(color=COLORS[bank], size=7, symbol="diamond"),
            hovertemplate=f"<b>{bank}</b> (forecast)<br>NII: €%{{y:,.0f}}m<extra></extra>",
        ))

    fig_nii.add_vline(x=2024.5, line_dash="dot", line_color="#475569")
    fig_nii.update_layout(
        **LAYOUT,
        title=f"NII Scenarios 2025–2026: {scenario}",
        height=420,
    )
    fig_nii.update_xaxes(tickvals=[2022, 2023, 2024, 2025, 2026])
    st.plotly_chart(fig_nii, use_container_width=True)

    # ── Forecast summary table ─────────────────────────────────────────────────
    st.subheader("Forecast Summary (€m)")
    fc_pivot = fc.pivot(index="bank", columns="year", values="nii")
    fc_pivot.columns = [f"NII {y}E" for y in fc_pivot.columns]
    act_24 = k24[["nii"]].rename(columns={"nii": "NII 2024A"})
    summary = act_24.join(fc_pivot)
    for col in summary.columns:
        summary[col] = summary[col].apply(lambda x: f"€{x:,.0f}m" if pd.notna(x) else "—")
    st.dataframe(summary, use_container_width=True, height=215)
    sector_24, sector_26 = k24["nii"].sum(), fc[fc.year == 2026]["nii"].sum()
    st.markdown(f"**Sector NII:** €{sector_24:,.0f}m in 2024 → €{sector_26:,.0f}m in 2026 "
                f"({(sector_26 / sector_24 - 1) * 100:+.1f}%) in this scenario.")
    st.caption(
        "E = scenario estimate. Rate sensitivities come from three yearly points per bank (2022 at near-zero "
        "rates), so they are steep; hedging and lower deposit costs soften the real effect. "
        "Assets +2% a year in every scenario. Not investment advice."
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — STRESS TEST
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("One-Year Stress Test (FY2024 base)")
    st.markdown(
        "Applies (1) NIM compression, (2) a fall in loans and earning assets and (3) extra cost of risk "
        "to FY2024 actuals. Costs flat, 29% tax on the change in profit, no dividends, RWAs unchanged. "
        "CET1 at the end of the stress year = (reported CET1 capital + stressed net profit) / reported RWAs. "
        "Same method as `04_forecasting/02_stress_test.ipynb`."
    )

    c_l, c_r = st.columns([1, 2])

    with c_l:
        st.markdown("**Stress Parameters**")
        cor_bps = st.slider(
            "Additional Cost of Risk (bps)",
            min_value=0, max_value=500, value=200, step=25,
            help="Basis points of additional loan loss provisions on stressed loan book.",
        )
        loan_growth = st.slider(
            "Loan Volume Change (%)",
            min_value=-40, max_value=10, value=-15, step=5,
            help="Change in gross loan book vs 2024 actuals.",
        )
        nim_comp = st.slider(
            "NIM Compression (bps)",
            min_value=0, max_value=200, value=50, step=10,
            help="Reduction in net interest margin applied to total assets.",
        )
        st.divider()
        eba = load_eba()
        st.markdown("**Defaults:** CoR +200bp | Loans −15% | NIM −50bp")
        st.markdown("**Official EBA 2023 stress test** (fully loaded CET1, Dec 2022 → adverse end-2025):")
        st.dataframe(eba[["cet1_fl_start_2022", "cet1_fl_adverse_2025"]].rename(
            columns={"cet1_fl_start_2022": "Start", "cet1_fl_adverse_2025": "Adverse 2025"}),
            use_container_width=True)
        st.caption(f"{CET1_REFERENCE}% line on the chart is a round reference level, not a regulatory minimum.")

    with c_r:
        # Compute stress for all banks
        results = {}
        for bank in BANKS:
            row = k24.loc[bank]
            results[bank] = stress_bank(row, cor_bps, loan_growth, nim_comp)

        # ── Results table ──────────────────────────────────────────────────────
        tbl_rows = []
        for bank in BANKS:
            r = results[bank]
            tbl_rows.append({
                "Bank":               bank,
                "Net Profit 2024A":   f"€{r['baseline_profit']:,.0f}m",
                "Stressed Profit":    f"€{r['stressed_profit']:,.0f}m",
                "Δ Profit":           f"{r['d_profit']:+,.0f}m",
                "CET1 end-2024":      f"{r['baseline_cet1']:.1f}%",
                "Stressed CET1":      f"{r['stressed_cet1']:.1f}%",
                "Δ CET1 (pp)":        f"{r['d_cet1']:+.1f}pp",
                f"Below {CET1_REFERENCE}%?": "Yes" if r["breaches_srep"] else "No",
            })

        tbl_df = pd.DataFrame(tbl_rows).set_index("Bank")

        def style_stress(df):
            styles = pd.DataFrame("", index=df.index, columns=df.columns)
            for bank in df.index:
                r = results[bank]
                flag = f"Below {CET1_REFERENCE}%?"
                if r["breaches_srep"]:
                    styles.loc[bank, flag] = "background-color: #450a0a; color: #fca5a5; font-weight: bold"
                    styles.loc[bank, "Stressed CET1"]  = "color: #fca5a5"
                else:
                    styles.loc[bank, flag] = "background-color: #14532d; color: #86efac"
                if r["d_profit"] < 0:
                    styles.loc[bank, "Δ Profit"] = "color: #f87171"
                if r["d_cet1"] < 0:
                    styles.loc[bank, "Δ CET1 (pp)"] = "color: #f87171"
            return styles

        st.dataframe(tbl_df.style.apply(style_stress, axis=None),
                     use_container_width=True, height=220)

        # ── CET1 waterfall ─────────────────────────────────────────────────────
        fig_cet = go.Figure()
        x_banks = BANKS

        fig_cet.add_trace(go.Bar(
            x=x_banks,
            y=[results[b]["baseline_cet1"] for b in x_banks],
            name="CET1 2024A",
            marker_color=[COLORS[b] for b in x_banks],
            opacity=0.85,
            hovertemplate="%{x}<br>CET1 2024A: %{y:.1f}%<extra></extra>",
        ))
        fig_cet.add_trace(go.Bar(
            x=x_banks,
            y=[results[b]["d_cet1"] for b in x_banks],
            name="Δ CET1 (stress)",
            marker_color=["#ef4444" if results[b]["d_cet1"] < 0 else "#10b981"
                          for b in x_banks],
            base=[results[b]["baseline_cet1"] for b in x_banks],
            hovertemplate="%{x}<br>Δ CET1: %{y:+.1f}pp<extra></extra>",
        ))
        fig_cet.add_hline(y=CET1_REFERENCE, line_dash="dash", line_color="#f59e0b",
                          annotation_text=f"{CET1_REFERENCE}% reference",
                          annotation_font_color="#f59e0b")
        fig_cet.update_layout(
            **LAYOUT,
            barmode="stack",
            title="CET1: end-2024 vs end of stress year",
            height=340,
        )
        fig_cet.update_yaxes(ticksuffix="%", range=[0, 25])
        st.plotly_chart(fig_cet, use_container_width=True)

    st.caption(
        "CET1 capital = reported CET1 ratio × reported RWAs (FY2024 annual reports). "
        "A bank that stays profitable under stress ends the year with more capital because no dividend is paid. "
        "Simplified single-period shock, not a multi-year dynamic model."
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SENSITIVITY ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Sensitivity Analysis")
    st.markdown(
        "Two grids: **(1)** how the justified P/TBV (Gordon growth) changes across cost of equity and growth assumptions, "
        "and **(2)** how stressed CET1 changes across cost-of-risk and loan-growth shocks. "
        "All figures use FY2024 actuals as the base."
    )

    sens_tab_a, sens_tab_b = st.tabs(["Justified P/TBV vs CoE & g", "CET1 vs CoR & Loan Growth"])

    # ── Grid A: Justified P/TBV sensitivity ─────────────────────────────────────
    with sens_tab_a:
        st.markdown("**Justified P/TBV = (RoTE − g) / (CoE − g)**  \n"
                    "Grid shows justified P/TBV for a selected bank across CoE and g ranges. "
                    "Green = above 1.0× (returns above the cost of equity), red = below 1.0×.")

        pb_bank = st.selectbox("Bank", BANKS, key="pb_bank")
        roe_for_pb = k24.loc[pb_bank, "rote"]
        st.caption(f"{pb_bank} FY2024 RoTE (average tangible equity): **{roe_for_pb:.1f}%**")

        coe_vals = [8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0]
        g_vals   = [1.0, 1.5, 2.0, 2.5, 3.0]

        pb_grid = np.array([
            [(roe_for_pb - g) / (coe - g) if (coe - g) > 0 else np.nan
             for coe in coe_vals]
            for g in g_vals
        ])

        fig_pb = go.Figure(go.Heatmap(
            z=pb_grid,
            x=[f"{c:.1f}%" for c in coe_vals],
            y=[f"{g:.1f}%" for g in g_vals],
            colorscale=[[0, "#450a0a"], [0.45, "#7f1d1d"], [0.5, "#1e293b"],
                        [0.55, "#14532d"], [1.0, "#052e16"]],
            zmid=1.0,
            text=[[f"{v:.2f}×" if not np.isnan(v) else "—" for v in row] for row in pb_grid],
            texttemplate="%{text}",
            textfont=dict(size=11, color="#f1f5f9"),
            hovertemplate="CoE: %{x}<br>g: %{y}<br>P/TBV: %{z:.2f}×<extra></extra>",
            showscale=True,
            colorbar=dict(title=dict(text="P/TBV", font=dict(color="#94a3b8")),
                          tickfont=dict(color="#94a3b8")),
        ))
        # Mark the default cell (CoE = 10.0%, g = 2.0%), the same defaults as the Investment Thesis page
        base_coe_idx = coe_vals.index(10.0)
        base_g_idx   = g_vals.index(2.0)
        fig_pb.add_shape(type="rect",
                         x0=base_coe_idx - 0.5, x1=base_coe_idx + 0.5,
                         y0=base_g_idx - 0.5,   y1=base_g_idx + 0.5,
                         line=dict(color="#f59e0b", width=2))
        fig_pb.update_layout(
            **{k: v for k, v in LAYOUT.items() if k not in ("xaxis", "yaxis")},
            title=f"{pb_bank}: Justified P/TBV Sensitivity (amber box: CoE 10.0%, g 2.0%)",
            height=340,
            xaxis=dict(title="Cost of Equity (CoE)", tickfont=dict(color="#94a3b8"),
                       gridcolor="#1e293b"),
            yaxis=dict(title="Long-run Growth (g)", tickfont=dict(color="#94a3b8"),
                       gridcolor="#1e293b"),
        )
        st.plotly_chart(fig_pb, use_container_width=True)
        st.caption(
            "Formula: (RoTE − g) / (CoE − g). RoTE = FY2024 on average tangible equity. "
            "Cost of equity and growth are assumptions (10.0% and 2.0% marked), not market data. "
            "Values above 1.0× mean the bank earns more than the assumed cost of equity."
        )

    # ── Grid B: CET1 sensitivity to CoR × Loan Growth ─────────────────────────
    with sens_tab_b:
        st.markdown("**CET1 at the end of the stress year = (CET1 capital + stressed net profit) / RWAs**  \n"
                    f"Red cells are below the {CET1_REFERENCE}% reference level (not a regulatory minimum).")

        cet1_bank = st.selectbox("Bank", BANKS, key="cet1_bank")
        brow = k24.loc[cet1_bank]

        cor_bps_grid  = [0, 50, 100, 150, 200, 250, 300, 400, 500]
        loan_gr_grid  = [0, -5, -10, -15, -20, -25, -30, -40]

        cet1_grid = np.array([
            [stress_bank(brow, cor_b, lg, 50)["stressed_cet1"]
             for cor_b in cor_bps_grid]
            for lg in loan_gr_grid
        ])

        colorscale_cet1 = [
            [0.0,  "#450a0a"],   # deep red, far below the reference level
            [0.3,  "#7f1d1d"],
            [0.45, "#ef4444"],   # red, below the reference level
            [0.55, "#14532d"],   # green, above the reference level
            [0.7,  "#16a34a"],
            [1.0,  "#052e16"],   # deep green
        ]

        fig_cet1 = go.Figure(go.Heatmap(
            z=cet1_grid,
            x=[f"+{c}bp" for c in cor_bps_grid],
            y=[f"{lg}%" for lg in loan_gr_grid],
            colorscale=colorscale_cet1,
            zmid=CET1_REFERENCE,
            text=[[f"{v:.1f}%" for v in row] for row in cet1_grid],
            texttemplate="%{text}",
            textfont=dict(size=11, color="#f1f5f9"),
            hovertemplate="CoR shock: %{x}<br>Loan Δ: %{y}<br>Stressed CET1: %{z:.1f}%<extra></extra>",
            showscale=True,
            colorbar=dict(title=dict(text="CET1 (%)", font=dict(color="#94a3b8")), ticksuffix="%",
                          tickfont=dict(color="#94a3b8")),
        ))
        # Mark the default shock (+200bp CoR, −15% loans)
        eba_cor_idx  = cor_bps_grid.index(200)
        eba_loan_idx = loan_gr_grid.index(-15)
        fig_cet1.add_shape(type="rect",
                           x0=eba_cor_idx - 0.5, x1=eba_cor_idx + 0.5,
                           y0=eba_loan_idx - 0.5, y1=eba_loan_idx + 0.5,
                           line=dict(color="#f59e0b", width=2))
        fig_cet1.update_layout(
            **{k: v for k, v in LAYOUT.items() if k not in ("xaxis", "yaxis")},
            title=f"{cet1_bank}: Stressed CET1 Sensitivity (amber = default: +200bp CoR, −15% loans)",
            height=380,
            xaxis=dict(title="Additional Cost of Risk", tickfont=dict(color="#94a3b8"),
                       gridcolor="#1e293b"),
            yaxis=dict(title="Loan Volume Change", tickfont=dict(color="#94a3b8"),
                       gridcolor="#1e293b"),
        )
        st.plotly_chart(fig_cet1, use_container_width=True)
        st.caption(
            f"NIM compression fixed at 50bp. Red = below the {CET1_REFERENCE}% reference level. "
            "RWAs and CET1 capital from the FY2024 annual reports; 29% tax; no dividends."
        )
