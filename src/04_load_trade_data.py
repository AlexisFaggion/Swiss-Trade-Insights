from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from pathlib import Path
import os
import zipfile

import pandas as pd
from dotenv import load_dotenv
from mssql_python import connect


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PROJECT_DIR.parent

ZIP_PATH = PROJECT_ROOT / "data" / "raw" / "VZ_IMPEXP_DEF.zip"

# ============================================================
# DATABASE CONNECTION
# ============================================================

load_dotenv(PROJECT_DIR / ".env")

CONNECTION_STRING = os.getenv("AZURE_SQL_CONNECTIONSTRING")

if not CONNECTION_STRING:
    raise ValueError("AZURE_SQL_CONNECTIONSTRING is missing from .env")


# ============================================================
# LOAD CONFIGURATION
# ============================================================

# Number of CSV rows read by pandas at a time.
CHUNK_SIZE = 50_000

# Number of rows sent per SQL bulk-copy transaction.
BULK_BATCH_SIZE = 5_000

# ============================================================
# TARGET SQL COLUMNS
# ============================================================

# loaded_at is intentionally omitted.
# Azure SQL will populate it automatically using:
#
# DEFAULT SYSUTCDATETIME()

# Column order must match the row conversion and bulk-copy mapping.
SQL_COLUMNS = [
    "trade_flow",
    "year",
    "quarter",
    "month",
    "vz5",
    "vz4",
    "vz3",
    "vz2",
    "vz1",
    "total_business_cycle",
    "partner_country_num",
    "partner_country_iso2",
    "partner_country_name",
    "net_mass_kg",
    "value_chf",
    "value_eur",
    "value_usd",
    "status",
    "updated_at",
    "source_file",
]


# ============================================================
# SOURCE CONFIGURATION
# ============================================================

