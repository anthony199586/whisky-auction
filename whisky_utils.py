"""
whisky_utils.py
Shared enrichment functions, reference data, and series classification
for the whisky auction price analysis project.
"""

from matplotlib.pyplot import title
import pandas as pd
import re
import os

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

KNOWN_DISTILLERIES = [
    # Islay
    "Ardbeg", "Laphroaig", "Lagavulin", "Bowmore", "Bunnahabhain",
    "Bruichladdich", "Kilchoman", "Caol Ila", "Ardnahoe", "Port Ellen",
    # Campbeltown
    "Springbank", "Longrow", "Hazelburn", "Glengyle", "Glen Scotia",
    "Kilkerran",
    # Highland
    "Dalmore", "Glenmorangie", "Balblair", "Clynelish", "Brora",
    "Old Pulteney", "Ben Nevis", "Oban", "Aberfeldy", "Blair Athol",
    "Edradour", "Glenturret", "Tomatin", "Talisker", "Highland Park",
    "Glengoyne", "Glendronach", "Benriach", "Daftmill", "Ardnamurchan",
    "Annandale", "Wolfburn", "Torabhaig", "Raasay","Glenglassaugh", "Fettercairn",
    # Speyside
    "Macallan", "Glenfarclas", "Aberlour", "Glenlivet", "Glenfiddich",
    "Balvenie", "Mortlach", "Craigellachie", "Dailuaine", "Linkwood",
    "Longmorn", "Strathisla", "Glenlossie", "Mannochmore", "Speyburn",
    "Knockando", "Benromach", "Cragganmore", "Cardhu", "Glen Grant",
    "Glen Moray", "Glenallachie", "Tamdhu", "Inchgower", "Kingsbarns",
    "Lindores",
    # Lowland
    "Rosebank", "Auchentoshan", "Glenkinchie", "Bladnoch",
    "Littlemill", "St Magdalene", "Inverleven",
    # Islands
    "Jura", "Isle of Jura", "Tobermory", "Ledaig",
    # New/craft Scottish
    "Nc'nean", "Ncnean", "Strathearn", "Waterford",
    # Japanese
    "Karuizawa", "Yamazaki", "Hakushu", "Hibiki",
    "Yoichi", "Miyagikyo", "Nikka", "Suntory",
    "Hanyu", "Chichibu", "Akkeshi", "Shizuoka", "Shirakawa",
    # Asian
    "Kavalan", "Nantou", "Amrut", "Paul John",
    # Irish
    "Midleton", "Redbreast", "Green Spot", "Teeling", "Dingle",
    "West Cork",
    # American
    "Jack Daniel's", "Buffalo Trace", "W.L. Weller", "Weller",
    "Eagle Rare", "Four Roses", "Maker's Mark", "Wild Turkey",
    "George T Stagg", "Stagg", "Heaven Hill",
    # Caribbean / other
    "Caroni",
    # Closed Scottish
    "Convalmore", "Banff", "Dallas Dhu", "Glen Albyn", "Glen Mhor",
    "Glenury Royal", "Imperial", "Lochside", "Caperdonich",
    "North Port", "Millburn", "Cambus", "Kinclaith", "Ladyburn",
    "Ben Wyvis", "Glenugie", "Glenlochy", "Mosstowie",
    "Glenflagler", "Killyloch", "Dumbarton", "Carsebridge",
    "Garnheath", "Coleburn", "Linlithgow",
]

REGION_WORDS = {
    "speyside", "islay", "highland", "highlands",
    "lowland", "lowlands", "campbeltown", "islands",
    "orkney", "skye", "japanese", "irish", "american"
}

KNOWN_DISTILLERIES = [d for d in KNOWN_DISTILLERIES
                      if d.lower() not in REGION_WORDS]

CLOSED_DISTILLERIES = {
    # Scottish
    "Port Ellen", "Brora", "Rosebank", "Littlemill",
    "St Magdalene", "Inverleven", "Convalmore", "Banff",
    "Dallas Dhu", "Glen Albyn", "Glen Mhor", "Glenury Royal",
    "Imperial", "Lochside", "Caperdonich", "Coleburn",
    "North Port", "Millburn", "Cambus", "Carsebridge",
    "Ladyburn", "Garnheath", "Ben Wyvis", "Glenugie",
    "Glenlochy", "Mosstowie", "Glenflagler", "Killyloch",
    "Dumbarton", "Kinclaith", "Linlithgow","Glenglassaugh",
    # Japanese
    "Karuizawa", "Hanyu", "Shirakawa",
    # Caribbean
    "Caroni",
}

GRAIN_DISTILLERIES = {
    "Dumbarton", "Cambus", "Carsebridge", "Invergordon",
    "North British", "Caledonian", "Garnheath", "Girvan",
    "Loch Lomond", "Strathclyde", "Cameronbridge",
    "Port Dundas", "Inchgower",  # debatable
}

def is_grain_distillery(distillery):
    if not distillery:
        return False
    return str(distillery) in GRAIN_DISTILLERIES

KNOWN_BOTTLERS = [
    "Gordon & MacPhail", "G&M",
    "Cadenhead's", "Cadenheads", "Cadenhead",
    "Signatory", "Signatory Vintage",
    "Berry Bros & Rudd", "Berry Bros", "Berry Brothers",
    "Douglas Laing", "Douglas Laing & Co",
    "Hunter Laing", "Hunter Laing & Co",
    "Duncan Taylor", "Murray McDavid",
    "Adelphi", "Blackadder", "Hart Brothers",
    "Old Malt Cask", "Old & Rare", "Platinum Old & Rare",
    "First Editions", "Remarkable Regional Malts",
    "SMWS", "Scotch Malt Whisky Society",
    "Whisky Agency", "The Whisky Agency",
    "Samaroli", "Moon Import", "Sestante", "Silver Seal",
    "Malts of Scotland", "Sansibar",
    "Number One Drinks", "Number One Drinks Company",
    "Compass Box",
    "That Boutique-y Whisky Company", "Boutique-y Whisky",
    "Master of Malt", "Elixir Distillers",
    "A D Rattray", "AD Rattray",
    "Scott's Selection", "Scotts Selection",
    "James MacArthur", "Chieftain's", "Chieftains",
    "Dun Bheagan", "Ian Macleod", "Ian MacLeod",
    "Gleann Mor", "North Star", "Chapter 7",
    "Carn Mor", "Decadent Drinks", "Kingsbury",
    "Wilson & Morgan", "Archives", "Liquid Treasures",
    "James Eadie", "Alistair Walker",
    "American Single Cask", "Single Cask Nation",
    "Wealth Solutions",
]

UNDISCLOSED_INDICATORS = [
    "undisclosed", "secret", "unknown distillery",
    "unnamed", "confidential"
]

BOTTLER_TIER = {
    # Tier 5 — legendary Italian bottlers
    "Samaroli": 5, "Moon Import": 5, "Sestante": 5, "Silver Seal": 5,
    # Tier 4 — prestige IBs
    "Gordon & MacPhail": 4, "Cadenhead's": 4, "Cadenhead": 4,
    "Signatory": 4, "Berry Bros & Rudd": 4, "Berry Bros": 4,
    "Adelphi": 4, "Blackadder": 4, "Kingsbury": 4, "Old & Rare": 4,
    "Hunter Laing": 4,
    # Tier 3 — established IBs
    "Hart Brothers": 3, "Douglas Laing": 3,
    "Duncan Taylor": 3, "Murray McDavid": 3,
    "Old Malt Cask": 3, "First Editions": 3,
    "SMWS": 3, "Scotch Malt Whisky Society": 3,
    "Malts of Scotland": 3, "James MacArthur": 3,
    "Wilson & Morgan": 3, "Chieftain's": 3,
    # Tier 2 — accessible IBs
    "North Star": 2, "Carn Mor": 2, "James Eadie": 2,
    "Master of Malt": 2, "Chapter 7": 2, "Compass Box": 2,
    "That Boutique-y Whisky Company": 2, "Boutique-y Whisky": 2,
}

LEGENDARY_BOTTLER_TIER_THRESHOLD = 4

# Volume premium factors relative to 70cl baseline
# Derived empirically from auction price data
# Factor > 1 means that format commands a per-ml premium
VOLUME_PREMIUMS = {
    3:   210/110,
    5:   180/110,
    10:  150/110,
    20:  158/110,
    35:  130/110,
    50:  105/110,
    60:   99/110,
    70:    1.0,
    75:  103/110,
    76:   88/110,
}


# ---------------------------------------------------------------------------
# Price normalisation
# ---------------------------------------------------------------------------

def price_per_70cl_adjusted(price, volume_cl):
    """
    Normalise hammer price to 70cl equivalent.
    Formula: price * (70/vol) / premium_factor
    Accounts for both volume difference AND format collectibility premium.
    Returns original price if volume is unknown or invalid.
    """
    if pd.isna(price) or pd.isna(volume_cl):
        return price
    vol = int(volume_cl)
    if vol <= 0:
        return price
    premium_factor = VOLUME_PREMIUMS.get(vol, vol / 70)
    volume_ratio   = 70 / vol
    return price * volume_ratio / premium_factor


