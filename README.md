# Student Data Pipeline & Shortlist Tool

A lightweight data processing and recruitment shortlisting application built with Python, Pandas, and Streamlit.

The application provides an end-to-end workflow for ingesting raw student data, validating and cleaning the dataset, maintaining student eligibility status, dynamically generating a shortlist based on a minimum total score, and exporting the resulting shortlist as a CSV file.

This project was developed as part of the Student Tech Team technical assessment for the Career Development and Industry Engagement (CDIE) Office, Delhi Technological University.

---

## Demo Video

https://github.com/user-attachments/assets/883e9161-5817-49de-9768-93b13394ba3f



## Overview

Recruitment and student-selection workflows frequently rely on datasets collected from multiple sources. Raw datasets may contain inconsistent formatting, duplicate records, missing values, non-numeric representations of marks, inconsistent grade formats, and unreliable derived fields such as total scores.

The objective of this application is to provide a small but robust data-processing layer between the raw dataset and the recruitment shortlisting workflow.

The application follows the pipeline:

```text
Raw Dataset
    |
    v
File Ingestion
    |
    v
Schema Validation
    |
    v
Data Normalization
    |
    +--> Name normalization
    +--> Gender normalization
    +--> Grade normalization
    +--> Marks normalization
    |
    v
Missing-Value Handling
    |
    v
Duplicate Detection
    |
    v
Score Validation
    |
    v
Total Recalculation
    |
    v
Cleaned Dataset
    |
    v
Active / Debarred Management
    |
    v
Minimum Total Score Filtering
    |
    v
Live Shortlist
    |
    v
CSV Export
````

The design intentionally separates the data-processing layer from the user interface so that the cleaning pipeline can be independently tested and reused.

---

## Key Features

### Data ingestion

The application supports the following input formats:

* CSV
* XLSX
* XLS

The file type is detected from the uploaded filename and passed to the appropriate Pandas reader.

### Automated cleaning

The cleaning pipeline handles:

* schema validation
* whitespace normalization
* name normalization
* gender normalization
* grade parsing
* numeric mark extraction
* missing subject marks
* invalid score handling
* duplicate removal
* Total validation and recalculation

### Cleaned data inspection

The cleaned dataset is displayed through an interactive Streamlit table.

Users can inspect the processed records before applying recruitment filters.

### Dynamic shortlisting

A minimum Total Score can be selected through the interface.

The shortlist is recalculated whenever the threshold changes.

### Active / Debarred management

Each student has an eligibility status:

```text
Active
Debarred
```

Debarred students are immediately excluded from the shortlist.

The status can be changed without uploading the dataset again.

### Shortlist statistics

The application calculates statistics for the current shortlist, including:

* matched student count
* average Total
* average Mathematics score
* average Science score
* average English score

### CSV export

The current shortlist can be exported as a CSV file for downstream recruitment workflows.

---

# Architecture

The application follows a simple two-layer architecture.

```text
+------------------------------+
|          Streamlit UI        |
|                              |
| Upload                       |
| Cleaning Report              |
| Cleaned Dataset              |
| Status Management            |
| Score Filter                 |
| Statistics                   |
| Export                       |
+---------------+--------------+
                |
                v
+------------------------------+
|       Cleaning Pipeline      |
|                              |
| Schema Validation            |
| Normalization                |
| Missing Values               |
| Duplicate Detection          |
| Score Validation             |
| Total Recalculation          |
+------------------------------+
```

The project deliberately avoids introducing a database or external service because the assessment dataset is small and the requested workflow is session-based.

For the provided dataset size, keeping the cleaned DataFrame in application memory provides low-latency filtering and avoids unnecessary I/O operations.

---

# Project Structure

```text
student-data-pipeline/
|
├── app.py
├── cleaning.py
├── requirements.txt
├── README.md
├── sample_raw_data.csv
├── .gitignore
|
├── tests/
│   └── test_pipeline.py
|
└── docs/
    └── demo.gif
