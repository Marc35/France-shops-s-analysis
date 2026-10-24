"""
Data storytelling dashboard — local shops in France (BANCO open data).
Run with:   streamlit run app.py

Built on the project skeleton (page 3 of the brief): same blocks, in the same order.
Comments marked "Skeleton:" show which line of the skeleton each block fills in.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from sections import conclusions, deep_dives, intro, overview
from utils.constants import (
    DEFAULT_BRANDS, DEFAULT_STORE_FORMAT, ESSENTIAL_CATEGORIES, ESSENTIAL_PLURALS, MAINLAND_REGIONS,
    NO_BRAND_LABEL, OTHER_BRANDS_LABEL, REGIONS, STORE_FORMATS,
)
from utils.io import license_text, load_data, load_population
from utils.prep import analysis_tables, make_tables
from utils.style import apply_style, chapter, hero
from utils.viz import bar_chart, heatmap_chart, line_chart, map_chart, missing_matrix, scatter_chart

st.set_page_config(page_title="Data Storytelling Dashboard — Local shops in France", page_icon="🥖", layout="wide")
apply_style()   # custom CSS (assets/style.css); colours and fonts: .streamlit/config.toml

# School logo, top-left of the sidebar (and of the page when the sidebar is closed)
LOGO = Path(__file__).resolve().parent / "assets" / "efrei_logo.png"
st.logo(str(LOGO), size="large", link="https://www.efrei.fr")


@st.cache_data(show_spinner="Loading and preparing the data (first run: about a minute)…")
def get_data():
    df_raw = load_data()
    pop_raw = load_population()                 # second dataset: INSEE population per municipality
    tables = make_tables(df_raw, pop_raw)       # cleaning + feature engineering + join + aggregated tables
    # The skeleton also returns df_raw. It is not used by the page, and st.cache_data hands back
    # a copy of everything it returns at each rerun (about 240 MB for the raw table), so only the
    # prepared tables are returned. The raw data stays available through load_data().
    return tables


@st.cache_data(show_spinner="Updating the tables for the selected years…")
def get_tables_for_years(year_min: int, year_max: int):
    """Recompute the analysis tables when the "last OSM update" filter is used."""
    tables = get_data()
    shops = tables["shops"]
    return analysis_tables(shops[shops["update_year"].between(year_min, year_max)], tables["population"])


def fmt(n, decimals=0):
    """Number with a thin space as thousands separator: 745 438 ; 22.4."""
    return f"{n:,.{decimals}f}".replace(",", " ")


# Skeleton: st.title / st.caption — the title is drawn as an enamel street sign
hero(
    kicker="Data storytelling dashboard",
    title="Bread, medicine, groceries",
    subtitle="Is France equal when it comes to local shops?",
)
st.caption(license_text())

# Skeleton: raw, tables = get_data() — called BEFORE the sidebar here,
# because the filter options (years, chains) come from the data.
tables = get_data()
shops = tables["shops"]

with st.container(key="intro"):
    intro.render(tables)    # context, objectives, data caveats (sections/intro.py)

# -----------------------------------------------------------------------------
# Skeleton: sidebar filters (Region / Date range / Metric)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("Filters")

    regions = st.multiselect(
        "Region", list(REGIONS),
        placeholder="Mainland France (all regions)",
        help="Leave empty to keep all mainland regions. Overseas regions can be selected one by one.",
    )

    # Skeleton: date_range. BANCO has no opening date, only the date of the last OSM edit:
    # this filter keeps only recently checked shops, to test if the results hold on fresher data.
    year_min, year_max = int(shops["update_year"].min()), int(shops["update_year"].max())
    date_range = st.slider(
        "Last OSM update (data freshness)", year_min, year_max, (year_min, year_max),
        help="Keep only the shops whose OpenStreetMap entry was edited in this period. "
             "Narrowing it removes entries that may be outdated.",
    )

    metric = st.selectbox(
        "Metric — essential shop studied (part 1)", list(ESSENTIAL_CATEGORIES),
    )

    st.divider()
    store_format = st.radio(
        "Store format (part 2)", list(STORE_FORMATS),
        index=list(STORE_FORMATS).index(DEFAULT_STORE_FORMAT),
        help="Compare chains like for like: a hypermarket and a convenience store each count as one store.",
    )
    top_chains = tables["by_region"][store_format].columns.drop(
        [OTHER_BRANDS_LABEL, NO_BRAND_LABEL], errors="ignore"
    ).tolist()
    chains = st.multiselect(
        "Chains to compare (part 2)", top_chains,
        default=[c for c in DEFAULT_BRANDS if c in top_chains] or top_chains[:3],
        max_selections=3,
        help="3 chains maximum so the colours stay readable.",
    )

# -----------------------------------------------------------------------------
# Apply the filters
# -----------------------------------------------------------------------------
selected_regions = regions or MAINLAND_REGIONS
full_period = tuple(date_range) == (year_min, year_max)

shops_sel = shops[shops["region"].isin(selected_regions)]
if not full_period:
    shops_sel = shops_sel[shops_sel["update_year"].between(*date_range)]
tables_f = tables if full_period else get_tables_for_years(*date_range)

geo_all = tables_f["geo"]
cat_all = geo_all[geo_all["essential_category"] == metric]                 # whole country (baseline)
geo_sel = geo_all[geo_all["region"].isin(selected_regions)]
cat_sel = geo_sel[geo_sel["essential_category"] == metric]                 # selected regions

# -----------------------------------------------------------------------------
# Skeleton: KPI row
# -----------------------------------------------------------------------------
kpis = overview.kpi_values(shops_sel, cat_sel, cat_all)
# "∆ vs. baseline" (skeleton): only meaningful when a region is selected
def delta(value):
    return f"{value:+.1f} pts vs. France" if regions else None

c1, c2, c3 = st.columns(3)
c1.metric(
    "Shops recorded", fmt(kpis["n_shops"]), border=True,
    help=f"In {fmt(kpis['n_municipalities'])} municipalities, for the selected regions and period.",
)
c2.metric(
    f"Municipalities with at least one {metric.lower()}", f"{kpis['coverage']:.1f} %",
    delta(kpis["coverage_delta"]), border=True,
    help="Among the municipalities that have at least one shop in the database.",
)
c3.metric(
    f"{metric} share of all shops", f"{kpis['share']:.1f} %",
    delta(kpis["share_delta"]), border=True,
)

# -----------------------------------------------------------------------------
# Skeleton: "Trends over time"
# BANCO has no time dimension (last_update is not an opening date), so this slot
# gives the high-level overview instead: where are the shops?
# -----------------------------------------------------------------------------
st.subheader("Overview: where are the shops?")
map_chart(
    shops_sel, kind="density", title="Density of shops",
    alt="Density map of shops: the darkest areas have the most shops.",
)
st.caption(
    "Colour intensity uses a logarithmic scale, so that small towns stay visible next to Paris."
)

# --- Second map: the same shops, divided by the number of inhabitants (INSEE) ---------------
st.subheader("Shops and population: more people, more shops?")
communes_sel = tables_f["communes"][tables_f["communes"]["region"].isin(selected_regions)]
pop_dept_sel = tables_f["pop_dept"][tables_f["pop_dept"]["region"].isin(selected_regions)]
pop_facts = overview.population_insights(communes_sel, pop_dept_sel)

if pop_facts is None:
    st.info("No population data for the selected regions (Mayotte is not covered by the INSEE file).")
else:
    # Colour = how far each department is from the average, on a log2 scale:
    # -1 = half as many shops per inhabitant, 0 = average, +1 = twice as many.
    vs_average = np.log2(pop_dept_sel["shops_per_1000"] / pop_facts["per_1000"]).clip(-1, 1)
    map_chart(
        pop_dept_sel.assign(population_k=pop_dept_sel["population"] / 1000, vs_average=vs_average),
        kind="bubble", size="population_k", color="vs_average",
        diverging=True, color_midpoint=0, color_range=[-1, 1],
        colorbar_ticks={-1: "half the average", -0.5: "", 0: "average", 0.5: "", 1: "twice the average"},
        title="Population (bubble size) and shops per inhabitant compared with the average (colour)",
        color_label="Shops per inhabitant", hover_name="dept_name",
        hover_data={"population_k": ":,.0f", "n_shops": ":,", "shops_per_1000": ":.1f",
                    "vs_average": False, "lat": False, "lon": False},
        alt="Map of departments: bubble size = population, colour = shops per inhabitant, "
            "blue above the average and orange below.",
    )
    st.caption(
        f"Average of the selection: {pop_facts['per_1000']:.1f} shops per 1,000 inhabitants. "
        "Blue = better equipped than average, orange = less. Hover a bubble for the population (thousands) "
        "and the exact ratio."
    )

    # Log scales: municipalities with 0 shop or 0 inhabitant cannot be drawn
    # (e.g. the "villages that died for France" near Verdun have no residents)
    with_shops = communes_sel[(communes_sel["n_shops"] > 0) & (communes_sel["population"] > 0)]
    scatter_chart(
        with_shops, x="population", y="n_shops",
        title="Population and number of shops, one point per municipality",
        x_label="Inhabitants (log scale)", y_label="Shops (log scale)",
        hover_name="com_nom", hover_data={"dept_name": True, "population": ":,.0f", "n_shops": ":,"},
        fit=(pop_facts["slope"], pop_facts["intercept"]), fit_label="Trend (log-log regression)",
        alt="Scatter plot: the number of shops rises almost in proportion to the population.",
    )

    slope = pop_facts["slope"]
    if slope > 1.15:
        slope_text = "more than twice as many shops: larger towns concentrate retail"
    elif slope < 0.85:
        slope_text = "fewer than twice as many shops: small municipalities are relatively well equipped"
    else:
        slope_text = "about twice as many shops"
    top = ", ".join(f"{name} ({value:.0f})" for name, value in pop_facts["top"])
    bottom = ", ".join(f"{name} ({value:.0f})" for name, value in pop_facts["bottom"])
    with st.container(border=True):
        st.markdown(
            f"""
            **What these maps tell us**

            - **Shops follow people.** Across {fmt(pop_facts['n_municipalities'])} municipalities, population and
              number of shops are strongly linked (correlation {pop_facts['r']:.2f} on log scales). The trend's slope
              is {slope:.2f}: a municipality with twice as many inhabitants has {slope_text}.
              The first map is therefore, above all, a map of where people live.
            - **The exceptions are the story.** Per inhabitant, the best-equipped departments are {top} shops per
              1,000 inhabitants, against {bottom} for the least equipped. A high ratio usually means shops also
              serve visitors (tourism, people coming to work); a low one, that residents shop elsewhere, as in the
              suburbs of large cities.
            - **Shopless municipalities are many but small.** {pop_facts['no_shop_pct']:.0f}% of municipalities have
              no shop at all in the database, yet they are home to only {pop_facts['no_shop_pop_pct']:.1f}% of the
              population (median: {pop_facts['no_shop_median_pop']:.0f} inhabitants). For these residents,
              every errand means a trip to the next town.

            *A correlation is not a cause, and OpenStreetMap is better filled in cities, which may slightly
            strengthen the link.*
            """
        )

# -----------------------------------------------------------------------------
# Skeleton: "Compare regions" — part 1, essential shops
# -----------------------------------------------------------------------------
chapter(1, f"Essential shops: where are {ESSENTIAL_PLURALS[metric]} scarce?")
headline = overview.essentials_headline(cat_sel, metric)
if headline:
    st.info(headline)

map_chart(
    cat_sel, kind="bubble", size="n", color="coverage_pct",
    title=f"{metric}: number (size) and municipality coverage (colour), by department",
    color_label="Municipalities covered (%)", hover_name="dept_name",
    hover_data={"n": ":,", "n_municipalities": ":,", "coverage_pct": ":.1f",
                "share_of_shops_pct": ":.1f", "lat": False, "lon": False},
    alt=f"Map of departments: bubble size = number of shops ({metric.lower()}), "
        "colour = share of municipalities with at least one.",
)
st.caption(
    "Coverage = share of the municipalities present in the database that have at least one shop of this type. "
    "Municipalities with no shop at all in the database are not counted: reality is probably even less favourable."
)

col1, col2 = st.columns(2)
with col1:
    reliable = cat_sel[cat_sel["n_municipalities"] >= overview.MIN_MUNICIPALITIES]
    bar_chart(
        reliable.nsmallest(10, "coverage_pct"), x="coverage_pct", y="dept_name", ascending=True,
        title="The 10 least-covered departments", x_label="Municipalities covered (%)", x_suffix=" %",
        hover_data={"n": ":,", "n_municipalities": ":,"},
        alt="Ranking of the 10 departments with the lowest coverage.",
    )
with col2:
    deep_dives.essentials_drilldown(geo_sel, cat_sel, metric)

# -----------------------------------------------------------------------------
# Skeleton: "Compare regions" — part 2, retail chains
# -----------------------------------------------------------------------------
chapter(2, "Retail chains: does each region have its champion?")
st.caption(
    f"Store format: **{store_format}** (change it in the sidebar). Stores are counted, not floor areas "
    "or turnover: comparing like for like stops a convenience store from weighing as much as a hypermarket."
)
single_region = len(regions) == 1
shares, level_label = deep_dives.chain_shares_view(tables_f, store_format, selected_regions, single_region)

if shares.empty:
    st.info("No chain data for the selected filters.")
else:
    headline = overview.brands_headline(shares, level_label)
    if headline:
        st.info(headline)

    selected = [c for c in chains if c in shares.columns]
    if selected:
        duel = (
            shares[selected].reset_index(names=level_label)
            .melt(id_vars=level_label, var_name="Chain", value_name="Share (%)")
        )
        duel[level_label] = duel[level_label].astype(str)
        fig = bar_chart(
            duel, x=level_label, y="Share (%)", color="Chain", category_order=selected,
            title=f"{' vs '.join(selected)}: share of stores by {level_label.lower()}",
            x_label="", y_label="Share of stores (%)", x_suffix=" %", show=False,
        )
        order = shares[selected[0]].sort_values(ascending=False).index.astype(str).tolist()
        fig.update_xaxes(categoryorder="array", categoryarray=order)
        st.plotly_chart(
            fig, width="stretch", theme=None,
            alt=f"Grouped bars comparing the share of {', '.join(selected)} in each {level_label.lower()}.",
        )
        st.caption(f"Areas sorted by the share of {selected[0]}, highest first.")

    heatmap_chart(
        shares, title=f"Share of each chain — {store_format.lower()} (%)", y_label=level_label,
        alt=f"Colour table of chain shares by {level_label.lower()}.",
    )
    st.caption(
        "How to read: each row adds up to 100%. "
        f"“{NO_BRAND_LABEL}” = independent shops OR brand not filled in OpenStreetMap."
    )

# -----------------------------------------------------------------------------
# Skeleton: "Map view"
# -----------------------------------------------------------------------------
st.subheader("Map view: where are the selected chains?")
if chains:
    stores = shops_sel[shops_sel["type"].isin(STORE_FORMATS[store_format]) & shops_sel["chain"].isin(chains)]
    stores = stores.assign(chain=stores["chain"].astype(str))
    map_chart(
        stores, kind="points", color="chain", category_order=chains,
        title="Stores of the selected chains", hover_name="name",
        hover_data={"com_nom": True, "type": True, "lat": False, "lon": False},
        alt="Map of the stores of the selected chains, one colour per chain.",
    )
else:
    st.caption("Pick chains in the sidebar to show the comparison and the map.")

div_sel = tables_f["diversity"][store_format]
deep_dives.brands_drilldown(div_sel[div_sel["region"].isin(selected_regions)])

# -----------------------------------------------------------------------------
# Skeleton: Data Quality & Limitations
# -----------------------------------------------------------------------------
st.markdown("### Data Quality & Limitations")
quality = tables["quality"]
q1, q2, q3, q4 = st.columns(4)
q1.metric("Raw rows", fmt(quality["n_rows"]), border=True)
q2.metric("Duplicates (same OSM object)", fmt(quality["duplicate_osm_id"]), border=True)
q3.metric("No municipality code", fmt(quality["missing_com_insee"]), border=True)
q4.metric("Brand filled in", f"{quality['brand_fill_pct']:.1f} %", border=True)

tab1, tab2, tab3 = st.tabs(["Missing values", "Freshness", "Checks"])
with tab1:
    bar_chart(
        quality["missing"], x="missing_pct", y="column",
        title="Share of missing values per column", x_label="Missing values (%)", x_suffix=" %",
        hover_data={"missing": ":,"},
        alt="Percentage of missing values for each of the 21 columns.",
    )
    with st.expander("Missing-value matrix (missingno)"):
        missing_matrix(quality["raw_sample"])
        st.caption("Each white line = a missing value. Sample of 5,000 shops.")
with tab2:
    line_chart(
        tables["timeseries"], x="year", y="n_shops",
        title="Data freshness: year of the last OpenStreetMap edit",
        x_label="Year of last edit", y_label="Number of shops",
        alt="Number of shops by year of their last edit in OpenStreetMap.",
    )
    st.caption("A shop not edited for a long time may have closed or changed brand without the map being updated.")
with tab3:
    checks = pd.DataFrame({
        "Check": [
            "Fully duplicated rows", "Duplicated OSM objects (removed)", "Invalid coordinates (removed)",
            "Missing municipality code", "Badly formatted municipality code",
            "Point outside mainland France for a mainland department", "Distinct shop types",
            "Shops whose municipality is found in the INSEE population file",
            "Shops in areas not covered by the INSEE file (Mayotte, overseas collectivities)",
        ],
        "Result": [
            quality["duplicate_rows"], quality["duplicate_osm_id"], quality["invalid_coords"],
            quality["missing_com_insee"], quality["bad_format_com_insee"],
            int(shops["suspicious_coords"].sum()), quality["n_types"],
            f"{quality['pop_match_pct']:.1f} %", quality["pop_unmatched_shops"],
        ],
    })
    checks["Result"] = checks["Result"].map(lambda v: fmt(v) if isinstance(v, (int, float)) else v)
    st.dataframe(checks, hide_index=True, width="stretch")

st.info(
    "**Limits to keep in mind**\n"
    "- Collaborative data (OpenStreetMap): coverage depends on contributors' activity, "
    "better in cities than in the countryside.\n"
    "- The brand is only filled for part of the stores; it is completed from the store name when possible.\n"
    "- Population is the INSEE resident population: shops per inhabitant ignore visitors "
    "(tourists, commuters), which inflates the ratio in tourist areas and city centres.\n"
    "- These results describe a situation; they do not prove causes."
)

# -----------------------------------------------------------------------------
# Skeleton: Key Insights & Next Steps
# -----------------------------------------------------------------------------
st.markdown("### Key Insights & Next Steps")
conclusions.render()