# ---------------------------------------------------------------------------
# Date extraction
# ---------------------------------------------------------------------------

def extract_year(date_str):
    if not date_str or pd.isna(date_str):
        return None, False
    date_str_lower = str(date_str).strip().lower()
    if any(w in date_str_lower for w in
           ["pre-war", "prewar", "pre war"]):
        return 1938, True
    is_approximate = any(w in date_str_lower for w in
                         ["circa", "around", "approx", "c.", "ca."])
    decade = re.search(r'\b(19\d0|20[012]0)s\b', date_str_lower)
    if decade:
        return int(decade.group(1)), True
    four_digit = re.findall(r'\b(19\d{2}|20\d{2})\b', date_str_lower)
    if not four_digit:
        return None, False
    years = [int(y) for y in four_digit]
    if len(years) > 1:
        return min(years), True
    return years[0], is_approximate


# ---------------------------------------------------------------------------
# Enrichment functions
# ---------------------------------------------------------------------------

def extract_distillery(title):
    if not title:
        return None
    title_lower = title.lower()
    if any(ind in title_lower for ind in UNDISCLOSED_INDICATORS):
        return None
    for distillery in KNOWN_DISTILLERIES:
        if distillery.lower() in title_lower:
            if distillery.lower() not in REGION_WORDS:
                return distillery
    return None

BOTTLER_ALIASES = {
    "Cadenheads":       "Cadenhead's",
    "Cadenhead":        "Cadenhead's",
    "Berry Bros":       "Berry Bros & Rudd",
    "Berry Brothers":   "Berry Bros & Rudd",
    "G&M":              "Gordon & MacPhail",
    "Signatory Vintage":"Signatory",
    "Douglas Laing & Co": "Douglas Laing",
    "Hunter Laing & Co":  "Hunter Laing",
    "Scotch Malt Whisky Society": "SMWS",
    "That Boutique-y Whisky Company": "Boutique-y Whisky",
}

def extract_bottler(title):
    if not title:
        return None
    title_lower = title.lower()
    for bottler in KNOWN_BOTTLERS:
        if bottler.lower() in title_lower:
            # Normalise to canonical name
            return BOTTLER_ALIASES.get(bottler, bottler)
    return None


def is_ob(title, bottler):
    if bottler and not pd.isna(bottler):
        return False
    return True


def is_closed_distillery(distillery):
    if not distillery:
        return False
    return distillery in CLOSED_DISTILLERIES


def normalise_cask_type(cask):
    if pd.isna(cask):
        return "unknown"
    cask_lower = cask.lower()
    if any(x in cask_lower for x in ["port", "porto"]):
        return "port"
    if "rum" in cask_lower:
        return "rum"
    if any(x in cask_lower for x in ["wine", "burgundy", "bordeaux",
                                       "sauternes", "madeira", "marsala"]):
        return "wine"
    if any(x in cask_lower for x in ["virgin", "new oak", "new american"]):
        return "virgin oak"
    if any(x in cask_lower for x in ["oloroso", "px", "pedro",
                                       "amontillado", "fino"]):
        return "sherry oloroso"
    if "sherry" in cask_lower:
        return "sherry"
    if any(x in cask_lower for x in ["bourbon", "american oak",
                                       "american white oak"]):
        return "bourbon"
    if "hogshead" in cask_lower:
        return "hogshead"
    if "butt" in cask_lower:
        return "butt"
    if "barrel" in cask_lower:
        return "barrel"
    if "puncheon" in cask_lower:
        return "puncheon"
    if any(x in cask_lower for x in ["quarter", "octave"]):
        return "small cask"
    return "other"

# ---------------------------------------------------------------------------
# OB series detection
# ---------------------------------------------------------------------------

def detect_lagavulin_expression(title, abv,
                                 bottling_year, age_years):
    title_lower = str(title).lower() if title else ""
    has_age  = age_years is not None and not pd.isna(age_years)
    has_year = (bottling_year is not None and
                not pd.isna(bottling_year))

    # Tier 5 — old era White Horse labels
    if any(kw in title_lower for kw in
            ["26 2/3", "circa 1970", "circa 1980"]):
        return "old era ob", 5

    # Old distillation year
    year_match = re.search(r'\b(19[6-8][0-9])\b', title_lower)
    if year_match and int(year_match.group(1)) <= 1985:
        return "vintage ob", 5

    # Tier 4 — prestige releases
    if has_age and age_years >= 25:
        return "ultra aged", 4
    if any(kw in title_lower for kw in
           ["feis ile", "feis ìle", "special release",
            "syndicate", "prima", "ultima"]):
        return "special release", 4
    if any(kw in title_lower for kw in
           ["25 year", "30 year", "37 year",
            "40 year", "29 year"]):
        return "ultra aged", 4

    # Tier 3 — premium
    if any(kw in title_lower for kw in
           ["distillers edition", "distiller's edition",
            "12 year", "cask strength"]):
        return "premium core", 3

    # Tier 2 — core range
    if any(kw in title_lower for kw in
           ["16 year", "8 year", "select"]):
        return "core range", 2

    return "standard ob", 2


def detect_ardbeg_expression(title, abv,
                              bottling_year, age_years):
    title_lower = str(title).lower() if title else ""
    has_age  = age_years is not None and not pd.isna(age_years)
    has_year = (bottling_year is not None and
                not pd.isna(bottling_year))

    # Tier 5 — pre-closure era (distilled <=1981)
    year_match = re.search(r'\b(197[0-9]|198[01])\b',
                           title_lower)
    if year_match:
        return "pre-closure era", 5
    if any(kw in title_lower for kw in
           ["26 2/3", "circa 1970", "provenance",
            "double barrel"]):
        return "pre-closure era", 5

    # Tier 4 — truly prestige:
    # Committee Reserve, early single cask Feis Ile,
    # very old age statements, rare vintage releases
    if any(kw in title_lower for kw in
           ["committee reserve", "21 year", "25 year",
            "very young", "still young", "almost there",
            "renaissance", "lord of the isles",
            "airigh nam beist"]):
        return "prestige release", 4

    # Early single cask Feis Ile (pre-2013 bottling)
    if any(kw in title_lower for kw in
           ["feis ile", "feis ìle"]):
        if has_year and bottling_year <= 2012:
            return "prestige release", 4
        return "annual limited", 3

    # Single cask releases (non-Feis Ile)
    if "single cask" in title_lower:
        if has_age and age_years >= 15:
            return "prestige release", 4
        return "annual limited", 3

    # Committee bottlings (not Reserve — those are tier 4)
    if "committee" in title_lower:
        return "annual limited", 3

    # Tier 3 — premium named expressions and
    # modern annual limited releases
    if any(kw in title_lower for kw in
           ["uigeadail", "corryvreckan",
            "blaaack", "grooves", "drum", "kelpie",
            "galileo", "supernova", "perpetuum",
            "alligator", "dark cove", "traigh bhan",
            "hypernova", "ardcore", "an oa",
            "rollercoaster"]):
        return "premium core", 3

    # Tier 2 — core range
    if any(kw in title_lower for kw in
           ["10 year", "wee beastie", "5 year",
            "8 year"]):
        return "core range", 2

    return "standard ob", 2


def detect_highland_park_expression(title, abv,
                                     bottling_year,
                                     age_years):
    title_lower = str(title).lower() if title else ""
    has_age  = age_years is not None and not pd.isna(age_years)
    has_year = (bottling_year is not None and
                not pd.isna(bottling_year))

    # Tier 5 — old era pre-1979
    if any(kw in title_lower for kw in
           ["26 2/3", "circa 1970", "circa 1960"]):
        return "old era ob", 5
    year_match = re.search(r'\b(19[5-7][0-9])\b',
                           title_lower)
    if year_match and int(year_match.group(1)) <= 1979:
        return "vintage ob", 5

    # Tier 4 — prestige age-stated and limited
    if has_age and age_years >= 30:
        return "ultra aged", 4
    if any(kw in title_lower for kw in
           ["40 year", "50 year", "30 year",
            "25 year", "full volume",
            "ambassador cask",  # moved from tier 1
            "bicentenary", "dark origins",
            "warriors series", "valknut",
            "odin", "thor", "loki", "freya",
            "single cask", "feis ile"]):
        return "prestige release", 4

    # Tier 3 — premium
    if any(kw in title_lower for kw in
           ["18 year", "21 year", "einar",
            "svein", "ingolfur"]):
        return "premium core", 3

    # Tier 2 — core range
    if any(kw in title_lower for kw in
           ["12 year", "10 year", "15 year",
            "magnus", "viking honour",
            "viking legend", "viking pride"]):
        return "core range", 2

    # Removed "ambassador" from tier 1 — 
    # ambassador without "cask" is still tier 2
    return "standard ob", 2


