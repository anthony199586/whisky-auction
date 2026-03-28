Whisky Auction Price Analysis
Hedonic pricing and informational asymmetry in the secondary whisky market

Background
I am an MSc graduate in experimental particle physics with a genuine
passion for old and rare whiskies. With no formal work experience, I
built this project to demonstrate my data analysis abilities using a
domain I know deeply — the secondary whisky auction market.
The goal was to merge quantitative analysis with whisky expertise to
find things a pure data scientist would miss. Physics training gives
you instincts about measurement, uncertainty, and modelling. Whisky
knowledge tells you which variables actually matter and why the data
looks the way it does.

Data
I scraped 115,561 individual bottle lot records from Scotch Whisky
Auctions (auctions 154–177, covering approximately April 2024 to
March 2026) using Python, requests, and BeautifulSoup. Each record
includes hammer price, distillery, age, ABV, volume, cask type,
distillation date, and bottling date where available.
Data is stored in a normalised SQLite database with 6 tables.
All enrichment — distillery identification, bottler classification,
OB/IB status, cask normalisation, series classification — is handled
by whisky_utils.py.

Key findings
1. Closed distillery premium (6.4x)
Bottles from closed distilleries command a 6.4x median price premium
over operational distillery bottles (£580 vs £90 median). Japanese
closed distilleries (Karuizawa, Hanyu, Shirakawa) command the highest
premiums — consistent with informational asymmetry, since fewer
informed bidders compete despite genuine rarity.
2. IB bottler premium is tier-dependent
The aggregate IB discount of 30% masks enormous within-category
variance. Prestige IBs (Old & Rare, Sestante, Kingsbury) command 3–4x
the OB median price. Volume IBs (Carn Mor, James Eadie) sell at
40–50% of OB median. Bottler reputation — specifically trust in the
selector's palate and connections — drives the premium.
3. Famous vintage years are efficiently priced
GlenDronach 1993 (the most celebrated vintage) has the highest lot
count (77) but trades at a slightly negative residual. The reputation
increased supply more than demand, diluting the average. Pre-1980
vintages with smaller supply show stronger unexplained premiums.
4. The auction market is stable (2022–2026)
Median prices and model residuals show no significant trend across
24 auctions. The post-COVID correction visible in the cask market
does not appear in the bottle market — bottle collectors appear less
driven by investment motives than cask investors.
5. ABV premium is non-linear and era-dependent
Two price peaks: 40–43% (old G&M and era bottlings where low ABV
signals authenticity, not dilution) and 50–55% (mainstream cask
strength collector expressions). A linear ABV coefficient
systematically undervalues pre-1980 bottlings.
6. The model reveals informational asymmetry
XGBoost model (R²=0.861, MAE=£73) performs very differently across
bottle types. Well-understood closed distillery bottles predict within
8% error. Bottles requiring specific vintage knowledge (Ardbeg 1976
Hand Fill) show 75% error — the gap represents approximately £3,000
of collector knowledge premium invisible to observable features.
7. Closed distillery market is highly efficient
Median value ratio of 1.04x for closed distillery bottles — the
premium is well understood by all participants. Informational
asymmetry lives in operational distillery bottles, particularly
obscure distillery names and private label bottlings.
8. IB series tier materially improves predictions on prestige lots
After classifying 89.6% of IB lots into named series (tier 1–5),
tier 5 lot median prediction error dropped from 15.7% to 12.9%.
The improvement is concentrated exactly where it should be — prestige
IBs (tier 4–5) show 1–2 percentage point error reduction while
standard OB lots (tier 1) are unchanged.

Model progression
ModelR²MAETraining samplesLinear regression baseline0.107n/a28,258Linear regression (cleaned)0.562n/a27,268XGBoost v1 — core features0.863£758,238XGBoost v2 — normalised price0.867£728,063XGBoost v3 — expanded distillery0.858£7035,267XGBoost v4a — series tier0.861£7335,525XGBoost v4b — expanded IB coverage0.861£7335,525XGBoost vintage (distil. year)0.919£658,756
Note: aggregate R² understates series tier impact. Tier 5 lot median
error reduced from 15.7% → 12.9% with expanded IB classification.
Tier 4 error reduced from 14.4% → 13.2%.

