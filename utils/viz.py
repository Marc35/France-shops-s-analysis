"""
Chart functions: one consistent style for the whole app.

As in the project skeleton (line_chart, bar_chart, map_chart), each function
DRAWS the chart in the Streamlit page and also returns the Plotly figure.
Pass show=False to only get the figure (e.g. in a notebook: fig.show()).

Each function adapts a chart from the labs, switched to Plotly to get the
interactivity (hover / tooltips) required by the project brief:
    - line_chart     <- plt.plot(by_date) frequency curves     (lab 1, Uber)
    - bar_chart      <- top 15 species px.bar / plt.bar        (trees lab, lab 1)
    - heatmap_chart  <- sns.heatmap(pivot_pct, annot=True)     (trees lab)
    - map_chart      <- px.scatter_map / px.density_map        (trees lab)
    - missing_matrix <- msno.matrix                            (trees lab)
"""
import matplotlib.pyplot as plt
import missingno as msno
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.constants import (
    MAP_CENTER_METRO, MAP_SAMPLE_SIZE, MAP_STYLE, MAP_ZOOM_METRO, METRO_BBOX, RANDOM_SEED,
)

# ---------------------------------------------------------------------------
# Shared style
# ---------------------------------------------------------------------------
# Colour-blind-safe categorical palette, in a FIXED order.
# On a point map, keep 3 colours maximum (beyond that they become hard to tell apart).
CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
MAIN_COLOR = "#1F3F77"      # enamel blue, same as the app theme (.streamlit/config.toml)
MUTED_COLOR = "#b9b8b3"
SEQUENTIAL = "Blues"        # one hue, light to dark, for magnitudes
# Two hues + a neutral midpoint, for "above / below average" (orange = below, blue = above)
DIVERGING = [[0.0, "#b5541c"], [0.5, "#dcdcd6"], [1.0, "#1F3F77"]]
TEMPLATE = "plotly_white"
FONT = "Barlow, sans-serif"                                   # same fonts as the app theme
TITLE_FONT = "Barlow Semi Condensed, Barlow, sans-serif"
INK = "#1C2430"
INK_MUTED = "#5B6573"
GRID = "#E6EAF0"
SOURCE_NOTE = "Source: BANCO (OpenStreetMap), data.gouv.fr — ODbL"
DENSITY_GRID = 0.05        # grid step (degrees) for the density map, about 5 km


def _finish(fig, height: int = 450):
    """Common layout: margins, font, source line under the title."""
    fig.update_layout(
        template=TEMPLATE,
        height=height,
        margin=dict(l=10, r=10, t=80, b=40),
        # Explicit white background: Streamlit installs its own default Plotly template,
        # which would otherwise paint the plot area with the theme's grey.
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family=FONT, size=13, color=INK),
        title_font=dict(family=TITLE_FONT, size=20, color=INK),
        title_x=0, title_xanchor="left", title_xref="container", title_pad_l=10,   # title aligned left
        hoverlabel=dict(font_family=FONT, font_size=13),
        legend=dict(font=dict(size=13)),
        # Source under the title (never overlaps the axes)
        title_subtitle_text=SOURCE_NOTE,
        title_subtitle_font=dict(family=FONT, size=11, color=INK_MUTED),
    )
    # Quiet axes: light grid, muted labels
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, title_font_color=INK_MUTED)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, title_font_color=INK_MUTED)
    return fig


def _show(fig, alt: str | None, show: bool):
    """Draw the figure in Streamlit, with an alt text for screen readers."""
    if show:
        # theme=None: keep our own styling instead of Streamlit's default Plotly theme
        st.plotly_chart(fig, width="stretch", alt=alt, theme=None)
    return fig


def color_map_for(categories) -> dict:
    """Fixed colour per category (the colour follows the chain, not its rank)."""
    return {cat: CATEGORICAL[i % len(CATEGORICAL)] for i, cat in enumerate(categories)}


