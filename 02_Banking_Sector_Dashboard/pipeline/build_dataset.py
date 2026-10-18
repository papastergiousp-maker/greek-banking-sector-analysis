"""
build_dataset.py
================
Step 2 of the data pipeline (no PDFs needed): turn the extracted statement
lines and the hand-collected regulatory figures into the three tables the
rest of the project reads.

Inputs
    data/processed/extracted_statements.csv   (from extract_statements.py)
    data/manual/regulatory_ratios.csv          (CET1, total capital, NPE, DTC, RWA)
    data/manual/opening_balances_2021.csv      (31.12.2021, for 2022 averages)

Outputs (data/processed/)
    income_statement_final.csv
    balance_sheet_final.csv
    kpis_final.csv
    sources.csv          one row per number, with report file and PDF page

KPI definitions (all ratios in %)
    ROE              net profit attributable / average equity attributable
    RoTE             net profit attributable / average tangible equity
                     (equity attributable - AT1 - goodwill and intangibles)
    ROA              net profit attributable / average total assets
    NIM              net interest income / average total assets
    Cost-to-income   operating expenses / operating income
    Cost of risk     loan impairments / average net loans
    Loan-to-deposit  net loans / customer deposits
Averages are (opening + closing) / 2 of the year-end balances.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
PROC = BASE / "data" / "processed"
MANUAL = BASE / "data" / "manual"

UNIT = "€ million"

IS_METRICS = [
    "Net interest income",
    "Net banking fee and commission income",
    "Operating income",
    "Operating expenses",
    "Profit from operations before impairments",
    "Impairment losses on loans",
    "Profit before tax",
    "Net profit attributable to shareholders",
]

BS_METRICS = [
    "Cash and balances with central banks",
    "Due from credit institutions",
    "Investment securities",
    "Loans and advances to customers",
    "Goodwill and intangible assets",
    "Total assets",
    "Due to central banks",
    "Due to credit institutions",
    "Deposits from customers",
    "Total liabilities",
    "Equity attributable to shareholders",
    "Additional Tier 1 instruments",
    "Non-controlling interests",
    "Total equity",
]


def load_extracted() -> pd.DataFrame:
    ext = pd.read_csv(PROC / "extracted_statements.csv")
    ext["source_ref"] = ext["source_file"] + " p." + ext["source_page"].astype(str)
    return ext


def derive(ext: pd.DataFrame) -> pd.DataFrame:
    """Add the derived lines (all simple sums/differences of extracted lines)."""
    rows = []
    wide = ext.pivot_table(index=["bank", "year"], columns="metric", values="value", aggfunc="first")
    ref = ext.groupby(["bank", "year", "statement"])["source_ref"].first()
    for (bank, year), r in wide.iterrows():
        is_ref = ref.get((bank, year, "IS"))
        bs_ref = ref.get((bank, year, "BS"))
        add = lambda m, v, st, rf, how: rows.append(  # noqa: E731
            {"bank": bank, "year": year, "statement": st, "metric": m, "value": round(v, 1),
             "source_ref": rf, "how": how})
        add("Profit from operations before impairments",
            r["Operating income"] + r["Operating expenses"], "IS", is_ref,
            "Operating income + operating expenses")
        if pd.isna(r.get("Equity attributable to shareholders", np.nan)):
            add("Equity attributable to shareholders",
                r["Total equity"] - r["Non-controlling interests"], "BS", bs_ref,
                "Total equity - non-controlling interests (no separate line printed)")
        if bank == "Eurobank":
            # Eurobank shows central bank funding on its own line; other banks include it in due to banks.
            add("Due to credit institutions",
                r["Due to central banks"] + r["Due to credit institutions only"], "BS", bs_ref,
                "Due to central banks + due to credit institutions")
    der = pd.DataFrame(rows)
    keep = ext[ext["metric"] != "Due to credit institutions only"].copy()
    keep["how"] = "As printed in the statement"
    out = pd.concat([keep[der.columns], der], ignore_index=True)
    # Banks without an AT1 line have none in issue in 2022-2024.
    missing_at1 = []
    for (bank, year), _ in wide.iterrows():
        if "Additional Tier 1 instruments" not in wide.columns or pd.isna(wide.loc[(bank, year)].get("Additional Tier 1 instruments")):
            missing_at1.append({"bank": bank, "year": year, "statement": "BS",
                                "metric": "Additional Tier 1 instruments", "value": 0.0,
                                "source_ref": ref.get((bank, year, "BS")), "how": "No AT1 line in the balance sheet"})
    return pd.concat([out, pd.DataFrame(missing_at1)], ignore_index=True)


def avg(cur: pd.Series, prev: pd.Series) -> pd.Series:
    return (cur + prev) / 2


def build():
    ext = load_extracted()
    lines = derive(ext)
    ratios = pd.read_csv(MANUAL / "regulatory_ratios.csv")
    opening = pd.read_csv(MANUAL / "opening_balances_2021.csv")

    # ── Long tables for the DB / dashboard ──────────────────────────────────
    inc = lines[lines["metric"].isin(IS_METRICS)].copy()
    bal = lines[lines["metric"].isin(BS_METRICS)].copy()
    for df in (inc, bal):
        df["unit"] = UNIT
    inc = inc.sort_values(["bank", "year", "metric"])[["bank", "year", "metric", "value", "unit", "source_ref"]]
    bal = bal.sort_values(["bank", "year", "metric"])[["bank", "year", "metric", "value", "unit", "source_ref"]]

    # ── KPI table ───────────────────────────────────────────────────────────
    w = lines.pivot_table(index=["bank", "year"], columns="metric", values="value", aggfunc="first")
    op = opening.pivot_table(index=["bank", "year"], columns="metric", values="value", aggfunc="first")
    full = pd.concat([w, op]).sort_index()
    full = full.reset_index()

    k = pd.DataFrame({
        "bank": full["bank"], "year": full["year"],
        "nii": full["Net interest income"],
        "fees": full["Net banking fee and commission income"],
        "operating_income": full["Operating income"],
        "operating_expenses": full["Operating expenses"],
        "net_profit": full["Net profit attributable to shareholders"],
        "pbt": full["Profit before tax"],
        "impairment": full["Impairment losses on loans"],
        "loans": full["Loans and advances to customers"],
        "deposits": full["Deposits from customers"],
        "equity": full["Equity attributable to shareholders"],
        "at1": full["Additional Tier 1 instruments"],
        "intangibles": full["Goodwill and intangible assets"],
        "total_assets": full["Total assets"],
    }).sort_values(["bank", "year"]).reset_index(drop=True)
    k["tangible_equity"] = k["equity"] - k["at1"] - k["intangibles"]

    g = k.groupby("bank")
    for col in ["equity", "tangible_equity", "total_assets", "loans"]:
        k[f"avg_{col}"] = avg(k[col], g[col].shift(1))
    k["roe"] = (k["net_profit"] / k["avg_equity"] * 100).round(1)
    k["rote"] = (k["net_profit"] / k["avg_tangible_equity"] * 100).round(1)
    k["roa"] = (k["net_profit"] / k["avg_total_assets"] * 100).round(2)
    k["nim"] = (k["nii"] / k["avg_total_assets"] * 100).round(2)
    k["cost_of_risk"] = (-k["impairment"] / k["avg_loans"] * 100).round(2)
    k["cost_to_income"] = (-k["operating_expenses"] / k["operating_income"] * 100).round(1)
    k["loan_to_deposit"] = (k["loans"] / k["deposits"] * 100).round(1)
    k["fee_share"] = (k["fees"] / k["operating_income"] * 100).round(1)
    k["equity_to_assets"] = (k["equity"] / k["total_assets"] * 100).round(1)
    for src, dst in [("nii", "nii_yoy"), ("net_profit", "profit_yoy"),
                     ("total_assets", "assets_yoy"), ("operating_income", "opincome_yoy")]:
        prev = g[src].shift(1)
        k[dst] = ((k[src] - prev) / prev * 100).round(1)

    k = k[k["year"] >= 2022].copy()
    # 2022 YoY would compare with 2021 income statements, which are not in the dataset.
    k.loc[k["year"] == 2022, ["nii_yoy", "profit_yoy", "opincome_yoy"]] = np.nan
    k.loc[k["year"] == 2022, "assets_yoy"] = np.nan

    rw = ratios.pivot_table(index=["bank", "year"], columns="metric", values="value", aggfunc="first").reset_index()
    rw = rw.rename(columns={"cet1_ratio": "cet1", "total_capital_ratio": "total_capital_ratio"})
    k = k.merge(rw, on=["bank", "year"], how="left")
    k["dtc_to_cet1"] = (k["dtc"] / (k["cet1"] / 100 * k["rwa"]) * 100).round(1)

    cols = ["bank", "year", "nii", "fees", "operating_income", "operating_expenses", "net_profit", "pbt",
            "impairment", "loans", "deposits", "equity", "at1", "intangibles", "tangible_equity",
            "total_assets", "roe", "rote", "roa", "nim", "cost_of_risk", "cost_to_income",
            "loan_to_deposit", "fee_share", "equity_to_assets", "nii_yoy", "profit_yoy", "assets_yoy",
            "opincome_yoy", "cet1", "total_capital_ratio", "npe_ratio", "dtc", "rwa", "dtc_to_cet1",
            "avg_equity", "avg_tangible_equity", "avg_total_assets", "avg_loans"]
    k = k[cols].sort_values(["bank", "year"]).reset_index(drop=True)

    # ── Source map: one row per number ───────────────────────────────────────
    src_lines = lines.rename(columns={"source_ref": "source"})[["bank", "year", "metric", "value", "source", "how"]]
    src_ratios = ratios.assign(source=ratios["source_file"] + " p." + ratios["source_page"].astype(str),
                               how=ratios["note"].fillna("As reported"))[["bank", "year", "metric", "value", "source", "how"]]
    src_open = opening.assign(source=opening["source_file"] + " p." + opening["source_page"].astype(str),
                              how=opening["note"].fillna("Comparative column"))[["bank", "year", "metric", "value", "source", "how"]]
    sources = pd.concat([src_lines, src_ratios, src_open], ignore_index=True).sort_values(["bank", "year", "metric"])

    PROC.mkdir(parents=True, exist_ok=True)
    inc.to_csv(PROC / "income_statement_final.csv", index=False)
    bal.to_csv(PROC / "balance_sheet_final.csv", index=False)
    k.to_csv(PROC / "kpis_final.csv", index=False)
    sources.to_csv(PROC / "sources.csv", index=False)
    print(f"income_statement_final.csv  {len(inc)} rows")
    print(f"balance_sheet_final.csv     {len(bal)} rows")
    print(f"kpis_final.csv              {len(k)} rows x {len(k.columns)} columns")
    print(f"sources.csv                 {len(sources)} rows")
    return k


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    kp = build()
    print(kp[["bank", "year", "nii", "net_profit", "total_assets", "roe", "rote", "nim", "cost_to_income",
              "cost_of_risk", "loan_to_deposit", "cet1", "npe_ratio", "dtc_to_cet1"]].to_string(index=False))
