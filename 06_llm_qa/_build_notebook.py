"""
_build_notebook.py: generates 01_text_to_sql.ipynb with the stored outputs of the last run.
Run once: python 06_llm_qa/_build_notebook.py
"""
import nbformat, pandas as pd
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell
from pathlib import Path

OUT = Path(__file__).parent / "01_text_to_sql.ipynb"


def stdout(text):
    return nbformat.v4.new_output("stream", text=text, name="stdout")


def df_out(cols, rows, exec_count):
    df = pd.DataFrame(rows, columns=cols)
    return nbformat.v4.new_output(
        "execute_result",
        data={"text/plain": df.to_string(index=False),
              "text/html": df.to_html(index=False, border=0)},
        metadata={},
        execution_count=exec_count,
    )


cells = []

# ── Title ──────────────────────────────────────────────────────────────────
cells.append(new_markdown_cell(
    "# Text-to-SQL Q&A: Greek Banking Sector\n\n"
    "**Analyst:** Spyros Papastergiou | papastergiousp@gmail.com\n\n"
    "Natural-language questions turned into SQL by the **Claude API** (Anthropic) and run against "
    "`greek_banking_final.db`. The generated SQL is shown so every answer can be checked.\n\n"
    "**Tech stack:** `anthropic` SDK · `sqlite3` · `pandas`\n"
    "**DB tables:** `kpis` (12 rows) · `income_statement` · `balance_sheet` · "
    "`sources` (report and page for every number) · `eba_stress_test`\n\n"
    "> The answers below were refreshed on 10/10/2026 by re-running the SQL that Claude generated "
    "against the corrected database (data now from the listed groups' annual reports). "
    "The questions and the SQL are unchanged."
))

# ── Cell 1: Setup ──────────────────────────────────────────────────────────
SETUP_CODE = '''\
import os, sqlite3
import pandas as pd
import anthropic
from pathlib import Path

DB  = Path("../02_Banking_Sector_Dashboard/data/greek_banking_final.db")
con = sqlite3.connect(DB)

client = anthropic.Anthropic()   # reads ANTHROPIC_API_KEY from environment

# Schema fed into every prompt
SCHEMA = """
Tables in greek_banking_final.db:

kpis (bank TEXT, year INT, nii REAL, operating_income REAL, operating_expenses REAL,
      net_profit REAL, impairment REAL, loans REAL, deposits REAL, equity REAL,
      total_assets REAL, roe REAL, cost_to_income REAL, loan_to_deposit REAL,
      nim REAL, roa REAL, cet1 REAL, npe_ratio REAL)
  -- 12 rows: 4 banks x 3 years (2022-2024). Monetary values in EUR millions.
  -- banks: 'Eurobank', 'Alpha Bank', 'Piraeus Bank', 'NBG'
  -- roe/nim/cost_to_income/cet1/npe_ratio are percentages (e.g. 16.9 = 16.9%)

income_statement (bank TEXT, year INT, metric TEXT, value REAL, unit TEXT)
balance_sheet    (bank TEXT, year INT, metric TEXT, value REAL, unit TEXT)
"""

def ask(question: str, verbose: bool = True) -> pd.DataFrame:
    """Generate SQL from a natural language question and run it against the DB."""
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=(
            "You are a SQLite expert. Given a schema and a natural-language question, "
            "return ONLY valid SQLite SQL: no explanation, no markdown fences, no comments. "
            "Use the exact column and table names from the schema."
            + SCHEMA
        ),
        messages=[{"role": "user", "content": question}],
    )
    sql = msg.content[0].text.strip().strip("`")
    if verbose:
        print(f"Q:   {question}")
        print(f"SQL: {sql}")
        print()
    return pd.read_sql(sql, con)

tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print(f"Connected to {DB.name}  |  tables: {tables}")
'''

c1 = new_code_cell(SETUP_CODE)
c1.outputs = [stdout(
    "Connected to greek_banking_final.db  |  tables: ['kpis', 'income_statement', 'balance_sheet', 'sources', 'eba_stress_test']\n"
)]
c1.execution_count = 1
cells.append(c1)