def map_view(data: pd.DataFrame) -> dict:
    """
    Map centre and zoom: mainland France by default; otherwise
    (e.g. an overseas region is selected) centred on the points shown.
    """
    in_metro = data["lat"].between(METRO_BBOX["lat_min"], METRO_BBOX["lat_max"]) & data["lon"].between(
        METRO_BBOX["lon_min"], METRO_BBOX["lon_max"])
    if data.empty or in_metro.mean() >= 0.5:
        return {"center": MAP_CENTER_METRO, "zoom": MAP_ZOOM_METRO}
    span = max(data["lat"].max() - data["lat"].min(), data["lon"].max() - data["lon"].min(), 0.5)
    zoom = 8 if span < 2 else 2   # one overseas department: close zoom; several: world view
    return {"center": {"lat": data["lat"].mean(), "lon": data["lon"].mean()}, "zoom": zoom}


# ---------------------------------------------------------------------------
# Line chart (lab 1: plt.plot(by_date), frequency per day of the month)
# ---------------------------------------------------------------------------
def line_chart(data: pd.DataFrame, x: str, y: str, title: str, x_label: str, y_label: str,
               alt: str | None = None, show: bool = True):
    """Simple line with markers, one series."""
    fig = px.line(
        data, x=x, y=y, markers=True, title=title,
        labels={x: x_label, y: y_label},
        color_discrete_sequence=[MAIN_COLOR],
    )
    fig.update_traces(line=dict(width=2), marker=dict(size=8))
    fig.update_xaxes(dtick=1)
    return _show(_finish(fig), alt, show)


# ---------------------------------------------------------------------------
# Bar chart (trees lab: top 15 species; lab 1: plt.bar sorted)
# ---------------------------------------------------------------------------
def bar_chart(data: pd.DataFrame, x: str, y: str, title: str, x_label: str, y_label: str = "",
              color: str | None = None, category_order=None, highlight: str | None = None,
              hover_data=None, ascending: bool = False, x_suffix: str | None = None,
              alt: str | None = None, show: bool = True):
    """
    Two uses:
    - ranking (color=None): horizontal bars sorted on x, first row at the top
      (like fig.update_yaxes(autorange='reversed') in the lab).
      highlight: one value of y drawn in colour, the others in grey.
    - comparison (color='chain'...): vertical grouped bars, one colour per category.
    """
    if color is None:
        data = data.sort_values(x, ascending=ascending)
        order = data[y].astype(str).tolist()
        bar_color = None
        if highlight is not None:
            data = data.assign(_hl=(data[y] == highlight).map({True: "selected", False: "others"}))
            bar_color = "_hl"
        fig = px.bar(
            data, x=x, y=y, orientation="h", title=title,
            labels={x: x_label, y: y_label},
            hover_data=hover_data,
            color=bar_color,
            color_discrete_map={"selected": MAIN_COLOR, "others": MUTED_COLOR},
            color_discrete_sequence=[MAIN_COLOR],
        )
        fig.update_yaxes(categoryorder="array", categoryarray=order, autorange="reversed",
                         ticklabelstandoff=8)   # small gap between labels and bars
        fig.update_layout(showlegend=False)
        if x_suffix:
            fig.update_xaxes(ticksuffix=x_suffix)
        height = max(350, 28 * len(data) + 140)
    else:
        fig = px.bar(
            data, x=x, y=y, color=color, barmode="group", title=title,
            category_orders={color: category_order},
            color_discrete_map=color_map_for(category_order),
            labels={x: x_label, y: y_label, color: ""},
            hover_data=hover_data,
        )
        fig.update_xaxes(tickangle=-35)
        if x_suffix:
            fig.update_yaxes(ticksuffix=x_suffix)
        fig.update_layout(legend=dict(orientation="h", y=1.02, x=1, xanchor="right", yanchor="bottom"))
        height = 480
    return _show(_finish(fig, height=height), alt, show)