IB series classification
A core contribution of this project is systematic classification of
independent bottler (IB) lots into named series using title keyword
detection and era-based inference in whisky_utils.py.
Coverage: 89.6% of IB lots classified across 20+ bottlers
Series tier hierarchy:
TierDescriptionExamples5Legendary discontinuedCadenhead dumpy, Signatory ink pot, SMWS Karuizawa, Samaroli founder era, Sestante4Prestige current/discontinuedG&M Private Collection, Signatory Silent Stills, Old & Rare, G&M Rare Vintage3Premium currentCadenhead Warehouse Tasting, Signatory Un-Chillfiltered, SMWS standard2Standard accessibleSignatory 100 Proof, Cadenhead Enigma, G&M Discovery1Unclassified OB standard—
Bottlers with full series detection:
Cadenhead's, Signatory, Gordon & MacPhail, Douglas Laing,
Hunter Laing, Old Malt Cask, First Editions, Old & Rare,
Berry Bros & Rudd, Samaroli, Moon Import, Sestante, Silver Seal,
Murray McDavid, Hart Brothers, Duncan Taylor, Adelphi, Compass Box,
That Boutique-y Whisky Company, SMWS, James MacArthur, Kingsbury,
Blackadder, Malts of Scotland, Chieftain's, Wilson & Morgan
Iterative refinement methodology:

Research — bottler websites, Whisky Exchange, WhiskyFun, Whiskybase
Implement — keyword detection and era-based ABV/volume inference
Validate — examine high-value "standard" lots for missing series
Cross-reference — verify expensive outliers against Whiskybase
Refine — add newly identified series keywords and re-run


Technical stack
ToolPurposePython 3.13Base languagerequests + BeautifulSoupWeb scrapingSQLiteData storage (normalised schema)pandasData cleaning and enrichmentXGBoostPrice prediction modelscikit-learnModel evaluationSHAPModel interpretabilitymatplotlibVisualisations

Project structure
whisky-auction/
├── scraper.py                  — scrapes lot pages from Scotch Whisky Auctions
├── whisky_utils.py             — enrichment functions, reference data,
│                                 IB series classification (1,300+ lines)
├── smws_codes.csv              — SMWS distillery code mapping (165 codes)
├── whisky_auctions.db          — SQLite database (115,561 lots) [not in repo]
├── model_v4b_final.pkl         — trained XGBoost model [not in repo]
├── label_encoders_v4b.pkl      — fitted label encoders [not in repo]
├── requirements.txt            — Python dependencies
├── week1_basics.ipynb          — Python fundamentals and data exploration
├── week2_pandas.ipynb          — pandas EDA and cleaning
├── week3_sql.ipynb             — SQL schema and queries
├── week4_enrichment.ipynb      — enrichment pipeline development
├── week5_model.ipynb           — XGBoost modelling and SHAP analysis
├── week6_visualisations.ipynb  — all 6 charts
└── viz1–6_*.png                — saved visualisation outputs

How to run
bash# Clone and set up environment
git clone https://github.com/anthony199586/whisky-auction
cd whisky-auction
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Open any notebook to explore
jupyter notebook

# To build the database from scratch (takes ~60 hours for full archive)
python scraper.py

# The database and model files are excluded from the repo (.gitignore)
# Run scraper.py then week3–week5 notebooks in order to regenerate them

Limitations and future work
Current limitations:

~35% of lots excluded from the model (no age statement or
unrecognised distillery) — NAS core range expressions are
the largest omitted category
Distillery encoding treats all expressions from one distillery
as equivalent — Macallan luxury tier vs core range requires
separate treatment
Distillation year available for only ~30% of lots
G&M series names systematically omitted from auction titles —
~370 G&M lots remain as "standard" despite being identifiable
on the bottle label

Planned improvements:

Separate IB-focused model relaxing the distillery filter,
using series tier as primary signal
Macallan tier split: separate luxury series from core range
using title keyword detection
NAS model: handle no-age-statement bottles separately
Streamlit dashboard: interactive price explorer
Expand scraping to full archive (auctions 1–153, back to 2011)
LuxAuc Hong Kong and Sotheby's as data sources for Asian
market analysis


Key technical decisions
Volume normalisation
Price normalised to 70cl equivalent using empirically derived
volume premium factors. Formula: price × (70/vol) / premium_factor
where premium_factor accounts for format collectibility premium.
Miniatures (5cl) carry a 1.64x per-ml premium vs standard 70cl.
Applied to all lots including miniatures — used as model target
variable (price_70cl_adj).
IB series classification
detect_bottler_series() in whisky_utils.py dispatches to
bottler-specific functions covering 20+ IBs. Each function combines
title keyword detection with era-based inference using ABV, volume,
and bottling year signals. Coverage: 89.6% of IB lots (12,398 total).
The series tier feature improved tier 5 lot prediction error from
15.7% to 12.9% despite representing only 0.4% of training data.
SMWS distillery identification
165-code mapping in smws_codes.csv links SMWS cask codes to source
distilleries. Closed distillery codes automatically receive tier 5.
Prestige operational distilleries receive tier 4. Coverage: 87.7%
of SMWS lots identified by distillery.
Model target variable
price_70cl_adj used as model target, replacing raw winning_bid.
Normalises across all volume formats including miniatures.
Log-transformed before modelling to handle the right-skewed price
distribution.