```

## `app.py`

The Streamlit application layer.

Responsibilities include:

* file upload
* application state management
* rendering the cleaning report
* displaying cleaned records
* managing Active/Debarred status
* applying shortlist filters
* calculating statistics
* generating CSV downloads

The UI does not contain the core data-cleaning rules. Those are delegated to `cleaning.py`.

---

## `cleaning.py`

The data-processing layer.

Responsibilities include:

* validating the input schema
* normalizing textual values
* parsing grades
* converting marks into numeric values
* handling missing marks
* detecting duplicates
* validating scores
* recalculating Total
* generating cleaning statistics

Keeping this logic independent from Streamlit makes it possible to test the pipeline without launching the application.

---

## `tests/test_pipeline.py`

Automated tests for the data-processing and file-ingestion layers.

The test suite covers:

* required-column validation
* missing-column handling
* name normalization
* gender normalization
* grade parsing
* invalid grade handling
* mark parsing
* score range validation
* missing values
* missing student names
* exact duplicate removal
* normalized duplicate removal
* Total recalculation
* CSV ingestion
* XLSX ingestion
* XLS ingestion
* file hashing
* validation against the assessment dataset

---

# Input Data Contract

The expected dataset contains the following columns:

| Column    | Type           | Description          |
| --------- | -------------- | -------------------- |
| `Name`    | String         | Student's full name  |
| `Gender`  | String         | Student's gender     |
| `Grade`   | Numeric/String | Academic grade level |
| `Math`    | Numeric/String | Mathematics marks    |
| `Science` | Numeric/String | Science marks        |
| `English` | Numeric/String | English marks        |
| `Total`   | Numeric/String | Total marks          |

The required schema is validated before the cleaning pipeline proceeds.

A dataset missing a required column is rejected rather than being processed partially.

This prevents silent corruption of the downstream shortlist.

---

# Data Cleaning Pipeline

The cleaning process is intentionally deterministic. Given the same input dataset, the cleaning layer should produce the same normalized output.

## 1. Schema validation

The first step verifies that all required columns are present:

```text
Name
Gender
Grade
Math
Science
English
Total
```

If a required column is missing, processing is stopped and an appropriate validation error is returned.

This is preferable to silently filling a structurally invalid dataset.

---

## 2. Name normalization

Names are normalized to remove common formatting inconsistencies.

Examples:

```text
"  Aarav  "  -> Aarav
ROHAN        -> Rohan
Aditi'       -> Aditi
```

The normalization process handles:

* leading and trailing whitespace
* surrounding quotation marks
* unnecessary apostrophes
* inconsistent capitalization

The implementation intentionally avoids aggressive fuzzy matching.

For recruitment data, automatically deciding that two similar but different names represent the same student can result in incorrect record merging. Safe normalization is therefore preferred over speculative identity correction.

---

## 3. Gender normalization

Gender values are mapped into a consistent representation.

Examples include:

```text
M
m
Male
male
```

being normalized to:

```text
Male
```

and:

```text
F
f
Female
female
```

being normalized to:

```text
Female
```

The dataset also contains encoded values that are mapped consistently according to the dataset's representation.

Values that cannot be safely interpreted are represented as:

```text
Unknown
```

rather than being assigned an arbitrary value.

---

## 4. Grade normalization

Grade values can appear in different textual formats.

For example:

```text
7
Grade 7
grade 7
Grade 11
```

are converted into numeric grade values.

Grades outside the supported academic range are considered invalid and removed from the cleaned dataset.

---

## 5. Mark normalization

Subject marks are converted to numeric values.

The pipeline supports values such as:

```text
85
"85"
"85 marks"
" 92 marks "
```

and extracts the numeric score.

Subject scores are constrained to the valid range:

```text
0 <= score <= 100
```

Values below zero are clipped to zero, while values above one hundred are clipped to one hundred.

This prevents malformed score values from affecting shortlist calculations.

---

## 6. Missing-value handling

Missing subject marks are handled during preprocessing so that the cleaned dataset does not contain unusable subject-score fields.

Rows without a usable student name are removed because such records cannot be reliably associated with a candidate.

The cleaning report records the number of affected records so that the user can inspect what occurred during processing.

---

## 7. Duplicate detection

Duplicate detection occurs at two levels.

### Exact duplicates

Identical rows are removed directly.

### Normalized duplicates

After normalization, records are checked again for duplicate values.

This catches records that are technically different in the raw dataset but become identical after safe normalization.

For example:

```text
"AARAV" | M    | Grade 7 | 80 marks | 90 marks | 85
Aarav   | Male | 7       | 80        | 90        | 85
```

can resolve to the same normalized record.

---

# Total Score Validation

`Total` is treated as a derived field rather than a trusted input field.

The application recalculates:

```text
Total = Math + Science + English
```

for every cleaned record.

For example:

```text
Math     = 80
Science  = 90
English  = 85

