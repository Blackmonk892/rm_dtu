import io
from pathlib import Path

import pandas as pd
import pytest

from cleaning import clean_dataframe
from app import read_uploaded_file, calculate_file_hash


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_PATH = (
    PROJECT_ROOT
    / "RM_Student_Selection_Dataset.xlsx"
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def messy_dataframe():

    return pd.DataFrame(
        {
            "Name": [
                '"  aarav  "',
                "ROHAN",
                "Aditi'",
                "Aarav",
                None,
            ],

            "Gender": [
                "male",
                "F",
                "female",
                "M",
                "unknown",
            ],

            "Grade": [
                7,
                "Grade 8",
                "grade 10",
                5,
                "invalid",
            ],

            "Math": [
                80,
                "75 marks",
                90,
                None,
                50,
            ],

            "Science": [
                85,
                70,
                "92 marks",
                80,
                None,
            ],

            "English": [
                90,
                65,
                88,
                75,
                60,
            ],

            "Total": [
                999,
                999,
                999,
                999,
                999,
            ],
        }
    )


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

def test_required_columns_are_present():

    df = pd.DataFrame(
        {
            "Name": [],
            "Gender": [],
            "Grade": [],
            "Math": [],
            "Science": [],
            "English": [],
            "Total": [],
        }
    )

    cleaned, report = clean_dataframe(df)

    assert cleaned is not None
    assert report["missing_col_error"] is None


def test_missing_required_column_is_rejected():

    df = pd.DataFrame(
        {
            "Name": ["Aarav"],
            "Gender": ["M"],
            "Grade": [7],
            "Math": [80],
            "Science": [90],
            # English missing
            "Total": [170],
        }
    )

    cleaned, report = clean_dataframe(df)

    assert cleaned is None

    assert "English" in report[
        "missing_col_error"
    ]


# ---------------------------------------------------------------------------
# Name cleaning
# ---------------------------------------------------------------------------

def test_names_are_normalized(
    messy_dataframe,
):

    cleaned, _ = clean_dataframe(
        messy_dataframe
    )

    assert "Aarav" in cleaned["Name"].values

    assert all(
        '"' not in name
        for name in cleaned["Name"]
    )

    assert all(
        "'" not in name
        for name in cleaned["Name"]
    )


# ---------------------------------------------------------------------------
# Gender cleaning
# ---------------------------------------------------------------------------

def test_gender_values_are_normalized(
    messy_dataframe,
):

    cleaned, _ = clean_dataframe(
        messy_dataframe
    )

    assert set(
        cleaned["Gender"].unique()
    ).issubset(
        {
            "Male",
            "Female",
            "Unknown",
        }
    )


# ---------------------------------------------------------------------------
# Grade cleaning
# ---------------------------------------------------------------------------

def test_grade_strings_are_parsed(
    messy_dataframe,
):

    cleaned, report = clean_dataframe(
        messy_dataframe
    )

    assert cleaned is not None

    assert all(
        cleaned["Grade"].between(1, 12)
    )


def test_invalid_grades_are_removed():

    df = pd.DataFrame(
        {
            "Name": [
                "Aarav",
                "Rohan",
            ],
            "Gender": [
                "M",
                "F",
            ],
            "Grade": [
                "Grade 7",
                "Grade 99",
            ],
            "Math": [
                80,
                70,
            ],
            "Science": [
                80,
                70,
            ],
            "English": [
                80,
                70,
            ],
            "Total": [
                240,
                210,
            ],
        }
    )

    cleaned, report = clean_dataframe(df)

    assert len(cleaned) == 1

    assert (
        report["rows_invalid_grade_dropped"]
        == 1
    )


# ---------------------------------------------------------------------------
# Score cleaning
# ---------------------------------------------------------------------------

def test_marks_with_text_are_parsed(
    messy_dataframe,
):

    cleaned, _ = clean_dataframe(
        messy_dataframe
    )

    assert 75 in cleaned["Math"].values

    assert 92 in cleaned["Science"].values


def test_scores_are_constrained_to_valid_range():

    df = pd.DataFrame(
        {
            "Name": ["Aarav"],
            "Gender": ["M"],
            "Grade": [7],
            "Math": [150],
            "Science": [-10],
            "English": [80],
            "Total": [220],
        }
    )

    cleaned, report = clean_dataframe(df)

    assert cleaned.iloc[0]["Math"] == 100

    assert cleaned.iloc[0]["Science"] == 0

    assert report[
        "invalid_scores_clipped"
    ] >= 2


# ---------------------------------------------------------------------------
# Missing values
# ---------------------------------------------------------------------------

def test_missing_subject_marks_are_filled(
    messy_dataframe,
):

    cleaned, report = clean_dataframe(
        messy_dataframe
    )

    assert not cleaned[
        ["Math", "Science", "English"]
    ].isna().any().any()

    assert (
        report["rows_missing_marks_filled"]
        > 0
    )


def test_missing_name_is_removed():

    df = pd.DataFrame(
        {
            "Name": [
                "Aarav",
                None,
            ],
            "Gender": [
                "M",
                "F",
            ],
            "Grade": [
                7,
                8,
            ],
            "Math": [
                80,
                70,
            ],
            "Science": [
                80,
                70,
            ],
            "English": [
                80,
                70,
            ],
            "Total": [
                240,
                210,
            ],
        }
    )

    cleaned, report = clean_dataframe(df)

    assert len(cleaned) == 1

    assert (
        report["rows_missing_name_dropped"]
        == 1
    )


# ---------------------------------------------------------------------------
# Duplicate tests
# ---------------------------------------------------------------------------

def test_exact_duplicates_are_removed():

    df = pd.DataFrame(
        {
            "Name": [
                "Aarav",
                "Aarav",
            ],
            "Gender": [
                "M",
                "M",
            ],
            "Grade": [
                7,
                7,
            ],
            "Math": [
                80,
                80,
            ],
            "Science": [
                90,
                90,
            ],
            "English": [
                85,
                85,
            ],
            "Total": [
                255,
                255,
            ],
        }
    )

    cleaned, report = clean_dataframe(df)

    assert len(cleaned) == 1

    assert (
        report["exact_duplicates_removed"]
        == 1
    )


def test_normalized_duplicates_are_removed():

    df = pd.DataFrame(
        {
            "Name": [
                "Aarav",
                '"AARAV"',
            ],
            "Gender": [
                "Male",
                "M",
            ],
            "Grade": [
                7,
                "Grade 7",
            ],
            "Math": [
                80,
                "80 marks",
            ],
            "Science": [
                90,
                "90 marks",
            ],
            "English": [
                85,
                85,
            ],
            "Total": [
                255,
                255,
            ],
        }
    )

    cleaned, report = clean_dataframe(df)

    assert len(cleaned) == 1

    assert (
        report[
            "normalized_duplicates_removed"
        ]
        == 1
    )


# ---------------------------------------------------------------------------
# Total validation
# ---------------------------------------------------------------------------

def test_total_is_recalculated():

    df = pd.DataFrame(
        {
            "Name": ["Aarav"],
            "Gender": ["M"],
            "Grade": [7],
            "Math": [80],
            "Science": [90],
            "English": [85],
            "Total": [999],
        }
    )

    cleaned, report = clean_dataframe(df)

    assert (
        cleaned.iloc[0]["Total"]
        == 255
    )

    assert (
        report["totals_recalculated"]
        == 1
    )


def test_total_is_correct_for_real_dataset():

    if not DATASET_PATH.exists():

        pytest.skip(
            "Real assessment dataset not present"
        )

    df = pd.read_excel(
        DATASET_PATH,
        engine="openpyxl",
    )

    cleaned, report = clean_dataframe(df)

    assert cleaned is not None

    calculated_total = (
        cleaned["Math"]
        + cleaned["Science"]
        + cleaned["English"]
    )

    pd.testing.assert_series_equal(
        cleaned["Total"],
        calculated_total,
        check_names=False,
    )


# ---------------------------------------------------------------------------
# Real dataset tests
# ---------------------------------------------------------------------------

def test_real_dataset_schema():

    if not DATASET_PATH.exists():

        pytest.skip(
            "Real assessment dataset not present"
        )

    df = pd.read_excel(
        DATASET_PATH,
        engine="openpyxl",
    )

    expected_columns = {
        "Name",
        "Gender",
        "Grade",
        "Math",
        "Science",
        "English",
        "Total",
    }

    assert set(df.columns) == expected_columns


def test_real_dataset_has_3000_rows():

    if not DATASET_PATH.exists():

        pytest.skip(
            "Real assessment dataset not present"
        )

    df = pd.read_excel(
        DATASET_PATH,
        engine="openpyxl",
    )

    assert len(df) == 3000


def test_real_dataset_has_no_missing_values():

    if not DATASET_PATH.exists():

        pytest.skip(
            "Real assessment dataset not present"
        )

    df = pd.read_excel(
        DATASET_PATH,
        engine="openpyxl",
    )

    assert not df.isna().any().any()


# ---------------------------------------------------------------------------
# File format tests
# ---------------------------------------------------------------------------

def test_csv_reader():

    csv_content = (
        "Name,Gender,Grade,Math,Science,English,Total\n"
        "Aarav,Male,7,80,90,85,255\n"
    )

    result = read_uploaded_file(
        csv_content.encode("utf-8"),
        "students.csv",
    )

    assert len(result) == 1

    assert list(result.columns) == [
        "Name",
        "Gender",
        "Grade",
        "Math",
        "Science",
        "English",
        "Total",
    ]


def test_xlsx_reader():

    buffer = io.BytesIO()

    df = pd.DataFrame(
        {
            "Name": ["Aarav"],
            "Gender": ["M"],
            "Grade": [7],
            "Math": [80],
            "Science": [90],
            "English": [85],
            "Total": [255],
        }
    )

    df.to_excel(
        buffer,
        index=False,
        engine="openpyxl",
    )

    result = read_uploaded_file(
        buffer.getvalue(),
        "students.xlsx",
    )

    assert len(result) == 1

    assert result.iloc[0]["Name"] == "Aarav"


def test_xls_reader():

    pytest.importorskip("xlwt")

    buffer = io.BytesIO()

    df = pd.DataFrame(
        {
            "Name": ["Aarav"],
            "Gender": ["M"],
            "Grade": [7],
            "Math": [80],
            "Science": [90],
            "English": [85],
            "Total": [255],
        }
    )

    df.to_excel(
        buffer,
        index=False,
        engine="xlwt",
    )

    result = read_uploaded_file(
        buffer.getvalue(),
        "students.xls",
    )

    assert len(result) == 1

    assert result.iloc[0]["Name"] == "Aarav"


# ---------------------------------------------------------------------------
# File hash tests
# ---------------------------------------------------------------------------

def test_file_hash_is_deterministic():

    data = b"student dataset"

    hash_1 = calculate_file_hash(
        data
    )

    hash_2 = calculate_file_hash(
        data
    )

    assert hash_1 == hash_2


def test_file_hash_changes_when_content_changes():

    hash_1 = calculate_file_hash(
        b"dataset A"
    )

    hash_2 = calculate_file_hash(
        b"dataset B"
    )

    assert hash_1 != hash_2