# Source-specific parsing, validation and column-mapping rules.
SOURCES = {
    # --------------------------------------------------------
    # HISTORICAL IMPORTS
    # --------------------------------------------------------
    "imports_history": {
        "inner_zip": "VZ_IMPEXP_DEF/VZ_IMP_def_fr.zip",
        "separator": ";",
        "encoding": "cp1252",
        "expected_rows": 2_183_779,
        "expected_flow": "IMP",
        "expected_min_year": 1988,
        "expected_max_year": 2024,

        "columns": [
            "Direction_trafic",
            "Année",
            "Trimestre",
            "Mois",
            "VZ5",
            "VZ4",
            "VZ3",
            "VZ2",
            "VZ1",
            "Total_conjoncturel",
            "Pays_num",
            "Pays_isoAlpha2",
            "Pays_txt",
            "Quantité_kg",
            "Valeur_CHF",
            "Valeur_EUR",
            "Valeur_USD",
            "Etat",
            "Date_actualisation",
        ],

        "dtype": {
            "Direction_trafic": "string",
            "VZ5": "string",
            "VZ4": "string",
            "VZ3": "string",
            "VZ2": "string",
            "VZ1": "string",
            "Total_conjoncturel": "string",
            "Pays_num": "string",
            "Pays_isoAlpha2": "string",
            "Pays_txt": "string",
            "Etat": "string",
        },

        "rename": {
            "Direction_trafic": "trade_flow",
            "Année": "year",
            "Trimestre": "quarter",
            "Mois": "month",
            "VZ5": "vz5",
            "VZ4": "vz4",
            "VZ3": "vz3",
            "VZ2": "vz2",
            "VZ1": "vz1",
            "Total_conjoncturel": "total_business_cycle",
            "Pays_num": "partner_country_num",
            "Pays_isoAlpha2": "partner_country_iso2",
            "Pays_txt": "partner_country_name",
            "Quantité_kg": "net_mass_kg",
            "Valeur_CHF": "value_chf",
            "Valeur_EUR": "value_eur",
            "Valeur_USD": "value_usd",
            "Etat": "status",
            "Date_actualisation": "updated_at",
        },
    },

    # --------------------------------------------------------
    # HISTORICAL EXPORTS
    # --------------------------------------------------------
    "exports_history": {
        "inner_zip": "VZ_IMPEXP_DEF/VZ_EXP_def_fr.zip",
        "separator": ";",
        "encoding": "cp1252",
        "expected_rows": 3_393_571,
        "expected_flow": "EXP",
        "expected_min_year": 1988,
        "expected_max_year": 2024,

        "columns": [
            "Direction_trafic",
            "Année",
            "Trimestre",
            "Mois",
            "VZ5",
            "VZ4",
            "VZ3",
            "VZ2",
            "VZ1",
            "Total_conjoncturel",
            "Pays_num",
            "Pays_isoAlpha2",
            "Pays_txt",
            "Quantité_kg",
            "Valeur_CHF",
            "Valeur_EUR",
            "Valeur_USD",
            "Etat",
            "Date_actualisation",
        ],

        "dtype": {
            "Direction_trafic": "string",
            "VZ5": "string",
            "VZ4": "string",
            "VZ3": "string",
            "VZ2": "string",
            "VZ1": "string",
            "Total_conjoncturel": "string",
            "Pays_num": "string",
            "Pays_isoAlpha2": "string",
            "Pays_txt": "string",
            "Etat": "string",
        },

        "rename": {
            "Direction_trafic": "trade_flow",
            "Année": "year",
            "Trimestre": "quarter",
            "Mois": "month",
            "VZ5": "vz5",
            "VZ4": "vz4",
            "VZ3": "vz3",
            "VZ2": "vz2",
            "VZ1": "vz1",
            "Total_conjoncturel": "total_business_cycle",
            "Pays_num": "partner_country_num",
            "Pays_isoAlpha2": "partner_country_iso2",
            "Pays_txt": "partner_country_name",
            "Quantité_kg": "net_mass_kg",
            "Valeur_CHF": "value_chf",
            "Valeur_EUR": "value_eur",
            "Valeur_USD": "value_usd",
            "Etat": "status",
            "Date_actualisation": "updated_at",
        },
    },

    # --------------------------------------------------------
    # 2025 IMPORTS
    # --------------------------------------------------------
    "imports_2025": {
        "inner_zip": "VZ_IMPEXP_DEF/VZ_IMP_def_2025.zip",
        "separator": ",",
        "encoding": "utf-8-sig",
        "expected_rows": 83_489,
        "expected_flow": "IMP",
        "expected_min_year": 2025,
        "expected_max_year": 2025,

        "columns": [
            "flow",
            "year",
            "quarter",
            "month",
            "vz5",
            "vz4",
            "vz3",
            "vz2",
            "vz1",
            "totalbusinesscycle",
            "country_code",
            "countryoforiginisoalpha2",
            "netmass",
            "value_chf",
            "value_euro",
            "value_usd",
            "status",
            "date_actualisation",
        ],

        "dtype": {
            "flow": "string",
            "vz5": "string",
            "vz4": "string",
            "vz3": "string",
            "vz2": "string",
            "vz1": "string",
            "totalbusinesscycle": "string",
            "country_code": "string",
            "countryoforiginisoalpha2": "string",
            "status": "string",
        },

        "rename": {
            "flow": "trade_flow",
            "year": "year",
            "quarter": "quarter",
            "month": "month",
            "vz5": "vz5",
            "vz4": "vz4",
            "vz3": "vz3",
            "vz2": "vz2",
            "vz1": "vz1",
            "totalbusinesscycle": "total_business_cycle",
            "country_code": "partner_country_num",
            "countryoforiginisoalpha2": "partner_country_iso2",
            "netmass": "net_mass_kg",
            "value_chf": "value_chf",
            "value_euro": "value_eur",
            "value_usd": "value_usd",
            "status": "status",
            "date_actualisation": "updated_at",
        },
    },

    # --------------------------------------------------------
    # 2025 EXPORTS
    # --------------------------------------------------------
    "exports_2025": {
        "inner_zip": "VZ_IMPEXP_DEF/VZ_EXP_def_2025.zip",
        "separator": ",",
        "encoding": "utf-8-sig",
        "expected_rows": 100_590,
        "expected_flow": "EXP",
        "expected_min_year": 2025,
        "expected_max_year": 2025,

        "columns": [
            "flow",
            "year",
            "quarter",
            "month",
            "vz5",
            "vz4",
            "vz3",
            "vz2",
            "vz1",
            "totalbusinesscycle",
            "country_code",
            "countryofdestinationisoalpha2",
            "netmass",
            "value_chf",
            "value_euro",
            "value_usd",
            "status",
            "date_actualisation",
        ],

        "dtype": {
            "flow": "string",
            "vz5": "string",
            "vz4": "string",
            "vz3": "string",
            "vz2": "string",
            "vz1": "string",
            "totalbusinesscycle": "string",
            "country_code": "string",
            "countryofdestinationisoalpha2": "string",
            "status": "string",
        },

        "rename": {
            "flow": "trade_flow",
            "year": "year",
            "quarter": "quarter",
            "month": "month",
            "vz5": "vz5",
            "vz4": "vz4",
            "vz3": "vz3",
            "vz2": "vz2",
            "vz1": "vz1",
            "totalbusinesscycle": "total_business_cycle",
            "country_code": "partner_country_num",
            "countryofdestinationisoalpha2": "partner_country_iso2",
            "netmass": "net_mass_kg",
            "value_chf": "value_chf",
            "value_euro": "value_eur",
            "value_usd": "value_usd",
            "status": "status",
            "date_actualisation": "updated_at",
        },
    },
}