def detect_glendronach_expression(title, abv,
                                   bottling_year,
                                   age_years):
    title_lower = str(title).lower() if title else ""
    has_age  = age_years is not None and not pd.isna(age_years)
    has_year = (bottling_year is not None and
                not pd.isna(bottling_year))

    # Tier 5 — old era pre-1978
    year_match = re.search(r'\b(19[6-7][0-9])\b', title_lower)
    if year_match and int(year_match.group(1)) <= 1978:
        return "vintage ob", 5

    # Tier 4 — prestige releases
    if has_age and age_years >= 25:
        return "ultra aged", 4
    if any(kw in title_lower for kw in
           ["parliament", "allardice",
            "recherche", "grandeur",
            "single cask", "batch",
            "master vintage", "aged 25",
            "aged 30", "aged 33"]):
        return "prestige release", 4

    # Old vintage year (1979-1990)
    if year_match and int(year_match.group(1)) <= 1990:
        return "vintage ob", 4

    # Tier 3 — premium
    if any(kw in title_lower for kw in
           ["revival", "18 year", "21 year",
            "peated", "benriach"]):
        return "premium core", 3

    # Tier 2 — core range
    if any(kw in title_lower for kw in
           ["12 year", "15 year", "original ten",
            "8 year"]):
        return "core range", 2

    return "standard ob", 2


def detect_glenfarclas_expression(title, abv,
                                   bottling_year,
                                   age_years):
    title_lower = str(title).lower() if title else ""
    has_age  = age_years is not None and not pd.isna(age_years)
    has_year = (bottling_year is not None and
                not pd.isna(bottling_year))

    # Tier 5 — Family Collector Series and old vintages
    if any(kw in title_lower for kw in
           ["family collector", "collector series",
            "1956", "1957", "1958", "1959",
            "1960", "1961", "1962", "1963",
            "1964", "1965", "1966"]):
        return "family collector", 5

    year_match = re.search(r'\b(19[5-6][0-9])\b', title_lower)
    if year_match and int(year_match.group(1)) <= 1966:
        return "vintage ob", 5

    # Tier 4 — Family Casks, very old age statements
    if any(kw in title_lower for kw in
           ["family cask", "family casks",
            "50 year", "58 year", "60 year"]):
        return "family casks", 4
    if has_age and age_years >= 40:
        return "ultra aged", 4

    # Old vintage year (1967-1980)
    if year_match:
        dist_year = int(year_match.group(1))
        if dist_year <= 1980:
            return "vintage ob", 4

    # Tier 3 — premium age statements
    if any(kw in title_lower for kw in
           ["25 year", "30 year", "40 year",
            "105", "heritage", "175th"]):
        return "premium core", 3

    if has_age and age_years >= 25:
        return "premium core", 3

    # Tier 2 — core range
    if any(kw in title_lower for kw in
           ["10 year", "12 year", "15 year",
            "17 year", "18 year", "21 year"]):
        return "core range", 2

    return "standard ob", 2


# ---------------------------------------------------------------------------
# IB series detection
# ---------------------------------------------------------------------------

def detect_cadenhead_series(title, abv, bottling_year):
    """
    Classify Cadenhead bottlings by series using title keywords
    and era-based ABV/year inference.
    Tier 5: Tall (pre-1977) and Dumpy (1977-1991) — legendary
    Tier 4: Authentic Collection, anniversary bottlings
    Tier 3: Chairman's Stock, Warehouse Tasting, Campbeltown Malts
    Tier 2: Enigma, Small Batch, Cask Ends, World Whiskies
    Tier 1: Standard / unclassified
    """
    title_lower = str(title).lower() if title else ""
    has_abv  = abv is not None and not pd.isna(abv)
    has_year = bottling_year is not None and not pd.isna(bottling_year)

    # Explicit keyword detection (highest priority)
    if any(kw in title_lower for kw in ["dumpy", "brown dumpy"]):
        return "dumpy", 5

    # Dumpy era inference: 45.7% or 46% ABV, bottled 1977-1991
    if has_abv and has_year:
        if abv in [45.7, 46.0] and bottling_year <= 1991:
            return "dumpy (inferred)", 5

    # Tall bottle era: pre-1977, no ABV (labels didn't always state it)
    if has_year and bottling_year < 1977 and (not has_abv or pd.isna(abv)):
        return "tall (inferred)", 5

    # Anniversary series
    if any(kw in title_lower for kw in ["175th anniversary", "175th"]):
        return "175th anniversary", 4
    if any(kw in title_lower for kw in ["150th anniversary", "150th"]):
        return "150th anniversary", 4
    if "authentic collection" in title_lower:
        return "authentic collection", 4

    # Tier 3 named series
    if any(kw in title_lower for kw in
           ["chairman's stock", "chairmans stock"]):
        return "chairmans stock", 3
    if "warehouse tasting" in title_lower:
        return "warehouse tasting", 3
    if any(kw in title_lower for kw in
           ["campbeltown malts festival", "campbeltown malt festival"]):
        return "campbeltown malts", 3

    # Tier 2 named series
    if "enigma" in title_lower:
        return "enigma", 2
    if "small batch" in title_lower:
        return "small batch", 2
    if "cask ends" in title_lower:
        return "cask ends", 3  # was 2
    if "world whisk" in title_lower:
        return "world whiskies", 2
    if "original collection" in title_lower:
        return "original collection", 2

    return "standard", 1


def detect_signatory_series(title, abv, bottling_year, volume_cl):
    title_lower = str(title).lower() if title else ""
    has_abv  = abv is not None and not pd.isna(abv)
    has_year = bottling_year is not None and not pd.isna(bottling_year)
    has_vol  = volume_cl is not None and not pd.isna(volume_cl)

    # Named series — highest priority
    if "rare reserve" in title_lower:
        return "rare reserve", 4
    if "silent stills" in title_lower:
        return "silent stills", 4
    if any(kw in title_lower for kw in
           ["cask strength collection", "straight from the cask"]):
        return "cask strength collection", 4
    if "symington" in title_lower:
        return "symingtons choice", 3
    if any(kw in title_lower for kw in
           ["un-chillfiltered collection", "unchillfiltered collection",
            "un chillfiltered"]):
        return "un-chillfiltered collection", 3
    if any(kw in title_lower for kw in
           ["decanter collection", "ibisco"]):
        return "decanter collection", 3

    # Anniversary releases — prestige commemorative
    if any(kw in title_lower for kw in
           ["anniversary", "30th", "35th", "40th"]):
        return "anniversary release", 4

    # 100 Proof — new 2024 affordable series at exactly 57.1%
    if any(kw in title_lower for kw in
       ["100 proof", "100º proof", "100° proof",
        "100° edition", "100º edition",
        "100&ordm;", "100 edition"]):
        return "100 proof", 2
    # Also catch by ABV if bottling year 2024+
    if (has_abv and abv == 57.1 and
            has_year and bottling_year >= 2024):
        return "100 proof", 2

    if "86 proof" in title_lower:
        return "86 proof", 2
    if any(kw in title_lower for kw in ["dun eideen", "dun eideann"]):
        return "dun eideen", 2
    if "small batch" in title_lower:
        return "small batch", 2

    # Era-based inference
    if has_year and bottling_year <= 1995:
        if has_vol and volume_cl == 75:
            return "ink pot / early (75cl)", 5
        return "ink pot / early", 4

    if has_year and 1996 <= bottling_year <= 2005:
        if has_vol and volume_cl == 75 and has_abv and 50 <= abv <= 65:
            return "dumpy (inferred)", 5
        if has_abv and abv == 43.0:
            return "vintage collection", 2
        if has_abv and abv == 46.0:
            return "un-chillfiltered (inferred)", 3
        return "early cask strength", 3

    # Modern era: high ABV cask strength = likely Cask Strength Collection
    if has_abv and abv >= 50 and has_year and bottling_year >= 2006:
        if not (abv == 57.1 and bottling_year >= 2024):
            return "cask strength (inferred)", 3

    # Modern era by ABV
    if has_abv and abv == 46.0:
        return "un-chillfiltered (inferred)", 3
    if has_abv and abv == 43.0:
        return "vintage collection", 2

    return "standard", 1


