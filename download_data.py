"""
Data download script: fetches the two datasets from data.gouv.fr into data/.

    python download_data.py           # only what is missing
    python download_data.py --force   # download again (today's BANCO export)

The app also calls it automatically on its first run if data/ is empty.
"""
import sys

from utils.io import fetch_and_cache

if __name__ == "__main__":
    fetch_and_cache(force="--force" in sys.argv)
    print("Data ready in data/.")