Total    = 255
```

If the uploaded dataset contains an incorrect Total value, the calculated value replaces it.

This ensures that filtering is always based on the underlying subject scores.

If the uploaded Total already matches the calculated value, no correction is required.

---

# Shortlisting Logic

The shortlist is generated from the cleaned dataset using two conditions:

```text
Status == Active
```

and:

```text
Total >= minimum_total
```

Conceptually:

```python
shortlist = cleaned_data[
    (cleaned_data["Status"] == "Active") &
    (cleaned_data["Total"] >= minimum_total)
]
```

This means a candidate is shortlisted only when both conditions are satisfied.

### Example

Given:

```text
Minimum Total = 200
```

the following candidates behave as follows:

| Status   | Total | Result      |
| -------- | ----: | ----------- |
| Active   |   240 | Shortlisted |
| Active   |   180 | Excluded    |
| Debarred |   240 | Excluded    |
| Debarred |   180 | Excluded    |

The status condition is applied at the same stage as the score threshold, ensuring that debarred students cannot appear in the final shortlist.

---

# Real-Time Status Management

Student status is maintained using Streamlit session state.

Each student can be changed between:

```text
Active
Debarred
```

When the status changes, the shortlist is recalculated against the current in-memory dataset.

No file re-upload is required.

For example:

```text
Student A
Status: Active
Total: 245
```

appears in a shortlist with a threshold of `200`.

If the user changes:

```text
Active -> Debarred
```

the candidate is immediately removed.

Changing:

```text
Debarred -> Active
```

allows the candidate to return if the score threshold is still satisfied.

This keeps the shortlist synchronized with the current recruitment state.

---

# Performance Considerations

The application uses Pandas for tabular data processing and keeps the cleaned dataset in memory during the Streamlit session.

The provided assessment dataset contains approximately 3,000 records, which is small enough for this architecture to process comfortably without requiring a database or distributed processing system.

The application avoids repeatedly reading the uploaded file when the user changes the shortlist threshold or candidate status.

The workflow is therefore:

```text
File I/O
    |
    v
Clean once
    |
    v
Keep cleaned DataFrame in session
    |
    +--> Change threshold -> filter in memory
    |
    +--> Change status    -> filter in memory
    |
    +--> Export           -> serialize current shortlist
```

This minimizes unnecessary computation and file I/O during interactive use.

---

# Error Handling

The application validates input before processing it.

Examples of handled conditions include:

* unsupported file format
* missing required columns
* invalid grade values
* malformed score values
* missing names
* duplicate records
* missing subject marks

The cleaning report exposes relevant processing statistics to the user instead of silently modifying the dataset.

The goal is to make transformations observable and reproducible.

---

# Testing Strategy

The project uses `pytest` for automated testing of the data-processing layer.

Testing is divided into several categories.

## Unit tests

Individual cleaning operations are tested independently.

Examples:

* name normalization
* grade parsing
* score conversion
* Total calculation
* duplicate detection

## Validation tests

Invalid input scenarios are tested explicitly.

Examples:

* missing required columns
* invalid grades
* missing names
* out-of-range scores

## File-format tests

The ingestion layer is tested with:

```text
CSV
XLSX
XLS
```

to ensure that the supported input formats are handled consistently.

## Dataset-level validation

When the assessment dataset is available locally, the test suite also verifies:

* expected schema
* expected record count
* absence of unexpected missing values
* correctness of calculated Total values

---

# Running the Tests

Create and activate a virtual environment.

### Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the test suite:

```bash
pytest -v
```

A successful test run should report all applicable tests as passing.

---

# Local Development

## Prerequisites

* Python 3.10 or newer
* pip
* Git

Clone the repository:

```bash
git clone <repository-url>
cd student-data-pipeline
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it.

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run app.py
```

The application will be available at:

```text
http://localhost:8501
```

---

# Supported File Formats

The application supports:

```text
.csv
.xlsx
.xls
```

The corresponding Python libraries are:

| Format | Library           |
| ------ | ----------------- |
| CSV    | Pandas            |
| XLSX   | Pandas + OpenPyXL |
| XLS    | Pandas + xlrd     |

---

# Example Workflow

A typical user session is:

```text
1. Launch application
        |