def detect_gm_series(title, abv, bottling_year):
    title_lower = str(title).lower() if title else ""
    has_year = bottling_year is not None and not pd.isna(bottling_year)
    has_abv  = abv is not None and not pd.isna(abv)

    # Tier 5
    if "generations" in title_lower:
        return "generations", 5
    if any(kw in title_lower for kw in
           ["book of kells", "dram takers"]):
        return "book of kells", 5
    if any(kw in title_lower for kw in
           ["mr george", "mr. george"]):
        return "mr george legacy", 5

    # Pre-1950 distillation vintage
    year_match = re.search(
        r'\b(19[0-4][0-9])\b', str(title) if title else ""
    )
    if year_match:
        dist_year = int(year_match.group(1))
        if dist_year <= 1950:
            return "old era pre-1950", 5
        if dist_year <= 1965:
            return "old era (inferred)", 4

    # Tier 4
    if "private collection" in title_lower:
        return "private collection", 4
    if any(kw in title_lower for kw in
           ["rare old", "rare vintage"]):
        return "rare old", 4
    if "recollection" in title_lower:
        return "recollection series", 4

    # Anniversary editions
    if any(kw in title_lower for kw in
           ["125th anniversary", "anniversary edition",
            "centenary", "jubilee"]):
        return "anniversary edition", 4

    # Imperial era bottles — "Circa 1970s", "26 2/3 Fl Oz"
    # "80º Proof", old format indicators
    if any(kw in title_lower for kw in
           ["circa 1970", "circa 1960", "26 2/3",
            "80º proof", "80° proof", "80 proof"]):
        return "imperial era", 4

    # CASK series — cask strength keyword in title
    if any(kw in title_lower for kw in
           ["cask strength", " cask ", "single cask"]):
        if has_year and bottling_year <= 2015:
            return "cask series", 4

    # 100 Proof era
    if any(kw in title_lower for kw in
           ["100 proof", "100º proof", "100° proof"]):
        return "100 proof era", 4

    # Decanter presentation
    if "decanter" in title_lower:
        return "decanter release", 4

    # Import / retailer exclusives
    if any(kw in title_lower for kw in
           ["for van wees", "van wees", "for japan",
            "japan import", "singapore exclusive",
            "queens award", "wealth solutions"]):
        return "import exclusive", 4

    # Tier 3
    if any(kw in title_lower for kw in
           ["connoisseurs choice", "connoisseur's choice"]):
        return "connoisseurs choice", 3
    if "speymalt" in title_lower:
        return "speymalt", 3
    if "discovery" in title_lower:
        return "discovery", 2
    if "distillery label" in title_lower:
        return "distillery label", 2
    if any(kw in title_lower for kw in
           ["macphail's", "macphails"]):
        return "macphails", 2

    # Pre-1990 bottling era inference
    if has_year and has_abv and bottling_year <= 1990:
        return "old era (inferred)", 4
    
    # Rare Vintage — named series for very old single malts
    if any(kw in title_lower for kw in
           ["rare vintage", "rare old"]):
        return "rare old", 4

    # Speyside Collection — prestigious multi-bottle set
    if "speyside collection" in title_lower:
        return "speyside collection", 5

    # Archive / Reserve releases
    if any(kw in title_lower for kw in
           ["archive release", "exclusive archive",
            "reserve"]):
        return "archive release", 4

    # Pre-1970 distillation with known bottling = Rare Vintage era
    dist_match = re.search(
        r'\b(19[0-6][0-9])\b', str(title) if title else ""
    )
    if dist_match:
        dist_year = int(dist_match.group(1))
        if dist_year <= 1969 and has_year:
            return "rare vintage (inferred)", 4
        if dist_year <= 1969 and not has_year:
            return "old era (inferred)", 4

    if "reserve" in title_lower:
        return "reserve", 3
    
    if "archive release" in title_lower or "exclusive archive" in title_lower:
        return "archive release", 4
    
    # In detect_gm_series, extend the vintage inference
    dist_match = re.search(
        r'\b(19[0-6][0-9]|197[0-9])\b', 
        str(title) if title else ""
    )
    if dist_match:
        dist_year = int(dist_match.group(1))
        if dist_year <= 1950:
            return "old era pre-1950", 5
        if dist_year <= 1969:
            return "rare vintage (inferred)", 4
        if dist_year <= 1979 and has_year:
            return "rare vintage (inferred)", 4
        if dist_year <= 1979 and not has_year:
            return "old era (inferred)", 4

    # Also add to private collection detection
    if any(kw in title_lower for kw in
        ["private collection", "private"]):
        if has_year and bottling_year >= 1990:
            return "private collection", 4

    return "standard", 2


def detect_douglas_laing_series(title):
    """
    Classify Douglas Laing bottlings by series.
    Tier 5: Old & Rare / Platinum
    Tier 3: Old Particular, Remarkable Regional Malts
    Tier 2: Premier Barrel, Double Barrel, Private Stock
    Tier 1: Standard
    Note: Old Malt Cask and First Editions are separate bottler
    entries in KNOWN_BOTTLERS so handled separately.
    """
    title_lower = str(title).lower() if title else ""

    if any(kw in title_lower for kw in
           ["old & rare", "old and rare", "platinum"]):
        return "old & rare", 5
    if "old particular" in title_lower:
        return "old particular", 3
    if "remarkable regional" in title_lower:
        return "remarkable regional", 3
    if "premier barrel" in title_lower:
        return "premier barrel", 2
    if "double barrel" in title_lower:
        return "double barrel", 2
    if "private stock" in title_lower:
        return "private stock", 2
    return "standard", 1


def detect_berry_bros_series(title, bottling_year):
    """
    Classify Berry Bros & Rudd bottlings by series.
    Tier 5: Berry's Own Selection pre-1990 (old vintage releases)
    Tier 3: Berry's Own Selection (modern), Classic range
    Tier 2: Standard
    """
    title_lower = str(title).lower() if title else ""
    has_year = bottling_year is not None and not pd.isna(bottling_year)

    if any(kw in title_lower for kw in
           ["berry's own selection", "berrys own selection",
            "berry's own", "good ordinary"]):
        if has_year and bottling_year <= 1990:
            return "own selection (vintage)", 5
        return "own selection", 3
    if "classic" in title_lower:
        return "classic range", 2
    return "standard", 2


def detect_samaroli_series(title, bottling_year, abv=None):
    title_lower = str(title).lower() if title else ""
    has_year = bottling_year is not None and not pd.isna(bottling_year)
    has_abv  = abv is not None and not pd.isna(abv)

    # Named series — always highest priority
    if any(kw in title_lower for kw in
           ["bouquet", "flowers", "flower"]):
        return "flowers / bouquet", 5
    if any(kw in title_lower for kw in
           ["coilltean", "coiltean"]):
        return "coilltean", 5
    if any(kw in title_lower for kw in
           ["handwritten", "hand written", "hand-written"]):
        return "handwritten labels", 5
    if "silence" in title_lower:
        return "silence series", 5
    if any(kw in title_lower for kw in ["colours", "colors"]):
        return "colours series", 5
    if "dreams" in title_lower:
        return "dreams series", 5
    if any(kw in title_lower for kw in
           ["silvano's collection", "silvanos collection", "masam"]):
        return "silvanos collection", 4
    if "magnifico" in title_lower:
        return "magnifico", 4
    if any(kw in title_lower for kw in ["no age", "pure malt"]):
        return "no age series", 4

    # Early Flowers era inference:
    # Pre-1990 bottling at 40-43% = likely Flowers era
    if has_year and has_abv and bottling_year <= 1990 and abv <= 43.0:
        return "flowers era (inferred)", 5

    # Era-based for all others
    if has_year:
        if bottling_year <= 2008:
            return "founder era (peak)", 5
        if bottling_year <= 2017:
            return "founder era (late)", 4
        return "post-founder", 3

    return "samaroli standard", 4


def detect_murray_mcdavid_series(title, bottling_year):
    """
    Classify Murray McDavid bottlings by era and series.
    Original ownership (pre-2000): prestige
    Post-2000: standard IB
    Named series: Mission, Celtic Heartlands, Benchmark
    """
    title_lower = str(title).lower() if title else ""
    has_year = bottling_year is not None and not pd.isna(bottling_year)

    if "mission" in title_lower:
        return "mission", 4
    if "benchmark" in title_lower:
        return "benchmark", 3
    if "celtic heartlands" in title_lower:
        return "celtic heartlands", 3

    if has_year and bottling_year <= 2000:
        return "early mcdavid", 4
    return "standard", 2


def detect_hart_brothers_series(title, abv, bottling_year):
    """
    Classify Hart Brothers bottlings by series.
    
    Series:
    Dynasty Decanter: ultra-premium crystal decanter series
    Legends:          flagship prestige single cask releases
    Finest Collection: semi-annual releases, often closed distilleries
    Cask Strength:    standard cask strength range
    """
    title_lower = str(title).lower() if title else ""
    has_year = bottling_year is not None and not pd.isna(bottling_year)
    has_abv  = abv is not None and not pd.isna(abv)

    # Named series
    if "dynasty" in title_lower:
        return "dynasty decanter", 5

    if "legend" in title_lower:
        return "legends collection", 4

    if any(kw in title_lower for kw in
           ["finest collection", "finest"]):
        return "finest collection", 3

    if any(kw in title_lower for kw in
           ["cask strength", "cask strength collection"]):
        return "cask strength", 3

    # Era inference: pre-2000 bottles at 43% = old Finest era
    if has_year and bottling_year <= 2000:
        return "early hart brothers", 4

    # Old vintage closed distillery at accessible ABV
    # Port Ellen, St Magdalene etc. pre-1985 = prestige regardless of series
    if has_year and has_abv and bottling_year <= 2005:
        return "vintage single cask", 3

    return "standard", 2



