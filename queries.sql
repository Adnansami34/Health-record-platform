-- Step 4: Analysis queries for the health record database
-- Each block starts with a "-- Q" title line. run_queries.py runs them all.

-- Q1: Visits per month (trend over time)
SELECT substr(visit_date, 1, 7) AS month,
       COUNT(*)                 AS visits
FROM visits
GROUP BY month
ORDER BY month;

-- Q2: Top 5 diagnoses by number of visits
SELECT d.diagnosis_name,
       d.diagnosis_code,
       COUNT(*) AS visits
FROM visits v
JOIN diagnoses d ON d.diagnosis_code = v.diagnosis_code
GROUP BY d.diagnosis_code
ORDER BY visits DESC
LIMIT 5;

-- Q3: Visits per clinic
SELECT c.clinic_name,
       COUNT(*) AS visits
FROM visits v
JOIN clinics c ON c.clinic_id = v.clinic_id
GROUP BY c.clinic_id
ORDER BY visits DESC;

-- Q4: Top 5 patients with the most visits
SELECT p.patient_id,
       p.full_name,
       COUNT(*) AS visits
FROM visits v
JOIN patients p ON p.patient_id = v.patient_id
GROUP BY p.patient_id
ORDER BY visits DESC, p.patient_id
LIMIT 5;

-- Q5: Rejected records by reason (data quality report)
SELECT reason,
       COUNT(*) AS rejected_rows
FROM error_log
GROUP BY reason
ORDER BY rejected_rows DESC;
