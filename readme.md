# Whisky auction price analysis
### Hedonic pricing and informational asymmetry in the secondary whisky market

---

## Background

I am an MSc graduate in experimental particle physics with a genuine
passion for old and rare whiskies. With no formal work experience, I
built this project to demonstrate my data analysis abilities using a
domain I know deeply — the secondary whisky auction market.

The goal was to merge quantitative analysis with whisky expertise to
find things a pure data scientist would miss. Physics training gives
you instincts about measurement, uncertainty, and modelling. Whisky
knowledge tells you which variables actually matter and why the data
looks the way it does.

---

## Data

I scraped 115,561 individual bottle lot records from Scotch Whisky
Auctions (auctions 154-177, covering approximately April 2024 to
March 2026) using Python, requests, and BeautifulSoup. Each record
includes hammer price, distillery, age, ABV, volume, cask type,
distillation date, and bottling date where available.

Data is stored in a normalised SQLite database with 6 tables.
All enrichment — distillery identification, bottler classification,
OB/IB status, cask normalisation — is handled by `whisky_utils.py`.

---

## Key findings

**1. Closed distillery premium (6.4x)**
Bottles from closed distilleries command a 6.4x median price premium
over operational distillery bottles (£580 vs £90 median). Japanese
closed distilleries (Karuizawa, Hanyu, Shirakawa) command the highest
premiums — consistent with informational asymmetry, since fewer
informed bidders compete despite genuine rarity.

**2. IB bottler premium is tier-dependent**
The aggregate IB discount of 30% masks enormous within-category
variance. Prestige IBs (Kingsbury, Old & Rare, Blackadder) command
3-4x the OB median price. Volume IBs (Carn Mor, James Eadie) sell
at 40-50% of OB median. Bottler reputation — specifically trust in
the selector's palate and connections — drives the premium.

**3. Famous vintage years are efficiently priced**
GlenDronach 1993 (the most celebrated vintage) has the highest lot
count (77) but trades at a slightly negative residual. The reputation
increased supply more than demand, diluting the average. Pre-1980
vintages with smaller supply show stronger unexplained premiums.

**4. The auction market is stable (2022-2026)**
Median prices and model residuals show no significant trend across
17 auctions. The post-COVID correction visible in the cask market
does not appear in the bottle market — bottle collectors appear less
driven by investment motives than cask investors.

**5. ABV premium is non-linear and era-dependent**
Two price peaks: 40-43% (old G&M and era bottlings where low ABV
signals authenticity, not dilution) and 50-55% (mainstream cask
strength collector expressions). A linear ABV coefficient
systematically undervalues pre-1980 bottlings.

**6. The model reveals informational asymmetry**
XGBoost model (R²=0.858, MAE=£70) performs very differently across
bottle types. Well-understood closed distillery bottles predict within
8% error. Bottles requiring specific vintage knowledge (Ardbeg 1976
Hand Fill) show 75% error — the gap represents approximately £3,000
of collector knowledge premium invisible to observable features.

**7. Closed distillery market is highly efficient**
Median value ratio of 1.04x for closed distillery bottles — the
premium is well understood by all participants. Informational
asymmetry lives in operational distillery bottles, particularly
obscure distillery names and private label bottlings.

---

## Model progression

| Model | R² | MAE | Training samples |
|---|---|---|---|
| Linear regression baseline | 0.107 | n/a | 28,258 |
| Linear regression (cleaned) | 0.562 | n/a | 27,268 |
| XGBoost v1 — core features | 0.863 | £75 | 8,238 |
| XGBoost v2 — normalised price | 0.867 | £72 | 8,063 |
| XGBoost v3 — expanded distillery | 0.858 | £70 | 35,267 |
| XGBoost vintage (distil. year) | 0.919 | £65 | 8,756 |

---

## Technical stack

| Tool | Purpose |
|---|---|
| Python | Base language |
| requests + BeautifulSoup | Web scraping |
| SQLite | Data storage (normalised schema) |
| pandas | Data cleaning and enrichment |
| XGBoost | Price prediction model |
| scikit-learn | Model evaluation |
| SHAP | Model interpretability |
| matplotlib | Visualisations |

---

