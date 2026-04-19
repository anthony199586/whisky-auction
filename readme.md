# Whisky Auction Price Analysis
### Hedonic pricing and informational asymmetry in the secondary whisky market

---

## Background

I am an MSc graduate in experimental particle physics with a genuine passion for old and rare whiskies. With no formal work experience, I built this project to demonstrate my data analysis abilities using a domain I know deeply — the secondary whisky auction market.

The goal was to merge quantitative analysis with whisky expertise to find things a pure data scientist would miss. Physics training gives you instincts about measurement, uncertainty, and modelling. Whisky knowledge tells you which variables actually matter and why the data looks the way it does.

---

## Data

I scraped 115,561 individual bottle lot records from Scotch Whisky Auctions (auctions 154–177, covering approximately April 2024 to March 2026) using Python, requests, and BeautifulSoup. Each record includes hammer price, distillery, age, ABV, volume, cask type, distillation date, and bottling date where available.

Data is stored in a normalised SQLite database with 6 tables. All enrichment — distillery identification, bottler classification, OB/IB status, cask normalisation, series classification, market regime assignment — is handled by `whisky_utils.py` (~2,400 lines).

Multi-bottle sets (244 lots) are excluded from model training as their per-70cl prices are not comparable to single bottle lots.

---

## Key Findings

**1. Closed distillery premium (6.4x)**
Bottles from closed distilleries command a 6.4x median price premium over operational distillery bottles (£580 vs £90 median). Japanese closed distilleries (Karuizawa, Hanyu, Shirakawa) command the highest premiums — consistent with informational asymmetry, since fewer informed bidders compete despite genuine rarity.

**2. IB bottler premium is tier-dependent**
The aggregate IB discount of 30% masks enormous within-category variance. Prestige IBs (Samaroli, Sestante, Kingsbury) command 3–4x the OB median price. Volume IBs (Carn Mor, James Eadie) sell at 40–50% of OB median. Bottler reputation — specifically trust in the selector's palate and connections — drives the premium.

**3. Famous vintage years are efficiently priced**
GlenDronach 1993 (the most celebrated vintage) has the highest lot count (77) but trades at a slightly negative residual. The reputation increased supply more than demand, diluting the average. Pre-1980 vintages with smaller supply show stronger unexplained premiums.

**4. The auction market is stable (2022–2026)**
Median prices and model residuals show no significant trend across 24 auctions. The post-COVID correction visible in the cask market does not appear in the bottle market — bottle collectors appear less driven by investment motives than cask investors.

**5. ABV premium is non-linear and era-dependent**
Two price peaks: 40–43% (old G&M and era bottlings where low ABV signals authenticity, not dilution) and 50–55% (mainstream cask strength collector expressions). A linear ABV coefficient systematically undervalues pre-1980 bottlings.

**6. The model reveals informational asymmetry**
XGBoost model (R²=0.875, MAE=£60) performs very differently across bottle types. Well-understood closed distillery bottles predict within 8% error. Bottles requiring specific vintage knowledge (Ardbeg 1976 Hand Fill) show 75% error — the gap represents approximately £3,000 of collector knowledge premium invisible to observable features.

**7. Market demand structure is the strongest price signal**
The four-regime market taxonomy (R1–R4) is the single most important model feature at 30%+ importance — more predictive than age alone. Correctly classifying whether a bottle sits in the normie market, geek market, holy grail category, or convergence zone explains more price variance than any individual bottle characteristic.

**8. The whisky market has been heavily commercialised since ~2010**
Pre-2010 bottlings of named expressions (Uigeadail, Distillers Edition, Cairdeas) command genuine auction premiums over RRP because production was limited and cask quality was genuinely different. Post-2010 versions of the same expressions trade at or below RRP — they are marketing exercises on commodity spirit. This era effect is encoded in the OB expression tier system.

**9. OB expression tier classification materially reduces per-distillery error**
Classifying OB lots by expression tier within each distillery — accounting for both expression name and bottling era — reduces median prediction error by 2–6 percentage points across 18 classified distilleries.

---

## Model Progression