def detect_duncan_taylor_series(title, abv, bottling_year):
    title_lower = str(title).lower() if title else ""
    has_year = bottling_year is not None and not pd.isna(bottling_year)
    has_abv  = abv is not None and not pd.isna(abv)

    # Named series — highest priority
    if any(kw in title_lower for kw in
           ["rarest of the rare", "rarest the rare"]):
        return "rarest of the rare", 5

    if any(kw in title_lower for kw in
           ["rare auld", "rare old"]):
        return "rare auld", 4

    if "peerless" in title_lower:
        return "peerless", 4

    if "octave" in title_lower:
        return "octave", 3

    if "dimensions" in title_lower:
        return "dimensions", 3

    if "lonach" in title_lower:
        return "lonach", 3

    if any(kw in title_lower for kw in ["nc2", "nc²"]):
        return "nc2", 2

    if any(kw in title_lower for kw in
           ["whisky galore", "whiskygalore"]):
        return "whisky galore", 2

    if "black bull" in title_lower:
        return "black bull", 2

    # Special edition / retailer exclusive
    if any(kw in title_lower for kw in
           ["tantalus", "slainte", "bicentenary",
            "special edition", "to celebrate"]):
        return "special edition", 3

    # Era inference: pre-2002 Abe Rosenberg era stock
    if has_year and bottling_year <= 2002:
        return "rosenberg era", 5

    # Pre-1985 distillation bottled pre-2013 = Rare Auld / Peerless era
    if has_year and bottling_year <= 2012:
        year_match = re.search(
            r'\b(19[0-9]{2})\b', str(title) if title else ""
        )
        if year_match:
            dist_year = int(year_match.group(1))
            if dist_year <= 1984:
                return "rare auld (inferred)", 4

    return "standard", 2


def detect_adelphi_series(title):
    """
    Classify Adelphi bottlings.
    Tier 4: Breath of Islay, Fascadale (house expressions)
    Tier 3: Standard single cask (Adelphi is consistently quality)
    """
    title_lower = str(title).lower() if title else ""

    if "fascadale" in title_lower:
        return "fascadale", 4
    if any(kw in title_lower for kw in
           ["breath of islay", "breath"]):
        return "breath of islay", 4
    return "standard", 3  # Adelphi standard is already tier 3


def detect_compass_box_series(title):
    """
    Classify Compass Box bottlings (blended malts).
    All Compass Box is consistent quality but named expressions vary.
    Tier 4: Ultramarine, Hedonism Maximus (ultra-premium)
    Tier 3: Peat Monster, Flaming Heart, Oak Cross, Great King St
    Tier 2: Standard blends
    """
    title_lower = str(title).lower() if title else ""

    if any(kw in title_lower for kw in
           ["ultramarine", "hedonism maximus"]):
        return "ultra premium", 4
    if any(kw in title_lower for kw in
           ["flaming heart", "peat monster", "hedonism",
            "oak cross", "spice tree", "the story"]):
        return "signature series", 3
    if "great king street" in title_lower:
        return "great king street", 2
    return "standard", 2


def detect_boutiquey_series(title):
    """
    Classify That Boutique-y Whisky Company bottlings.
    Named by batch number and distillery — generally consistent quality.
    Some special releases command premiums.
    """
    title_lower = str(title).lower() if title else ""

    if "batch 1" in title_lower or "first batch" in title_lower:
        return "batch 1", 3  # first batches often command premium
    if "10th anniversary" in title_lower or "anniversary" in title_lower:
        return "anniversary release", 3
    return "standard", 2


def load_smws_codes(csv_path="smws_codes.csv"):
    """
    Load SMWS distillery code mapping from CSV file.
    Returns dict: code_str -> (distillery, is_closed)
    """
    if not os.path.exists(csv_path):
        return {}
    try:
        codes_df = pd.read_csv(csv_path)
        mapping = {}
        for _, row in codes_df.iterrows():
            code = str(row["code"])
            mapping[code] = (
                row["distillery"],
                bool(row["is_closed"])
            )
        return mapping
    except Exception:
        return {}

# Load at module level
SMWS_CODE_MAP = load_smws_codes()

# In detect_smws_series, update prestige codes
# Rosebank (25) and Bladnoch (50) should be tier 4
# as closed/nearly-closed distilleries

SMWS_PRESTIGE_CLOSED = {
    "20",   # Inverleven
    "25",   # Rosebank
    "38",   # Caperdonich  
    "43",   # Port Ellen
    "45",   # Dallas Dhu
    "49",   # St Magdalene
    "56",   # Coleburn
    "57",   # Glen Mhor
    "62",   # Glenlochy
    "65",   # Imperial
    "67",   # Banff
    "69",   # Glen Albyn
    "74",   # North Port
    "75",   # Glenury Royal
    "83",   # Convalmore
    "86",   # Glenesk
    "87",   # Millburn
    "90",   # Pittyvaich
    "92",   # Lochside
    "97",   # Littlemill
    "98",   # Lomond
    "99",   # Glenugie
    "109",  # Mosstowie
    "131",  # Hanyu
    "132",  # Karuizawa
    "G2",   # Carsebridge
    "G3",   # Caledonian
    "G6",   # Port Dundas
    "G8",   # Cambus
    "G14",  # Dumbarton
    "R13",  # Caroni
}

SMWS_PRESTIGE_OPERATIONAL = {
    "3",    # Bowmore
    "4",    # Highland Park
    "10",   # Bunnahabhain
    "14",   # Talisker
    "23",   # Bruichladdich
    "24",   # Macallan
    "26",   # Clynelish
    "27",   # Springbank
    "29",   # Laphroaig
    "33",   # Ardbeg
    "40",   # Balvenie
    "53",   # Caol Ila
    "61",   # Brora (reopened)
    "76",   # Mortlach
    "111",  # Lagavulin
    "116",  # Yoichi
    "119",  # Yamazaki
    "120",  # Hakushu
    "124",  # Miyagikyo
    "130",  # Chichibu
}


def detect_smws_series(title):
    title_str = str(title) if title else ""
    title_lower = title_str.lower()

    cask_match = re.search(r'\b([A-Z]*\d{1,3})\.(\d+)\b',
                           title_str)
    if cask_match:
        dist_code = cask_match.group(1)
        if dist_code in SMWS_CODE_MAP:
            distillery, is_closed = SMWS_CODE_MAP[dist_code]
            name = f"smws {distillery.lower()}"
            if dist_code in SMWS_PRESTIGE_CLOSED:
                return name, 5
            if dist_code in SMWS_PRESTIGE_OPERATIONAL:
                return name, 4
            return name, 3

    if any(kw in title_lower for kw in
           ["fable", "whisky show", "festival",
            "tasting room", "extravaganza"]):
        return "smws event release", 3

    return "smws standard", 2


def detect_hunter_laing_series(title, abv, bottling_year, distillery = None):
    """
    Hunter Laing series (est. 2013, split from Douglas Laing):
    Tier 5: Old & Rare Platinum — legendary old casks
    Tier 4: First Editions Authors Series — prestige long-aged
    Tier 3: Old Malt Cask, First Editions — standard premium
    Tier 2: Hepburn's Choice (46%), Distiller's Art (48%),
             Sovereign (grain), Scarabus (Islay)
    """
    title_lower = str(title).lower() if title else ""
    has_abv  = abv is not None and not pd.isna(abv)
    has_year = bottling_year is not None and not pd.isna(bottling_year)

    if any(kw in title_lower for kw in
           ["old & rare", "old and rare", "platinum"]):
        return detect_old_rare_series(
            title, distillery, bottling_year
        )

    if "authors" in title_lower:
        return "first editions authors", 4

    if any(kw in title_lower for kw in
           ["first edition", "first editions"]):
        if has_year and bottling_year <= 2016:
            return "first editions (cask strength)", 3
        return "first editions", 3

    if "old malt cask" in title_lower:
        return "old malt cask", 3

    if "hepburn" in title_lower:
        return "hepburns choice", 2

    if any(kw in title_lower for kw in
           ["distiller's art", "distillers art"]):
        return "distillers art", 2

    if "scarabus" in title_lower:
        return "scarabus", 2

    if "sovereign" in title_lower:
        return "sovereign", 2

    if "kill devil" in title_lower:
        return "kill devil", 2

    return "standard", 3  # Hunter Laing standard is already quality


def detect_old_malt_cask_series(title, abv, bottling_year):
    """
    Old Malt Cask — originally Douglas Laing (1998-2013),
    then Hunter Laing (2013+).
    Single cask, 50% ABV, no colouring or chill filtration.
    Pre-2013 bottles are Douglas Laing era.
    """
    title_lower = str(title).lower() if title else ""
    has_year = bottling_year is not None and not pd.isna(bottling_year)

    # Some OMC lots explicitly mention distillery era
    if any(kw in title_lower for kw in
           ["old & rare", "old and rare"]):
        return "old & rare", 5

    # Pre-2013 = Douglas Laing era (same quality, different ownership)
    if has_year and bottling_year <= 2013:
        return "old malt cask (DL era)", 3
    return "old malt cask", 3


def detect_first_editions_series(title, abv, bottling_year):
    """
    First Editions — Hunter Laing sub-label.
    Until 2016: cask strength only.
    2014+: Authors Series (prestige long-aged).
    Post-2016: mix of cask strength and 46%.
    """
    title_lower = str(title).lower() if title else ""
    has_year = bottling_year is not None and not pd.isna(bottling_year)

    if "authors" in title_lower:
        return "first editions authors", 4

    if has_year and bottling_year <= 2016:
        return "first editions (cask strength)", 3
    return "first editions", 3


def detect_sestante_series(title, bottling_year):
    """
    Sestante — Italian IB, 1979-1999.
    All Sestante is prestige tier 5.
    Crystal decanter versions are particularly collectible.
    """
    title_lower = str(title).lower() if title else ""

    if any(kw in title_lower for kw in
           ["decanter", "crystal"]):
        return "sestante decanter", 5
    return "sestante standard", 5


