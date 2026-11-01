from pathlib import Path
import os
import re

from dotenv import load_dotenv
from mssql_python import connect


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

SQL_FILE = (
    PROJECT_ROOT
    / "01_create_staging_schema.sql"
)


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(PROJECT_ROOT / ".env")

CONNECTION_STRING = os.getenv("AZURE_SQL_CONNECTIONSTRING")

if not CONNECTION_STRING:
    raise ValueError("AZURE_SQL_CONNECTIONSTRING is missing from .env")


# ============================================================
# TEST CONNECTION
# ============================================================

def test_connection():

    print("Connecting to Azure SQL...")

    with connect(CONNECTION_STRING) as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                DB_NAME(),
                CURRENT_USER
            """
        )

        database_name, current_user = cursor.fetchone()

        print("Connection successful.")
        print("Database:", database_name)
        print("User:", current_user)


# ============================================================
# READ SQL FILE
# ============================================================

def read_sql_file():

    if not SQL_FILE.exists():
        raise FileNotFoundError(f"SQL file not found: {SQL_FILE}")

    return SQL_FILE.read_text(encoding="utf-8")


# ============================================================
# SPLIT GO BATCHES
# ============================================================

def split_sql_batches(sql_script):

    batches = re.split(
        r"^\s*GO\s*;?\s*$",
        sql_script,
        flags=re.MULTILINE | re.IGNORECASE
    )

    return [
        batch.strip()
        for batch in batches
        if batch.strip()
    ]


# ============================================================
# EXECUTE SQL SCRIPT
# ============================================================

def execute_schema_script():

    sql_script = read_sql_file()

    batches = split_sql_batches(sql_script)

    print(f"Executing {len(batches)} SQL batch(es)...")

    with connect(CONNECTION_STRING) as connection:
        cursor = connection.cursor()

        for number, batch in enumerate(batches, start=1):
            print(f"Executing batch {number}/{len(batches)}...")

            cursor.execute(batch)

        connection.commit()

    print("SQL script executed successfully.")


# ============================================================
# VERIFY TABLE
# ============================================================

def verify_table():

    with connect(CONNECTION_STRING) as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM staging.trade_raw
            """
        )

        row_count = cursor.fetchone()[0]

        print("staging.trade_raw rows:", row_count)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("AZURE SQL DATABASE SETUP")
    print("=" * 60)

    test_connection()

    execute_schema_script()

    verify_table()

    print()
    print("=" * 60)
    print("DATABASE SETUP COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()