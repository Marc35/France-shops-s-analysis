"""
Conclusions: insights, implications, next steps (sections/conclusions.py in the project brief).

The figures below summarise the whole story for mainland France. They were computed with the
project's own tables (BANCO export of 20 October 2026, INSEE 2023 population) and do not change
with the sidebar filters. If the data is downloaded again, check them in the app before quoting them.
"""
import streamlit as st


def render():
    # --- Back to the opening question (the hook of the title plaque) ---------------------------
    st.markdown(
        "Back to our question: **is France equal when it comes to local shops?** No. "
        "But the gaps are not only where one would expect them."
    )

    # --- Key insights: one headline sentence each, then the evidence ---------------------------
    st.success(
        "**1. The countryside lacks shops more than shoppers.** 36% of mainland municipalities have no "
        "shop at all in the database, yet only 4.7% of residents (3.1 million people) live there. "
        "For essentials the gap is wider: 11.3 million residents (17%) live in a municipality with no "
        "bakery recorded, 13.4 million (20%) with no pharmacy. In the Hautes-Pyrénées and the Ariège, "
        "fewer than one listed municipality in four has a bakery."
    )
    st.success(
        "**2. Per resident, the thinnest offer is in the suburbs.** The number of shops grows almost in "
        "proportion to the population (correlation 0.80). Per inhabitant, Seine-Saint-Denis has 5 shops "
        "per 1,000 residents: half the national average (10.8) and a fifth of Paris (24.5). At the top, "
        "tourist departments such as the Hautes-Alpes (23) have shops that also serve visitors."
    )
    st.success(
        "**3. There is no national supermarket champion: each region has its own.** Intermarché leads "
        "7 of the 13 mainland regions, but Carrefour leads Hauts-de-France and Normandy, Lidl Grand Est "
        "and Île-de-France, Système U the Pays de la Loire (2.5 times its national share) and Spar "
        "Corsica (34% of supermarkets, against 2.7% nationally). In Haute-Corse, one chain holds 43% "
        "of the stores."
    )

    # --- So what? -------------------------------------------------------------------------------
    st.markdown(
        """
        **What it means**
        - **Rural departments:** the priority is to keep a last shop in small municipalities
          (multi-service shops, mobile shops, pharmacy deliveries), where many have none at all.
        - **Dense suburbs:** shops exist, but not enough for the number of residents. This is a
          question of urban planning and of space for retail in new neighbourhoods.
        - **Markets dominated by one chain** (Corsica, Haute-Marne): shoppers have less choice,
          which competition authorities may want to watch.

        **Next steps**
        - Measure the distance to the nearest bakery or pharmacy from the shops' coordinates,
          rather than its presence in the municipality.
        - Weigh chains by floor area or turnover, not only by number of stores.
        - Compare successive BANCO exports to follow openings and closures over time.
        """
    )
    st.caption(
        "Figures for mainland France, whatever the filters. OpenStreetMap is less complete in rural "
        "areas, so rural gaps may be slightly overstated; the results describe a situation, not its causes."
    )
