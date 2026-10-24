"""
Page style: loads assets/style.css and draws the two custom page elements
(title plaque, chapter headings). Colours and fonts live in .streamlit/config.toml.
"""
from html import escape
from pathlib import Path

import streamlit as st

CSS_PATH = Path(__file__).resolve().parent.parent / "assets" / "style.css"


def apply_style():
    """Inject the custom CSS once, at the top of the page."""
    st.html(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>")


def hero(kicker: str, title: str, subtitle: str):
    """Title plaque, drawn like a French enamel street sign."""
    st.html(
        f"""
        <header class="plaque">
          <p class="plaque-kicker">{escape(kicker)}</p>
          <h1 class="plaque-title">{escape(title)}</h1>
          <p class="plaque-sub">{escape(subtitle)}</p>
        </header>
        """
    )


def chapter(number: int, title: str):
    """Chapter heading of the story, numbered with an enamel 'house number'."""
    st.html(
        f"""
        <div class="chapter">
          <span class="house-number" aria-hidden="true">{number}</span>
          <h2 class="chapter-title">{escape(title)}</h2>
        </div>
        """
    )