# ============================================================
# TYPE CONVERSION HELPERS
# ============================================================

def is_null(value):
    """
    Return True when a pandas value represents SQL NULL.
    """

    if value is None:
        return True

    return bool(pd.isna(value))


def to_python_string(value):
    """
    Convert pandas string values to native Python strings.
    """

    if is_null(value):
        return None

    return str(value)


def to_python_int(value):
    """
    Convert pandas / NumPy numbers to native Python int.

    Fractional values are rejected instead of silently
    truncating them.
    """

    if is_null(value):
        return None

    decimal_value = Decimal(str(value))

    integer_value = (decimal_value.to_integral_value())

    if decimal_value != integer_value:
        raise ValueError(f"Expected an integer value but received: {value}")

    return int(integer_value)



DECIMAL_SCALE_12 = Decimal("0.000000000001")
DECIMAL_SCALE_18 = Decimal("0.000000000000000001")


def to_decimal_12(value):
    """
    Target: DECIMAL(28,12)
    """

    if is_null(value):
        return None

    return Decimal(str(value)).quantize(
        DECIMAL_SCALE_12,
        rounding=ROUND_HALF_UP
    )


def to_decimal_18(value):
    """
    Target: DECIMAL(38,18)
    """

    if is_null(value):
        return None

    return Decimal(str(value)).quantize(
        DECIMAL_SCALE_18,
        rounding=ROUND_HALF_UP
    )


def to_python_datetime(value):
    """
    Convert pandas Timestamp values to native
    Python datetime objects.
    """

    if is_null(value):
        return None

    timestamp = pd.to_datetime(value, errors="raise")

    return timestamp.to_pydatetime()


# ============================================================
# DATABASE SAFETY CHECK
# ============================================================

