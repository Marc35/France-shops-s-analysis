"""
BANCO data preparation.

The file follows the same steps as the labs:
    1. Data exploration & data quality  (trees lab: isnull, % missing, duplicated)
    2. Basic cleaning                   (trees lab: to_datetime, strip, dropna lat/lon)
    3. Feature engineering              (lab 1: get_xxx functions applied with .map,
                                         trees lab: pd.cut into classes)
    4. Analysis tables                  (lab 1: groupby + unstack,
                                         trees lab: crosstab in %, Shannon index)

Entry point used by app.py (same signature as the project skeleton):
    tables = make_tables(df_raw)
"""
import re

import numpy as np
import pandas as pd
from scipy.stats import entropy

from utils.constants import (
    BRAND_PATTERNS,
    DEPT_NAMES,
    DEPT_TO_REGION,
    ESSENTIAL_CATEGORIES,
    FOOD_RETAIL_TYPES,
    FRESHNESS_BINS,
    FRESHNESS_LABELS,
    METRO_BBOX,
    NAME_EXCLUSIONS,
    NO_BRAND_LABEL,
    OTHER_BRANDS_LABEL,
    OVERSEAS_DEPTS,
    POP_MEASURE,
    RANDOM_SEED,
    STORE_FORMATS,
    TYPE_TO_ESSENTIAL,
)


