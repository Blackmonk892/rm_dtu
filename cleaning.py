"""
Student Data Pipeline - Cleaning Module
---------------------------------------

Contains all data validation and cleaning logic for the application.

Supported input schema:
    Name, Gender, Grade, Math, Science, English, Total
"""

import re
from typing import Optional, Tuple

import pandas as pd


REQUIRED_COLUMNS = [
    "Name",
    "Gender",
    "Grade",
    "Math",
    "Science",
    "English",
    "Total",
]

SUBJECTS = ["Math", "Science", "English"]


def clean_name(raw) -> str:
    """
    Normalize a student's name.

    Handles:
    - Missing values
    - Extra whitespace
    - Stray quotation marks
    - Inconsistent casing
    """
    if pd.isna(raw):
        return ""

    name = str(raw).strip()

    # Remove common stray quote characters.
    name = name.replace('"', "")
    name = name.replace("'", "")

    # Collapse repeated whitespace.
    name = re.sub(r"\s+", " ", name).strip()

    if not name:
        return ""

    return name.title()


def clean_gender(raw) -> str:
    """
    Normalize gender values.

    Supported:
        Male / M
        Female / F

    Numeric 0/1 values are NOT guessed because their meaning
    depends on the source dataset's documentation.

    Unknown/unrecognized values become 'Unknown'.
    """
    if pd.isna(raw):
        return "Unknown"

    value = str(raw).strip().lower()

    male_tokens = {
        "male",
        "m",
        "man",
        "boy",
        "1",
    }

    female_tokens = {
        "female",
        "f",
        "woman",
        "girl",
        "0",
    }

    if value in male_tokens:
        return "Male"

    if value in female_tokens:
        return "Female"

    return "Unknown"


def clean_grade(raw) -> Optional[int]:
    """
    Parse and validate an academic grade.

    Examples:
        7          -> 7
        "7"        -> 7
        "Grade 7"  -> 7
        "grade 10" -> 10

    Valid grades are 1-12.
    """
    if pd.isna(raw):
        return None

    text = str(raw).strip()

    # Extract a standalone integer.
    match = re.search(r"\d+", text)

    if not match:
        return None

    try:
        grade = int(match.group())
    except ValueError:
        return None

    if 1 <= grade <= 12:
        return grade

    return None


def clean_score(raw) -> Optional[float]:
    """
    Parse and validate a subject mark.

    Handles:
        82
        82.0
        "82"
        "82 marks"
        "Score: 82.5"

    Values are constrained to the valid 0-100 range.

    Returns None when the value cannot be parsed.
    """
    if pd.isna(raw):
        return None

    text = str(raw).strip()

    if not text:
        return None

    # Find the first integer or decimal number.
    match = re.search(r"-?\d+(?:\.\d+)?", text)

    if not match:
        return None

    try:
        score = float(match.group())
    except ValueError:
        return None

    # Invalid negative scores become 0.
    # Values over 100 are capped at 100.
    score = max(0.0, min(100.0, score))

    return score


def validate_columns(df: pd.DataFrame):
    """
    Validate that all required columns are present.

    Returns:
        list[str]: missing columns
    """
    normalized_columns = {
        str(column).strip(): column
        for column in df.columns
    }

    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in normalized_columns
    ]

    return missing