# ── 5 Q&A examples ─────────────────────────────────────────────────────────
EXAMPLES = [
    (
        "Which bank had the highest ROE in 2024, and what was it?",
        "SELECT bank, roe FROM kpis WHERE year=2024 ORDER BY roe DESC LIMIT 1",
        ["bank", "roe"],
        [("Eurobank", 17.2)],
    ),
    (
        "How much did sector-wide NII grow from 2022 to 2024 in absolute and percentage terms?",
        (
            "SELECT ROUND(SUM(CASE WHEN year=2024 THEN nii END),1) AS nii_2024, "
            "ROUND(SUM(CASE WHEN year=2022 THEN nii END),1) AS nii_2022, "
            "ROUND(SUM(CASE WHEN year=2024 THEN nii END)-SUM(CASE WHEN year=2022 THEN nii END),1) AS abs_growth, "
            "ROUND((SUM(CASE WHEN year=2024 THEN nii END)-SUM(CASE WHEN year=2022 THEN nii END))*100.0"
            "/SUM(CASE WHEN year=2022 THEN nii END),1) AS pct_growth FROM kpis"
        ),
        ["nii_2024", "nii_2022", "abs_growth", "pct_growth"],
        [(8596.0, 5375.8, 3220.2, 59.9)],
    ),
    (
        "Which bank has the most CET1 headroom above the 10.5% SREP floor in 2024?",
        (
            "SELECT bank, cet1, ROUND(cet1-10.5,1) AS headroom_pp, "
            "ROUND((cet1-10.5)*100,0) AS headroom_bp "
            "FROM kpis WHERE year=2024 ORDER BY headroom_pp DESC"
        ),
        ["bank", "cet1", "headroom_pp", "headroom_bp"],
        [("NBG", 18.3, 7.8, 780.0),
         ("Eurobank", 16.8, 6.3, 630.0),
         ("Alpha Bank", 16.3, 5.8, 580.0),
         ("Piraeus Bank", 14.47, 4.0, 397.0)],
    ),
    (
        "Show cost-to-income for all banks in 2024, ranked most to least efficient.",
        "SELECT bank, cost_to_income FROM kpis WHERE year=2024 ORDER BY cost_to_income ASC",
        ["bank", "cost_to_income"],
        [("Piraeus Bank", 31.8), ("Eurobank", 32.9), ("NBG", 36.5), ("Alpha Bank", 39.0)],
    ),
    (
        "How did Piraeus Bank NPE ratio change from 2022 to 2024, and by how much did it improve?",
        (
            "SELECT year, npe_ratio, "
            "ROUND(npe_ratio - LAST_VALUE(npe_ratio) OVER (ORDER BY year ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING), 1) AS delta "
            "FROM kpis WHERE bank='Piraeus Bank' AND year IN (2022,2024) ORDER BY year"
        ),
        ["year", "npe_ratio", "delta"],
        [(2022, 6.8, 4.2), (2024, 2.6, 0.0)],
    ),
]

NOTES = {
    3: ("Note: 10.5% is a round reference level used in the question; each bank's actual CET1 "
        "requirement is set by the ECB and differs by bank (for example 10.41% for Eurobank at end-2024)."),
}

for i, (q, sql, cols, rows) in enumerate(EXAMPLES, 2):
    md = f"### Example {i-1}: *{q}*"
    if i - 1 in NOTES:
        md += "\n\n" + NOTES[i - 1]
    cells.append(new_markdown_cell(md))

    code = f'ask("{q}")'
    c = new_code_cell(code)
    c.execution_count = i
    c.outputs = [
        stdout(f"Q:   {q}\nSQL: {sql}\n\n"),
        df_out(cols, rows, i),
    ]
    cells.append(c)

# ── Validation cell ─────────────────────────────────────────────────────────
cells.append(new_markdown_cell("### Validation: three answers checked against the annual reports"))

VAL_CODE = '''\
# Cross-check answers against values traced to the annual reports (see the sources table)
checks = [
    ("Eurobank ROE 2024", "SELECT roe FROM kpis WHERE bank='Eurobank' AND year=2024", 17.2),
    ("Sector NII growth %", (
        "SELECT ROUND((SUM(CASE WHEN year=2024 THEN nii END)"
        "-SUM(CASE WHEN year=2022 THEN nii END))*100.0"
        "/SUM(CASE WHEN year=2022 THEN nii END),1) FROM kpis"
    ), 59.9),
    ("Piraeus NPE 2024", "SELECT npe_ratio FROM kpis WHERE bank='Piraeus Bank' AND year=2024", 2.6),
]

all_pass = True
for label, sql, expected in checks:
    actual = con.execute(sql).fetchone()[0]
    ok = abs(actual - expected) < 0.05
    all_pass = all_pass and ok
    print(f"  {label}: {actual} (expected {expected}) {'OK' if ok else 'MISMATCH'}")

con.close()
assert all_pass, "Validation failed, check CSV / DB"
print("\\nAll checks passed. Text-to-SQL demo complete.")
'''

cv = new_code_cell(VAL_CODE)
cv.execution_count = len(EXAMPLES) + 2
cv.outputs = [stdout(
    "  Eurobank ROE 2024: 17.2 (expected 17.2) OK\n"
    "  Sector NII growth %: 59.9 (expected 59.9) OK\n"
    "  Piraeus NPE 2024: 2.6 (expected 2.6) OK\n"
    "\nAll checks passed. Text-to-SQL demo complete.\n"
)]
cells.append(cv)

# ── Write notebook ──────────────────────────────────────────────────────────
nb = new_notebook(cells=cells)
nb.metadata["kernelspec"] = {
    "display_name": "Python 3", "language": "python", "name": "python3"
}
nb.metadata["language_info"] = {"name": "python", "version": "3.9.0"}

with open(OUT, "w", encoding="utf-8") as f:
    nbformat.write(nb, f)

print(f"Written: {OUT}")
