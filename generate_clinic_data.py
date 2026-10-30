"""
Step 1: Generate FAKE (synthetic) private-clinic visit data with deliberate problems.

Run:  python generate_clinic_data.py
Output: clinic_visits.csv  (about 600 rows)

No real patient data is used. Everything is random.
The data is messy on purpose, so our pipeline has something to clean:
  - dates in different formats
  - missing patient IDs
  - gender written in many ways
  - duplicate visit IDs
  - impossible birth dates (in the future)
  - missing diagnosis codes
"""
import csv
import random
from datetime import date, datetime, timedelta

random.seed(42)  # same fake data every time you run it

MALE_NAMES = ["Mohammed", "Ahmed", "Omar", "Khalid", "Yousef", "Ali", "Hassan", "Ibrahim"]
FEMALE_NAMES = ["Layla", "Sara", "Fatima", "Aisha", "Noor", "Mariam", "Huda", "Amina"]
LAST = ["Al Naimi", "Hassan", "Khalid", "Ahmed", "Al Sulaiti", "Mansour", "Saleh",
        "Rahman", "Farouk", "Nasser", "Haddad", "Karim"]
CLINICS = ["Doha Care Clinic", "Al Wakra Family Clinic", "West Bay Medical Center"]
BLOOD = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]

# (diagnosis text, ICD-10-CM code, usual medicine)
DIAGNOSES = [
    ("Type 2 diabetes", "E11.9", "Metformin 500 mg"),
    ("Hypertension", "I10", "Amlodipine 5 mg"),
    ("Asthma", "J45.909", "Salbutamol inhaler"),
    ("Iron-deficiency anemia", "D50.9", "Ferrous sulfate 200 mg"),
    ("High cholesterol", "E78.5", "Atorvastatin 20 mg"),
    ("Common cold", "J06.9", "Paracetamol 500 mg"),
]
ALLERGIES = ["None", "None", "None", "Penicillin", "Peanuts", "Sulfa drugs"]
MALE_WRITINGS = ["M", "Male", "male", "m"]       # the same gender, written 4 ways
FEMALE_WRITINGS = ["F", "Female", "female", "f"]


def random_date(start_year, end_year):
    start = date(start_year, 1, 1)
    days = (date(end_year, 12, 31) - start).days
    return start + timedelta(days=random.randint(0, days))


def messy_date(d):
    """Write the same date in a random format (this is the 'mess')."""
    fmt = random.choice(["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d %H:%M:%S", "%d-%m-%Y"])
    return datetime(d.year, d.month, d.day, 10, 30).strftime(fmt)


# 120 fake patients
patients = []
for i in range(1, 121):
    is_female = random.random() < 0.5
    first = random.choice(FEMALE_NAMES if is_female else MALE_NAMES)
    patients.append({
        "id": f"P{i:04d}",
        "name": f"{first} {random.choice(LAST)}",
        "dob": random_date(1950, 2010),
        "gender": random.choice(FEMALE_WRITINGS if is_female else MALE_WRITINGS),
        "blood": random.choice(BLOOD),
        "allergy": random.choice(ALLERGIES),
    })

rows = []
for n in range(1, 601):
    p = random.choice(patients)
    diag, code, med = random.choice(DIAGNOSES)
    row = {
        "visit_id": f"V{n:05d}",
        "patient_id": p["id"],
        "patient_name": p["name"],
        "date_of_birth": messy_date(p["dob"]),
        "gender": p["gender"],
        "blood_group": p["blood"],
        "visit_date": messy_date(random_date(2022, 2026)),
        "diagnosis": diag,
        "diagnosis_code": code,
        "allergy": p["allergy"],
        "medication": med,
        "clinic": random.choice(CLINICS),
    }

    # --- add deliberate problems ---
    if random.random() < 0.03:
        row["patient_id"] = ""                       # missing patient ID
    if random.random() < 0.04:
        row["diagnosis_code"] = ""                   # missing diagnosis code
    if random.random() < 0.02:
        row["date_of_birth"] = messy_date(date(2031, 5, 1))  # birth date in the future
    if random.random() < 0.03:
        row["blood_group"] = random.choice(["unknown", "", "o+", "b +"])
    rows.append(row)

# duplicate visits (same visit_id twice)
for dup in random.sample(rows, 12):
    rows.append(dict(dup))

random.shuffle(rows)

with open("clinic_visits.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print(f"Done. Wrote {len(rows)} rows to clinic_visits.csv")
