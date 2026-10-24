"""
Overview: KPIs and high-level insights (sections/overview.py in the project brief).
These functions only COMPUTE; app.py displays the KPI row, as in the skeleton.
"""
import numpy as np
import pandas as pd

from utils.constants import NO_BRAND_LABEL, OTHER_BRANDS_LABEL

# Below this number of municipalities, a coverage rate is not representative
MIN_MUNICIPALITIES = 20


def _coverage(cat: pd.DataFrame) -> float:
    """Share of municipalities with at least one shop of the category, over a set of departments."""
    return cat["n_municipalities_with"].sum() / cat["n_municipalities"].sum() * 100 if len(cat) else float("nan")


def _share(cat: pd.DataFrame) -> float:
    """Share of the category among all shops, over a set of departments."""
    return cat["n"].sum() / cat["n_shops"].sum() * 100 if len(cat) else float("nan")


def kpi_values(shops_sel: pd.DataFrame, cat_sel: pd.DataFrame, cat_all: pd.DataFrame) -> dict:
    """
    KPI row values, tied to the filters.
    cat_sel / cat_all: rows of tables["geo"] for the chosen metric, selected regions vs whole country.
    The baseline ("∆ vs. France") is the whole country.
    """
    return {
        "n_shops": len(shops_sel),
        "n_municipalities": shops_sel["com_insee"].nunique(),
        "coverage": _coverage(cat_sel),
        "coverage_delta": _coverage(cat_sel) - _coverage(cat_all),
        "share": _share(cat_sel),
        "share_delta": _share(cat_sel) - _share(cat_all),
    }


def essentials_headline(cat_sel: pd.DataFrame, metric: str) -> str | None:
    """One-sentence headline insight for part 1, computed from the data."""
    reliable = cat_sel[cat_sel["n_municipalities"] >= MIN_MUNICIPALITIES]
    if reliable.empty:
        return None
    worst = reliable.nsmallest(1, "coverage_pct").iloc[0]
    best = reliable.nlargest(1, "coverage_pct").iloc[0]
    return (
        f"**{worst['dept_name']}**: only **{worst['coverage_pct']:.0f}%** of the municipalities in the database "
        f"have at least one {metric.lower()}, against **{best['coverage_pct']:.0f}%** in {best['dept_name']}."
    )


def brands_headline(shares: pd.DataFrame, level_label: str) -> str | None:
    """One-sentence headline insight for part 2: the chain ranked #1 in the most areas."""
    named = shares.drop(columns=[OTHER_BRANDS_LABEL, NO_BRAND_LABEL], errors="ignore")
    if named.empty:
        return None
    leaders = named.idxmax(axis=1).value_counts()
    return (
        f"**{leaders.index[0]}** is the #1 chain in **{leaders.iloc[0]}** "
        f"{level_label.lower()}(s) out of {len(shares)}."
    )


def population_insights(communes_sel: pd.DataFrame, pop_dept_sel: pd.DataFrame) -> dict | None:
    """
    Figures for the "shops and population" maps, computed on the selected regions:
    - correlation between population and number of shops (log-log, one point per municipality)
    - slope of the log-log regression: 1 means "twice the people, twice the shops"
    - municipalities with no shop at all, and the share of the population living there
    - departments with the most / fewest shops per 1,000 inhabitants
    """
    if communes_sel.empty or pop_dept_sel.empty:
        return None
    with_shops = communes_sel[(communes_sel["n_shops"] > 0) & (communes_sel["population"] > 0)]
    log_pop, log_shops = np.log10(with_shops["population"]), np.log10(with_shops["n_shops"])
    slope, intercept = np.polyfit(log_pop, log_shops, 1)
    no_shop = communes_sel[communes_sel["n_shops"] == 0]
    ranked = pop_dept_sel.sort_values("shops_per_1000", ascending=False)
    return {
        "r": float(np.corrcoef(log_pop, log_shops)[0, 1]),
        "slope": float(slope),
        "intercept": float(intercept),
        "n_municipalities": len(communes_sel),
        "no_shop_pct": len(no_shop) / len(communes_sel) * 100,
        "no_shop_pop_pct": no_shop["population"].sum() / communes_sel["population"].sum() * 100,
        "no_shop_median_pop": float(no_shop["population"].median()) if len(no_shop) else float("nan"),
        "per_1000": communes_sel["n_shops"].sum() / communes_sel["population"].sum() * 1000,
        "top": ranked.head(3)[["dept_name", "shops_per_1000"]].values.tolist(),
        "bottom": ranked.tail(3)[::-1][["dept_name", "shops_per_1000"]].values.tolist(),
    }
