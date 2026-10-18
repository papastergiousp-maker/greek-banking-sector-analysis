"""
sources.py
==========
The 12 annual reports behind the dataset (4 listed groups x FY2022-FY2024),
where to download them, and the PDF pages that hold the consolidated
statements used by extract_statements.py.

Page numbers are physical PDF pages (1 = first page of the file), not the
page numbers printed in the report.
"""

from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

ENTITIES = {
    "Alpha Bank": "Alpha Services and Holdings S.A. (group)",
    "Eurobank": "Eurobank Ergasias Services and Holdings S.A. (group)",
    "NBG": "National Bank of Greece S.A. (group)",
    "Piraeus Bank": "Piraeus Financial Holdings S.A. (group)",
}

REPORTS = {
    ("Alpha Bank", 2022): {
        "file": "alpha_holdings_2022.pdf",
        "url": "https://www.alpha.gr/-/media/AlphaHoldings/Files/apotelesmata/FY2022/Alpha-Services-and-Holdings-Financial-Statements-31122022-EN.pdf",
    },
    ("Alpha Bank", 2023): {
        "file": "alpha_holdings_2023.pdf",
        "url": "https://www.alpha.gr/-/media/AlphaHoldings/Files/apotelesmata/FY2023/Group-Holdco-31122023-ENG060324Disclaimer.pdf",
    },
    ("Alpha Bank", 2024): {
        "file": "alpha_holdings_2024.pdf",
        "url": "https://www.alpha.gr/-/media/AlphaHoldings/Files/apotelesmata/FY2024/Group-Holdco-31122024-ENG060324Disclaimer.pdf",
    },
    ("Eurobank", 2022): {
        "file": "eurobank_holdings_2022.pdf",
        "url": "https://www.eurobank.gr/-/media/holding/omilos/enimerosi-ependuton/enimerosi-metoxon-eurobank/oikonomika-apotelesmata-part-01/2023/fy-2022/etisia-oikonomiki-ekthesi-en-2022.pdf",
    },
    ("Eurobank", 2023): {
        "file": "eurobank_holdings_2023.pdf",
        "url": "https://www.eurobank.gr/-/media/holding/omilos/enimerosi-ependuton/enimerosi-metoxon-eurobank/oikonomika-apotelesmata-part-01/2024/fy-2023/etisia-oikonomiki-ekthesi-en-2023.pdf",
    },
    ("Eurobank", 2024): {
        "file": "eurobank_holdings_2024.pdf",
        "url": "https://www.eurobank.gr/-/media/holding/omilos/enimerosi-ependuton/enimerosi-metoxon-eurobank/oikonomika-apotelesmata-part-01/2025/fy-2024/etisia-oikonomiki-ekthesi-en-2024.pdf",
    },
    ("NBG", 2022): {
        "file": "nbg_2022.pdf",
        "url": "https://www.nbg.gr/en/group/investor-relations/financial-information/annual-and-interim-financial-statements",
    },
    ("NBG", 2023): {
        "file": "nbg_2023.pdf",
        "url": "https://www.nbg.gr/en/group/investor-relations/financial-information/annual-and-interim-financial-statements",
    },
    ("NBG", 2024): {
        "file": "nbg_2024.pdf",
        "url": "https://www.nbg.gr/en/group/investor-relations/financial-information/annual-and-interim-financial-statements",
    },
    ("Piraeus Bank", 2022): {
        "file": "pfh_2022.pdf",
        "url": "https://www.piraeusgroup.gr/-/media/Com/2022/Files/investors/financial-results/Q4/Annual-Financial-Report-2022-of-PFH.pdf",
    },
    ("Piraeus Bank", 2023): {
        "file": "pfh_2023.pdf",
        "url": "https://www.piraeusgroup.gr/en/investor-relations/oikonomikes-katastaseis-loipes-plhrofories",
    },
    ("Piraeus Bank", 2024): {
        "file": "pfh_2024.pdf",
        "url": "https://www.piraeusgroup.gr/en/investor-relations/oikonomikes-katastaseis-loipes-plhrofories",
    },
}

# Consolidated income statement (IS) and balance sheet (BS) pages.
# FY2024 reports give 2024 and 2023; FY2023 reports give 2022.
STATEMENT_PAGES = {
    "Alpha Bank": {2024: {"IS": 246, "BS": 248}, 2023: {"IS": 150, "BS": 152}},
    "Eurobank": {2024: {"IS": 256, "BS": 255}, 2023: {"IS": 147, "BS": 146}},
    "NBG": {2024: {"IS": 367, "BS": 366}, 2023: {"IS": 242, "BS": 241}},
    "Piraeus Bank": {2024: {"IS": 423, "BS": 425}, 2023: {"IS": 172, "BS": 174}},
}