# =============================================================================
# 1. DATA QUALITY (on the raw data)
# =============================================================================
def missing_values_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Missing values per column, as a count and a %.
    = df3.isnull().sum() and (df3.isnull().sum() / len(df3)) * 100 from the trees lab,
    gathered in one sorted table.
    """
    missing = pd.DataFrame({
        "missing": df.isnull().sum(),
        "missing_pct": (df.isnull().sum() / len(df) * 100).round(1),
    })
    missing.index.name = "column"
    return missing.sort_values("missing_pct", ascending=False).reset_index()


def quality_report(raw: pd.DataFrame) -> dict:
    """Every indicator shown in the "Data Quality" section of the app."""
    lon = pd.to_numeric(raw["X"], errors="coerce")
    lat = pd.to_numeric(raw["Y"], errors="coerce")
    com = raw["com_insee"]

    return {
        "n_rows": len(raw),
        "n_cols": raw.shape[1],
        "missing": missing_values_table(raw),
        # Duplicate detection (trees lab): fully identical rows...
        "duplicate_rows": int(raw.duplicated().sum()),
        # ... and, more precisely, the same OpenStreetMap object listed twice
        "duplicate_osm_id": int(raw["osm_id"].duplicated().sum()),
        # Validation checks
        "invalid_coords": int((lon.isna() | lat.isna()).sum()),
        "missing_com_insee": int(com.isna().sum()),
        "bad_format_com_insee": int((com.notna() & ~com.str.fullmatch(r"\d[\dAB]\d{3}", na=False)).sum()),
        "n_types": int(raw["type"].nunique()),
        "brand_fill_pct": round(raw["brand"].notna().mean() * 100, 1),
        # Sample for the missingno matrix (745,000 rows is too many for an image)
        "raw_sample": raw.sample(min(5_000, len(raw)), random_state=RANDOM_SEED),
    }


# =============================================================================
# 3. FEATURE ENGINEERING: elementary functions
#    (same idea as get_dom / get_hour / get_weekday in lab 1:
#     a small function on ONE value, applied to the column with .map)
# =============================================================================
def get_dept(com_insee):
    """'24520' -> '24' ; '2A004' -> '2A' ; '97411' -> '974' ; unknown -> NaN."""
    if not isinstance(com_insee, str):
        return np.nan
    dept = com_insee[:3] if com_insee.startswith("97") else com_insee[:2]
    return dept if dept in DEPT_NAMES else np.nan


def get_region(dept):
    """'35' -> 'Brittany'."""
    return DEPT_TO_REGION.get(dept, np.nan)


def get_essential_category(osm_type):
    """'bakery' -> 'Bakery' ; non-essential type -> NaN."""
    return TYPE_TO_ESSENTIAL.get(osm_type, np.nan)


# Regexes are compiled once (faster on thousands of rows)
_BRAND_REGEX = [(re.compile(pattern, re.IGNORECASE), label) for pattern, label in BRAND_PATTERNS]
_NAME_EXCLUSION_REGEX = re.compile(NAME_EXCLUSIONS, re.IGNORECASE)


def get_chain(text):
    """
    Harmonise a brand: 'E. Leclerc', 'Centre Commercial E.Leclerc' -> 'E.Leclerc',
    'Carrefour City' -> 'Carrefour', 'Hyper U' -> 'Système U'... ; unknown -> NaN.
    """
    if not isinstance(text, str):
        return np.nan
    for regex, label in _BRAND_REGEX:
        if regex.search(text):
            return label
    return np.nan


def get_chain_from_name(name):
    """
    Same thing from the store NAME, ignoring names such as
    'Épicerie du Carrefour' (a crossroads, not the brand).
    """
    if not isinstance(name, str) or _NAME_EXCLUSION_REGEX.search(name):
        return np.nan
    return get_chain(name)


# =============================================================================
# 2 + 3. CLEANING AND NEW COLUMNS
# =============================================================================
def clean(raw: pd.DataFrame) -> pd.DataFrame:
    """Clean the raw data and add the analysis columns."""
    df = raw.copy()

    # ---------------- Basic cleaning (trees lab) ----------------
    # Type conversions
    df = df.rename(columns={"X": "lon", "Y": "lat"})
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["last_update"] = pd.to_datetime(df["last_update"], errors="coerce")

    # String standardisation.
    # .str.strip() as in the lab, but NOT .str.title():
    # it would break brand names ("McDonald's" -> "Mcdonald'S").
    for col in ["type", "name", "brand", "com_nom"]:
        df[col] = df[col].str.strip()
    df["type"] = df["type"].str.lower()

    # Duplicates: an OSM object must only appear once
    df = df.drop_duplicates(subset="osm_id")

    # Drop rows without latitude / longitude (trees lab)
    df = df.dropna(subset=["lat", "lon"])

    # ---------------- Geography (.map functions, lab 1) ----------------
    df["dept"] = df["com_insee"].map(get_dept)
    df["dept_name"] = df["dept"].map(DEPT_NAMES)
    df["region"] = df["dept"].map(get_region)
    df["overseas"] = df["dept"].isin(OVERSEAS_DEPTS)

    # Coordinate validation: like the .between() filter in the trees lab,
    # a shop in a mainland department must lie inside mainland France
    in_metro_box = (
        df["lon"].between(METRO_BBOX["lon_min"], METRO_BBOX["lon_max"])
        & df["lat"].between(METRO_BBOX["lat_min"], METRO_BBOX["lat_max"])
    )
    df["suspicious_coords"] = df["dept"].notna() & ~df["overseas"] & ~in_metro_box

    # ---------------- Data freshness (pd.cut, trees lab) ----------------
    # last_update is NOT an opening date: it is the last OSM edit.
    # It is used to judge how fresh the data is (data quality section).
    reference_date = df["last_update"].max()
    df["age_years"] = (reference_date - df["last_update"]).dt.days / 365.25
    df["freshness"] = pd.cut(
        df["age_years"], bins=FRESHNESS_BINS, labels=FRESHNESS_LABELS, include_lowest=True
    )
    df["update_year"] = df["last_update"].dt.year

    # ---------------- Essential shops (part 1) ----------------
    df["essential_category"] = df["type"].map(get_essential_category)
    df["is_essential"] = df["essential_category"].notna()

    # ---------------- Retail chains (part 2) ----------------
    # The chain is only looked for in supermarkets / convenience stores:
    # otherwise drives, parapharmacies, Brico Leclerc... would be counted too.
    df["is_food_retail"] = df["type"].isin(FOOD_RETAIL_TYPES)
    food = df["is_food_retail"]

    from_brand = df.loc[food, "brand"].map(get_chain)
    # Fallback on the name when 'brand' is empty (brand is only filled for ~22% of rows)
    from_name = df.loc[food & df["brand"].isna(), "name"].map(get_chain_from_name)

    df["chain"] = from_brand.combine_first(from_name)          # NaN outside grocery retail
    df["chain_source"] = np.select(
        [df.index.isin(from_brand.dropna().index), df.index.isin(from_name.dropna().index)],
        ["brand", "name"],
        default="none",
    )

    return df.reset_index(drop=True)


# =============================================================================
# 4. ANALYSIS TABLES
# =============================================================================
def shannon_diversity(species_counts: pd.Series) -> float:
    """Shannon index — taken as is from the trees lab (species -> chains)."""
    proportions = species_counts / species_counts.sum()
    return entropy(proportions)


def essentials_by_dept(df: pd.DataFrame) -> pd.DataFrame:
    """
    Part 1 — per department and per essential category:
    - n                    : number of shops of that category
    - share_of_shops_pct   : share of that category among all the department's shops
    - coverage_pct         : share of municipalities (present in BANCO) with
                             at least one shop of that category
    "Long" format (one row per dept x category), handy for Plotly.
    """
    geo = df.dropna(subset=["dept"])
    ess = geo[geo["is_essential"]]
    categories = list(ESSENTIAL_CATEGORIES)

    # Number of shops: groupby + unstack, like df.groupby(['weekday','hour'])
    # .apply(count_rows).unstack() in lab 1 (.size() does the same, faster)
    counts = (
        ess.groupby(["dept", "essential_category"]).size()
        .unstack(fill_value=0)
        .reindex(columns=categories, fill_value=0)
    )
    # Number of municipalities with at least one shop of the category
    municipalities_with = (
        ess.groupby(["dept", "essential_category"])["com_insee"].nunique()
        .unstack(fill_value=0)
        .reindex(columns=categories, fill_value=0)
    )

    # Totals per department (+ mean point, to place a bubble on a map)
    totals = geo.groupby("dept").agg(
        n_shops=("osm_id", "size"),
        n_municipalities=("com_insee", "nunique"),
        lat=("lat", "mean"),
        lon=("lon", "mean"),
    )
    counts = counts.reindex(totals.index, fill_value=0)
    municipalities_with = municipalities_with.reindex(totals.index, fill_value=0)

    # Long format + indicators
    out = (
        counts.stack().rename("n").to_frame()
        .join(municipalities_with.stack().rename("n_municipalities_with"))
        .reset_index()
        .merge(totals, left_on="dept", right_index=True)
    )
    out["share_of_shops_pct"] = out["n"] / out["n_shops"] * 100
    out["coverage_pct"] = out["n_municipalities_with"] / out["n_municipalities"] * 100
    out["dept_name"] = out["dept"].map(DEPT_NAMES)
    out["region"] = out["dept"].map(get_region)
    return out


def chain_shares(df: pd.DataFrame, level: str = "region", top_n: int = 10, types=None) -> pd.DataFrame:
    """
    Part 2 — share of each chain in grocery retail, per region (or department).
    Same method as the heatmap in the trees lab:
        pivot = pd.crosstab(zone, species)
        pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100
    Chains outside the top N are grouped into 'Other brands'.
    types: OSM types to keep (e.g. ["supermarket"]) to compare like for like.
    Returns the % table (rows = zones, columns = chains).
    """
    food = df[df["type"].isin(types or FOOD_RETAIL_TYPES)].dropna(subset=[level])
    chain = food["chain"].fillna(NO_BRAND_LABEL)

    top = chain[chain != NO_BRAND_LABEL].value_counts().nlargest(top_n).index
    chain = chain.where(chain.isin(top) | (chain == NO_BRAND_LABEL), OTHER_BRANDS_LABEL)

    pivot = pd.crosstab(food[level], chain)
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    # Readable column order: top N (largest first), then Other brands, then No identified brand
    ordered = [b for b in top if b in pivot_pct.columns] + [
        c for c in [OTHER_BRANDS_LABEL, NO_BRAND_LABEL] if c in pivot_pct.columns
    ]
    pivot_pct = pivot_pct[ordered].round(1)
    pivot_pct.index.name = level
    pivot_pct.columns.name = "chain"
    return pivot_pct


def diversity_by_dept(df: pd.DataFrame, types=None) -> pd.DataFrame:
    """
    Part 2 — diversity of grocery chains per department.
    Same construction as diversity_summary in the trees lab:
    Shannon + richness + count, combined with .merge().
    The dominant chain and its share (concentration) are added.
    """
    food = df[df["type"].isin(types or FOOD_RETAIL_TYPES) & df["chain"].notna()].dropna(subset=["dept"])
    grouped = food.groupby("dept")["chain"]

    diversity = grouped.apply(lambda x: shannon_diversity(x.value_counts())).reset_index(name="shannon")
    richness = grouped.nunique().reset_index(name="n_chains")
    store_counts = grouped.size().reset_index(name="n_stores")
    dominant = grouped.agg(lambda x: x.value_counts().idxmax()).reset_index(name="dominant_chain")
    dominant_share = grouped.agg(
        lambda x: x.value_counts(normalize=True).iloc[0] * 100).reset_index(name="dominant_share_pct")

    summary = (
        diversity.merge(richness, on="dept")
        .merge(store_counts, on="dept")
        .merge(dominant, on="dept")
        .merge(dominant_share, on="dept")
        .sort_values("shannon", ascending=False)
    )
    summary["dept_name"] = summary["dept"].map(DEPT_NAMES)
    summary["region"] = summary["dept"].map(get_region)
    return summary.reset_index(drop=True)


def updates_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """Number of shops per year of last OSM edit (like the frequency plots of lab 1)."""
    counts = df["update_year"].dropna().astype(int).value_counts().sort_index()
    return counts.rename_axis("year").reset_index(name="n_shops")


# Columns used in the analysis that are stored as 'category' in the app (to save memory)
_CATEGORY_COLUMNS = ["type", "dept", "dept_name", "region", "essential_category", "chain", "chain_source"]

# Raw columns actually used by clean(); the others (phone, email, website...) are only
# looked at in the data-quality report, then dropped to save memory.
RAW_COLUMNS_USED = ["X", "Y", "osm_id", "type", "name", "brand", "address", "com_insee", "com_nom", "last_update"]

# Columns kept in the "shops" table used by the maps and KPIs
APP_COLUMNS = [
    "osm_id", "lon", "lat", "type", "name", "brand", "address", "com_insee", "com_nom",
    "dept", "dept_name", "region", "overseas", "suspicious_coords",
    "update_year", "freshness", "essential_category", "is_essential",
    "is_food_retail", "chain", "chain_source",
]


# =============================================================================
# 5. POPULATION (second dataset: INSEE legal populations, joined on the INSEE code)
# =============================================================================
def clean_population(pop_raw: pd.DataFrame) -> pd.DataFrame:
    """
    INSEE file in long format -> one row per municipality:
    keep municipalities (GEO_OBJECT == 'COM') and the municipal population (PMUN).
    Paris, Lyon and Marseille are kept as whole cities (75056, 69123, 13055), like in BANCO,
    so their districts ('ARM') are dropped.
    """
    pop = pop_raw[(pop_raw["GEO_OBJECT"] == "COM") & (pop_raw["POPREF_MEASURE"] == POP_MEASURE)]
    pop = pop.rename(columns={"GEO": "com_insee"})[["com_insee", "OBS_VALUE"]].copy()
    pop["population"] = pd.to_numeric(pop["OBS_VALUE"], errors="coerce").astype("Int64")
    pop = pop.drop(columns="OBS_VALUE").drop_duplicates(subset="com_insee")
    pop["dept"] = pop["com_insee"].map(get_dept)
    pop["dept_name"] = pop["dept"].map(DEPT_NAMES)
    pop["region"] = pop["dept"].map(get_region)
    return pop.reset_index(drop=True)


def shops_by_commune(df: pd.DataFrame, population: pd.DataFrame) -> pd.DataFrame:
    """
    One row per municipality of the INSEE file, with its number of shops.
    Left join FROM the population side: municipalities with no shop at all are kept (n_shops = 0),
    which is exactly what BANCO alone cannot show.
    """
    counts = df.dropna(subset=["com_insee"]).groupby("com_insee").agg(
        n_shops=("osm_id", "size"), com_nom=("com_nom", "first"),
        lat=("lat", "mean"), lon=("lon", "mean"),
    )
    out = population.merge(counts, left_on="com_insee", right_index=True, how="left")
    out["n_shops"] = out["n_shops"].fillna(0).astype(int)
    out["population"] = out["population"].astype(float)
    return out


def shops_per_capita_by_dept(communes: pd.DataFrame, geo: pd.DataFrame) -> pd.DataFrame:
    """Shops per 1,000 inhabitants per department (+ mean point of the shops, for the bubble map)."""
    dept = communes.dropna(subset=["dept"]).groupby("dept").agg(
        population=("population", "sum"), n_shops=("n_shops", "sum"),
        n_municipalities=("com_insee", "size"),
        n_municipalities_no_shop=("n_shops", lambda s: int((s == 0).sum())),
    )
    dept["shops_per_1000"] = dept["n_shops"] / dept["population"] * 1000
    position = geo.drop_duplicates("dept").set_index("dept")[["lat", "lon"]]
    dept = dept.join(position, how="inner").reset_index()
    dept["dept_name"] = dept["dept"].map(DEPT_NAMES)
    dept["region"] = dept["dept"].map(get_region)
    return dept


def population_quality(df: pd.DataFrame, population: pd.DataFrame) -> dict:
    """Join checks between BANCO and the INSEE file (shown in the Data Quality section)."""
    with_code = df.dropna(subset=["com_insee"])
    matched = with_code["com_insee"].isin(population["com_insee"])
    unmatched = with_code.loc[~matched, "com_insee"]
    return {
        "pop_n_municipalities": len(population),
        "pop_match_pct": matched.mean() * 100,
        "pop_unmatched_shops": int((~matched).sum()),
        # 976 = Mayotte (not in the INSEE file); 975, 977, 978, 98x = overseas collectivities
        "pop_unmatched_prefixes": unmatched.str[:3].value_counts().head(8).to_dict(),
    }


def analysis_tables(shops: pd.DataFrame, population: pd.DataFrame | None = None) -> dict:
    """
    Aggregated tables for parts 1 and 2. Called once in make_tables(), and again
    by the app when the "last OSM update" filter changes the set of shops.
    """
    df = shops.copy()
    for col in _CATEGORY_COLUMNS:          # back to plain values for groupby / crosstab
        if col in df.columns and isinstance(df[col].dtype, pd.CategoricalDtype):
            df[col] = df[col].astype(object)

    geo = essentials_by_dept(df)
    pop_tables = {}
    if population is not None:
        communes = shops_by_commune(df, population)
        pop_tables = {"communes": communes, "pop_dept": shops_per_capita_by_dept(communes, geo)}

    return {
        **pop_tables,
        # Part 1: essential shops per department (with lat/lon for the bubble map)
        "geo": geo,
        # Part 2: one set of tables per store format ("Store format" filter in the sidebar)
        "by_region": {fmt: chain_shares(df, level="region", types=t) for fmt, t in STORE_FORMATS.items()},
        "by_dept": {fmt: chain_shares(df, level="dept", types=t) for fmt, t in STORE_FORMATS.items()},
        "diversity": {fmt: diversity_by_dept(df, types=t) for fmt, t in STORE_FORMATS.items()},
    }


def make_tables(df_raw: pd.DataFrame, pop_raw: pd.DataFrame | None = None) -> dict:
    """
    Everything the app needs, from the raw data (signature of the project skeleton,
    plus the optional INSEE population file):
        tables["shops"]      cleaned shops (maps, KPIs)
        tables["quality"]    data-quality indicators (on the raw data)
        tables["timeseries"] shops per year of last OSM update
        tables["geo"]        essential shops per department
        tables["by_region"]  chain shares per region      (one table per store format)
        tables["by_dept"]    chain shares per department  (one table per store format)
        tables["diversity"]  chain diversity per department (one table per store format)
        tables["population"] INSEE population per municipality
        tables["communes"]   shops + population per municipality (incl. municipalities with no shop)
        tables["pop_dept"]   shops per 1,000 inhabitants per department
    """
    quality = quality_report(df_raw)                        # on ALL raw columns
    df = clean(df_raw[RAW_COLUMNS_USED])                    # then only the useful ones
    population = clean_population(pop_raw) if pop_raw is not None else None
    if population is not None:
        quality.update(population_quality(df, population))

    shops = df[APP_COLUMNS].copy()
    shops[_CATEGORY_COLUMNS] = shops[_CATEGORY_COLUMNS].astype("category")   # ~5x less memory

    return {
        "shops": shops,
        "quality": quality,
        "timeseries": updates_by_year(df),
        "population": population,
        **analysis_tables(df, population),
    }
