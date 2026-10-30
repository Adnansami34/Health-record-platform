"""
Step 3: The data pipeline (ETL = Extract, Transform, Load)

Run:  python pipeline.py
Needs: clinic_visits.csv and schema.sql in the same folder. No installs needed.

What it does:
  1. EXTRACT  - reads the messy clinic_visits.csv
  2. TRANSFORM - cleans every row (dates, gender, blood group, codes)
  3. VALIDATE - rejects rows that cannot be fixed (reason goes to the error log)
  4. LOAD     - saves good rows into health_record.db
Running it twice is safe: visits already loaded are skipped (incremental load).

Assumption: dates like 01-02-2023 are DAY-MONTH-YEAR (1 February 2023).
"""
import csv
import json
import logging
import os
import sqlite3
from datetime import date, datetime

CSV_FILE = "clinic_visits.csv"
SCHEMA_FILE = "schema.sql"
DB_FILE = "health_record.db"
LOG_FILE = "pipeline.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d %H:%M:%S", "%d-%m-%Y"]
VALID_BLOOD = {"A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"}


# ---------- cleaning helpers ----------
def parse_date(text):
    """Turn any of our date formats into a real date. Returns None if impossible."""
    text = (text or "").strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def clean_gender(text):
    value = (text or "").strip().lower()
    if value in ("m", "male"):
        return "Male"
    if value in ("f", "female"):
        return "Female"
    return None


def clean_blood(text):
    value = (text or "").replace(" ", "").upper()
    return value if value in VALID_BLOOD else "Unknown"


# ---------- database helpers ----------
def open_database():
    """Create the database from schema.sql the first time only."""
    first_time = not os.path.exists(DB_FILE)
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    if first_time:
        with open(SCHEMA_FILE, encoding="utf-8") as f:
            conn.executescript(f.read())
        logging.info("Created new database from %s", SCHEMA_FILE)
    return conn


def log_error(conn, visit_id, reason, raw_row):
    # do not log the same problem twice when the pipeline is run again
    if conn.execute("SELECT 1 FROM error_log WHERE visit_id = ? AND reason = ?",
                    (visit_id, reason)).fetchone():
        return
    conn.execute(
        "INSERT INTO error_log (visit_id, reason, raw_row) VALUES (?, ?, ?)",
        (visit_id, reason, json.dumps(raw_row, ensure_ascii=False)),
    )
    logging.warning("Rejected %s: %s", visit_id or "(no id)", reason)


def get_clinic_id(conn, name):
    conn.execute("INSERT OR IGNORE INTO clinics (clinic_name) VALUES (?)", (name,))
    return conn.execute(
        "SELECT clinic_id FROM clinics WHERE clinic_name = ?", (name,)
    ).fetchone()[0]


# ---------- main pipeline ----------
def run():
    conn = open_database()
    today = date.today()

    # lookup: diagnosis name -> code (used to repair missing codes)
    name_to_code = {
        name.lower(): code
        for code, name in conn.execute("SELECT diagnosis_code, diagnosis_name FROM diagnoses")
    }
    valid_codes = set(name_to_code.values())

    stats = {"read": 0, "loaded": 0, "rejected": 0, "duplicates": 0, "already_loaded": 0,
             "codes_repaired": 0}
    seen_in_file = set()

    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            stats["read"] += 1
            visit_id = (row["visit_id"] or "").strip()

            # duplicate inside the file -> keep first copy only
            if visit_id in seen_in_file:
                stats["duplicates"] += 1
                logging.info("Duplicate in file skipped: %s", visit_id)
                continue
            seen_in_file.add(visit_id)

            # incremental load: skip visits already in the database
            if conn.execute("SELECT 1 FROM visits WHERE visit_id = ?", (visit_id,)).fetchone():
                stats["already_loaded"] += 1
                continue

            # ---- validate (reject what cannot be fixed) ----
            patient_id = (row["patient_id"] or "").strip()
            if not patient_id:
                log_error(conn, visit_id, "Missing patient_id", row)
                stats["rejected"] += 1
                continue

            dob = parse_date(row["date_of_birth"])
            if dob is None:
                log_error(conn, visit_id, "Unreadable date of birth", row)
                stats["rejected"] += 1
                continue
            if dob > today:
                log_error(conn, visit_id, "Date of birth is in the future", row)
                stats["rejected"] += 1
                continue

            visit_date = parse_date(row["visit_date"])
            if visit_date is None:
                log_error(conn, visit_id, "Unreadable visit date", row)
                stats["rejected"] += 1
                continue

            gender = clean_gender(row["gender"])
            if gender is None:
                log_error(conn, visit_id, "Unknown gender value", row)
                stats["rejected"] += 1
                continue

            # ---- fix what can be fixed ----
            code = (row["diagnosis_code"] or "").strip()
            if not code:
                code = name_to_code.get((row["diagnosis"] or "").strip().lower(), "")
                if code:
                    stats["codes_repaired"] += 1
                    logging.info("Repaired missing diagnosis code for %s -> %s", visit_id, code)
            if code not in valid_codes:
                log_error(conn, visit_id, "Missing or unknown diagnosis code", row)
                stats["rejected"] += 1
                continue

            # ---- load ----
            conn.execute(
                "INSERT OR IGNORE INTO patients "
                "(patient_id, full_name, date_of_birth, gender, blood_group, allergy) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (patient_id, row["patient_name"].strip(), dob.isoformat(), gender,
                 clean_blood(row["blood_group"]), (row["allergy"] or "None").strip()),
            )
            conn.execute(
                "INSERT INTO visits "
                "(visit_id, patient_id, clinic_id, diagnosis_code, visit_date, medication) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (visit_id, patient_id, get_clinic_id(conn, row["clinic"].strip()), code,
                 visit_date.isoformat(), (row["medication"] or "").strip()),
            )
            stats["loaded"] += 1

    conn.commit()
    conn.close()

    summary = (
        f"Rows read:            {stats['read']}\n"
        f"Loaded (new):         {stats['loaded']}\n"
        f"Rejected (error log): {stats['rejected']}\n"
        f"Duplicates skipped:   {stats['duplicates']}\n"
        f"Already in database:  {stats['already_loaded']}\n"
        f"Codes repaired:       {stats['codes_repaired']}"
    )
    logging.info("Run finished:\n%s", summary)
    print(summary)


if __name__ == "__main__":
    run()