## Project structure
```
whisky-auctions/
├── scraper.py              — scrapes lot pages from Scotch Whisky Auctions
├── whisky_utils.py         — shared enrichment functions and reference data
├── whisky_auctions.db      — SQLite database (115,561 lots)
├── model_final.pkl         — trained XGBoost model
├── model_vintage.pkl       — vintage model (distillation year feature)
├── label_encoders_final.pkl — fitted label encoders
├── requirements.txt        — Python dependencies
├── week1_basics.ipynb      — Python fundamentals
├── week2_pandas.ipynb      — pandas exploration and EDA
├── week3_sql.ipynb         — SQL schema and queries
├── week4_enrichment.ipynb  — data enrichment pipeline
├── week5_model.ipynb       — modelling and SHAP analysis
├── week6_visualisations.ipynb — all charts
└── viz1-6_*.png            — saved visualisation outputs
```

---

## How to run
```bash
# Clone and set up environment
git clone https://github.com/yourusername/whisky-auctions
cd whisky-auctions
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# The database is included — open any notebook to explore
jupyter notebook

# To re-scrape (takes ~60 hours for full archive)
python scraper.py
```

---

## Limitations and future work

**Current limitations:**
- 65% of lots excluded from the model (no age statement or
  unrecognised distillery) — NAS core range expressions are
  the largest omitted category
- Distillery encoding treats all expressions from one distillery
  as equivalent — Macallan luxury tier vs core range requires
  separate treatment
- Bottler list covers major IBs but misses smaller operators
- Distillation year available for only 30% of lots

**Planned improvements:**
- Macallan tier split: separate luxury series from core range
  using title keyword detection
- NAS model: handle no-age-statement bottles as a separate
  feature rather than excluding them
- Samaroli founder-era analysis: split pre/post-2017 bottlings
  to test quality change hypothesis
- GlenDronach specific date effect: full date parsing to isolate
  19/3/1993 lots
- Streamlit dashboard: interactive price explorer by distillery
- Expand scraping to full archive (auctions 1-153, back to 2011)

## Key technical decisions

**Volume normalisation**
Price normalised to 70cl equivalent using empirically derived
volume premium factors. Formula: price × (70/vol) / premium_factor
where premium_factor accounts for format collectibility premium.
Miniatures (5cl) carry 1.64x per-ml premium vs standard 70cl.

**IB series classification**
detect_bottler_series() in whisky_utils.py classifies lots from
major IBs into named series using title keyword detection and
era-based ABV/volume inference. Coverage: 4.8% of all lots,
~35% of high-value IB lots.

Series tier hierarchy (1-5):
  5 = legendary discontinued (Cadenhead dumpy, Signatory ink pot)
  4 = prestige current/discontinued (Authentic Collection, etc.)
  3 = premium current (Warehouse Tasting, Un-Chillfiltered etc.)
  2 = standard accessible (100 Proof, Small Batch etc.)
  1 = unclassified standard

**Price target variable**
price_70cl_adj used as model target, replacing winning_bid.
Normalises across all volume formats including miniatures.
```

**For the code** — everything important lives in `whisky_utils.py`. That file is your single source of truth. Make sure it's saved and backed up. The key functions that encode all our analytical decisions are:
```
extract_distillery()      — distillery identification
extract_bottler()         — bottler identification  
is_closed_distillery()    — closed distillery flag
normalise_cask_type()     — cask normalisation
price_per_70cl_adjusted() — volume normalisation
detect_bottler_series()   — IB series classification
enrich_dataframe()        — master enrichment pipeline

## Iterative IB series refinement methodology

Series classification for major IBs follows an iterative process:

1. **Research** — search official bottler websites, Whisky Exchange,
   WhiskyFun, Whiskybase for complete series lists with distinguishing
   characteristics (ABV, volume, bottling era, label design)

2. **Implement** — add keyword detection and era-based inference to
   detect_[bottler]_series() in whisky_utils.py

3. **Validate** — examine "standard" (unclassified) lots, sorted by
   price. High-value standard lots indicate missing series coverage.

4. **Cross-reference** — search Whiskybase/WhiskyFun for specific
   expensive lots to find their canonical series names

5. **Refine** — add newly identified series keywords and re-run

Current refinement status:
  ✓ Signatory:      standard reduced from 426 → 43 lots
  ✓ SMWS:           87.7% distillery identified via code mapping
  ✓ Cadenhead's:    dumpy era inference working
  ✓ G&M:            old era inference added
  → Hart Brothers:  41.7% of standard >£300 — needs research
  → Duncan Taylor:  34.4% of standard >£300 — needs research
  → G&M:            29.2% of standard >£300 — needs refinement
  → Berry Bros:     11.2% of standard >£300 — moderate priority