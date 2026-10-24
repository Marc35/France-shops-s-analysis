"""
Deep dives: comparisons, distributions, drill-downs (sections/deep_dives.py in the project brief).
"""
import streamlit as st

from sections.overview import MIN_MUNICIPALITIES
from utils import viz
from utils.constants import DEPT_NAMES


# =============================================================================
# Part 1 — Essential shops
# =============================================================================
def essentials_drilldown(geo_sel, cat_sel, metric):
    """Which essential shop is the scarcest? + full table by department."""
    by_cat = (
        geo_sel.groupby("essential_category")[["n_municipalities_with", "n_municipalities"]].sum()
        .assign(coverage_pct=lambda d: d["n_municipalities_with"] / d["n_municipalities"] * 100)
        .reset_index()
    )
    viz.bar_chart(
        by_cat, x="coverage_pct", y="essential_category",
        title="Average coverage, by type of essential shop",
        x_label="Municipalities covered (%)", highlight=metric, x_suffix=" %",
        alt="Bar chart comparing municipality coverage across types of essential shops.",
    )

    with st.expander("See the table by department"):
        table = cat_sel[["dept", "dept_name", "region", "n", "n_municipalities", "coverage_pct", "share_of_shops_pct"]]
        table = table.sort_values("coverage_pct").rename(columns={
            "dept": "Code", "dept_name": "Department", "region": "Region", "n": metric,
            "n_municipalities": "Municipalities in database", "coverage_pct": "Coverage (%)",
            "share_of_shops_pct": "Share of all shops (%)",
        })
        st.dataframe(table.round(1), hide_index=True, width="stretch")
        st.download_button(
            "Download (CSV)", table.to_csv(index=False).encode("utf-8"),
            file_name=f"coverage_{metric.lower().replace(' ', '_')}.csv", mime="text/csv",
        )


# =============================================================================
# Part 2 — Retail chains
# =============================================================================
def chain_shares_view(tables_f, store_format, regions, single_region):
    """
    Chain-share table to show: by region, or — drill-down — by department
    when a single region is selected.
    """
    if single_region:
        diversity = tables_f["diversity"][store_format]
        depts = diversity.loc[diversity["region"] == regions[0], "dept"].tolist()
        shares = tables_f["by_dept"][store_format].loc[lambda t: t.index.isin(depts)].copy()
        shares.index = shares.index.map(DEPT_NAMES)
        return shares, "Department"
    shares = tables_f["by_region"][store_format].loc[lambda t: t.index.isin(regions)]
    return shares, "Region"


def brands_drilldown(div_sel):
    """Market concentration: Shannon index (trees lab), lowest = few chains share the market."""
    div_sel = div_sel[div_sel["n_stores"] >= MIN_MUNICIPALITIES]
    if div_sel.empty:
        return
    viz.bar_chart(
        div_sel.nsmallest(10, "shannon"), x="shannon", y="dept_name", ascending=True,
        title="The 10 departments where supply is most concentrated (lowest Shannon index)",
        x_label="Shannon diversity index",
        hover_data={"dominant_chain": True, "dominant_share_pct": ":.0f", "n_stores": ":,"},
        alt="Ranking of the departments where only a few chains share the market.",
    )
    st.caption(
        "Shannon index: the lower it is, the more a few chains share the local market. "
        "Hover a bar to see the dominant chain and its share."
    )