def detect_silver_seal_series(title, bottling_year):
    """
    Silver Seal — successor to Sestante (2000+).
    Sestante Collection = old Sestante casks bottled by Silver Seal.
    Modern Silver Seal = tier 4.
    """
    title_lower = str(title).lower() if title else ""
    has_year = bottling_year is not None and not pd.isna(bottling_year)

    if "sestante collection" in title_lower:
        return "sestante collection", 5

    if any(kw in title_lower for kw in
           ["decanter", "crystal", "magnum"]):
        return "silver seal premium", 4

    if has_year and bottling_year <= 2010:
        return "silver seal mainardi era", 5
    return "silver seal standard", 4


def detect_moon_import_series(title, bottling_year):
    """
    Moon Import — Pepi Mongiardino, mid-1980s onwards.
    Three iconic named series: Birds, Costumes, Sea.
    Half Moon / Second Collection = earliest series.
    All Moon Import is prestige.
    """
    title_lower = str(title).lower() if title else ""

    if any(kw in title_lower for kw in
           ["half moon", "second collection"]):
        return "half moon", 5

    if any(kw in title_lower for kw in
           ["the birds", "birds series"]):
        return "the birds", 5

    if any(kw in title_lower for kw in
           ["the costumes", "costumes series"]):
        return "the costumes", 5

    if any(kw in title_lower for kw in
           ["the sea", "sea series"]):
        return "the sea", 5

    if "representation" in title_lower:
        return "representation series", 5

    return "moon import standard", 4


def detect_james_macarthur_series(title, abv, bottling_year):
    """
    James MacArthur — Scottish IB, active 1980s-2000s.
    Old Masters series: prestige long-aged (40+ year old casks).
    Fine Malt Selection: standard range.
    All pre-2000 James MacArthur is sought after.
    """
    title_lower = str(title).lower() if title else ""
    has_year = bottling_year is not None and not pd.isna(bottling_year)

    if "old masters" in title_lower:
        return "old masters", 4

    if any(kw in title_lower for kw in
           ["fine malt selection", "fine malt"]):
        return "fine malt selection", 3

    if has_year and bottling_year <= 2000:
        return "early macarthur", 4

    return "standard", 3


def detect_kingsbury_series(title, abv, bottling_year):
    """
    Kingsbury — Japanese-focused prestige IB.
    Gold Series: ultra-premium.
    Silver Series: premium.
    All Kingsbury is high quality.
    """
    title_lower = str(title).lower() if title else ""

    if "gold" in title_lower:
        return "gold series", 5

    if "silver" in title_lower:
        return "silver series", 4

    if any(kw in title_lower for kw in
           ["mizuhashi", "for japan"]):
        return "japan exclusive", 5

    return "kingsbury standard", 4


def detect_blackadder_series(title, abv, bottling_year):
    """
    Blackadder — Adam Eckfeldt's Scottish IB.
    Raw Cask: bottled straight from cask, unfiltered.
    Aberdeen Distillers: standard range.
    Black Snake: vatted malt series.
    """
    title_lower = str(title).lower() if title else ""

    if "raw cask" in title_lower:
        return "raw cask", 4

    if "black snake" in title_lower:
        return "black snake", 3

    if any(kw in title_lower for kw in
           ["aberdeen distillers", "aberdeen"]):
        return "aberdeen distillers", 3

    return "blackadder standard", 3


def detect_malts_of_scotland_series(title, abv, bottling_year):
    """
    Malts of Scotland — German IB (Thomas Ewers).
    Cask series: premium single casks.
    Rare Malts: ultra-premium.
    All MoS is consistently good quality.
    """
    title_lower = str(title).lower() if title else ""
    has_year = bottling_year is not None and not pd.isna(bottling_year)

    if "rare malts" in title_lower:
        return "rare malts", 4

    if any(kw in title_lower for kw in
           ["exclusive cask", "single cask"]):
        return "exclusive cask", 3

    return "malts of scotland standard", 3


def detect_chieftains_series(title, abv, bottling_year):
    """
    Chieftain's — Ian MacLeod Distillers sub-label.
    Choice Collection: standard IB range.
    """
    title_lower = str(title).lower() if title else ""

    if "choice collection" in title_lower:
        return "choice collection", 3

    return "chieftains standard", 2


def detect_wilson_morgan_series(title, bottling_year):
    """
    Wilson & Morgan — Italian IB (Fabio Rossi).
    Barrel Selection: standard range at 40-46%.
    All W&M is quality but accessible.
    """
    title_lower = str(title).lower() if title else ""
    has_year = bottling_year is not None and not pd.isna(bottling_year)

    if "barrel selection" in title_lower:
        return "barrel selection", 3

    if has_year and bottling_year <= 2005:
        return "early wilson morgan", 4

    return "wilson morgan standard", 3

def detect_old_rare_series(title, distillery,
                            bottling_year):
    """
    Old & Rare tier should reflect the liquid,
    not just the series name.
    Tier 5: closed distillery or pre-1985 distillation
    Tier 4: prestige operational distillery old vintage
    Tier 3: modern distillery in Old & Rare format
    """
    title_lower = str(title).lower() if title else ""
    has_year = (bottling_year is not None and
                not pd.isna(bottling_year))

    # Closed distillery = always tier 5
    if distillery in CLOSED_DISTILLERIES:
        return "old & rare", 5

    # Pre-1985 distillation year in title = tier 5
    year_match = re.search(
        r'\b(19[0-8][0-9])\b', title_lower
    )
    if year_match and int(year_match.group(1)) <= 1984:
        return "old & rare", 5

    # 1985-1994 distillation = tier 4
    if year_match and int(year_match.group(1)) <= 1994:
        return "old & rare", 4

    # Pre-2000 bottling without distillation year = tier 4
    if has_year and bottling_year <= 2000:
        return "old & rare", 4

    # Modern = tier 3
    return "old & rare", 3

def detect_laphroaig_expression(title, abv,
                                 bottling_year, age_years):
    """
    Classify Laphroaig OB expressions by tier.
    Tier 5: legendary old era OBs (pre-1985 distillation)
    Tier 4: prestige age-stated releases (25yo+, Cairdeas
             special, Feis Ile, retailer exclusives)
    Tier 3: premium expressions (18yo, 10yo CS, Quarter Cask,
             Triple Wood, standard Cairdeas)
    Tier 2: core range (10yo standard, Select)
    Tier 1: NAS entry level
    """
    title_lower = str(title).lower() if title else ""
    has_age  = age_years is not None and not pd.isna(age_years)
    has_year = (bottling_year is not None and
                not pd.isna(bottling_year))

    # Tier 5 — old era OBs (caught by R3 regime already
    # but also classify here for series_tier consistency)
    if any(kw in title_lower for kw in
            ["26 2/3", "circa 1970", "circa 1980",
            "vintage 75cl", "vintage 26"]):
        return "old era ob", 5

    # Old distillation year → tier 5
    year_match = re.search(r'\b(19[6-8][0-9])\b', title_lower)
    if year_match:
        dist_year = int(year_match.group(1))
        if dist_year <= 1985:
            return "vintage ob", 5

    # Tier 4 — prestige releases
    # 30yo+ always tier 4
    if has_age and age_years >= 30:
        return "ultra aged", 4

    # Named prestige series
    if any(kw in title_lower for kw in
           ["cairdeas", "wall collection",
            "archive collection", "feis ile",
            "friends of laphroaig"]):
        if has_age and age_years >= 25:
            return "cairdeas prestige", 4
        return "cairdeas", 3

    # 25yo
    if has_age and age_years >= 25:
        return "25 year old", 4

    # Retailer/club exclusives — hard to detect by keyword
    # but these are typically high-age or named bottlings
    if any(kw in title_lower for kw in
           ["dr jekyll", "for cecbl", "exclusive",
            "single cask", "distillery exclusive"]):
        return "exclusive ob", 4

    # Tier 3 — premium expressions
    if has_age and age_years >= 18:
        return "aged ob", 3

    if any(kw in title_lower for kw in
           ["cask strength", "10 year old cask",
            "quarter cask", "triple wood",
            "double wood"]):
        return "premium core", 3

    # Tier 2 — core range
    if any(kw in title_lower for kw in
           ["10 year old", "10yo", "select",
            "oak select"]):
        return "core range", 2

    # Tier 1 — NAS entry
    if any(kw in title_lower for kw in
           ["lore", "px wood", "explore"]):
        return "nas entry", 1

    # Default — standard OB without clear expression signal
    return "standard ob", 2
# ---------------------------------------------------------------------------
# Master series dispatcher
# ---------------------------------------------------------------------------

