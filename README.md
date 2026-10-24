# Bread, medicine, groceries — is France equal when it comes to local shops?

Individual data-storytelling project, **Data Visualization** course, Efrei Paris (2026).
Author: **Thomas DURIAUD** (DAI) — Teacher: Mano Joseph Mathew.
An AI coding assistant was used for part of the code: see [section 7](#7-ai-assistance-and-credits).

- Deployed app: https://france-shops-s-analysis.streamlit.app/
- Repository: https://github.com/Marc35/France-shops-s-analysis

---

## 1. The story

**Question.** Buying bread, going to the pharmacy, doing the weekly shopping depend on the shops around you.
Are these shops spread evenly across France?

The dashboard follows a problem → analysis → insights → implications arc:

| Step | What the app shows |
|---|---|
| Hook | 35 % of French municipalities have no shop at all in the database, but they hold under 5 % of the population. |
| Overview | Density map of 713,000 shops, then shops compared with population (map + scatter plot with a regression). |
| Part 1 — Essential shops | For a chosen essential shop (bakery, pharmacy, post office…): coverage of municipalities by department, the 10 least-covered departments, comparison between shop types. |
| Part 2 — Retail chains | Share of each supermarket chain by region (or by department when one region is selected), chain comparison, store map, market concentration (Shannon index). |
| Data quality | Missing values, duplicates, validation checks, data freshness, join rate with the population file. |
| Conclusions | Key insights, implications, next steps. |

**Audience.** Local authorities looking for under-served areas, and anyone curious about the geography of retail in France.

**Key findings** (BANCO export of 20 October 2026):
- Shops follow people: across 34,746 mainland municipalities, the correlation between population and number of shops is 0.80 (log scales), with a slope of 0.96 — twice the inhabitants, about twice the shops.
- The exceptions tell the story: Paris and tourist departments (Hautes-Alpes, Alpes-de-Haute-Provence) have 20–24 shops per 1,000 inhabitants; Paris suburbs (Seine-Saint-Denis, Val-d'Oise) only 5–6.
- Essential shops: only 23 % of the municipalities of the Hautes-Pyrénées listed in the database have a bakery.
- Chains: Intermarché is the #1 supermarket chain in 7 of 13 mainland regions; Système U is 2.5 times more present in Pays de la Loire than nationally, E.Leclerc 1.3 times more in Brittany.

## 2. Data

Both datasets come from the same portal, **data.gouv.fr**, and are joined on the INSEE municipality code.

| Dataset | Producer | Licence | Use |
|---|---|---|---|
| [BAse Nationale des Commerces Ouverte (BANCO)](https://www.data.gouv.fr/datasets/base-nationale-des-commerces-ouverte) | Ça reste ouvert / OpenStreetMap contributors | ODbL | 745,000 shops with type, brand, coordinates, municipality |
| [Populations de référence 2023](https://www.data.gouv.fr/datasets/populations-de-reference) | INSEE | Licence Ouverte 2.0 | Legal municipal population, per municipality |

Data © OpenStreetMap contributors, available under the Open Database License. The raw files are **not** stored in the
repository (the BANCO CSV is 131 MB): they are downloaded automatically (see below).

## 3. Run the app

Requirements: Python 3.12 or later (tested with Python 3.13; versions pinned in `requirements.txt`).

```bash
# 1. Create an environment and install the pinned dependencies
python -m venv .venv
.venv\Scripts\activate            # Windows   (macOS / Linux: source .venv/bin/activate)
pip install -r requirements.txt

# 2. (optional) Download the data — the app also does it by itself on its first run
python download_data.py           # add --force to get today's BANCO export

# 3. Start the dashboard
streamlit run app.py
```

The first run downloads the two files (about 50 MB) and prepares the tables (about a minute); the next runs take a few seconds.

**Deploy on Streamlit Community Cloud:** push the repository to GitHub, create an app on share.streamlit.io with
`app.py` as the main file (Python 3.12+). The data is downloaded on the first start. The app uses about
1.1 to 1.6 GB of memory (Community Cloud limit: 2.7 GB).

## 4. Project structure

```
app.py                  # page layout, following the skeleton of the brief: filters, KPIs, sections
download_data.py        # data download script
sections/
  intro.py              # context, questions, data caveats
  overview.py           # KPI values and headline insights (computed from the data)
  deep_dives.py         # drill-downs: shop types, departments, market concentration
  conclusions.py        # insights, implications, next steps
utils/
  io.py                 # fetch_and_cache(), load_data(), load_population(), licence text
  prep.py               # cleaning, feature engineering, join, aggregated tables
  viz.py                # chart functions with one consistent style
  constants.py          # reference tables: regions, shop categories, brand patterns, seed
  style.py              # title plaque and chapter headings
assets/                 # style.css, Efrei logo
static/fonts/           # Barlow font files (SIL Open Font License)
.streamlit/config.toml  # theme (colours, fonts)
data/                   # downloaded data + Parquet cache (ignored by git)
explore.ipynb           # first exploration of the dataset
```

## 5. Method

**Cleaning** (`utils/prep.py`, same steps as the course labs)
- Every column read as text, so INSEE codes keep their leading zero (`01004`).
- Duplicated OpenStreetMap objects removed, rows without coordinates removed, text fields stripped.
- Department and region derived from the municipality code (including Corsica 2A/2B and overseas 97x).
- Coordinates checked against the bounding box of mainland France.

**Feature engineering**
- 8 essential-shop categories built from the OpenStreetMap shop types.
- Retail chains harmonised with 47 text patterns (e.g. "E. Leclerc", "Centre Commercial E.Leclerc" → E.Leclerc;
  Carrefour City / Market / Express → Carrefour). The brand is filled for only 22 % of rows, so the store name is used
  as a fallback, except for names such as "Épicerie du Carrefour" (a crossroads, not the brand).
- Chains are only compared within grocery stores, and by store format (supermarkets vs convenience stores):
  drives, fuel stations and car repair shops of a brand are not counted.

**Indicators**
- Coverage: share of the municipalities present in the database with at least one shop of the chosen type.
- Shops per 1,000 inhabitants, by department, compared with the average of the selection.
- Log-log regression of the number of shops on the population (one point per municipality).
- Chain shares: `pd.crosstab` normalised by row; concentration: Shannon diversity index.

**Performance**: `st.cache_data` on the data loading and on the tables recomputed by the year filter, Parquet cache of
the raw file, pre-aggregated density map (5 km grid), point maps sampled with a fixed seed (`RANDOM_SEED = 42`).

**Accessibility**: colour-blind-safe palettes, alt text on every chart, labelled axes and units, a diverging scale
with a neutral midpoint for "above / below average".

## 6. Limitations and ethics

- OpenStreetMap is collaborative: cities are better mapped than the countryside, so a missing shop is not necessarily
  missing on the ground, and the population–shops link may be slightly overstated.
- BANCO has no opening date: `last_update` is the last edit in OpenStreetMap, used only to judge data freshness.
- Shops are counted, not floor areas or turnover: a convenience store weighs as much as a hypermarket within a format.
- Population is the resident population: ratios ignore tourists and commuters.
- Mayotte is not covered by the INSEE file; overseas collectivities (Polynesia, New Caledonia…) are excluded.
- BANCO is updated daily, so figures may change slightly from one download to the next.
- No personal data: shops are businesses and results are aggregated by department or region.
- The results describe a situation; they do not establish causes.

## 7. AI assistance and credits

**Use of AI.** Claude (Anthropic) was used as a coding assistant during the project, in particular to build the
Streamlit charts and maps (Plotly) and to prepare the deployment of the app (data download script, pinned
dependencies, Streamlit Community Cloud setup). The choice of the dataset, the questions explored and the final
review of the results are the author's. Every piece of suggested code was run, tested on the real data and adapted
before being kept.

**Credits.** Data: OpenStreetMap contributors via BANCO (ODbL) and INSEE (Licence Ouverte 2.0). Fonts: Barlow,
SIL Open Font License (`static/fonts/OFL-LICENSE.txt`). Logo: Efrei Paris. Parts of the data preparation reuse the
methods of the course labs (Uber and San Francisco trees notebooks).