# ---------------------------------------------------------------------------
# Heatmap of shares (trees lab: sns.heatmap(pivot_pct, annot=True, fmt='.0f'))
# ---------------------------------------------------------------------------
def heatmap_chart(pivot_pct: pd.DataFrame, title: str, x_label: str = "Chain", y_label: str = "Region",
                  alt: str | None = None, show: bool = True):
    """Heatmap of shares in %, values written in the cells."""
    fig = px.imshow(
        pivot_pct,
        text_auto=".0f",
        aspect="auto",
        color_continuous_scale=SEQUENTIAL,
        labels={"x": x_label, "y": y_label, "color": "Share (%)"},
        title=title,
    )
    fig.update_traces(hovertemplate=f"{y_label}: %{{y}}<br>{x_label}: %{{x}}<br>Share: %{{z:.1f}} %<extra></extra>")
    fig.update_xaxes(side="bottom", tickangle=-35, title_text=None)
    fig.update_yaxes(ticklabelstandoff=8)
    return _show(_finish(fig, height=max(450, 32 * len(pivot_pct) + 200)), alt, show)


# ---------------------------------------------------------------------------
# Maps (trees lab: px.scatter_map / px.density_map, carto-positron style)
# ---------------------------------------------------------------------------
def map_chart(data: pd.DataFrame, kind: str, title: str, color: str | None = None, size: str | None = None,
              color_label: str | None = None, hover_name: str | None = None, hover_data=None,
              category_order=None, sample: int = MAP_SAMPLE_SIZE, color_midpoint: float | None = None,
              diverging: bool = False, color_range=None, colorbar_ticks: dict | None = None,
              alt: str | None = None, show: bool = True):
    """
    kind = "points"  : one point per shop, coloured by category (e.g. chain).
                       Sampled with random_state, as in the lab, to keep the map smooth.
                       Keep 3 categories maximum so the colours stay distinguishable.
    kind = "bubble"  : one bubble per department, placed at the mean point of its shops
                       (no boundary file needed). Size = a count, colour = a rate.
                       diverging=True + color_midpoint: colour scale centred on a reference value
                       (e.g. the average), orange below, blue above.
                       color_range=[min, max] and colorbar_ticks={value: label} fix the colour bar.
    kind = "density" : density map (where shops are most concentrated).
    """
    view = map_view(data)
    if kind == "points":
        data = data.sample(min(sample, len(data)), random_state=RANDOM_SEED)
        categories = category_order or sorted(data[color].dropna().unique())
        # Colours follow category_order; drawing order goes from the most to the least
        # frequent category, so that a small chain is not hidden under a big one.
        draw_order = data[color].value_counts().index.tolist()
        fig = px.scatter_map(
            data, lat="lat", lon="lon", color=color,
            hover_name=hover_name, hover_data=hover_data,
            category_orders={color: draw_order},
            color_discrete_map=color_map_for(categories),
            title=title, **view,
        )
        fig.update_traces(marker=dict(size=6, opacity=0.7))
        fig.update_layout(legend_title_text="")
    elif kind == "bubble":
        fig = px.scatter_map(
            data, lat="lat", lon="lon", size=size, color=color,
            hover_name=hover_name, hover_data=hover_data,
            color_continuous_scale=DIVERGING if diverging else SEQUENTIAL,
            color_continuous_midpoint=color_midpoint,
            range_color=color_range,
            labels={color: color_label or color},
            size_max=28, title=title, **view,
        )
        fig.update_traces(marker=dict(opacity=0.9))
        if colorbar_ticks:
            fig.update_coloraxes(colorbar=dict(tickvals=list(colorbar_ticks), ticktext=list(colorbar_ticks.values())))
    elif kind == "density":
        # Sending ~700,000 points to the browser makes the tab crash ("Out of Memory").
        # Pre-aggregation (brief: "pre-aggregation as needed"): shops are grouped on a grid
        # of DENSITY_GRID degrees (~5 km) and each cell is drawn once, weighted by its count.
        grid = (
            data.assign(lat=((data["lat"] / DENSITY_GRID).round() * DENSITY_GRID).round(3),
                        lon=((data["lon"] / DENSITY_GRID).round() * DENSITY_GRID).round(3))
            .groupby(["lat", "lon"]).size().reset_index(name="n_shops")
        )
        # Logarithmic weight: the Paris cell holds ~20,000 shops and a typical cell ~6.
        # With raw counts every cell is drawn relative to Paris and the rest of France
        # disappears; with log(1 + n) small towns stay visible.
        # The colour range is set to twice the maximum weight so that overlapping cells in
        # dense areas do not saturate the whole map.
        grid["weight"] = np.log1p(grid["n_shops"])
        fig = px.density_map(
            grid, lat="lat", lon="lon", z="weight", radius=6,
            range_color=[0, 2 * grid["weight"].max()],
            color_continuous_scale=SEQUENTIAL,
            title=title, **view,
        )
        fig.update_traces(hoverinfo="skip", hovertemplate=None)
        fig.update_layout(coloraxis_showscale=False)
    else:
        raise ValueError(f"Unknown map kind: {kind!r} (expected 'points', 'bubble' or 'density')")

    fig.update_layout(map_style=MAP_STYLE)
    return _show(_finish(fig, height=650), alt, show)


