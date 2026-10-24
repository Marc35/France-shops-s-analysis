"""Intro: context, objectives and data caveats (sections/intro.py in the project brief)."""
import streamlit as st


def render(tables):
    """Hook, questions, audience and data caveats."""
    communes = tables["communes"]                       # every municipality of the INSEE file
    no_shop = communes["n_shops"] == 0
    no_shop_pct = no_shop.mean() * 100
    no_shop_pop_pct = communes.loc[no_shop, "population"].sum() / communes["population"].sum() * 100

    st.markdown(
        f"""
        Buying bread, going to the pharmacy, doing the weekly shopping: these everyday errands depend on
        the shops around you. Yet out of France's **{len(communes):,} municipalities**, **{no_shop_pct:.0f}%**
        do not have a single shop in this database. They are small: together they are home to
        {no_shop_pop_pct:.1f}% of the population.

        **The questions this dashboard answers:**
        1. In which areas are essential shops (bakery, pharmacy, post office…) scarce?
        2. Which supermarket chains dominate each region? Are there regional "strongholds"?

        **Who is it for?** Local authorities looking for fragile areas, and anyone curious about the
        geography of retail in France.
        """
    )

    with st.expander("About the data and its limits"):
        st.markdown(
            """
            - BANCO lists the shops mapped in **OpenStreetMap**, a collaborative map. A shop missing from
              the database is **not necessarily** missing on the ground: cities are better mapped than
              the countryside.
            - The database has **no opening date**: `last_update` is the date of the last OSM edit.
              It cannot be used to study change over time.
            - Population comes from **INSEE** (legal population 2023, municipal population), joined on the
              municipality code. Mayotte is not covered by this file.
            """
        )
