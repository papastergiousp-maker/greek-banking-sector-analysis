"""
rebuild_db.py
=============
Step 3 of the data pipeline: load the processed CSVs into SQLite.

    python 02_Banking_Sector_Dashboard/pipeline/extract_statements.py   # needs the PDFs
    python 02_Banking_Sector_Dashboard/pipeline/build_dataset.py
    python 02_Banking_Sector_Dashboard/rebuild_db.py

Tables
    kpis               one row per bank and year (12 rows)
    income_statement   long format: bank, year, metric, value, unit, source_ref
    balance_sheet      long format: bank, year, metric, value, unit, source_ref
    sources            every number with its report file and PDF page
    eba_stress_test    official EBA 2023 stress test results (fully loaded CET1)
    ecb_funding        amounts due to the ECB and central banks at each year end
    ecb_rates          ECB deposit facility rate, yearly average and year end
"""

import shutil
import sqlite3
import sys
from pathlib import Path

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).parent
DB_PATH = BASE / "data" / "greek_banking_final.db"
CSV_DIR = BASE / "data" / "processed"
MANUAL_DIR = BASE / "data" / "manual"
DOCS_DB = BASE.parent / "docs" / "data" / "greek_banking_final.db"


def rebuild():
    tables = {
        "kpis": pd.read_csv(CSV_DIR / "kpis_final.csv"),
        "income_statement": pd.read_csv(CSV_DIR / "income_statement_final.csv"),
        "balance_sheet": pd.read_csv(CSV_DIR / "balance_sheet_final.csv"),
        "sources": pd.read_csv(CSV_DIR / "sources.csv"),
        "eba_stress_test": pd.read_csv(MANUAL_DIR / "eba_stress_test_2023.csv"),
        "ecb_funding": pd.read_csv(MANUAL_DIR / "ecb_funding.csv"),
        "ecb_rates": pd.read_csv(MANUAL_DIR / "ecb_deposit_rate.csv"),
    }
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    for name, df in tables.items():
        df.to_sql(name, conn, index=False)
        print(f"  {name:18s} {len(df):4d} rows")
    c = conn.cursor()
    c.execute("CREATE INDEX idx_kpis_bank_year ON kpis(bank, year)")
    c.execute("CREATE INDEX idx_inc_bank_year ON income_statement(bank, year)")
    c.execute("CREATE INDEX idx_bs_bank_year ON balance_sheet(bank, year)")
    conn.commit()

    checks = [
        ("Sector NII 2024 (€m)", "SELECT ROUND(SUM(nii), 0) FROM kpis WHERE year = 2024"),
        ("Alpha Bank net profit 2024 (€m)", "SELECT net_profit FROM kpis WHERE bank = 'Alpha Bank' AND year = 2024"),
        ("Alpha Bank total assets 2024 (€m)", "SELECT total_assets FROM kpis WHERE bank = 'Alpha Bank' AND year = 2024"),
        ("NBG CET1 2024 (%)", "SELECT cet1 FROM kpis WHERE bank = 'NBG' AND year = 2024"),
        ("Numbers without a source", "SELECT COUNT(*) FROM sources WHERE source IS NULL OR source = ''"),
    ]
    for label, sql in checks:
        print(f"  {label:36s} = {conn.execute(sql).fetchone()[0]}")
    conn.close()

    DOCS_DB.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DB_PATH, DOCS_DB)
    root = BASE.parent
    print(f"\nDatabase rebuilt: {DB_PATH.relative_to(root)}\nCopied to:        {DOCS_DB.relative_to(root)}")


if __name__ == "__main__":
    rebuild()