# ---------------------------------------------------------------------------
# Missing-value matrix (trees lab: msno.matrix)
# ---------------------------------------------------------------------------
def missing_matrix(raw_sample: pd.DataFrame, show: bool = True):
    """msno.matrix from the trees lab, on a sample of the raw data (static image)."""
    ax = msno.matrix(raw_sample, figsize=(12, 5), fontsize=9, sparkline=False)
    ax.set_title(f"Where values are missing (sample of {len(raw_sample):,} rows)")
    fig = ax.get_figure()
    if show:
        st.pyplot(fig)
    plt.close(fig)
    return fig


# ---------------------------------------------------------------------------
# Scatter plot on log scales (CM 2: px.scatter with a trendline)
# ---------------------------------------------------------------------------
def scatter_chart(data: pd.DataFrame, x: str, y: str, title: str, x_label: str, y_label: str,
                  hover_name: str | None = None, hover_data=None, fit: tuple | None = None,
                  fit_label: str = "Trend", alt: str | None = None, show: bool = True):
    """
    One point per row, both axes in log scale (populations range from 10 to 2 million).
    fit = (slope, intercept) of log10(y) = slope * log10(x) + intercept, drawn as a line.
    """
    fig = px.scatter(
        data, x=x, y=y, log_x=True, log_y=True, title=title,
        labels={x: x_label, y: y_label},
        hover_name=hover_name, hover_data=hover_data,
        color_discrete_sequence=[MAIN_COLOR],
        render_mode="webgl",              # tens of thousands of points stay smooth
    )
    fig.update_traces(marker=dict(size=4, opacity=0.35), name="Municipalities", showlegend=False)
    fig.update_xaxes(dtick=1)      # one label per power of ten: 10, 100, 1k, 10k...
    y_max = data[y].max()
    fig.update_yaxes(dtick=1, range=[np.log10(0.7), np.log10(y_max * 1.6)])   # no empty band below 1
    if fit is not None:
        slope, intercept = fit
        positive = data.loc[data[x] > 0, x]
        xs = np.logspace(np.log10(positive.min()), np.log10(positive.max()), 50)
        # Scattergl like the points, so that the line is drawn ON TOP of them (WebGL layer)
        fig.add_trace(go.Scattergl(
            x=xs, y=10 ** (slope * np.log10(xs) + intercept), mode="lines", name=fit_label,
            line=dict(color="#eb6834", width=3), hoverinfo="skip",
        ))
        fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.02, x=1, xanchor="right", yanchor="bottom"))
    return _show(_finish(fig, height=520), alt, show)
