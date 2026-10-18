# Loom Walkthrough Script: Greek Banking Sector Analysis
# Target length: 3 minutes | Audience: FinTech and banking recruiters

Every number in this script comes from `kpis_final.csv` or from the verified results of the project.
The spoken text is about 380 words, so there is room for the clicks.

---

## Setup before recording

- Browser: open the Streamlit app (https://greek-banking-sector-analysis.streamlit.app/). If the hosted app is not up, run `streamlit run 05_streamlit_app/app.py`.
- VS Code: project root open. Keep the README closed until it shows the corrected numbers.
- Keep `06_llm_qa/01_text_to_sql.ipynb` closed until its contact line and its example question about a CET1 floor are corrected.
- Do not zoom in on the ROE charts of the Overview and Bank Deep Dive pages until their cost of equity line (10.3%) matches the 10% used everywhere else.
- Terminal: ready to run `pytest tests/ -v`.
- Notebooks ready in tabs: `03_analysis/04_nii_rate_volume_walk.ipynb` and `03_analysis/05_earnings_quality.ipynb`.
- Close all unrelated tabs and notifications.

---

## 0:00 to 0:20, Hook: what the project answers

> "Net interest income of the four big Greek banks grew by almost 60% from 2022 to 2024.
> I built this project to answer two questions from their annual reports.
> What drove that rise? And which bank would take the hardest hit if conditions turn?"

**Show:** the Overview page of the app, with the sector headline cards. Do not read the cards out loud.

---

## 0:20 to 0:45, Data foundation: credibility first

> "All the data comes from 12 annual reports. I read the statements with pdfplumber and
> recorded the report and PDF page of every number in sources.csv.
> Now the tests. They recompute the ratios from the statement lines and check that
> assets equal liabilities plus equity. They pass."

**Show:**
1. `02_Banking_Sector_Dashboard/data/processed/kpis_final.csv`, just flash it. 12 rows, one per bank and year.
2. `sources.csv`, scroll for two seconds.
3. Terminal: run `pytest tests/ -v` live and let the passes scroll.

---

## 0:45 to 1:15, The analysis: what drove the rise

**Switch to the notebook `04_nii_rate_volume_walk.ipynb`, then to `05_earnings_quality.ipynb`.**

> "Here is the NII walk. In 2023, wider margins added €2,891m to sector NII. That is the rate effect.
> In 2024 NII rose by only €497m: €270m from rate and €225m from volume.
> Eurobank had €265m of volume after it consolidated Hellenic Bank from 30 June 2024.
> One more point: 2022 profit included one-offs. On underlying figures,
> 2023 profit rose about 42%, not fell 3.5%."

**Show:** the walk table first, then the reported against underlying profit cells.

---

## 1:15 to 1:40, The app: Bank Deep Dive and Investment Thesis

**Switch to the Streamlit app.**

> "Back in the app, Bank Deep Dive shows eight KPI cards for each bank.
> RoTE is return on tangible equity.
> On Investment Thesis I move the cost of equity from 10% to 9% and the justified P/TBV of each bank updates.
> There are no market prices and no ratings. It is not investment advice."

**Show:**
- Bank Deep Dive: pick Eurobank and point at the KPI cards.
- Investment Thesis: drag the cost of equity slider from 10% to 9% and watch the bars move.

---

## 1:40 to 2:10, The hard analysis: capital quality and funding

**Switch to DTC Analysis, then to Macro and Funding.**

> "A deferred tax credit, or DTC, is a tax claim on the Greek State that counts in CET1 capital.
> DTCs of the four banks fell from €13.5bn in 2022 to €12.0bn in 2024.
> At end-2024 they were 36% of CET1 capital at Eurobank and 63% at Piraeus.
> On Macro and Funding, ECB funding fell from €35.1bn at end-2022 to €2.6bn at end-2024, all of it Alpha's."

**Show:** the DTC share of CET1 chart, then the ECB funding section.

---

## 2:10 to 2:40, Stress test: who takes the hardest hit

**Switch to Forecast and Stress, Stress Test tab, then the Sensitivity tab.**

> "This is a one-year stress test: cost of risk up 200 basis points, loans down 15%, NIM down 50 basis points.
> Three banks stay profitable. Alpha loses €118m.
> Alpha could absorb 209 basis points of extra cost of risk before a pre-tax loss.
> The other three could absorb 353 to 420.
> In the heatmap, the amber box is the default shock."

**Show:**
- Stress Test tab: the results table, then drag the cost of risk slider to 400bp and watch the table and the CET1 bars update.
- Sensitivity tab: the CET1 heatmap for one bank, with the default shock in the amber box.
- Do not describe any level as a regulatory minimum. The app marks a round reference level only.

---

## 2:40 to 3:00, Close: stack and signal

> "The stack: pdfplumber, pandas, SQLite, pytest, six analysis notebooks, two forecasting notebooks,
> a Text-to-SQL notebook with the Claude API, Streamlit, an Excel model and a 12-slide deck.
> From the processed data onward, everything runs from one git clone.
> The repo is linked below. Feedback is welcome."

**Show:** the repository folder tree for 3 seconds, then cut.

---

## Video description (paste under the video)

Greek Banking Sector Analysis, FY2022 to FY2024. Consolidated group figures of Alpha Services and Holdings S.A.,
Eurobank Ergasias Services and Holdings S.A., National Bank of Greece S.A. and Piraeus Financial Holdings S.A.
Latest restated figures, every number traced to a PDF page. For portfolio and educational purposes only. Not investment advice.

Spyros Papastergiou | papastergiousp@gmail.com
GitHub: github.com/papastergiousp-maker/greek-banking-sector-analysis
Dashboard: phytai.com/dashboard

---

## Recording tips

- Do not read slides. Talk over the visuals.
- Keep cursor movement slow and deliberate.
- If you stumble: pause, breathe, continue. Do not re-record the whole thing.
- Target 3:00. 3:30 is the maximum.
- Add captions in Loom after recording (auto-generated, just review).
- Thumbnail: use the radar chart screenshot from the Peer Comparison page.
