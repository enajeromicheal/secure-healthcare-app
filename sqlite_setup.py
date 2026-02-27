import sqlite3
import pandas as pd

DB_NAME = "healthcare.db"
CSV_FILE = "cleaned_heart_disease_dataset.csv"

def main():
    # Load the cleaned dataset
    df = pd.read_csv(CSV_FILE)

    # Connect to (or create) the SQLite database
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Create the table (in case it doesn't exist)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS patient_records (
        patient_id INTEGER PRIMARY KEY,
        age INTEGER NOT NULL,
        sex TEXT NOT NULL,
        blood_pressure INTEGER NOT NULL,
        cholesterol_level INTEGER NOT NULL,
        fasting_blood_sugar_over_120mg_dl TEXT NOT NULL,
        resting_ecg TEXT NOT NULL,
        exercise_induced_angina TEXT NOT NULL
    );
    """)

    # Import data (replace guarantees table exists and prevents duplicates)
    df.to_sql("patient_records", conn, if_exists="replace", index=False)

    # Proof check
    cur.execute("SELECT COUNT(*) FROM patient_records;")
    print("Rows in patient_records:", cur.fetchone()[0])

    conn.commit()
    conn.close()

    print("✅ SQLite database created and data imported into patient_records.")

if __name__ == "__main__":
    main()