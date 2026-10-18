"""
smoke_test.py — run every page of the Streamlit app headlessly and fail on any exception.

    python 05_streamlit_app/smoke_test.py
"""

import sys
import warnings
from pathlib import Path

from streamlit.testing.v1 import AppTest

warnings.filterwarnings("ignore")
APP = Path(__file__).resolve().parent
files = [APP / "app.py"] + sorted((APP / "pages").glob("*.py"))

failed = 0
for f in files:
    at = AppTest.from_file(str(f), default_timeout=120)
    at.run()
    errors = [e.value for e in at.exception]
    print(f"{'ERR' if errors else 'OK '} {f.relative_to(APP)}")
    for e in errors:
        print("    ", str(e)[:500])
    failed += bool(errors)

sys.exit(1 if failed else 0)
