"""
Loading the data (the "Load the data" step of the labs).

- fetch_and_cache(): downloads the two datasets from data.gouv.fr into data/ when they are
  missing (first run, clean checkout, Streamlit Cloud). Run it on its own with:
      python download_data.py
- load_data(): reads the BANCO CSV. The first read writes a Parquet copy
  (data/banco_raw.parquet), much faster to read back afterwards.
- load_population(): reads the INSEE population file.
- nrows option: like "df = df[:3000]" in lab 1, to work on an extract while developing.
"""
import csv
import fnmatch
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

from utils.constants import (
    POP_DOWNLOAD_URL, POP_SOURCE_LICENSE, POP_SOURCE_PRODUCER, POP_SOURCE_TITLE, POP_SOURCE_URL,
    SOURCE_DOWNLOAD_URL, SOURCE_LICENSE, SOURCE_PORTAL, SOURCE_PRODUCER, SOURCE_TITLE, SOURCE_URL,
)

# Paths are built from this file's location, so the app works
# whatever folder it is launched from.
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_CSV = DATA_DIR / "data.csv"
RAW_PARQUET = DATA_DIR / "banco_raw.parquet"
# INSEE file name as downloaded, e.g. DS_POPULATIONS_REFERENCE_2023_data.csv
POP_CSV_PATTERN = "DS_POPULATIONS_REFERENCE_*_data.csv"


# =============================================================================
# Download (data download script with caching, as asked in the project brief)
# =============================================================================
def _download(url: str, destination: Path) -> Path:
    """Stream a file to disk (no need to hold 50 MB in memory)."""
    request = urllib.request.Request(url, headers={"User-Agent": "efrei-dataviz-student-project"})
    with urllib.request.urlopen(request, timeout=300) as response, open(destination, "wb") as out:
        shutil.copyfileobj(response, out)
    return destination


def _extract(archive: Path, keep: dict[str, str]) -> list[Path]:
    """
    Extract from a zip the members whose file name matches one of the patterns of `keep`
    (exact name or shell pattern such as '*_data.csv'), saved in data/ under the matching
    value ('' = keep the original file name).
    Exact matching matters: 'metadata.csv' also ENDS with 'data.csv'.
    """
    saved = []
    with zipfile.ZipFile(archive) as zf:
        for member in zf.namelist():
            name = Path(member).name
            for pattern, target in keep.items():
                if fnmatch.fnmatchcase(name, pattern):
                    destination = DATA_DIR / (target or name)
                    with zf.open(member) as src, open(destination, "wb") as out:
                        shutil.copyfileobj(src, out)
                    saved.append(destination)
                    break
    return saved


def _has_population_file() -> bool:
    return any(DATA_DIR.glob(POP_CSV_PATTERN))


def fetch_and_cache(force: bool = False) -> None:
    """
    Download BANCO and the INSEE population file into data/ if they are not there yet.
    force=True downloads them again (e.g. to get today's BANCO export).
    """
    DATA_DIR.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        if force or not (RAW_CSV.exists() or RAW_PARQUET.exists()):
            print(f"Downloading BANCO from {SOURCE_URL} ...")
            archive = _download(SOURCE_DOWNLOAD_URL, Path(tmp) / "banco.zip")
            saved = _extract(archive, {"data.csv": "data.csv", "license.txt": "license.txt",
                                       "metadata.csv": "metadata.csv"})
            if RAW_CSV not in saved:
                raise RuntimeError("The BANCO archive did not contain the expected data.csv file.")
            RAW_PARQUET.unlink(missing_ok=True)   # the old cache would hide the new file

        if force or not _has_population_file():
            print(f"Downloading the INSEE population file from {POP_SOURCE_URL} ...")
            downloaded = _download(POP_DOWNLOAD_URL, Path(tmp) / "population")
            if zipfile.is_zipfile(downloaded):
                _extract(downloaded, {POP_CSV_PATTERN: "", "DS_POPULATIONS_REFERENCE_*_metadata.csv": ""})
            else:                                  # plain CSV: give it the expected name
                shutil.copy(downloaded, DATA_DIR / "DS_POPULATIONS_REFERENCE_2023_data.csv")
            if not _has_population_file():
                raise RuntimeError(f"No file matching {POP_CSV_PATTERN} after the download.")


# =============================================================================
# Loading
# =============================================================================
def detect_delimiter(path: Path) -> str:
    """Guess the delimiter (',' or ';') from the beginning of the file."""
    with open(path, encoding="utf-8") as f:
        sample = f.read(20_000)
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;").delimiter
    except csv.Error:
        return ","


def load_data(path: Path = RAW_CSV, nrows: int | None = None, use_cache: bool = True) -> pd.DataFrame:
    """
    Load the raw BANCO data (downloaded first if missing).

    Every column is read as text (dtype=str) so that INSEE codes are not
    damaged (e.g. '01004' would become 1004). Type conversions are done
    afterwards in prep.clean().

    nrows: number of rows to keep (None = whole file).
    """
    if use_cache and nrows is None and RAW_PARQUET.exists():
        return pd.read_parquet(RAW_PARQUET)

    if not path.exists() and path == RAW_CSV:
        fetch_and_cache()
    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}\n"
            f"Run `python download_data.py`, or download the CSV from {SOURCE_URL}, "
            "unzip it and put data.csv in data/."
        )

    df = pd.read_csv(path, delimiter=detect_delimiter(path), dtype=str, encoding="utf-8", nrows=nrows)

    # The disk cache is only written for the full file
    if use_cache and nrows is None:
        try:
            df.to_parquet(RAW_PARQUET, index=False)
        except ImportError:
            pass  # pyarrow not installed: carry on without the cache
    return df


def load_population(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """
    Load the raw INSEE legal-population file ("Populations de référence"), downloaded first if missing.
    Long format, one row per area x measure:
        GEO (area code) ; GEO_OBJECT (COM, ARM, DEP, REG...) ; POPREF_MEASURE (PMUN, PCAP, PTOT) ; OBS_VALUE
    Codes are read as text, like for BANCO.
    """
    if data_dir == DATA_DIR and not _has_population_file():
        fetch_and_cache()
    files = sorted(data_dir.glob(POP_CSV_PATTERN))
    if not files:
        raise FileNotFoundError(
            f"No population file matching {POP_CSV_PATTERN} in {data_dir}.\n"
            f"Run `python download_data.py`, or download it from {POP_SOURCE_URL} and put it in data/."
        )
    return pd.read_csv(files[-1], sep=";", dtype=str, encoding="utf-8")   # latest year if several


def overview(df: pd.DataFrame) -> dict:
    """
    First look at the dataset (shape / head / tail / describe from the labs),
    in a form that can be displayed in Streamlit or a notebook.
    """
    return {
        "shape": df.shape,
        "columns": list(df.columns),
        "head": df.head(),
        "tail": df.tail(),
        "describe": df.describe(include="all").T,
    }


def license_text() -> str:
    """Citation line shown in the app and the README."""
    return (
        f"Sources: {SOURCE_TITLE}, {SOURCE_PRODUCER}, {SOURCE_LICENSE}; "
        f"{POP_SOURCE_TITLE}, {POP_SOURCE_PRODUCER}, {POP_SOURCE_LICENSE}. Both published on {SOURCE_PORTAL}."
    )