| Model | R² | MAE | Key addition |
|---|---|---|---|
| Linear regression baseline | 0.107 | — | Raw features |
| Linear regression (cleaned) | 0.562 | — | Data cleaning |
| XGBoost v1 — core features | 0.863 | £75 | Age, ABV, distillery, cask |
| XGBoost v2 — normalised price | 0.867 | £72 | price_70cl_adj target |
| XGBoost v3 — expanded distillery | 0.858 | £70 | Broader distillery list |
| XGBoost v4b — IB series tiers | 0.861 | £73 | IB series classification |
| XGBoost v5 — market regime | 0.866 | £68 | R1–R4 demand taxonomy |
| XGBoost v5b — grain + bottler | 0.867 | £68 | is_grain, legendary bottler R3 |
| XGBoost v6 — OB expression tiers | 0.869 | £66 | 9-distillery OB classification |
| XGBoost v6 final — tier redesign | 0.875 | £60 | Data-driven tier discipline, set exclusion |

---

## Market Regime Framework (R1–R4)

The most important analytical contribution of this project. Classifies each lot by demand-side market structure rather than supply-side provenance alone.

| Regime | Lots | Median | Description |
|---|---|---|---|
| R1 | 19,603 | £130 | Brand/luxury driven — normie market (Dalmore, modern Macallan, airport duty-free). Knowledgeable buyers walk away due to opportunity cost. |
| R2 | 88,324 | £85 | Liquid/provenance driven — default geek market. Price anchored to IB series tier, distillery reputation, vintage, cask provenance. |
| R3 | 3,205 | £600 | Holy grail — legendary scarcity (Karuizawa, Hanyu, Port Ellen, Brora, Rosebank, pre-era distillations). Zero normie demand. |
| R4 | 4,429 | £240 | Convergence — geek and normie demand independently defensible (Japanese mainstream OB, pre-2004 old sherry Macallan OB). |

**R3 vs R4 critical distinction:** The test is whether normies are *genuinely bidding*, not merely whether a bottle is expensive within whisky circles. Bowmore 1964 = R3 (famous within whisky, invisible outside it). Yamazaki = R4 (normies independently know and want it).

**Classification logic (precedence order):**
1. Named R3 distilleries (Karuizawa, Hanyu, Port Ellen, Brora, Rosebank)
2. Legendary bottler override: series_tier=5 + bottler_tier≥4 → R3
3. General closed distillery rule: pre-1990 distillation year or age≥30 → R3
4. Distillery-specific golden era thresholds (`DISTILLERY_R3_ERA` dict)
5. Implied distillation year from age + bottling year
6. R4 rules: Japanese mainstream OB, old sherry Macallan OB
7. R1 rules: luxury keywords, brand distilleries
8. R2 default

**Selected golden era thresholds:**

| Distillery | Threshold | Reason |
|---|---|---|
| Ardbeg | 1981 | Distillery closure |
| Laphroaig | 1985 | Character change |
| Bowmore | 1974 | Pre-soapy era |
| GlenDronach | 1978 | Direct-fired stills era |
| Glenfarclas | 1980 | Steam experiment end |
| Mortlach | 1975 | Old character era |
| Bunnahabhain | 1982 | Pre-modern era |
| Talisker | 1979 | Pre-modern era |

---

## IB Series Classification

`detect_bottler_series()` assigns `bottler_series` and `series_tier` (1–5) to IB lots. Dispatches to bottler-specific functions combining title keyword detection with era-based ABV/volume/year inference.

**Coverage:** ~95.6% of IB lots classified across 26 bottlers

**Tier hierarchy:**

| Tier | Description | Examples |
|---|---|---|
| 5 | Legendary discontinued | Cadenhead dumpy, Signatory ink pot, SMWS Karuizawa, Samaroli founder era, Sestante crystal |
| 4 | Prestige current/discontinued | G&M Private Collection, Signatory Silent Stills, Old & Rare pre-1985, G&M Rare Vintage |
| 3 | Premium current | Cadenhead Warehouse Tasting, Signatory Un-Chillfiltered, SMWS standard |
| 2 | Standard accessible | Signatory 100 Proof, Cadenhead Enigma, G&M Discovery |
| 1 | Unclassified / standard OB | — |

