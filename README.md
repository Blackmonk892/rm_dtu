# 🎓 Student Data Pipeline & Shortlist Tool

A simple Streamlit application for uploading, cleaning, inspecting, filtering, and exporting student datasets.

The application supports:

- CSV (`.csv`)
- Excel (`.xlsx`)
- Excel 97–2003 (`.xls`)

It automatically cleans the uploaded dataset, validates the required schema, recalculates student totals, provides real-time Active/Debarred status management, filters candidates using a minimum Total score, displays live statistics, and exports the final shortlist as CSV.

---

## 🚀 Features

### 1. Data Upload & Automatic Cleaning

Upload a raw CSV or Excel dataset.

Supported formats:

- `.csv`
- `.xlsx`
- `.xls`

The application automatically:

- Validates the required columns
- Removes duplicate records
- Normalizes names
- Normalizes gender values
- Parses academic grades
- Parses messy subject scores
- Handles missing marks
- Removes unusable student records
- Validates grade ranges
- Constrains marks to 0–100
- Recalculates the `Total` column

No manual cleaning step is required.

---

### 2. Cleaned Dataset

After upload, the cleaned student dataset is displayed in an interactive table.

The table contains:

- Status
- Name
- Gender
- Grade
- Math
- Science
- English
- Total

Only the `Status` field is editable.

---

### 3. Active / Debarred Management

Every student starts as:

```text
Active