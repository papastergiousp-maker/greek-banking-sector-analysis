"""
Data-quality tests for the Greek banking dataset.

They re-derive every KPI from the statement lines, check the balance sheet
identity, check that every number has a source page, and spot-check figures
against the annual reports.

Run with:  pytest tests/ -v
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).parent.parent
DATA = ROOT / "02_Banking_Sector_Dashboard" / "data"
PROC = DATA / "processed"
MANUAL = DATA / "manual"

BANKS = {"Eurobank", "Alpha Bank", "NBG", "Piraeus Bank"}
YEARS = {2022, 2023, 2024}


@pytest.fixture(scope="module")
def kpis():
    return pd.read_csv(PROC / "kpis_final.csv")


@pytest.fixture(scope="module")
def inc():
    return pd.read_csv(PROC / "income_statement_final.csv")


@pytest.fixture(scope="module")
def bal():
    return pd.read_csv(PROC / "balance_sheet_final.csv")


@pytest.fixture(scope="module")
def wide(inc, bal):
    both = pd.concat([inc, bal])
    return both.pivot_table(index=["bank", "year"], columns="metric", values="value", aggfunc="first")


@pytest.fixture(scope="module")
def opening():
    op = pd.read_csv(MANUAL / "opening_balances_2021.csv")
    return op.pivot_table(index=["bank", "year"], columns="metric", values="value", aggfunc="first")


def prior(wide, opening, bank, year, metric):
    if year == 2022:
        return opening.loc[(bank, 2021), metric]
    return wide.loc[(bank, year - 1), metric]


# ── Structure ─────────────────────────────────────────────────────────────────
class TestStructure:
    def test_twelve_rows(self, kpis):
        assert len(kpis) == 12

    def test_banks_and_years(self, kpis):
        assert set(kpis["bank"]) == BANKS
        assert set(kpis["year"]) == YEARS

    def test_unique_bank_year(self, kpis):
        assert not kpis.duplicated(["bank", "year"]).any()

    def test_no_missing_core_values(self, kpis):
        core = ["nii", "operating_income", "operating_expenses", "net_profit", "impairment", "loans",
                "deposits", "equity", "total_assets", "roe", "rote", "roa", "nim", "cost_to_income",
                "cost_of_risk", "loan_to_deposit", "cet1", "total_capital_ratio", "npe_ratio", "dtc", "rwa"]
        for col in core:
            assert kpis[col].notna().all(), f"missing values in {col}"

    def test_yoy_only_from_2023(self, kpis):
        for col in ["nii_yoy", "profit_yoy", "assets_yoy", "opincome_yoy"]:
            assert kpis.loc[kpis.year == 2022, col].isna().all()
            assert kpis.loc[kpis.year > 2022, col].notna().all()

    def test_sign_conventions(self, kpis):
        assert (kpis["operating_expenses"] < 0).all()
        assert (kpis["impairment"] <= 0).all()


# ── Every number has a source ────────────────────────────────────────────────
class TestSources:
    def test_statement_lines_have_a_page(self, inc, bal):
        for df in (inc, bal):
            assert df["source_ref"].notna().all()
            assert df["source_ref"].str.match(r"^\w+_20\d\d\.pdf p\.\d+$").all()

    def test_ratios_have_a_page(self):
        r = pd.read_csv(MANUAL / "regulatory_ratios.csv")
        assert r["source_file"].notna().all() and (r["source_page"] > 0).all()
        assert len(r) == 4 * 3 * 5  # 4 banks x 3 years x 5 measures

    def test_sources_table_complete(self):
        s = pd.read_csv(PROC / "sources.csv")
        assert s["source"].notna().all()
        assert (s["source"].str.len() > 0).all()

    def test_ecb_funding_has_a_page_and_matches_the_system_total(self):
        e = pd.read_csv(MANUAL / "ecb_funding.csv")
        assert len(e) == 12 and (e["source_page"] > 0).all()
        total = e.groupby("year")["value"].sum()
        # Piraeus FY2023 / FY2024 reports (p.12): ECB funding to the whole Greek banking
        # system was €35.4bn at end-2022 and €14.3bn at end-2023; the four banks are most of it.
        assert 34_000 < total[2022] <= 35_400
        assert 14_000 < total[2023] <= 14_350
        # The balance sheet line for Eurobank must equal the note figure
        bal = pd.read_csv(PROC / "balance_sheet_final.csv")
        eb = bal[(bal.bank == "Eurobank") & (bal.metric == "Due to central banks")].set_index("year")["value"]
        assert (eb == e[e.bank == "Eurobank"].set_index("year")["value"]).all()


# ── Balance sheet identity ───────────────────────────────────────────────────
class TestBalanceSheet:
    def test_assets_equal_liabilities_plus_equity(self, wide):
        diff = (wide["Total assets"] - wide["Total liabilities"] - wide["Total equity"]).abs()
        assert (diff <= 0.2).all(), diff[diff > 0.2]

    def test_equity_split(self, wide):
        # Reports round each line to €1m, so the split can differ by €1m
        diff = (wide["Total equity"] - wide["Equity attributable to shareholders"]
                - wide["Non-controlling interests"]).abs()
        assert (diff <= 1.0).all()

    def test_ppop(self, wide):
        diff = (wide["Profit from operations before impairments"]
                - wide["Operating income"] - wide["Operating expenses"]).abs()
        assert (diff <= 0.2).all()

    def test_leverage_range(self, kpis):
        lev = kpis["total_assets"] / kpis["equity"]
        assert lev.between(5, 20).all()


# ── KPI re-derivation from the statement lines ───────────────────────────────
class TestKPIs:
    @pytest.mark.parametrize("bank", sorted(BANKS))
    @pytest.mark.parametrize("year", sorted(YEARS))
    def test_return_and_margin_ratios(self, kpis, wide, opening, bank, year):
        k = kpis.set_index(["bank", "year"]).loc[(bank, year)]
        w = wide.loc[(bank, year)]
        np_ = w["Net profit attributable to shareholders"]
        avg_eq = (w["Equity attributable to shareholders"]
                  + prior(wide, opening, bank, year, "Equity attributable to shareholders")) / 2
        avg_ta = (w["Total assets"] + prior(wide, opening, bank, year, "Total assets")) / 2
        avg_ln = (w["Loans and advances to customers"]
                  + prior(wide, opening, bank, year, "Loans and advances to customers")) / 2
        assert k["roe"] == pytest.approx(np_ / avg_eq * 100, abs=0.06)
        assert k["roa"] == pytest.approx(np_ / avg_ta * 100, abs=0.006)
        assert k["nim"] == pytest.approx(w["Net interest income"] / avg_ta * 100, abs=0.006)
        assert k["cost_of_risk"] == pytest.approx(-w["Impairment losses on loans"] / avg_ln * 100, abs=0.006)
        assert k["cost_to_income"] == pytest.approx(-w["Operating expenses"] / w["Operating income"] * 100, abs=0.06)
        assert k["loan_to_deposit"] == pytest.approx(
            w["Loans and advances to customers"] / w["Deposits from customers"] * 100, abs=0.06)

    def test_yoy_growth(self, kpis):
        k = kpis.sort_values(["bank", "year"]).copy()
        prev = k.groupby("bank")["nii"].shift(1)
        calc = ((k["nii"] - prev) / prev * 100).round(1)
        mask = k["year"] > 2022
        assert np.allclose(calc[mask], k.loc[mask, "nii_yoy"], atol=0.06)

    def test_dtc_share_matches_banks_own_disclosure(self, kpis):
        k = kpis.set_index(["bank", "year"])
        # Alpha: DTC = 49.2% of Group CET1 (FY2024 report); Eurobank: 36% (FY2024 report)
        assert k.loc[("Alpha Bank", 2024), "dtc_to_cet1"] == pytest.approx(49.2, abs=1.0)
        assert k.loc[("Eurobank", 2024), "dtc_to_cet1"] == pytest.approx(36.0, abs=1.0)


# ── Spot checks against the annual reports ───────────────────────────────────
class TestReportedFigures:
    @pytest.mark.parametrize("bank,year,col,value", [
        ("Alpha Bank", 2024, "net_profit", 654.0),        # Alpha Services and Holdings FY2024 p.246
        ("Alpha Bank", 2024, "total_assets", 72075.0),    # p.248
        ("Alpha Bank", 2023, "nii", 1659.0),              # FY2024 report, restated 2023
        ("Alpha Bank", 2022, "nii", 1173.8),              # FY2023 report, restated 2022
        ("Eurobank", 2024, "net_profit", 1448.0),         # Eurobank Holdings FY2024 p.256
        ("Eurobank", 2024, "deposits", 78593.0),
        ("NBG", 2024, "net_profit", 1158.0),              # NBG FY2024 p.367
        ("NBG", 2024, "cet1", 18.3),                      # NBG FY2024 p.40
        ("Piraeus Bank", 2024, "total_assets", 80044.0),  # PFH FY2024 p.425
        ("Piraeus Bank", 2024, "cet1", 14.47),            # PFH FY2024 p.566
        ("Piraeus Bank", 2024, "dtc", 3119.0),            # PFH FY2024 p.567, DTC in regulatory capital
    ])
    def test_value(self, kpis, bank, year, col, value):
        got = kpis.set_index(["bank", "year"]).loc[(bank, year), col]
        assert got == pytest.approx(value, abs=0.05)

    def test_ratio_ranges(self, kpis):
        assert kpis["cet1"].between(10, 25).all()
        assert kpis["npe_ratio"].between(0, 10).all()
        assert kpis["cost_to_income"].between(20, 60).all()
        assert kpis["nim"].between(0.5, 5).all()
        assert kpis["loan_to_deposit"].between(50, 100).all()
