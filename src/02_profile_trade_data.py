from io import BytesIO
from pathlib import Path
import zipfile

import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ZIP_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "VZ_IMPEXP_DEF.zip"
)


# ============================================================
# CONFIGURATION
# ============================================================

SAMPLE_ROWS = 5
CSV_CHUNK_ROWS = 100_000


TARGET_ARCHIVES = {
    "imports_history": "VZ_IMPEXP_DEF/VZ_IMP_def_fr.zip",
    "exports_history": "VZ_IMPEXP_DEF/VZ_EXP_def_fr.zip",
    "imports_2025": "VZ_IMPEXP_DEF/VZ_IMP_def_2025.zip",
    "exports_2025": "VZ_IMPEXP_DEF/VZ_EXP_def_2025.zip",
}


PARSING_CONFIG = {

    "imports_history": {
        "sep": ";",
        "encoding": "cp1252",
        "year_col": "Année",
        "direction_col": "Direction_trafic",
        "state_col": "Etat",
    },

    "exports_history": {
        "sep": ";",
        "encoding": "cp1252",
        "year_col": "Année",
        "direction_col": "Direction_trafic",
        "state_col": "Etat",
    },

    "imports_2025": {
        "sep": ",",
        "encoding": "utf-8-sig",
        "year_col": "year",
        "direction_col": "flow",
        "state_col": "status",
    },

    "exports_2025": {
        "sep": ",",
        "encoding": "utf-8-sig",
        "year_col": "year",
        "direction_col": "flow",
        "state_col": "status",
    },
}


# ============================================================
# FUNCTIONS
# ============================================================

def open_inner_zip(outer_archive, inner_zip_name):
    """
    Open a nested ZIP archive without extracting it to disk.

    The entire inner ZIP is loaded into memory. CSV files inside
    the archive are subsequently processed in chunks, limiting
    DataFrame memory usage but not the memory required for the ZIP.
    """

    with outer_archive.open(inner_zip_name) as inner_file:
        inner_zip_bytes = BytesIO(inner_file.read())

    return zipfile.ZipFile(inner_zip_bytes, "r")


def profile_large_csv(csv_file, config):
    """
    Profile the full CSV in chunks to limit memory usage.
    """

    total_rows = 0

    min_year = None
    max_year = None

    directions = set()
    states = set()

    year_col = config["year_col"]
    direction_col = config["direction_col"]
    state_col = config["state_col"]

    # Process the CSV in batches rather than loading it entirely.
    for chunk in pd.read_csv(
        csv_file,
        sep=config["sep"],
        encoding=config["encoding"],
        chunksize=CSV_CHUNK_ROWS
    ):
        total_rows += len(chunk)
        
        # Assumes year values are numeric and valid.
        # Missing or invalid years are not explicitly checked.
        chunk_min_year = chunk[year_col].min()
        chunk_max_year = chunk[year_col].max()

        if min_year is None or chunk_min_year < min_year:
            min_year = chunk_min_year

        if max_year is None or chunk_max_year > max_year:
            max_year = chunk_max_year

        directions.update(
            chunk[direction_col]
            .dropna()
            .astype(str)
            .unique()
        )

        states.update(
            chunk[state_col]
            .dropna()
            .astype(str)
            .unique()
        )

    print()
    print("Rows:", total_rows)
    print("Years:", min_year, "-", max_year)
    print("Directions:", directions)
    print("States:", states)


def inspect_csv(inner_archive, trade_type):
    """
    Inspect CSV columns, sample records and data types,
    then run full-file profiling.
    """

    config = PARSING_CONFIG[trade_type]

    csv_files = []

    for name in inner_archive.namelist():
        if name.lower().endswith(".csv"):
            csv_files.append(name)

    if len(csv_files) != 1:
        raise ValueError(f"Expected exactly one CSV, found {len(csv_files)}.")

    csv_name = csv_files[0]

    print()
    print("=" * 60)
    print(f"{trade_type.upper()} - {csv_name}")
    print("=" * 60)

    # Read a small sample to inspect the CSV structure.
    with inner_archive.open(csv_name) as csv_file:
        df = pd.read_csv(
            csv_file,
            sep=config["sep"],
            encoding=config["encoding"],
            nrows=SAMPLE_ROWS
        )

    # Validate the columns required for full-file profiling.
    required_columns = [
        config["year_col"],
        config["direction_col"],
        config["state_col"]
    ]

    missing_columns = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{trade_type}: missing expected columns: {missing_columns}. "
            f"Available columns: {df.columns.tolist()}"
        )

    print()
    print("Columns:")
    print(df.columns.tolist())

    print()
    print("Sample:")
    print(df.to_string())

    print()
    print("Sample data types:")
    print(df.dtypes)

    # Profile the complete CSV in chunks.
    print()
    print("Profiling full CSV...")

    with inner_archive.open(csv_name) as csv_file:
        profile_large_csv(csv_file, config)


# ============================================================
# MAIN
# ============================================================

def main():

    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"Main ZIP not found: {ZIP_PATH}")

    print("=" * 60)
    print("SWISS TRADE DATA - CSV PROFILING")
    print("=" * 60)

    with zipfile.ZipFile(ZIP_PATH, "r") as outer_archive:
        available_files = outer_archive.namelist()

        # Debugging: uncomment to list all files in the main ZIP
        # and verify the paths defined in TARGET_ARCHIVES.
        #
        # for name in available_files:
        #     print(name)


        for trade_type, inner_zip_name in TARGET_ARCHIVES.items():
            if inner_zip_name not in available_files:
                raise FileNotFoundError(f"{inner_zip_name} was not found in the main archive.")

            with open_inner_zip(outer_archive, inner_zip_name) as inner_archive:
                inspect_csv(inner_archive, trade_type)

    print()
    print("=" * 60)
    print("CSV PROFILING COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()