def detect_bottler_series(title, bottler, abv,
                           bottling_year, volume_cl=None, distillery=None):
    if pd.isna(bottler) or not bottler:
        return None, None

    b = str(bottler)

    if b in ["Cadenhead's", "Cadenhead", "Cadenheads"]:
        return detect_cadenhead_series(title, abv, bottling_year)
    if b in ["Signatory", "Signatory Vintage"]:
        return detect_signatory_series(
            title, abv, bottling_year, volume_cl)
    if b in ["Gordon & MacPhail", "G&M"]:
        return detect_gm_series(title, abv, bottling_year)
    if b in ["Douglas Laing", "Douglas Laing & Co"]:
        return detect_douglas_laing_series(title)
    if b in ["Berry Bros & Rudd", "Berry Bros", "Berry Brothers"]:
        return detect_berry_bros_series(title, bottling_year)
    if b == "Samaroli":
        return detect_samaroli_series(title, bottling_year, abv)
    if b == "Moon Import":
        return detect_moon_import_series(title, bottling_year)
    if b == "Murray McDavid":
        return detect_murray_mcdavid_series(title, bottling_year)
    if b == "Hart Brothers":
        return detect_hart_brothers_series(title, abv, bottling_year)
    if b == "Duncan Taylor":
        return detect_duncan_taylor_series(title, abv, bottling_year)
    if b == "Adelphi":
        return detect_adelphi_series(title)
    if b == "Compass Box":
        return detect_compass_box_series(title)
    if b in ["That Boutique-y Whisky Company", "Boutique-y Whisky"]:
        return detect_boutiquey_series(title)
    if b in ["SMWS", "Scotch Malt Whisky Society"]:
        return detect_smws_series(title)

    # New bottlers
    if b in ["Hunter Laing", "Hunter Laing & Co"]:
        return detect_hunter_laing_series(title, abv, bottling_year)
    if b == "Old Malt Cask":
        return detect_old_malt_cask_series(title, abv, bottling_year)
    if b == "First Editions":
        return detect_first_editions_series(title, abv, bottling_year)
    if b == "Sestante":
        return detect_sestante_series(title, bottling_year)
    if b == "Silver Seal":
        return detect_silver_seal_series(title, bottling_year)
    if b in ["James MacArthur"]:
        return detect_james_macarthur_series(
            title, abv, bottling_year)
    if b == "Kingsbury":
        return detect_kingsbury_series(title, abv, bottling_year)
    if b in ["Blackadder"]:
        return detect_blackadder_series(title, abv, bottling_year)
    if b in ["Malts of Scotland"]:
        return detect_malts_of_scotland_series(
            title, abv, bottling_year)
    if b in ["Chieftain's", "Chieftains"]:
        return detect_chieftains_series(title, abv, bottling_year)
    if b in ["Wilson & Morgan"]:
        return detect_wilson_morgan_series(title, bottling_year)
    if b == "Old & Rare":
        return detect_old_rare_series(title, distillery, bottling_year)
    if b in ["Hunter Laing", "Hunter Laing & Co"]:
        # Also update Hunter Laing Old & Rare detection
        return detect_hunter_laing_series(title, abv, bottling_year, distillery)

    return None, None


def detect_ob_expression(title, distillery, abv,
                          bottling_year, age_years):
    if not distillery:
        return None, None
    dist = str(distillery)

    if dist == "Laphroaig":
        return detect_laphroaig_expression(
            title, abv, bottling_year, age_years)
    if dist == "Lagavulin":
        return detect_lagavulin_expression(
            title, abv, bottling_year, age_years)
    if dist == "Ardbeg":
        return detect_ardbeg_expression(
            title, abv, bottling_year, age_years)
    if dist == "Highland Park":
        return detect_highland_park_expression(
            title, abv, bottling_year, age_years)
    if dist == "Glendronach":  # this is the actual stored value
        return detect_glendronach_expression(
            title, abv, bottling_year, age_years)
    if dist == "Glenfarclas":
        return detect_glenfarclas_expression(
            title, abv, bottling_year, age_years)

    return None, None

# In whisky_utils.py — add after detect_bottler_series

REGIME_3_DISTILLERIES = {
    "Karuizawa", "Hanyu", "Port Ellen", "Rosebank",
    "Brora", "Springbank", "Laphroaig", "Ardbeg",
}

REGIME_4_DISTILLERIES_OB = {
    "Yamazaki", "Hakushu", "Hibiki", "Chichibu",
    "Akkeshi", "Yoichi", "Miyagikyo", "Kavalan",
}

REGIME_1_DISTILLERIES = {
    "Dalmore",       # luxury brand play, Luminary/Constellation etc.
    "Glenmorangie",  # Signet, luxury limited — normie gifting brand
    "Glenfiddich",   # commodity + luxury tier, airport staple
    "Balvenie",      # mainstream premium, normie gifting
}

DISTILLERY_R3_ERA = {
    # Islay
    "Ardbeg":        1981,
    "Laphroaig":     1985,
    "Bowmore":       1974,
    "Bunnahabhain":  1982,
    "Caol Ila":      1979,
    "Bruichladdich": 1979,
    # Highland
    "Highland Park": 1979,
    "Clynelish":     1983,
    "Talisker":      1979,
    "Ben Nevis":     1978,
    "GlenDronach":   1978,  # pre-1978 old era, direct fired
    "Glendronach":   1978,  # capitalisation variant
    # Speyside
    "Glenfarclas":   1980,
    "Mortlach":      1975,
    "Longmorn":      1979,
    "Glen Grant":    1979,
    "Strathisla":    1979,
    "Linkwood":      1971,
    "Glenlivet":     1969,
    "Cragganmore":   1979,
    "Craigellachie": 1979,
    "Glenlossie":    1979,
    "Longrow":       1979,
    "Glenfiddich":  1974,  # pre-1974 old character era
    # Campbeltown
    "Springbank":    1979,
    # Islands
    "Tobermory":     1979,
    # Lowland
    "Glenkinchie":   1979,
    "Auchentoshan":  1979,
    "Glen Moray":    1979,
    "Glen Moray":    1979,
    "Lagavulin":     1979,
    "Glenglassaugh": 1986,  # closed 1986
    "Fettercairn":   1979,
    "Glengoyne":     1979,  # already in era dict
    "Aberfeldy":     1979,
    "Blair Athol":   1979,
    "Edradour":      1979,
    "Balblair":      1979,
    "Tomatin":       1979,
    "Benriach":      1979,
    "Glendullan":    1979,
    "Dailuaine":     1979,
}

