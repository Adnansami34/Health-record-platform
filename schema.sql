-- Step 2: Database tables for the health record platform
-- Works in SQLite now. Close to SQL Server / Azure SQL syntax for later.
-- Synthetic data only.

PRAGMA foreign_keys = ON;

-- Who the patients are
CREATE TABLE patients (
    patient_id     TEXT PRIMARY KEY,
    full_name      TEXT NOT NULL,
    date_of_birth  TEXT NOT NULL,                       -- YYYY-MM-DD
    gender         TEXT NOT NULL CHECK (gender IN ('Male', 'Female')),
    blood_group    TEXT NOT NULL DEFAULT 'Unknown',
    allergy        TEXT NOT NULL DEFAULT 'None'
);

-- Standard diagnosis codes (ICD-10-CM)
CREATE TABLE diagnoses (
    diagnosis_code TEXT PRIMARY KEY,
    diagnosis_name TEXT NOT NULL
);

-- The private clinics sending data
CREATE TABLE clinics (
    clinic_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    clinic_name    TEXT NOT NULL UNIQUE
);

-- Every visit
CREATE TABLE visits (
    visit_id       TEXT PRIMARY KEY,
    patient_id     TEXT NOT NULL REFERENCES patients(patient_id),
    clinic_id      INTEGER NOT NULL REFERENCES clinics(clinic_id),
    diagnosis_code TEXT NOT NULL REFERENCES diagnoses(diagnosis_code),
    visit_date     TEXT NOT NULL,                       -- YYYY-MM-DD
    medication     TEXT,
    loaded_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Bad records go here, with the reason
CREATE TABLE error_log (
    error_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_id       TEXT,
    reason         TEXT NOT NULL,
    raw_row        TEXT,
    logged_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes: make common searches faster
CREATE INDEX idx_visits_date      ON visits(visit_date);
CREATE INDEX idx_visits_patient   ON visits(patient_id);
CREATE INDEX idx_visits_diagnosis ON visits(diagnosis_code);

-- Starting data for the lookup table
INSERT INTO diagnoses (diagnosis_code, diagnosis_name) VALUES
    ('E11.9',   'Type 2 diabetes'),
    ('I10',     'Hypertension'),
    ('J45.909', 'Asthma'),
    ('D50.9',   'Iron-deficiency anemia'),
    ('E78.5',   'High cholesterol'),
    ('J06.9',   'Common cold');
