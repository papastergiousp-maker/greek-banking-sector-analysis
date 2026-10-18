"""
extract_statements.py
=====================
Step 1 of the data pipeline: read the consolidated income statement and
balance sheet of the four listed Greek banking groups straight from their
annual report PDFs and write every line item we use, with its source page.

Which reports and which columns
-------------------------------
Each year is taken from the most recent annual report that contains it, so
that every year-on-year change compares figures prepared on the same basis:

    2024 and 2023  ->  FY2024 annual report (2023 = restated comparative column)
    2022           ->  FY2023 annual report (2022 = restated comparative column)

Entities (the companies listed on the Athens Exchange in 2022-2024):
    Alpha Bank    -> Alpha Services and Holdings S.A. (group)
    Eurobank      -> Eurobank Ergasias Services and Holdings S.A. (group)
    NBG           -> National Bank of Greece S.A. (group)
    Piraeus Bank  -> Piraeus Financial Holdings S.A. (group)
(In 2025 each holding company merged with its bank; the listed company is now
the bank itself. The 2022-2024 figures are those of the listed holdings.)

The PDFs are not stored in the repo (size). Download them from the URLs in
pipeline/sources.py into 02_Banking_Sector_Dashboard/data/raw/ and run:

    python 02_Banking_Sector_Dashboard/pipeline/extract_statements.py

Output: data/processed/extracted_statements.csv
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sources import REPORTS, RAW_DIR, STATEMENT_PAGES  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "data" / "processed" / "extracted_statements.csv"

# A value token: 1,234 | (1,234) | 1,234.5 | - (zero)
NUM = r"\(?-?\d[\d,]*(?:\.\d+)?\)?"
TOKEN_RE = re.compile(rf"(?<!\S)(?:{NUM}|-)(?!\S)")


def parse_number(tok: str) -> float:
    tok = tok.strip()
    if tok == "-":
        return 0.0
    neg = tok.startswith("(") and tok.endswith(")")
    tok = tok.strip("()").replace(",", "")
    val = float(tok)
    return -val if neg else val


def trailing_values(line: str, n: int) -> list[float] | None:
    """Return the last n numeric tokens of a line, or None if fewer exist."""
    toks = TOKEN_RE.findall(line)
    if len(toks) < n:
        return None
    return [parse_number(t) for t in toks[-n:]]


# Line-item rules per bank. Each metric maps to one or more label patterns.
# "sum" adds all matching lines (e.g. Alpha's three investment-securities lines).
# "next_line" means the values sit on the line after the label (wrapped text).
RULES = {
    "Alpha Bank": {
        "IS": {
            "Net interest income": [r"^Net interest income\b"],
            "Net banking fee and commission income": [r"^Net fee and commission income\b"],
            "Operating income": [r"^Total income from banking operations\b"],
            "Operating expenses": [r"^Total expenses\b"],
            "Impairment losses on loans": [r"^Impairment losses and provisions to cover credit risk\b"],
            "Profit before tax": [r"^Profit/\(loss\) before income tax\b"],
            "Net profit attributable to shareholders": [r"^Equity Holders of the Company\b"],
        },
        "BS": {
            "Cash and balances with central banks": [r"^Cash and balances with central banks\b"],
            "Due from credit institutions": [r"^Due from (banks|financial institutions)\b"],
            "Loans and advances to customers": [r"^Loans and advances to customers\b"],
            "Investment securities": {"sum": [r"^- Measured at fair value through other comprehensive income\b",
                                              r"^- Measured at amortized cost\b",
                                              r"^- Measured at fair value through profit or loss\b"]},
            "Goodwill and intangible assets": [r"^Goodwill and other intangible assets\b"],
            "Total assets": [r"^Total Assets\b"],
            "Due to credit institutions": [r"^Due to banks\b"],
            "Deposits from customers": [r"^Due to customers\b"],
            "Total liabilities": [r"^Total Liabilities\b"],
            "Additional Tier 1 instruments": [r"^Other .quity .nstruments\b"],
            "Non-controlling interests": [r"^Non-controlling interests\b"],
            "Total equity": [r"^Total Equity\b"],
        },
    },
    "Eurobank": {
        "IS": {
            "Net interest income": [r"^Net interest income\b"],
            "Net banking fee and commission income": [r"^Net banking fee and commission income\b"],
            "Operating income": [r"^Operating income\b"],
            "Operating expenses": [r"^Operating expenses\b"],
            "Impairment losses on loans": {"next_line": r"^Impairment losses relating to loans and$"},
            "Profit before tax": [r"^Profit before tax\b"],
            "Net profit attributable to shareholders": [r"^Net profit attributable to shareholders\b"],
        },
        "BS": {
            "Cash and balances with central banks": [r"^Cash and balances with central banks\b"],
            "Due from credit institutions": [r"^Due from credit institutions\b"],
            "Loans and advances to customers": [r"^Loans and advances to customers\b"],
            "Investment securities": [r"^Investment securities\b"],
            "Goodwill and intangible assets": [r"^Intangible assets\b"],
            "Total assets": [r"^Total assets\b"],
            "Due to central banks": [r"^Due to central banks\b"],
            "Due to credit institutions only": [r"^Due to credit institutions\b"],
            "Deposits from customers": [r"^Due to customers\b"],
            "Total liabilities": [r"^Total liabilities\b"],
            "Equity attributable to shareholders": {"if_present": [r"^Equity attributable to shareholders of the Company\b"]},
            "Non-controlling interests": {"optional": [r"^Non controlling interests\b"]},
            "Total equity": [r"^Total equity\b"],
        },
    },
    "NBG": {
        "IS": {
            "Net interest income": [r"^Net interest income\b"],
            "Net banking fee and commission income": [r"^Net fee and commission income\b"],
            "Operating income": [r"^Total income\b"],
            "Operating expenses": {"sum": [r"^Personnel expenses\b",
                                           r"^Administrative and other operating expenses\b",
                                           {"next_line": r"^Depreciation and amortisation on investment property,"}]},
            "Impairment losses on loans": [r"^Credit provisions\b"],
            "Profit before tax": [r"^Profit before tax\b"],
            "Net profit attributable to shareholders": [r"^NBG equity shareholders\b"],
        },
        "BS": {
            "Cash and balances with central banks": [r"^Cash and balances with [Cc]entral [Bb]anks\b"],
            "Due from credit institutions": [r"^Due from banks\b"],
            "Loans and advances to customers": [r"^Loans and advances to customers\b"],
            "Investment securities": [r"^Investment securities\b"],
            "Goodwill and intangible assets": [r"^Software\b"],
            "Total assets": [r"^Total assets\b"],
            "Due to credit institutions": [r"^Due to banks\b"],
            "Deposits from customers": [r"^Due to customers\b"],
            "Total liabilities": [r"^Total liabilities\b"],
            "Equity attributable to shareholders": [r"^Equity attributable to NBG shareholders\b"],
            "Non-controlling interests": [r"^Non-controlling interests\b"],
            "Total equity": [r"^Total equity\b"],
        },
    },
    "Piraeus Bank": {
        "IS": {
            "Net interest income": [r"^NET INTEREST INCOME\b"],
            "Net banking fee and commission income": [r"^NET FEE AND COMMISSION INCOME\b"],
            "Operating income": [r"^TOTAL NET INCOME\b"],
            "Operating expenses": [r"^TOTAL OPERATING EXPENSES\b"],
            "Impairment losses on loans": [r"^Impairment \(losses\) ?/ releases on loans and advances to customers at amortised cost\b",
                                           {"next_line": r"^Impairment \(losses\) ?/ releases on loans and advances to$"}],
            "Profit before tax": [r"^PROFIT BEFORE INCOME TAX\b"],
            "Net profit attributable to shareholders": {"sum": [r"^Profit attributable to the equity holders of the parent\b"]},
        },
        "BS": {
            "Cash and balances with central banks": [r"^Cash and balances with Central Banks\b"],
            "Due from credit institutions": [r"^Due from banks\b"],
            "Loans and advances to customers": {"sum": [r"^Loans and advances to customers at amortised cost\b",
                                                        r"^Loans and advances to customers mandatorily measured at FVTPL\b"]},
            "Investment securities": [r"^Investment securities\b"],
            "Goodwill and intangible assets": [r"^Intangible assets\b"],
            "Total assets": [r"^TOTAL ASSETS\b"],
            "Due to credit institutions": [r"^Due to banks\b"],
            "Deposits from customers": [r"^Due to customers\b"],
            "Total liabilities": [r"^TOTAL LIABILITIES\b"],
            "Additional Tier 1 instruments": [r"^.ther equity instruments\b"],
            "Equity attributable to shareholders": [
                r"^Capital and reserves attributable to the equity holders of the parent\b",
                {"next_line": r"^Capital and reserves attributable to the equity holders of the$"}],
            "Non-controlling interests": [r"^Non controlling interest\b"],
            "Total equity": [r"^TOTAL EQUITY\b"],
        },
    },
}

# Number of value columns printed on each statement page and how many belong
# to the group (NBG and Piraeus also print the parent company's columns).
COLUMNS = {"Alpha Bank": (2, 2), "Eurobank": (2, 2), "NBG": (4, 2), "Piraeus Bank": (4, 2)}


def page_lines(pdf_path: Path, page_no: int) -> tuple[list[str], float]:
    import pdfplumber

    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[page_no - 1].extract_text() or ""
    scale = 1000.0 if "thousands of Euro" in text else 1.0
    return [ln.strip() for ln in text.split("\n")], scale


def find_values(lines: list[str], rule, n_cols: int) -> tuple[list[float], list[str]] | None:
    """Apply one rule (regex string, next_line dict, sum dict or list of alternatives)."""
    if isinstance(rule, str):
        pat = re.compile(rule)
        for ln in lines:
            if pat.search(ln):
                vals = trailing_values(ln, n_cols)
                if vals is not None:
                    return vals, [ln]
        return None
    if isinstance(rule, dict) and "next_line" in rule:
        pat = re.compile(rule["next_line"])
        for i, ln in enumerate(lines[:-1]):
            if pat.search(ln):
                for nxt in lines[i + 1:i + 3]:
                    vals = trailing_values(nxt, n_cols)
                    if vals is not None:
                        return vals, [ln, nxt]
        return None
    if isinstance(rule, dict) and "sum" in rule:
        total, used = None, []
        for sub in rule["sum"]:
            subs = [sub] if not isinstance(sub, str) else None
            if isinstance(sub, str):
                pat = re.compile(sub)
                hits = [ln for ln in lines if pat.search(ln) and trailing_values(ln, n_cols)]
                if not hits:
                    return None
                for ln in hits:
                    vals = trailing_values(ln, n_cols)
                    total = vals if total is None else [a + b for a, b in zip(total, vals)]
                    used.append(ln)
            else:
                res = find_values(lines, subs[0], n_cols)
                if res is None:
                    return None
                total = res[0] if total is None else [a + b for a, b in zip(total, res[0])]
                used += res[1]
        return total, used
    if isinstance(rule, dict) and "if_present" in rule:
        res = find_values(lines, rule["if_present"], n_cols)
        return res if res is not None else "absent"
    if isinstance(rule, dict) and "optional" in rule:
        res = find_values(lines, rule["optional"], n_cols)
        return res if res is not None else ([0.0] * n_cols, ["(not shown, taken as 0)"])
    if isinstance(rule, list):
        for alt in rule:
            res = find_values(lines, alt, n_cols)
            if res is not None:
                return res
        return None
    raise ValueError(f"Bad rule: {rule!r}")


def extract() -> pd.DataFrame:
    rows = []
    for (bank, report_year), rep in REPORTS.items():
        if report_year not in STATEMENT_PAGES.get(bank, {}):
            continue
        pdf_path = RAW_DIR / rep["file"]
        if not pdf_path.exists():
            raise FileNotFoundError(f"Missing {pdf_path}. Download it from {rep['url']}")
        pages = STATEMENT_PAGES[bank][report_year]
        n_cols, n_group = COLUMNS[bank]
        # FY2024 report -> 2024 and 2023 columns; FY2023 report -> 2022 column only
        years = {2024: [2024, 2023], 2023: [None, 2022]}[report_year]
        for stmt in ("IS", "BS"):
            lines, scale = page_lines(pdf_path, pages[stmt])
            for metric, rule in RULES[bank][stmt].items():
                res = find_values(lines, rule, n_cols)
                if res == "absent":
                    continue  # line not printed in this report; derived later in build_dataset.py
                if res is None:
                    raise ValueError(f"{bank} FY{report_year} {stmt}: '{metric}' not found on page {pages[stmt]}")
                vals, used = res
                for col, year in enumerate(years):
                    if year is None or col >= n_group:
                        continue
                    rows.append({
                        "bank": bank, "year": year, "statement": stmt, "metric": metric,
                        "value": round(vals[col] / scale, 1),
                        "source_file": rep["file"], "source_page": pages[stmt],
                        "source_label": " / ".join(u[:90] for u in used),
                    })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = extract()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Wrote {len(df)} line items to {OUT}")
    print(df.pivot_table(index=["bank", "metric"], columns="year", values="value").to_string())
