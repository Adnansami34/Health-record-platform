# Clinic-to-Hub Health Record (prototype)

**Live demo:** https://adnansami34.github.io/Health-record-platform/app.html

A prototype data pipeline and patient app that takes messy private-clinic data, cleans it, validates it, and stores it in a structured database. Built as a portfolio project for healthcare data engineering. **All data is synthetic (fake). No real patient data is used.**

## The problem
Clinics often keep records in their own formats: mixed date styles, inconsistent values, missing fields. Before data can be shared with national health systems (which use standards such as HL7 FHIR), it must be cleaned and validated.

## What the pipeline does
1. Reads the messy file `clinic_visits.csv`.
2. Cleans every row (dates, gender, blood group, diagnosis codes).
3. Rejects rows that cannot be fixed, and writes the reason to an error log.
4. Loads only new visits, so running it twice never creates duplicates (incremental load).

## Cleaning rules
| Problem | What the pipeline does |
|---|---|
| Gender written as M, m, male, Female... | Standardised to Male or Female |
| Dates in 4 different formats | Converted to YYYY-MM-DD (day-month-year assumed) |
| Missing patient ID | Rejected and logged |
| Missing diagnosis code | Repaired from the diagnosis name when possible |
| Birth date in the future | Rejected and logged |
| Blood group blank, unknown, or lowercase | Fixed, or stored as Unknown |
| Duplicate visit IDs | One copy kept |

## Results
- Rows read: 612
- Loaded: 580
- Rejected: 20 (13 missing patient ID, 7 birth date in the future)
- Duplicates skipped: 12
- Diagnosis codes repaired: 32
- Second run: 0 new rows loaded (incremental load works)

## Analysis queries
Five SQL queries answer: visits per month, top diagnoses, visits per clinic, patients with the most visits, and rejected records by reason. See `queries.sql` and `query_results.txt`.

## The app
`app.html` reads the cleaned data exported from the database (`data.js`) and shows a patient record, an emergency view (critical information only, with an access log), a plain-language summary, and an English/Arabic switch.

## Files
- `generate_clinic_data.py` : creates the fake messy data
- `clinic_visits.csv` : the messy input
- `schema.sql` : database tables, keys and indexes
- `pipeline.py` : the ETL pipeline
- `queries.sql`, `run_queries.py`, `query_results.txt` : analysis queries and results
- `export_for_app.py`, `data.js`, `app.html` : the app and its data export
- `index.html` : dashboard design (static)

## How to run
Python 3 is needed. No extra packages.

    python pipeline.py
    python run_queries.py
    python export_for_app.py

Then open `app.html` in a browser.

## Next steps
- Convert cleaned records to FHIR resources
- Power BI dashboard
- Deploy on Azure with CI/CD

## Notes
- This is a prototype with synthetic data, not a production system.
- Production use would need in-country hosting and a compliance review under local data protection law.
