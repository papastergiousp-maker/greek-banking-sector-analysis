"""
data.py — shared data loading, constants and the scenario engines.
Every figure comes from greek_banking_final.db, built from the annual reports
(see 02_Banking_Sector_Dashboard/pipeline and the `sources` table).
"""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "02_Banking_Sector_Dashboard" / "data" / "greek_banking_final.db"
MANUAL = ROOT / "02_Banking_Sector_Dashboard" / "data" / "manual"

# ── Constants ─────────────────────────────────────────────────────────────────
BANKS = ["Eurobank", "Alpha Bank", "Piraeus Bank", "NBG"]
YEARS = [2022, 2023, 2024]

ENTITIES = {
    "Alpha Bank": "Alpha Services and Holdings",
    "Eurobank": "Eurobank Ergasias Services and Holdings",
    "NBG": "National Bank of Greece",
    "Piraeus Bank": "Piraeus Financial Holdings",
}

COLORS = {
    "Eurobank":     "#0067B1",
    "Alpha Bank":   "#E2231A",
    "Piraeus Bank": "#F7A600",
    "NBG":          "#003087",
}

# ECB deposit facility rate, daily average per year (%), from the ECB key interest rates page
_ecb = pd.read_csv(MANUAL / "ecb_deposit_rate.csv")
ECB_HIST = dict(zip(_ecb["year"], _ecb["dfr_avg"]))
ECB_YEAR_END = dict(zip(_ecb["year"], _ecb["dfr_year_end"]))

# ECB deposit rate scenarios: yearly average rate (%), the same measure the NIM sensitivity
# is estimated on. The actual rate reached 2.00% in June 2025.
ECB_SCENARIOS = {
    "Dovish (faster cuts)":  {2025: 1.75, 2026: 1.50},
    "Base (gradual cuts)":   {2025: 2.25, 2026: 2.00},
    "Hawkish (cuts pause)":  {2025: 3.00, 2026: 2.75},
}

# Round reference level for charts. Not a regulatory minimum: each bank's CET1
# requirement is set by the ECB and differs by bank. At end-2024: NBG 9.64% (FY2024
# report p.445); Eurobank 10.41%, or 12.45% while it had no AT1 capital (p.304).
CET1_REFERENCE = 10.5
SREP_FLOOR = CET1_REFERENCE  # kept for backwards compatibility

TAX_RATE = 0.29  # Greek corporate income tax rate for credit institutions


# ── Loaders ───────────────────────────────────────────────────────────────────
def _connect():
    return sqlite3.connect(DB)


def load_kpis() -> pd.DataFrame:
    con = _connect()
    df = pd.read_sql("SELECT * FROM kpis ORDER BY bank, year", con)
    con.close()
    # Backwards-compatible aliases used by some pages
    df["roe_avg_eq"] = df["roe"]                     # ROE is already on average equity
    df["dtc_pct_equity"] = (df["dtc"] / df["equity"] * 100).round(1)
    df["cet1_capital"] = df["cet1"] / 100 * df["rwa"]
    # CET1 ratio if all DTCs were deducted. DTCs carry a 100% risk weight (CRR art. 39),
    # so a deduction also removes them from RWAs. Illustrative only.
    df["cet1_ex_dtc"] = ((df["cet1_capital"] - df["dtc"]) / (df["rwa"] - df["dtc"]) * 100).round(1)
    return df


def _pivot(table: str) -> pd.DataFrame:
    con = _connect()
    raw = pd.read_sql(f"SELECT * FROM {table}", con)
    con.close()
    pivot = raw.pivot_table(index=["bank", "year"], columns="metric", values="value").reset_index()
    pivot.columns.name = None
    return pivot


def load_income() -> pd.DataFrame:
    return _pivot("income_statement")


def load_balance() -> pd.DataFrame:
    return _pivot("balance_sheet")


def load_sources() -> pd.DataFrame:
    con = _connect()
    df = pd.read_sql("SELECT * FROM sources", con)
    con.close()
    return df


def load_eba() -> pd.DataFrame:
    con = _connect()
    df = pd.read_sql("SELECT * FROM eba_stress_test", con)
    con.close()
    return df.set_index("bank")


def load_ecb_funding() -> pd.DataFrame:
    """Amounts due to the ECB and central banks at each year end (€m), with report and page."""
    con = _connect()
    df = pd.read_sql("SELECT * FROM ecb_funding ORDER BY bank, year", con)
    con.close()
    return df


# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_eur(val, decimals=0):
    """Format a value in €m with suffix."""
    if pd.isna(val):
        return "—"
    if abs(val) >= 1_000:
        return f"€{val/1_000:.1f}bn"
    return f"€{val:,.{decimals}f}m"


def pct(val, decimals=1):
    if val is None or pd.isna(val):
        return "—"
    return f"{val:.{decimals}f}%"