**Bottlers with full series detection:**
Cadenhead's, Signatory, Gordon & MacPhail, Douglas Laing, Hunter Laing, Old Malt Cask, First Editions, Old & Rare (distillery-aware), Berry Bros & Rudd, Samaroli, Moon Import, Sestante, Silver Seal, Murray McDavid, Hart Brothers, Duncan Taylor, Adelphi, Compass Box, That Boutique-y Whisky Company, SMWS, James MacArthur, Kingsbury, Blackadder, Malts of Scotland, Chieftain's, Wilson & Morgan

**Key design decisions:**
- Old & Rare tier is distillery-aware: closed distillery = tier 5, pre-1985 distillation = tier 5, modern operational = tier 3
- Legendary bottler override: Samaroli/Moon Import/Sestante at tier 4–5 → R3 regardless of distillery (bottler reputation transcends distillery)

---

## OB Expression Classification

`detect_ob_expression()` dispatches to distillery-specific functions assigning `ob_tier` (1–5). Combined with IB series tiers into `effective_tier` (model feature).

**Core design principle:** Tier assignment depends on both expression name AND bottling era. The whisky market commercialised heavily around 2010. Pre-2010 bottlings of named expressions (Uigeadail, Cairdeas, Distillers Edition) commanded genuine premiums because production was limited and cask quality was genuinely different. Post-2010 versions trade at or below retail — they are tier 2 regardless of name.