def clean_dataframe(
    df_raw: pd.DataFrame,
) -> Tuple[Optional[pd.DataFrame], dict]:
    """
    Run the complete cleaning pipeline.

    Returns:
        cleaned_dataframe, report

    If schema validation fails:
        cleaned_dataframe = None
    """
    if df_raw is None:
        report = {
            "rows_in": 0,
            "missing_col_error": ["The uploaded file is empty."],
            "exact_duplicates_removed": 0,
            "normalized_duplicates_removed": 0,
            "rows_missing_name_dropped": 0,
            "rows_missing_marks_filled": 0,
            "rows_invalid_grade_dropped": 0,
            "invalid_scores_clipped": 0,
            "totals_recalculated": 0,
            "rows_out": 0,
        }
        return None, report

    report = {
        "rows_in": len(df_raw),
        "missing_col_error": None,
        "exact_duplicates_removed": 0,
        "normalized_duplicates_removed": 0,
        "rows_missing_name_dropped": 0,
        "rows_missing_marks_filled": 0,
        "rows_invalid_grade_dropped": 0,
        "invalid_scores_clipped": 0,
        "totals_recalculated": 0,
        "rows_out": 0,
    }

    df = df_raw.copy()

    # ---------------------------------------------------------
    # 1. Normalize column names & validate schema
    # ---------------------------------------------------------
    df.columns = [str(column).strip() for column in df.columns]

    missing_columns = validate_columns(df)
    if missing_columns:
        report["missing_col_error"] = missing_columns
        return None, report

    # Keep only required columns
    df = df[REQUIRED_COLUMNS].copy()

    # If the DataFrame has 0 rows but valid columns, return empty cleaned DataFrame
    if df.empty:
        report["rows_out"] = 0
        return df, report

    # ---------------------------------------------------------
    # 2. Remove exact duplicate rows
    # ---------------------------------------------------------
    before = len(df)
    df = df.drop_duplicates(keep="first")
    report["exact_duplicates_removed"] = before - len(df)

    # ---------------------------------------------------------
    # 3. Clean text / numeric columns
    # ---------------------------------------------------------
    df["Name"] = df["Name"].apply(clean_name)
    df["Gender"] = df["Gender"].apply(clean_gender)
    df["Grade"] = df["Grade"].apply(clean_grade)

    for subject in SUBJECTS:
        original = df[subject].copy()
        df[subject] = df[subject].apply(clean_score)

        for old, new in zip(original, df[subject]):
            if not pd.isna(old) and not pd.isna(new):
                try:
                    numeric_old = float(old)
                    if numeric_old < 0 or numeric_old > 100:
                        report["invalid_scores_clipped"] += 1
                except (ValueError, TypeError):
                    pass

    # ---------------------------------------------------------
    # 4. Remove rows without a usable name
    # ---------------------------------------------------------
    before = len(df)
    df = df[df["Name"].astype(str).str.strip().str.len() > 0].copy()
    report["rows_missing_name_dropped"] = before - len(df)

    # ---------------------------------------------------------
    # 5. Drop rows with invalid grades
    # ---------------------------------------------------------
    before = len(df)
    df = df[df["Grade"].notna()].copy()
    report["rows_invalid_grade_dropped"] = before - len(df)

    # ---------------------------------------------------------
    # 6. Fill missing subject marks
    # ---------------------------------------------------------
    missing_cells = int(df[SUBJECTS].isna().sum().sum())
    report["rows_missing_marks_filled"] = missing_cells

    for subject in SUBJECTS:
        if not df[subject].isna().any():
            continue

        median_value = df[subject].median()
        if pd.isna(median_value):
            median_value = 0

        df[subject] = df[subject].fillna(median_value)

    # ---------------------------------------------------------
    # 7. Normalize duplicate records AFTER cleaning
    # ---------------------------------------------------------
    before = len(df)
    duplicate_columns = [
        "Name",
        "Gender",
        "Grade",
        "Math",
        "Science",
        "English",
    ]
    df = df.drop_duplicates(subset=duplicate_columns, keep="first")
    report["normalized_duplicates_removed"] = before - len(df)

    # ---------------------------------------------------------
    # 8. Recalculate Total
    # ---------------------------------------------------------
    for subject in SUBJECTS:
        df[subject] = pd.to_numeric(df[subject], errors="coerce").fillna(0)

    new_total = df["Math"] + df["Science"] + df["English"]
    old_total = pd.to_numeric(df["Total"], errors="coerce")

    report["totals_recalculated"] = int(old_total.ne(new_total).sum())
    df["Total"] = new_total

    # ---------------------------------------------------------
    # 9. Final data types
    # ---------------------------------------------------------
    df["Grade"] = df["Grade"].astype(int)

    for subject in SUBJECTS:
        df[subject] = df[subject].round(2)

    df["Total"] = df["Total"].round(2)

    # ---------------------------------------------------------
    # 10. Reset index
    # ---------------------------------------------------------
    df = df.reset_index(drop=True)
    report["rows_out"] = len(df)

    return df, report