def classify_market_regime(title, distillery, bottler,
                            is_ob, is_closed, series_tier,
                            abv, bottling_year, age_years):
    title_lower = str(title).lower() if title else ""
    dist = str(distillery) if distillery else ""
    has_year = bottling_year is not None and not pd.isna(bottling_year)
    has_age  = age_years is not None and not pd.isna(age_years)  # ADD THIS
    
    # ------------------------------------------------------------------
    # REGIME 3 — holy grail. Check first, highest priority.
    # ------------------------------------------------------------------

    # Karuizawa — all whisky R3, non-whisky R2
    if dist == "Karuizawa":
        if any(kw in title_lower for kw in
               ["gin", "kohakuroman", "blend",
                "club 72", "shinshu", "mars"]):
            return 2
        return 3

    # Hanyu — all serious bottlings R3, cheap blends R2
    if dist == "Hanyu":
        if any(kw in title_lower for kw in
               ["golden horse", "bushu"]):
            return 2
        return 3

    # Rosebank, Brora, Port Ellen — all R3
    if dist in {"Rosebank", "Brora", "Port Ellen"}:
        return 3

    if (series_tier is not None and
        not pd.isna(series_tier) and
        series_tier == 5):
        # Check if bottler is in the legendary tier
        bottler_tier_val = BOTTLER_TIER.get(
            str(bottler) if bottler else "", 0
        )
        if bottler_tier_val >= 4:
            return 3

    # General closed distillery rule
    if is_closed:
        # Pre-1990 distillation year in title
        dist_year_match = re.search(
            r'\b(19[0-9]{2})\b', title_lower
        )
        if dist_year_match:
            dist_year = int(dist_year_match.group(1))
            if dist_year <= 1989:
                return 3
        # Age statement implies old distillation
        # 30+ year old closed distillery = always R3
        if has_age and age_years >= 30:
            return 3
        # Very long age even without explicit statement
        # e.g. "47 Year Old" without year
        age_match = re.search(
            r'\b([3-9][0-9]|[1-9][0-9]{2})\s*year', title_lower
        )
        if age_match and int(age_match.group(1)) >= 30:
            return 3
        
    # For operational distilleries: implied old distillation
    # from age statement + bottling year
    if dist in DISTILLERY_R3_ERA:
        threshold = DISTILLERY_R3_ERA[dist]
        # Direct year in title
        dist_year_match = re.search(
            r'\b(19[0-9]{2})\b', title_lower
        )
        if dist_year_match:
            dist_year = int(dist_year_match.group(1))
            if dist_year <= threshold:
                return 3
        # Implied distillation year from age + bottling year
        if has_age and has_year:
            implied_dist_year = bottling_year - age_years
            if implied_dist_year <= threshold:
                return 3
        # Fallback: use current auction window if no bottling year
        if has_age and not has_year:
            # Assume bottled approximately now (2024)
            implied_dist_year = 2024 - age_years
            if implied_dist_year <= threshold:
                return 3
            
        # Bowmore — 1964 trilogy and named legendary expressions
        if dist == "Bowmore":
            if any(kw in title_lower for kw in
                ["black bowmore", "white bowmore",
                    "gold bowmore", "bouquet",
                    "largiemeanoch", "bicentenary"]):
                return 3

        # Ardbeg 1970s
        if dist == "Ardbeg":
            if re.search(r'\b197[0-9]\b', title_lower):
                return 3

        # Springbank 1960s-1970s
        if dist == "Springbank":
            # 1960s-1970s vintage year in title → R3
            if re.search(r'\b19[67][0-9]\b', title_lower):
                return 3

            # Pre-1990 distillation vintage explicitly stated → R3
            dist_year = re.search(r'\b(19[0-8][0-9])\b', title_lower)
            if dist_year and int(dist_year.group(1)) <= 1989:
                return 3

            # Old era format indicators → R3
            if any(kw in title_lower for kw in
                ["26 2/3", "pear shaped", "circa 1970",
                    "circa 1980"]):
                return 3

            # 100º/100° proof — only R3 if clearly old era
            # (not modern NAS or young expressions)
            if any(kw in title_lower for kw in
                ["100° proof", "100º proof"]):
                # Modern bottling year = modern product
                if has_year and bottling_year >= 2010:
                    return 2
                # Young age statement = modern product
                if any(kw in title_lower for kw in
                    ["5 year", "8 year", "10 year",
                        "12 year", "15 year"]):
                    return 2
                return 3

            return 2

        # Laphroaig 1970s
        if dist == "Laphroaig":
            if re.search(r'\b197[0-9]\b', title_lower):
                return 3

        # GENERAL PRE-1975 RULE
        # Any lot with a pre-1975 distillation year in the title
        # from a distillery with known vintage character = R3
        # This catches Bowmore 1960s, Mortlach 1950s-1960s,
        # Highland Park 1960s-1970s, Glenfarclas 1950s-1960s etc.
        
        # Replace the general pre-1975 rule with:

        # Distillery-specific golden era rule
        dist_year_match = re.search(
            r'\b(19[0-9]{2})\b', title_lower
        )
        if dist_year_match and dist in DISTILLERY_R3_ERA:
            dist_year = int(dist_year_match.group(1))
            threshold = DISTILLERY_R3_ERA[dist]
            if dist_year <= threshold:
                return 3

        if has_age and not has_year:
            # Assume bottled approximately now (2024)
            implied_dist_year = 2024 - age_years
            if implied_dist_year <= threshold:
                return 3

    # ------------------------------------------------------------------
    # REGIME 4 — convergence (geek + normie)
    # ------------------------------------------------------------------

    if dist in REGIME_4_DISTILLERIES_OB and is_ob:
        return 4

    if dist == "Chichibu":
        return 4

    # Macallan
    if dist == "Macallan":
        if is_ob and any(kw in title_lower for kw in
               ["fine oak", "triple cask", "double cask",
                "gold", "amber", "sienna", "ruby",
                "1824", "rare cask"]):
            return 1
        if is_ob and any(kw in title_lower for kw in
               ["harmony", "archival", "folio",
                "masters of photography", "no. 6",
                "number 6", "m decanter", "reflexion",
                "concept", "anecdotes", "sir peter blake",
                "red collection", "aera", "a night on earth",
                "distil your world", "lalique", "genesis",
                "tales of", "exceptional cask",
                "easter elchies", "edition no",
                "capsule edition"]):
            return 1
        if is_ob:
            old_vintage = re.search(r'\b19[0-7][0-9]\b',
                                    title_lower)
            fine_rare   = "fine & rare" in title_lower
            select_res  = "select reserve" in title_lower
            if has_year and bottling_year >= 2005:
                if not old_vintage and not fine_rare \
                        and not select_res:
                    return 1
            if not has_year and not old_vintage \
                    and not fine_rare and not select_res:
                return 1
        return 4

    # ------------------------------------------------------------------
    # REGIME 1 — brand/luxury driven OB
    # ------------------------------------------------------------------

    if any(kw in title_lower for kw in
           ["royal salute", "chivas regal",
            "johnnie walker"]):
        return 1

    if dist == "Dalmore":
        return 1

    if is_ob and not is_closed and \
            dist in REGIME_1_DISTILLERIES:
        return 1

    if dist == "Glenfiddich" and is_ob:
        if any(kw in title_lower for kw in
               ["rare collection", "time series",
                "grand series", "experimental",
                "janet sheed", "50 year"]):
            return 4
        return 1
    
    # In the Macallan/Dalmore/Glenfiddich R1 block, or as
    # a separate Bowmore luxury catch before the Bowmore R3 block:
    if dist == "Bowmore" and is_ob:
        if any(kw in title_lower for kw in
            ["four guardian", "aston martin",
                "timeless", "inspired by", "lalique"]):
            return 1
        
    if dist == "Highland Park" and is_ob:
        if any(kw in title_lower for kw in
            ["king christian", "magnus", "viking",
                "full volume", "50 year", "40 year",
                "fire", "ice"]):
            return 1
    
    if is_ob and "lalique" in title_lower:
        return 1    

    # ------------------------------------------------------------------
    # REGIME 2 — default
    # ------------------------------------------------------------------
    return 2
# ---------------------------------------------------------------------------
# Master enrichment pipeline
# ---------------------------------------------------------------------------

def enrich_dataframe(df):
    """
    Apply all enrichment steps to a raw lots dataframe.
    Adds: distillery, bottler, is_ob, is_closed, distillation_year,
          bottling_year, bottling_year_derived, bottle_age_at_auction,
          cask_normalised, price_per_70cl, price_70cl_adj,
          bottler_series, series_tier
    """
    print("Applying enrichment...")
    df = df.copy()

    df["distillery"] = df["title"].apply(extract_distillery)
    df["bottler"]    = df["title"].apply(extract_bottler)
    df["is_ob"]      = df.apply(
        lambda r: is_ob(r["title"], r["bottler"]), axis=1
    )
    df["is_closed"]  = df["distillery"].apply(is_closed_distillery)
    df["is_grain"] = df["distillery"].apply(is_grain_distillery).astype(int)
    
    df[["distillation_year", "distillation_approx"]] = (
        df["distilled_date"].apply(
            lambda x: pd.Series(extract_year(x))
        )
    )
    df[["bottling_year", "bottling_approx"]] = (
        df["bottled_date"].apply(
            lambda x: pd.Series(extract_year(x))
        )
    )

    # Sanity check on distillation year
    df["distillation_year"] = df["distillation_year"].where(
        df["distillation_year"] <= 2026, None
    )

    # Derive bottling year from distillation + age where missing
    df["bottling_year_derived"] = df["bottling_year"].copy()
    mask = (
        df["bottling_year_derived"].isna() &
        df["distillation_year"].notna() &
        df["age_years"].notna()
    )
    df.loc[mask, "bottling_year_derived"] = (
        df.loc[mask, "distillation_year"] +
        df.loc[mask, "age_years"]
    ).round(0)

    df["bottle_age_at_auction"] = (
        df["bottling_year"] - df["distillation_year"]
    )
    df["bottle_age_at_auction"] = df["bottle_age_at_auction"].where(
        df["bottle_age_at_auction"] >= 0, None
    )

    df["cask_normalised"] = df["cask_type"].apply(normalise_cask_type)

    # Simple linear volume normalisation (valid for 45-76cl only)
    df["price_per_70cl"] = df.apply(
        lambda r: r["winning_bid"] * 70 / r["volume_cl"]
        if pd.notna(r["volume_cl"]) and 45 <= r["volume_cl"] <= 76
        else r["winning_bid"],
        axis=1
    )

    # Full volume normalisation including miniatures
    df["price_70cl_adj"] = df.apply(
        lambda r: price_per_70cl_adjusted(
            r["winning_bid"], r["volume_cl"]
        ), axis=1
    )

    # IB series classification
    df[["bottler_series", "series_tier"]] = df.apply(
        lambda r: pd.Series(detect_bottler_series(
            r["title"], r["bottler"],
            r["abv"], r["bottling_year_derived"],
            r["volume_cl"], r["distillery"]
        )), axis=1
    )

    # OB expression classification
    ob_mask = df["is_ob"] == True
    df.loc[ob_mask, ["ob_expression", "ob_tier"]] = (
        df[ob_mask].apply(
            lambda r: pd.Series(detect_ob_expression(
                r["title"], r["distillery"],
                r["abv"], r["bottling_year_derived"],
                r["age_years"]
            )), axis=1
        ).values
    )

    # Combine: use ob_tier for OBs, series_tier for IBs
    df["effective_tier"] = df.apply(
        lambda r: (
            r["ob_tier"] if (r["is_ob"] and
                            pd.notna(r.get("ob_tier")))
            else r["series_tier"] if pd.notna(r["series_tier"])
            else r.get("bottler_tier", 1)
        ), axis=1
    )

    df["market_regime"] = df.apply(lambda r: classify_market_regime(
        r["title"], r["distillery"], r["bottler"],
        r["is_ob"], r["is_closed"], r["series_tier"],
        r["abv"], r["bottling_year_derived"], r["age_years"]
    ), axis=1)

    print(f"Done. {len(df):,} lots enriched.")
    return df