**Tier framework for OB:**
- Tier 5: Legendary old era — pre-golden-era vintages, iconic discontinued series (Manager's Dram, old White Horse Lagavulin)
- Tier 4: Genuinely prestige limited — named releases people pay above RRP at auction (Syndicate, Prima/Ultima, Midnight Malt, Family Casks, early Feis Ile SC, Casks of Distinction)
- Tier 3: Above core range — expressions that genuinely exceed standard (Octomore, Black Art, Signet, Kilchoman inaugural, Corryvreckan, pre-2010 named expressions)
- Tier 2: Core range including named expressions — Uigeadail, Cairdeas, Lasanta, Distillers Edition modern, Parliament, Allardice, all standard age statements
- Tier 1: NAS entry level

**Distilleries classified and error improvement (v5b → final):**

| Distillery | Error before | Error after | Improvement |
|---|---|---|---|
| Ardbeg | 20.3% | 14.3% | −6.0pp |
| Glenfarclas | 18.5% | 12.3% | −6.2pp |
| Kilchoman | 21.0% | 15.4% | −5.6pp |
| Redbreast | 19.5% | 14.9% | −4.6pp |
| Glenmorangie | 19.1% | 16.2% | −2.9pp |
| Lagavulin | 24.1% | 22.2% | −1.9pp |
| Laphroaig | 30.4% | 28.3% | −2.1pp |
| Bunnahabhain | 21.5% | 19.6% | −1.9pp |
| Caol Ila | 19.5% | 17.7% | −1.8pp |
| Tobermory | 18.2% | 16.5% | −1.7pp |
| Benriach | 18.2% | 15.8% | −2.4pp |
| GlenDronach | 20.3% | 18.9% | −1.4pp |
| Ben Nevis | 26.9% | 25.7% | −1.2pp |
| Mortlach | 20.1% | 19.5% | −0.6pp |
| Talisker | 21.2% | 20.3% | −0.9pp |
| Highland Park | 24.8% | 23.9% | −0.9pp |
| Old Pulteney | 18.1% | 17.2% | −0.9pp |
| Bruichladdich | 20.0% | 19.6% | −0.4pp |
| Ledaig | 18.7% | 20.3% | +1.6pp (market too thin) |

---

## Model Features (final)

| Feature | Importance | Description |
|---|---|---|
| `market_regime` | ~31% | R1–R4 demand taxonomy |
| `age_years` | ~28% | Age statement |
| `is_grain` | ~9% | Grain vs malt distillery flag |
| `distillery_enc` | ~7% | Label-encoded distillery |
| `abv_bin` | ~7% | ABV in 8 bins |
| `volume_cl` | ~6% | Bottle volume |
| `effective_tier` | ~5% | IB series or OB expression tier (1–5) |
| `is_closed` | ~3% | Closed distillery flag |
| `cask_enc` | ~3% | Normalised cask type |
| `auction_recency` | ~1% | 177 minus auction number |

---

## Technical Stack

| Tool | Purpose |
|---|---|
| Python 3.13 | Base language |
| requests + BeautifulSoup | Web scraping |
| SQLite | Data storage (normalised schema) |
| pandas | Data cleaning and enrichment |
| XGBoost | Price prediction model |
| scikit-learn | Model evaluation |
| SHAP | Model interpretability |
| matplotlib | Visualisations |

---

## Project Structure

```
whisky-auction/
├── scraper.py                  — scrapes lot pages from Scotch Whisky Auctions
├── whisky_utils.py             — enrichment, classification, regime logic (~2,400 lines)
├── smws_codes.csv              — SMWS distillery code mapping (165 codes)
├── whisky_auctions.db          — SQLite database (115,561 lots) [not in repo]
├── model_v6_final.pkl          — trained XGBoost model [not in repo]
├── label_encoders_v6_final.pkl — fitted label encoders [not in repo]
├── requirements.txt            — Python dependencies
├── week1_basics.ipynb          — Python fundamentals and data exploration
├── week2_pandas.ipynb          — pandas EDA and cleaning
├── week3_sql.ipynb             — SQL schema and queries
├── week4_enrichment.ipynb      — enrichment pipeline development
├── week5_model.ipynb           — XGBoost modelling and SHAP analysis
├── week6_visualisations.ipynb  — all 6 charts
└── viz1–6_*.png                — saved visualisation outputs
```

---

## How to Run

```bash
# Clone and set up environment
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
```

---

## Key Technical Decisions

**Volume normalisation**
Price normalised to 70cl equivalent using empirically derived volume premium factors. Multi-bottle sets excluded from model training — their per-70cl prices are not comparable to single bottle lots and cause 60%+ prediction error.

**Market regime taxonomy**
Four demand-side regimes (R1–R4) assigned per lot via `classify_market_regime()`. Regime is the top model feature (~31% importance), more predictive than age alone. The R3 vs R4 distinction — whether normie demand is genuine vs absent — required deep domain knowledge to implement correctly.

**IB series classification**
`detect_bottler_series()` dispatches to 26 bottler-specific functions. Each combines title keyword detection with era-based inference using ABV, volume, and bottling year signals. Coverage: ~95.6% of IB lots. The `distillery` parameter enables context-aware tier assignment (Old & Rare tier depends on whether the distillery is closed).

**OB expression classification**
`detect_ob_expression()` dispatches to 19 distillery-specific functions. The key design insight is that bottling era matters as much as expression name — the same Uigeadail bottled in 2003 vs 2023 represents fundamentally different products at fundamentally different price points. Pre-2010 named expressions receive tier 3; post-2010 receive tier 2.

**Grain whisky flag**
`is_grain` binary feature (~9% importance) captures the systematic discount on grain distilleries. Old grain (30–40yo Dumbarton, Cambus) commands only £200–300 vs equivalent-age malt at £800+.

**SMWS distillery identification**
165-code mapping in `smws_codes.csv` links SMWS cask codes to source distilleries. Closed distillery codes receive tier 5. Coverage: 87.7% of SMWS lots.

---

## Known Limitations and Future Work

**Distillery reputation within R3**
Not all R3 distilleries command equal premiums. Tomintoul 1971 and Port Ellen 1979 are both R3 but the market prices them very differently. A `dist_regime_enc` compound interaction feature would capture this but requires more lot volume per distillery.

**Laphroaig bottling year ceiling**
Bottling year is the primary price signal for Laphroaig (a 1975-bottled 10yo = £2,000; a 2020-bottled 10yo = £60). Title-based classification cannot distinguish these without structured bottling date data.

**Thin markets**
Ledaig (174 lots), Shirakawa (2 lots), Hanyu (58 lots) — insufficient data for reliable pattern learning. Will improve naturally as auctions 1–153 are scraped (back to 2011), roughly tripling the dataset.

**Planned improvements**
- `dist_regime_enc` compound feature: distillery × regime interaction
- Scrape auctions 1–153 (2011–present) to triple dataset size
- NAS model: separate treatment for no-age-statement lots (~35% of dataset)
- Streamlit dashboard: interactive price explorer
- LuxAuc Hong Kong / Sotheby's for Asian market pricing context