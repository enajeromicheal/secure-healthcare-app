# sqlite_setup.py
# - Initialises SQLite dataset table
# - Loads cleaned heart-disease dataset from CSV
# - Imports dataset into SQLite
# - Uses a separate table to avoid overwriting patient_records used by the app

import os
import sqlite3
import pandas as pd

# Database configuration (can be overridden via environment variable)
DB_NAME = os.environ.get("SQLITE_DB_PATH", "healthcare.db")
CSV_FILE = "cleaned_heart_disease_dataset.csv"

# Dataset table name (separate from patient_records)
DATASET_TABLE = "heart_dataset"


def main():
    # ------------------------
    # Load dataset from CSV
    # ------------------------
    df = pd.read_csv(CSV_FILE)

    if df.empty:
        raise RuntimeError("Dataset CSV is empty or failed to load.")

    # ------------------------
    # Connect to SQLite database
    # ------------------------
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # ------------------------
    # Import dataset into SQLite
    # ------------------------
    # NOTE: Uses a separate table to avoid modifying patient_records
    df.to_sql(DATASET_TABLE, conn, if_exists="replace", index=False)

    # ------------------------
    # Verification
    # ------------------------
    cur.execute(f"SELECT COUNT(*) FROM {DATASET_TABLE};")
    print("Rows in heart_dataset:", cur.fetchone()[0])

    # ========================
    # Audit Log Table
    # ========================
    conn.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        action TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

    print("✓ Dataset imported successfully.")


if __name__ == "__main__":
    main()