def prepare_source(connection, cursor, source_file, expected_rows):
    """
    Resume loading safely by source file.

    Complete source:
        skip it

    Partial source:
        delete only that source and reload it

    Missing source:
        load normally
    """

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM staging.trade_raw
        WHERE source_file = ?;
        """,
        (source_file,)
    )

    existing_rows = cursor.fetchone()[0]

    # Row counts determine whether a source is skipped or reloaded.
    # Matching counts do not guarantee identical or up-to-date data.
    if existing_rows == expected_rows:
        print(f"{source_file}: already complete ({existing_rows:,} rows). SKIPPED.")

        return False


    if existing_rows > 0:
        print(f"{source_file}: partial load detected ({existing_rows:,} rows).")

        print("Removing incomplete rows...")

        cursor.execute(
            """
            DELETE FROM staging.trade_raw
            WHERE source_file = ?;
            """,
            (source_file,)
        )

        connection.commit()

        print("Incomplete rows removed.")


    return True

# ============================================================
# OPEN NESTED ZIP
# ============================================================

def open_inner_zip(outer_archive, inner_zip_name):
    """
    Open a nested ZIP archive without extracting it to disk.

    The entire inner ZIP is loaded into memory, while its CSV
    contents are subsequently processed in chunks.
    
    """

    with outer_archive.open(inner_zip_name) as inner_file:
        inner_zip_bytes = BytesIO(inner_file.read())

    return zipfile.ZipFile(
        inner_zip_bytes,
        mode="r"
    )


# ============================================================
# NORMALIZE ONE DATAFRAME CHUNK
# ============================================================

# Invalid source dates are converted to NULL rather than rejecting the row.
def normalize_chunk(chunk, source_name, source_file, config):
    """
    Harmonize historical and 2025 source schemas
    into one common staging schema.
    """

    # --------------------------------------------------------
    # Rename source columns
    # --------------------------------------------------------
    chunk = chunk.rename(columns=config["rename"])

    # --------------------------------------------------------
    # Normalize trade-flow codes
    # --------------------------------------------------------

    # Standardise historical I/E codes to IMP/EXP.
    chunk["trade_flow"] = (
        chunk["trade_flow"]
        .replace({
            "I": "IMP",
            "E": "EXP",
        })
    )


    # --------------------------------------------------------
    # Country name
    # --------------------------------------------------------

    # Country names are unavailable in the 2025 files.
    # Missing names remain NULL until reference-data enrichment.
    if "partner_country_name" not in chunk.columns:
        chunk["partner_country_name"] = None

    # --------------------------------------------------------
    # Source lineage
    # --------------------------------------------------------
    chunk["source_file"] = (source_file)


    # --------------------------------------------------------
    # Date parsing
    # --------------------------------------------------------

    # Invalid source dates are converted to NULL rather than rejecting the row.
    chunk["updated_at"] = (
        pd.to_datetime(
            chunk["updated_at"],
            errors="coerce"
        )
    )


    # --------------------------------------------------------
    # Validate flow
    # --------------------------------------------------------

    # Missing flow values are excluded from this check.
    # The SQL NOT NULL constraint will reject them during loading.
    flows = set(
        chunk["trade_flow"]
        .dropna()
        .astype(str)
        .unique()
    )

    expected_flow = (config["expected_flow"])

    if flows != {expected_flow}:
        raise ValueError(
            f"{source_name}: unexpected "
            f"trade flow(s): {flows}. "
            f"Expected: {expected_flow}"
        )


    # --------------------------------------------------------
    # Validate year
    # --------------------------------------------------------

    if chunk["year"].isna().any():
        raise ValueError(f"{source_name}: missing year detected.")

    min_year = int(chunk["year"].min())

    max_year = int(chunk["year"].max())

    # Checks year boundaries, but not the presence of every
    # intermediate year within the expected range.
    if (min_year < config["expected_min_year"] or max_year > config["expected_max_year"]):
        raise ValueError(
            f"{source_name}: "
            f"unexpected year range "
            f"{min_year}-{max_year}."
        )


    # --------------------------------------------------------
    # Return only target columns
    # --------------------------------------------------------

    return chunk[SQL_COLUMNS]


# ============================================================
# CONVERT PANDAS ROWS FOR SQL SERVER
# ============================================================

def build_bulk_rows(chunk):
    """
    Convert pandas / NumPy values into native Python
    types expected by mssql-python and Azure SQL.

    Python int       -> SQL integer / BIGINT
    Decimal          -> SQL DECIMAL
    str              -> SQL VARCHAR / NVARCHAR
    datetime         -> SQL DATETIME2
    None             -> SQL NULL
    """

    rows = []

    for row in chunk.itertuples(index=False, name=None):
        # Values must follow the column order defined in SQL_COLUMNS.
        converted_row = (
            to_python_string(row[0]),     # trade_flow
            to_python_int(row[1]),        # year
            to_python_int(row[2]),        # quarter
            to_python_int(row[3]),        # month
            to_python_string(row[4]),     # vz5
            to_python_string(row[5]),     # vz4
            to_python_string(row[6]),     # vz3
            to_python_string(row[7]),     # vz2
            to_python_string(row[8]),     # vz1
            to_python_string(row[9]),     # total_business_cycle
            to_python_string(row[10]),    # partner_country_num
            to_python_string(row[11]),    # partner_country_iso2
            to_python_string(row[12]),    # partner_country_name
            to_decimal_18(row[13]),       # net_mass_kg
            to_python_int(row[14]),       # value_chf
            to_decimal_12(row[15]),       # value_eur
            to_decimal_12(row[16]),       # value_usd
            to_python_string(row[17]),    # status
            to_python_datetime(row[18]),  # updated_at
            to_python_string(row[19]),    # source_file
        )

        rows.append(converted_row)

    return rows


# ============================================================
# LOAD ONE SOURCE FILE
# ============================================================

def load_source(connection, cursor, outer_archive, source_name, config):
    """
    Read one source CSV by chunks, normalize it,
    convert Python types, and bulk-load it to Azure SQL.
    """

    inner_zip_name = (config["inner_zip"])

    print()
    print("=" * 60)
    print(f"LOADING: {source_name}")
    print("=" * 60)

    loaded_rows = 0


    # --------------------------------------------------------
    # Open inner ZIP
    # --------------------------------------------------------

    with open_inner_zip(outer_archive, inner_zip_name) as inner_archive:
        # ----------------------------------------------------
        # Find CSV
        # ----------------------------------------------------
        csv_files = [
            name
            for name
            in inner_archive.namelist()
            if name.lower().endswith(
                ".csv"
            )
        ]

        if len(csv_files) != 1:
            raise ValueError(
                f"{source_name}: "
                "expected exactly one CSV "
                f"but found {len(csv_files)}."
            )

        csv_name = (csv_files[0])

        print("CSV:", csv_name)

        should_load = prepare_source(
            connection,
            cursor,
            csv_name,
            config["expected_rows"]
        )

        
        # Include previously loaded rows in the final expected total.
        if not should_load:
            return config["expected_rows"]
        # ----------------------------------------------------
        # Open CSV
        # ----------------------------------------------------

        with inner_archive.open(csv_name) as csv_file:
            # ------------------------------------------------
            # Read by chunks
            # ------------------------------------------------

            # Precision limitation:
            # Pandas may parse net mass values as floating-point numbers.
            # Precision may be lost before conversion to DECIMAL(38,18).
            # The original pipeline is preserved for reproducibility.


            # Preserve country codes such as "NA" while treating empty fields as missing.
            chunks = pd.read_csv(
                csv_file,
                sep=config["separator"],
                encoding=config["encoding"],
                usecols=config["columns"],
                dtype=config["dtype"],
                chunksize=CHUNK_SIZE,
                low_memory=False,
                keep_default_na=False,
                na_values=[""],
            )


            # ------------------------------------------------
            # Process each chunk
            # ------------------------------------------------

            for (chunk_number, chunk) in enumerate(chunks, start=1):
                # --------------------------------------------
                # Normalize source schema
                # --------------------------------------------
                chunk = normalize_chunk(
                    chunk,
                    source_name,
                    csv_name,
                    config
                )

                # --------------------------------------------
                # Convert pandas types -> Python types
                # --------------------------------------------
                rows = build_bulk_rows(chunk)

                # --------------------------------------------
                # Bulk copy into Azure SQL
                # --------------------------------------------
                # Each bulk-copy batch uses its own transaction.
                # Successfully committed batches remain in the database if a later batch fails.
                # Partial source loads are detected and reloaded on the next run.
                result = cursor.bulkcopy(
                    "staging.trade_raw",
                    rows,
                    column_mappings=SQL_COLUMNS,
                    batch_size=BULK_BATCH_SIZE,
                    table_lock=True,
                    keep_nulls=True,
                    use_internal_transaction=True,
                    timeout=300,
                )

                # --------------------------------------------
                # Count inserted rows
                # --------------------------------------------
                copied_rows = (result["rows_copied"])

                loaded_rows += (copied_rows)

                # --------------------------------------------
                # Progress
                # --------------------------------------------
                print(
                    f"Chunk {chunk_number}: "
                    f"{copied_rows:,} rows "
                    f"| Total: "
                    f"{loaded_rows:,}"
                )


    # --------------------------------------------------------
    # Validate source row count
    # --------------------------------------------------------

    expected_rows = (config["expected_rows"])

    if loaded_rows != expected_rows:
        raise RuntimeError(
            f"{source_name}: "
            f"expected {expected_rows:,} rows "
            f"but loaded {loaded_rows:,}."
        )

    print()
    print(f"{source_name} completed: {loaded_rows:,} rows.")

    return loaded_rows


# ============================================================
# FINAL DATABASE VALIDATION
# ============================================================

def verify_database(cursor):
    """
    Validate the final staging data by source,
    flow, status and year.
    """

    print()
    print("=" * 60)
    print("DATABASE VALIDATION")
    print("=" * 60)

    # Report source-level counts and attributes for manual review.
    # The final automated check compares total row counts only.
    cursor.execute(
        """
        SELECT
            source_file,
            trade_flow,
            status,
            MIN([year]) AS min_year,
            MAX([year]) AS max_year,
            COUNT(*) AS row_count
        FROM staging.trade_raw
        GROUP BY
            source_file,
            trade_flow,
            status
        ORDER BY
            source_file,
            trade_flow,
            status;
        """
    )


    results = (cursor.fetchall())

    for row in results:
        print(
            row[0],
            "|",
            row[1],
            "|",
            row[2],
            "|",
            f"{row[3]}-{row[4]}",
            "|",
            f"{row[5]:,} rows"
        )


    # --------------------------------------------------------
    # Total database row count
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM staging.trade_raw;
        """
    )

    database_total = (cursor.fetchone()[0])

    print()
    print(f"Database total: {database_total:,}")

    return database_total


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("SWISS TRADE DATA - AZURE SQL LOAD")
    print("=" * 60)

    # --------------------------------------------------------
    # Verify ZIP exists
    # --------------------------------------------------------
    if not ZIP_PATH.exists():
        raise FileNotFoundError(
            "\n"
            "Main ZIP file not found:\n"
            f"{ZIP_PATH}\n"
            "\n"
            "Check ZIP_PATH at the top "
            "of 04_load_trade_data.py."
        )

    print("Dataset:", ZIP_PATH)

    # --------------------------------------------------------
    # Expected total
    # --------------------------------------------------------

    expected_total = sum(
        config["expected_rows"]
        for config
        in SOURCES.values()
    )

    print(f"Expected total rows: {expected_total:,}")

    # --------------------------------------------------------
    # Connect to Azure SQL
    # --------------------------------------------------------

    print()
    print("Connecting to Azure SQL...")


    with connect(CONNECTION_STRING, timeout=60) as connection:
        cursor = (connection.cursor())

        # ----------------------------------------------------
        # Confirm database
        # ----------------------------------------------------
        cursor.execute(
            """
            SELECT
                DB_NAME(),
                CURRENT_USER;
            """
        )

        database_name, user_name = (cursor.fetchone())

        print("Connection successful.")
        print("Database:", database_name)
        print("User:", user_name)
        
        # ----------------------------------------------------
        # Load data
        # ----------------------------------------------------
        # Includes both newly loaded rows and previously completed sources.
        total_loaded = 0


        with zipfile.ZipFile(ZIP_PATH, mode="r") as outer_archive:
            for (source_name, config) in SOURCES.items():
                loaded = load_source(
                    connection,
                    cursor,
                    outer_archive,
                    source_name,
                    config
                )

                total_loaded += (loaded)

        # ----------------------------------------------------
        # Validate Python total
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("PYTHON LOAD VALIDATION")
        print("=" * 60)
        print("Expected total:", f"{expected_total:,}")
        print("Loaded total:", f"{total_loaded:,}")


        if total_loaded != expected_total:
            raise RuntimeError("Total Python row-count validation failed.")

        # ----------------------------------------------------
        # Validate SQL database
        # ----------------------------------------------------

        database_total = (verify_database(cursor))

        # Matching row counts do not guarantee data integrity:
        # duplicates, missing records or incorrect values may remain.
        if database_total != expected_total:
            raise RuntimeError(
                "\n"
                "Database row-count "
                "validation failed.\n"
                f"Expected: {expected_total:,}\n"
                f"Azure SQL: {database_total:,}"
            )


    # --------------------------------------------------------
    # Success
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("LOAD COMPLETED SUCCESSFULLY")
    print("=" * 60)

# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()