2. Upload CSV/XLSX/XLS
        |
3. Validate input schema
        |
4. Automatically clean dataset
        |
5. Review cleaning report
        |
6. Inspect cleaned records
        |
7. Set minimum Total Score
        |
8. Review live shortlist
        |
9. Debar or undebar candidates
        |
10. Review updated shortlist
        |
11. Export final shortlist
```

---

# Deployment

The application is compatible with Streamlit Community Cloud and other Python-capable hosting environments.

For Streamlit Community Cloud:

1. Push the project to GitHub.
2. Open Streamlit Community Cloud.
3. Create a new application.
4. Select the GitHub repository.
5. Select the appropriate branch.
6. Set `app.py` as the application entry point.
7. Deploy.

The project does not require a database or additional infrastructure for the assessment workflow.

### Deployment

Live application:

```text
[Add deployed application URL]
```

---



# Assessment Requirement Coverage

The implementation maps directly to the requested technical assessment requirements.

| Requirement                      | Implementation                           |
| -------------------------------- | ---------------------------------------- |
| Raw CSV upload                   | Implemented                              |
| Excel upload                     | Implemented                              |
| Automatic cleaning               | Implemented                              |
| Duplicate handling               | Exact and normalized duplicate detection |
| Typo/inconsistency handling      | Safe textual normalization               |
| Missing-value handling           | Implemented                              |
| Total validation                 | Recalculated from subject scores         |
| Cleaned dataset view             | Implemented                              |
| Minimum Total filter             | Implemented                              |
| Live shortlist                   | Implemented                              |
| Shortlist statistics             | Implemented                              |
| CSV export                       | Implemented                              |
| Active/Debarred management       | Implemented                              |
| Real-time exclusion              | Implemented                              |
| No re-upload after status change | Implemented                              |
| Automated tests                  | Implemented                              |
| Documentation                    | This README                              |
| Video demonstration              | To be linked above                       |
| Live deployment                  | Optional                                 |

---

# Design Principles

The implementation follows several principles relevant to a recruitment-data workflow.

### Deterministic processing

Cleaning rules are explicit and deterministic. The same input produces the same cleaned representation.

### Data integrity

Derived fields such as Total are recalculated instead of blindly trusting uploaded values.

### Safe normalization

Formatting inconsistencies are corrected without aggressively guessing candidate identity.

### Separation of concerns

UI logic and data-processing logic are kept separate.

### Immediate feedback

Cleaning statistics, shortlist statistics, and eligibility changes are reflected directly in the interface.

### Minimal infrastructure

The application uses an in-memory Pandas DataFrame because the assessment workload does not justify introducing a database or distributed processing system.

### Testability

The cleaning layer is independent of Streamlit and can therefore be tested through automated unit and integration tests.

---

# Limitations and Future Improvements

The current implementation is intentionally scoped to the requirements of the assessment.

For a production recruitment platform, additional functionality could include:

* persistent candidate storage
* authentication and authorization
* audit logs for status changes
* role-based recruiter access
* database-backed persistence
* candidate IDs for stronger identity management
* configurable validation rules
* configurable scoring schemes
* bulk status updates
* import history
* data-quality dashboards
* structured error reporting
* API-based ingestion
* automated deployment and CI testing

These capabilities are intentionally outside the scope of the current assessment implementation.

---

# Security and Privacy Considerations

Student information can contain personally identifiable information.

The application therefore avoids unnecessary external data-processing services and performs cleaning locally within the application runtime.

For production use, additional controls would be required, including:

* authenticated access
* authorization
* encrypted storage
* audit logging
* secure file handling
* retention policies
* access controls
* appropriate handling of personally identifiable information

The current project is intended as a technical assessment implementation rather than a production recruitment system.

---

# Dependencies

The main dependencies are listed in `requirements.txt`.

Core dependencies:

```text
streamlit
pandas
openpyxl
xlrd
```

Testing:

```text
pytest
```

---

# License

This repository was created for the Student Tech Team technical assessment at Delhi Technological University.

Unless otherwise specified, the project should be treated as an assessment submission and not as a production recruitment system.

---

# Author

**Anand Singh**

B.Tech, Electrical Engineering
Delhi Technological University

Student Tech Team Technical Assessment
Career Development and Industry Engagement (CDIE)