# ── Plotly dark layout ────────────────────────────────────────────────────────
LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", size=12),
    title_font=dict(color="#f1f5f9", size=14),
    xaxis=dict(gridcolor="#1e293b", zerolinecolor="#334155",
               tickfont=dict(color="#94a3b8")),
    yaxis=dict(gridcolor="#1e293b", zerolinecolor="#334155",
               tickfont=dict(color="#94a3b8")),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8")),
    margin=dict(l=50, r=20, t=40, b=50),
    hovermode="x unified",
)


# ── Stress-test engine ────────────────────────────────────────────────────────
def stress_bank(row: pd.Series, delta_cor_bps: int, loan_growth_pct: float, nim_comp_bps: int) -> dict:
    """
    One-year shock on FY2024 actuals (same method as 04_forecasting/02_stress_test.ipynb).

    NII falls with the NIM shock and with earning assets (assets shrink by the loan change);
    loan impairments = (FY2024 cost of risk + shock) x loans after the shock; costs flat;
    29% tax on the change in profit; no dividends; RWAs unchanged.
    CET1 at the end of the stress year = (CET1 capital + stressed net profit) / RWAs.
    """
    loans_adv = row["loans"] * (1 + loan_growth_pct / 100)
    assets_adv = row["avg_total_assets"] + row["loans"] * loan_growth_pct / 100
    nim_adv = row["nii"] / row["avg_total_assets"] - nim_comp_bps / 10_000
    cor_adv = -row["impairment"] / row["avg_loans"] + delta_cor_bps / 10_000

    nii_adv = nim_adv * assets_adv
    imp_adv = cor_adv * loans_adv
    pbt_adv = row["pbt"] + (nii_adv - row["nii"]) - (imp_adv + row["impairment"])
    np_adv = row["net_profit"] + (pbt_adv - row["pbt"]) * (1 - TAX_RATE)

    cet1_capital = row["cet1"] / 100 * row["rwa"]
    cet1_adv = (cet1_capital + np_adv) / row["rwa"] * 100
    return {
        "baseline_profit": row["net_profit"],
        "stressed_profit": round(np_adv, 0),
        "d_profit": round(np_adv - row["net_profit"], 0),
        "baseline_cet1": row["cet1"],
        "stressed_cet1": round(cet1_adv, 1),
        "d_cet1": round(cet1_adv - row["cet1"], 1),
        "breaches_srep": cet1_adv < CET1_REFERENCE,
    }


# ── NII scenario engine ───────────────────────────────────────────────────────
def nim_rate_sensitivity(kpis_df: pd.DataFrame) -> dict:
    """
    Historical NIM sensitivity to the ECB deposit rate, per bank: slope of NIM on the
    yearly average rate over 2022-2024 (pp of NIM per 1pp of rate). Three points per
    bank, so this is a rough guide, not a disclosed sensitivity.
    """
    rates = np.array([ECB_HIST[y] for y in YEARS])
    out = {}
    for bank in BANKS:
        nim = kpis_df[kpis_df.bank == bank].sort_values("year")["nim"].values
        out[bank] = float(np.polyfit(rates, nim, 1)[0])
    return out


ASSET_GROWTH = 0.02  # yearly growth of total assets, the same in every scenario


def forecast_nii(kpis_df: pd.DataFrame, scenario_name: str) -> pd.DataFrame:
    """
    Project NII for 2025-2026: NII = NIM x average total assets.
    Same method as 04_forecasting/01_forecast_nii_2025_2026.ipynb.

      • NIM = 2024 NIM + the bank's historical NIM sensitivity x (scenario average
        rate - 2024 average rate).
      • Total assets grow 2% a year from the end-2024 balance sheet, so the 2025
        average is TA_2024 x (1 + g/2) and the 2026 average TA_2024 x (1 + g) x (1 + g/2).
        Starting from end-2024 captures Eurobank's mid-2024 consolidation of Hellenic Bank.
      • rate_effect = change in NIM x last year's average assets; vol_effect = the rest.
    """
    k24 = kpis_df[kpis_df.year == 2024].set_index("bank")
    sens = nim_rate_sensitivity(kpis_df)
    rates = ECB_SCENARIOS[scenario_name]

    result = []
    for bank in BANKS:
        nim_prev = k24.loc[bank, "nim"]
        assets_prev = k24.loc[bank, "avg_total_assets"]
        nii_prev = k24.loc[bank, "nii"]
        for i, year in enumerate([2025, 2026]):
            nim = k24.loc[bank, "nim"] + sens[bank] * (rates[year] - ECB_HIST[2024])
            assets = k24.loc[bank, "total_assets"] * (1 + ASSET_GROWTH) ** i * (1 + ASSET_GROWTH / 2)
            nii = nim / 100 * assets
            rate_effect = (nim - nim_prev) / 100 * assets_prev
            result.append({   # unrounded, so totals match the notebook; round when displaying
                "bank": bank, "year": year, "nim": nim, "avg_assets": assets, "nii": nii,
                "rate_effect": rate_effect, "vol_effect": nii - nii_prev - rate_effect,
            })
            nim_prev, assets_prev, nii_prev = nim, assets, nii
    return pd.DataFrame(result)
