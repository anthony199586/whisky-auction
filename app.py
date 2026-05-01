"""
Whisky Auction Analytics Dashboard
Hedonic pricing and market analysis for the secondary whisky market
"""

import streamlit as st
import pandas as pd
import numpy as np
import pickle
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
import json
from datetime import datetime
from rapidfuzz import process, fuzz
# ---------------------------------------------------------------------------
# Page config — must be first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Whisky Auction Analytics",
    page_icon="🥃",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Typography and base */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }

    /* Sidebar */
    .css-1d391kg, [data-testid="stSidebar"] {
        background-color: #0f0f0f;
    }
    [data-testid="stSidebar"] * {
        color: #e8e0d0 !important;
    }

    /* Main background */
    .main .block-container {
        background-color: #faf8f4;
        padding-top: 2rem;
    }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid #e8e0d0;
        border-radius: 4px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }

    /* Headers */
    h1 { font-family: 'Playfair Display', serif; color: #1a1a1a; }
    h2 { font-family: 'Playfair Display', serif; color: #1a1a1a; font-size: 1.4rem; }
    h3 { font-family: 'IBM Plex Sans', sans-serif; color: #333; font-weight: 500; }

    /* Predicted price display */
    .price-display {
        font-family: 'Playfair Display', serif;
        font-size: 3rem;
        font-weight: 700;
        color: #1a1a1a;
        letter-spacing: -1px;
    }
    .price-range {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.9rem;
        color: #666;
        margin-top: 0.25rem;
    }
    .regime-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 2px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.8rem;
        font-weight: 500;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .regime-1 { background: #fef3c7; color: #92400e; }
    .regime-2 { background: #f0fdf4; color: #14532d; }
    .regime-3 { background: #fdf2f8; color: #701a75; }
    .regime-4 { background: #eff6ff; color: #1e3a8a; }

    /* Dividers */
    hr { border-color: #e8e0d0; margin: 1.5rem 0; }

    /* Dataframe styling */
    .dataframe { font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; }

    /* Sidebar nav */
    .nav-item {
        padding: 0.5rem 0;
        cursor: pointer;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.85rem;
        letter-spacing: 0.05em;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REGIME_LABELS = {
    1: "R1 — Brand / Luxury",
    2: "R2 — Geek Market",
    3: "R3 — Holy Grail",
    4: "R4 — Convergence",
}
REGIME_DESC = {
    1: "Brand or luxury driven. Price anchored to marketing rather than liquid quality.",
    2: "Provenance driven. Price anchored to distillery reputation, vintage and cask.",
    3: "Holy grail. Legendary scarcity — Karuizawa, Port Ellen, pre-era distillations.",
    4: "Convergence. Geek and normie demand both independently justified.",
}
REGIME_COLOURS = {1: "#f59e0b", 2: "#22c55e", 3: "#a855f7", 4: "#3b82f6"}
REGIME_BADGE_CLASS = {1: "regime-1", 2: "regime-2", 3: "regime-3", 4: "regime-4"}

DB_PATH = "whisky_auctions.db"
MODEL_PATH = "model_v6_final.pkl"
ENCODERS_PATH = "label_encoders_v6_final.pkl"

# ---------------------------------------------------------------------------
# Data loading — cached
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_parquet("enriched_df.parquet")
    # Derive is_closed if not present
    if "is_closed" not in df.columns:
        df["is_closed"] = False
    # Ensure winning_bid exists
    if "winning_bid" not in df.columns and "price_70cl_adj" in df.columns:
        df["winning_bid"] = df["price_70cl_adj"]
    return df

def load_enriched():
    return None  # no longer needed — load_data() returns enriched df


@st.cache_resource
def load_model():
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(ENCODERS_PATH, "rb") as f:
        encoders = pickle.load(f)
    return model, encoders



# ---------------------------------------------------------------------------
# Distilleries with OB classifiers (for coverage flagging)
# ---------------------------------------------------------------------------
OB_CLASSIFIED_DISTILLERIES = {
    "Ardbeg", "Laphroaig", "Lagavulin", "Highland Park",
    "Glendronach", "Glenfarclas", "Talisker", "Bunnahabhain",
    "Bruichladdich", "Caol Ila", "Mortlach", "Tobermory", "Ledaig",
    "Glenmorangie", "Ben Nevis", "Redbreast", "Old Pulteney",
    "Benriach", "Kilchoman",
    "Tomatin", "Ardnahoe", "Oban", "Tamdhu",  # ← add this line
}

FEEDBACK_LOG = "distillery_feedback.json"

def fuzzy_distillery_search(query, all_dists, threshold=40):
    """Return best matching distillery or None if below threshold."""
    if not query or not query.strip():
        return None, []
    query = query.strip()
    # Exact match first (case-insensitive)
    for d in all_dists:
        if d.lower() == query.lower():
            return d, [(d, 100)]
    # Fuzzy match
    results = process.extract(query, all_dists, scorer=fuzz.WRatio, limit=5)
    hits = [(r[0], r[1]) for r in results if r[1] >= threshold]
    if hits:
        return hits[0][0], hits
    return None, []

def get_distillery_coverage(distillery, df):
    """Return coverage stats for a distillery."""
    subset = df[df["distillery"] == distillery]
    lot_count = len(subset)
    has_ob_classifier = distillery in OB_CLASSIFIED_DISTILLERIES
    regime_coverage = subset["market_regime"].notna().mean() if lot_count > 0 else 0
    return {
        "distillery": distillery,
        "lot_count": lot_count,
        "has_ob_classifier": has_ob_classifier,
        "regime_coverage": round(regime_coverage, 3),
        "thin_market": lot_count < 30,
    }

def log_distillery_feedback(query, matched, coverage_info):
    """
    Log every distillery search with metadata for model improvement.
    Entries: query, matched distillery, lot count, coverage flags, timestamp.
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "matched": matched,
        **coverage_info,
    }
    # Load existing log
    if os.path.exists(FEEDBACK_LOG):
        with open(FEEDBACK_LOG) as f:
            log = json.load(f)
    else:
        log = []
    log.append(entry)
    with open(FEEDBACK_LOG, "w") as f:
        json.dump(log, f, indent=2)

def distillery_search_widget(df, key="dist_search", default="Ardbeg"):
    """
    Reusable fuzzy distillery search widget.
    Returns selected distillery name and logs feedback.
    """
    all_dists = sorted(df["distillery"].dropna().unique().tolist())
    query = st.text_input(
        "Distillery",
        value=default,
        placeholder="Type any part of the name...",
        key=key,
        help="Fuzzy search — 'glen drona', 'ardb', 'karu' all work",
    )
    best_match, candidates = fuzzy_distillery_search(query, all_dists)

    if best_match:
        coverage = get_distillery_coverage(best_match, df)
        # Show match confirmation
        if query.strip().lower() != best_match.lower():
            st.caption(f"Matched: **{best_match}**")
        # Show alternatives if close competitors exist
        if len(candidates) > 1:
            others = [f"{c[0]}" for c in candidates[1:4] if c[1] >= 55]
            if others:
                st.caption(f"Also try: {' · '.join(others)}")
        # Coverage warnings — useful for you as developer
        if coverage["thin_market"]:
            st.info(
                f"⚠️ **Thin market** — only {coverage['lot_count']} lots for "
                f"{best_match}. Model predictions may be unreliable.",
                icon=None,
            )
        if not coverage["has_ob_classifier"]:
            st.info(
                f"ℹ️ No OB expression classifier for {best_match}. "
                f"All OB lots use generic tier assignment.",
                icon=None,
            )
        # Log every successful match with coverage info
        log_distillery_feedback(query, best_match, coverage)
        return best_match, all_dists

    else:
        # No match found
        if query.strip():
            st.warning(
                f"No distillery found matching **'{query}'**. "
                f"Check spelling or try a partial name."
            )
            log_distillery_feedback(query, None, {
                "distillery": None,
                "lot_count": 0,
                "has_ob_classifier": False,
                "regime_coverage": 0,
                "thin_market": True,
            })
        return all_dists[0] if all_dists else None, all_dists

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🥃 Whisky Auction\nAnalytics")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["Price Estimator", "Market Overview", "Distillery Deep Dive"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("""
    <div style='font-family: IBM Plex Mono, monospace; font-size: 0.72rem; color: #888; line-height: 1.8'>
    115,561 lots<br>
    Auctions 154–177<br>
    Apr 2024 – Mar 2026<br>
    <br>
    Model: XGBoost<br>
    R² = 0.875<br>
    MAE = £60
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Load assets
# ---------------------------------------------------------------------------
df_raw = load_data()
df_enriched = load_enriched()

try:
    model, encoders = load_model()
    model_loaded = True
except Exception:
    model_loaded = False

# ---------------------------------------------------------------------------
# Helper: predict price
# ---------------------------------------------------------------------------
def predict_price(distillery, age, abv, volume, cask,
                  is_ob, bottling_year, market_regime,
                  effective_tier, is_closed, is_grain):
    if not model_loaded:
        return None, None, None

    le_dist = encoders["distillery"]
    le_cask = encoders["cask"]
    features = encoders["features"]

    ## Encode distillery — fallback to index 0 if unseen
    if distillery in le_dist.classes_:
        dist_enc = le_dist.transform([distillery])[0]
    else:
        dist_enc = 0

    # Encode cask — fallback to index 0 if unseen
    cask_map = {
        "Bourbon": "bourbon", "Sherry (Oloroso/PX)": "sherry oloroso",
        "Sherry": "sherry", "Port": "port", "Rum": "rum",
        "Wine": "wine", "Virgin Oak": "virgin oak",
        "Hogshead": "hogshead", "Other": "other", "Unknown": "bourbon",
    }
    cask_norm = cask_map.get(cask, "bourbon")
    if cask_norm in le_cask.classes_:
        cask_enc = le_cask.transform([cask_norm])[0]
    else:
        cask_enc = 0

    # ABV bin
    bins = [0, 40, 43, 46, 50, 55, 60, 70, 100]
    abv_bin = np.digitize(abv, bins) - 1

    # Recency — assume auction 177 (latest)
    auction_recency = 0

    row = {
        "age_years": age,
        "abv_bin": float(abv_bin),
        "volume_cl": volume,
        "distillery_enc": float(dist_enc),
        "cask_enc": float(cask_enc),
        "is_closed": float(is_closed),
        "is_grain": float(is_grain),
        "effective_tier": float(effective_tier),
        "auction_recency": float(auction_recency),
        "market_regime": float(market_regime),
    }

    X = pd.DataFrame([row])[features]
    log_pred = model.predict(X)[0]
    pred = np.exp(log_pred)

    # Rough confidence interval (±25% based on MAE of £60)
    lower = pred * 0.75
    upper = pred * 1.35

    return pred, lower, upper


# ===========================================================================
# PAGE 1 — PRICE ESTIMATOR
# ===========================================================================
if page == "Price Estimator":
    st.markdown("# Price Estimator")
    st.markdown("Predict the auction hammer price for a bottle based on its characteristics.")
    st.markdown("---")

    col_form, col_result = st.columns([1, 1], gap="large")

    with col_form:
        st.markdown("### Bottle Details")

        # Distillery — fuzzy search with feedback logging
        distillery, all_dists = distillery_search_widget(
            df_raw, key="estimator_dist", default="Ardbeg"
        )

        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("Age (years)", min_value=3, max_value=80, value=12)
        with col2:
            abv = st.number_input("ABV (%)", min_value=30.0, max_value=70.0, value=46.0, step=0.1)

        col3, col4 = st.columns(2)
        with col3:
            volume = st.selectbox("Volume (cl)", [70, 75, 50, 35, 20, 10, 5], index=0)
        with col4:
            cask = st.selectbox("Cask type", [
                "Bourbon", "Sherry (Oloroso/PX)", "Sherry", "Port",
                "Rum", "Wine", "Virgin Oak", "Hogshead", "Other", "Unknown"
            ])

        bottling_year = st.slider("Bottling year", 1970, 2025, 2015)

        st.markdown("### Classification")
        col5, col6 = st.columns(2)
        with col5:
            is_ob = st.toggle("Official Bottling (OB)", value=True)
        with col6:
            is_closed = st.toggle("Closed Distillery", value=False)

        market_regime = st.select_slider(
            "Market Regime",
            options=[1, 2, 3, 4],
            value=2,
            format_func=lambda x: REGIME_LABELS[x],
        )

        effective_tier = st.select_slider(
            "Expression Tier",
            options=[1, 2, 3, 4, 5],
            value=2,
            format_func=lambda x: {
                1: "1 — Standard", 2: "2 — Core range",
                3: "3 — Premium", 4: "4 — Prestige", 5: "5 — Legendary"
            }[x],
        )

        is_grain = st.toggle("Grain distillery", value=False)

        predict_btn = st.button("Estimate Price →", type="primary", use_container_width=True)

    with col_result:
        st.markdown("### Estimated Price")

        if predict_btn or True:  # show on load with defaults
            pred, lower, upper = predict_price(
                distillery, age, abv, volume, cask,
                is_ob, bottling_year, market_regime,
                effective_tier, is_closed, is_grain
            )

            if pred is not None:
                st.markdown(f"""
                <div class='price-display'>£{pred:,.0f}</div>
                <div class='price-range'>Range: £{lower:,.0f} – £{upper:,.0f}</div>
                """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                badge_class = REGIME_BADGE_CLASS[market_regime]
                st.markdown(f"""
                <span class='regime-badge {badge_class}'>{REGIME_LABELS[market_regime]}</span>
                """, unsafe_allow_html=True)
                st.markdown(f"*{REGIME_DESC[market_regime]}*")

                st.markdown("---")

                # Similar lots from database
                st.markdown("### Similar Lots")
                similar = df_raw[
                    (df_raw["distillery"] == distillery) &
                    (df_raw["age_years"].between(age - 3, age + 3)) &
                    (df_raw["price_70cl_adj"].notna())
                ].sort_values("price_70cl_adj", ascending=False).head(8)

                if len(similar) > 0:
                    display = similar[["title", "price_70cl_adj", "age_years", "abv"]].copy()
                    display.columns = ["Title", "Hammer (£)", "Age", "ABV%"]
                    display["Hammer (£)"] = display["Hammer (£)"].apply(lambda x: f"£{x:,.0f}")
                    st.dataframe(display, hide_index=True, use_container_width=True)
                else:
                    st.info("No similar lots found in database.")
            else:
                st.warning("Model not loaded. Place model_v6_final.pkl in the project folder.")

        # Regime explainer
        st.markdown("---")
        st.markdown("### Regime Guide")
        for r, label in REGIME_LABELS.items():
            badge = REGIME_BADGE_CLASS[r]
            st.markdown(f"<span class='regime-badge {badge}'>{label}</span> {REGIME_DESC[r]}<br>", unsafe_allow_html=True)


# ===========================================================================
# PAGE 2 — MARKET OVERVIEW
# ===========================================================================
elif page == "Market Overview":
    st.markdown("# Market Overview")
    st.markdown("115,561 lots from Scotch Whisky Auctions, April 2024 – March 2026.")
    st.markdown("---")

    df = df_raw.copy()

    # Filter to model-eligible lots only
    df_model = df[
        df["winning_bid"].notna() &
        df["price_70cl_adj"].notna() &
        (df["price_70cl_adj"] > 0)
    ].copy()

    # --- Row 1: Summary metrics ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total lots", f"{len(df_model):,}")
    with col2:
        st.metric("Median price", f"£{df_model['price_70cl_adj'].median():,.0f}")
    with col3:
        st.metric("Distilleries", f"{df_model['distillery'].nunique():,}")
    with col4:
        auctions = df_model["auction_number"].nunique() if "auction_number" in df_model.columns else 24
        st.metric("Auctions covered", f"{auctions}")

    st.markdown("---")

    # --- Row 2: Regime distribution ---
    st.markdown("### Market Regime Distribution")
    st.markdown("Each lot is classified into one of four demand-side regimes based on who is bidding and why.")

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        regime_stats = df_model.groupby("market_regime").agg(
            lots=("price_70cl_adj", "count"),
            median=("price_70cl_adj", "median"),
        ).reset_index()
        regime_stats["label"] = regime_stats["market_regime"].map(REGIME_LABELS)
        regime_stats["colour"] = regime_stats["market_regime"].map(REGIME_COLOURS)

        fig = px.bar(
            regime_stats, x="label", y="lots",
            color="market_regime",
            color_discrete_map=REGIME_COLOURS,
            labels={"label": "", "lots": "Number of lots"},
            title="Lots by regime",
        )
        fig.update_layout(
            showlegend=False,
            plot_bgcolor="white",
            paper_bgcolor="white",
            font_family="IBM Plex Sans",
            title_font_family="Playfair Display",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        fig2 = px.box(
            df_model[df_model["price_70cl_adj"] <= 2000],
            x="market_regime", y="price_70cl_adj",
            color="market_regime",
            color_discrete_map=REGIME_COLOURS,
            labels={"market_regime": "Regime", "price_70cl_adj": "Price per 70cl (£)"},
            title="Price distribution by regime (capped at £2,000)",
        )
        fig2.update_layout(
            showlegend=False,
            plot_bgcolor="white",
            paper_bgcolor="white",
            font_family="IBM Plex Sans",
            title_font_family="Playfair Display",
        )
        fig2.update_xaxes(
            tickvals=[1, 2, 3, 4],
            ticktext=["R1\nLuxury", "R2\nGeek", "R3\nHoly Grail", "R4\nConvergence"]
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # --- Row 3: Age vs price scatter ---
    st.markdown("### Age vs Price")

    df_scatter = df_model[
        df_model["age_years"].notna() &
        (df_model["age_years"] <= 60) &
        (df_model["price_70cl_adj"] <= 3000)
    ].sample(min(5000, len(df_model)), random_state=42)

    fig3 = px.scatter(
        df_scatter,
        x="age_years", y="price_70cl_adj",
        color="market_regime",
        color_discrete_map=REGIME_COLOURS,
        opacity=0.4,
        labels={"age_years": "Age (years)", "price_70cl_adj": "Price per 70cl (£)",
                "market_regime": "Regime"},
        title="Age vs hammer price coloured by market regime (sample of 5,000 lots)",
        hover_data=["distillery"] if "distillery" in df_scatter.columns else None,
    )
    fig3.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_family="IBM Plex Sans",
        title_font_family="Playfair Display",
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")

    # --- Row 4: Top distilleries ---
    st.markdown("### Top Distilleries by Median Price")

    top_dists = (
        df_model[df_model["distillery"].notna()]
        .groupby("distillery")
        .agg(lots=("price_70cl_adj", "count"),
             median=("price_70cl_adj", "median"))
        .query("lots >= 20")
        .sort_values("median", ascending=False)
        .head(20)
        .reset_index()
    )

    fig4 = px.bar(
        top_dists,
        x="median", y="distillery",
        orientation="h",
        labels={"median": "Median price per 70cl (£)", "distillery": ""},
        title="Top 20 distilleries by median hammer price (min 20 lots)",
        color="median",
        color_continuous_scale=[[0, "#e8e0d0"], [1, "#1a1a1a"]],
    )
    fig4.update_layout(
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_family="IBM Plex Sans",
        title_font_family="Playfair Display",
        yaxis={"categoryorder": "total ascending"},
        height=550,
    )
    fig4.update_coloraxes(showscale=False)
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")

    # --- Row 5: Price over auctions ---
    st.markdown("### Price Trend Over Auctions")

    if "auction_number" in df_model.columns:
        auction_trend = (
            df_model.groupby("auction_number")
            .agg(median=("price_70cl_adj", "median"),
                 lots=("price_70cl_adj", "count"))
            .reset_index()
        )

        fig5 = px.line(
            auction_trend, x="auction_number", y="median",
            labels={"auction_number": "Auction number", "median": "Median price per 70cl (£)"},
            title="Median hammer price per auction (all lots)",
            markers=True,
        )
        fig5.update_traces(line_color="#1a1a1a", marker_color="#1a1a1a")
        fig5.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            font_family="IBM Plex Sans",
            title_font_family="Playfair Display",
        )
        st.plotly_chart(fig5, use_container_width=True)


# ===========================================================================
# PAGE 3 — DISTILLERY DEEP DIVE
# ===========================================================================
elif page == "Distillery Deep Dive":
    st.markdown("# Distillery Deep Dive")
    st.markdown("---")

    df = df_raw.copy()

    col_select, _ = st.columns([1, 2])
    with col_select:
        selected_dist, all_dists = distillery_search_widget(
            df, key="deep_dive_dist", default="Ardbeg"
        )

    dist_df = df[
        (df["distillery"] == selected_dist) &
        df["price_70cl_adj"].notna()
    ].copy()

    if len(dist_df) == 0:
        st.warning(f"No data found for {selected_dist}.")
    else:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total lots", f"{len(dist_df):,}")
        with col2:
            st.metric("Median price", f"£{dist_df['price_70cl_adj'].median():,.0f}")
        with col3:
            st.metric("Max price", f"£{dist_df['price_70cl_adj'].max():,.0f}")
        with col4:
            if "is_closed" in dist_df.columns:
                closed = dist_df["is_closed"].iloc[0]
                st.metric("Status", "Closed" if closed else "Operational")

        st.markdown("---")

        col_left, col_right = st.columns([1, 1], gap="large")

        # Price distribution
        with col_left:
            st.markdown("### Price Distribution")
            cap = dist_df["price_70cl_adj"].quantile(0.95)
            fig = px.histogram(
                dist_df[dist_df["price_70cl_adj"] <= cap],
                x="price_70cl_adj",
                nbins=40,
                labels={"price_70cl_adj": "Price per 70cl (£)", "count": "Lots"},
                title=f"{selected_dist} — price distribution (95th pct cap)",
                color_discrete_sequence=["#1a1a1a"],
            )
            fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font_family="IBM Plex Sans",
                title_font_family="Playfair Display",
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

        # Regime breakdown
        with col_right:
            st.markdown("### Regime Breakdown")
            regime_breakdown = (
                dist_df.groupby("market_regime")
                .agg(lots=("price_70cl_adj", "count"),
                     median=("price_70cl_adj", "median"))
                .reset_index()
            )
            regime_breakdown["label"] = regime_breakdown["market_regime"].map(REGIME_LABELS)

            fig2 = px.bar(
                regime_breakdown, x="label", y="lots",
                color="market_regime",
                color_discrete_map=REGIME_COLOURS,
                labels={"label": "", "lots": "Lots"},
                title=f"{selected_dist} — lots by regime",
                text="lots",
            )
            fig2.update_layout(
                showlegend=False,
                plot_bgcolor="white",
                paper_bgcolor="white",
                font_family="IBM Plex Sans",
                title_font_family="Playfair Display",
            )
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")

        # Age vs price for this distillery
        st.markdown("### Age vs Price")
        dist_scatter = dist_df[
            dist_df["age_years"].notna() &
            (dist_df["age_years"] <= 60)
        ]
        if len(dist_scatter) > 0:
            fig3 = px.scatter(
                dist_scatter,
                x="age_years", y="price_70cl_adj",
                color="market_regime",
                color_discrete_map=REGIME_COLOURS,
                hover_data=["title"],
                labels={"age_years": "Age (years)",
                        "price_70cl_adj": "Price per 70cl (£)",
                        "market_regime": "Regime"},
                title=f"{selected_dist} — age vs price",
            )
            fig3.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font_family="IBM Plex Sans",
                title_font_family="Playfair Display",
            )
            st.plotly_chart(fig3, use_container_width=True)

        st.markdown("---")

        # Most expensive lots table
        st.markdown("### Most Expensive Lots")
        top_lots = (
            dist_df.sort_values("price_70cl_adj", ascending=False)
            .head(15)[["title", "winning_bid", "price_70cl_adj",
                        "age_years", "abv", "auction_number"]]
            .copy()
        )
        top_lots.columns = ["Title", "Hammer (£)", "Per 70cl (£)",
                             "Age", "ABV%", "Auction"]
        top_lots["Hammer (£)"] = top_lots["Hammer (£)"].apply(
            lambda x: f"£{x:,.0f}" if pd.notna(x) else "—"
        )
        top_lots["Per 70cl (£)"] = top_lots["Per 70cl (£)"].apply(
            lambda x: f"£{x:,.0f}" if pd.notna(x) else "—"
        )
        top_lots["Age"] = top_lots["Age"].apply(
            lambda x: f"{x:.0f}yo" if pd.notna(x) else "NAS"
        )
        top_lots["ABV%"] = top_lots["ABV%"].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "—"
        )
        st.dataframe(top_lots, hide_index=True, use_container_width=True)

        # Price by auction trend
        if "auction_number" in dist_df.columns:
            st.markdown("---")
            st.markdown("### Price Trend Over Auctions")
            auction_trend = (
                dist_df.groupby("auction_number")
                .agg(median=("price_70cl_adj", "median"),
                     lots=("price_70cl_adj", "count"))
                .reset_index()
                .query("lots >= 3")
            )
            if len(auction_trend) > 2:
                fig4 = px.line(
                    auction_trend, x="auction_number", y="median",
                    labels={"auction_number": "Auction number",
                            "median": "Median price per 70cl (£)"},
                    title=f"{selected_dist} — median price per auction",
                    markers=True,
                )
                fig4.update_traces(line_color="#1a1a1a", marker_color="#1a1a1a")
                fig4.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    font_family="IBM Plex Sans",
                    title_font_family="Playfair Display",
                )
                st.plotly_chart(fig4, use_container_width=True)