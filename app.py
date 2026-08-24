"""
Student Data Pipeline & UI
--------------------------

A Streamlit application that:

1. Accepts CSV, XLSX and XLS student datasets.
2. Automatically cleans and validates the data.
3. Displays the cleaned dataset.
4. Allows real-time Active/Debarred status management.
5. Filters active students using a minimum Total score.
6. Displays live shortlist statistics.
7. Exports the final shortlist as CSV.
"""

import hashlib
import io
from datetime import datetime

import pandas as pd
import streamlit as st

from cleaning import (
    REQUIRED_COLUMNS,
    clean_dataframe,
)


# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Student Data Pipeline",
    page_icon="🎓",
    layout="wide",
)


# ---------------------------------------------------------------------------
# File reading
# ---------------------------------------------------------------------------

def read_uploaded_file(
    file_bytes: bytes,
    filename: str,
) -> pd.DataFrame:
    """
    Read CSV, XLSX or XLS files into a pandas DataFrame.

    The cleaning pipeline receives the same DataFrame regardless
    of the original file format.
    """

    file_stream = io.BytesIO(file_bytes)

    extension = (
        filename.lower()
        .rsplit(".", 1)[-1]
    )

    if extension == "csv":

        # UTF-8 first.
        try:
            return pd.read_csv(
                file_stream
            )

        except UnicodeDecodeError:

            file_stream.seek(0)

            return pd.read_csv(
                file_stream,
                encoding="latin-1",
            )

    if extension == "xlsx":

        return pd.read_excel(
            file_stream,
            engine="openpyxl",
        )

    if extension == "xls":

        return pd.read_excel(
            file_stream,
            engine="xlrd",
        )

    raise ValueError(
        "Unsupported file format. "
        "Please upload CSV, XLSX or XLS."
    )


# ---------------------------------------------------------------------------
# File hashing
# ---------------------------------------------------------------------------

def calculate_file_hash(
    file_bytes: bytes,
) -> str:
    """
    Generate a SHA-256 hash for the uploaded file.

    This allows the application to detect a changed file even
    when the filename remains identical.
    """

    return hashlib.sha256(
        file_bytes
    ).hexdigest()


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def init_state():

    defaults = {
        "working_df": None,
        "clean_report": None,
        "source_name": None,
        "source_hash": None,
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


def reset_state():

    st.session_state.working_df = None
    st.session_state.clean_report = None
    st.session_state.source_name = None
    st.session_state.source_hash = None

    # Reset the data editor widget as well.
    if "status_editor" in st.session_state:
        del st.session_state["status_editor"]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_and_clean(
    file_bytes: bytes,
    source_name: str,
):
    """
    Read and clean an uploaded dataset.
    """

    df_raw = read_uploaded_file(
        file_bytes,
        source_name,
    )

    cleaned, report = clean_dataframe(
        df_raw
    )

    if cleaned is None:
        return None, report

    # Add interactive status column.
    cleaned.insert(
        0,
        "Status",
        "Active",
    )

    return cleaned, report


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def display_cleaning_report(report):

    with st.expander(
        "🧹 Cleaning Report",
        expanded=True,
    ):

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Rows in",
            report["rows_in"],
        )

        c2.metric(
            "Exact duplicates removed",
            report["exact_duplicates_removed"],
        )

        dropped = (
            report["rows_missing_name_dropped"]
            + report["rows_invalid_grade_dropped"]
        )

        c3.metric(
            "Invalid rows dropped",
            dropped,
        )

        c4.metric(
            "Rows out",
            report["rows_out"],
        )

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:

            st.write(
                "### Cleaning actions"
            )

            st.write(
                f"• Missing mark cells filled: "
                f"**{report['rows_missing_marks_filled']}**"
            )

            st.write(
                f"• Exact duplicate rows removed: "
                f"**{report['exact_duplicates_removed']}**"
            )

            st.write(
                f"• Duplicate rows found after normalization: "
                f"**{report['normalized_duplicates_removed']}**"
            )

            st.write(
                f"• Invalid grade rows removed: "
                f"**{report['rows_invalid_grade_dropped']}**"
            )

        with col2:

            st.write(
                "### Validation"
            )

            st.write(
                f"• Missing-name rows removed: "
                f"**{report['rows_missing_name_dropped']}**"
            )

            st.write(
                f"• Score values clipped to 0–100: "
                f"**{report['invalid_scores_clipped']}**"
            )

            st.write(
                f"• Total values recalculated: "
                f"**{report['totals_recalculated']}**"
            )

            st.write(
                "• Total = Math + Science + English"
            )


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

def main():

    init_state()

    # -----------------------------------------------------------------------
    # Header
    # -----------------------------------------------------------------------

    st.title(
        "🎓 Student Data Pipeline & Shortlist Tool"
    )

    st.caption(
        "Upload a raw CSV or Excel dataset → "
        "automatically clean it → manage Active/Debarred "
        "status → filter by minimum Total → export."
    )

    # -----------------------------------------------------------------------
    # 1. Upload
    # -----------------------------------------------------------------------

    st.header(
        "1. Upload & Clean"
    )

    uploaded = st.file_uploader(
        "Upload raw student dataset",
        type=[
            "csv",
            "xlsx",
            "xls",
        ],
        help=(
            "Supported formats: "
            "CSV (.csv), Excel (.xlsx), "
            "and Excel 97-2003 (.xls)"
        ),
    )

    col_a, col_b = st.columns(
        [3, 1]
    )

    with col_a:

        if uploaded is not None:

            file_bytes = uploaded.getvalue()

            current_hash = calculate_file_hash(
                file_bytes
            )

            # Process only when the file contents actually change.
            if (
                st.session_state.source_hash
                != current_hash
            ):

                with st.spinner(
                    "Reading and cleaning dataset..."
                ):

                    try:

                        cleaned, report = load_and_clean(
                            file_bytes,
                            uploaded.name,
                        )

                    except Exception as exc:

                        st.error(
                            "Could not read the uploaded file."
                        )

                        st.exception(exc)

                        return

                if cleaned is None:

                    st.error(
                        "Upload failed."
                    )

                    if report.get(
                        "missing_col_error"
                    ):

                        st.error(
                            "Missing required columns: "
                            + ", ".join(
                                report[
                                    "missing_col_error"
                                ]
                            )
                        )

                    return

                # Store processed data.
                st.session_state.working_df = cleaned

                st.session_state.clean_report = report

                st.session_state.source_name = (
                    uploaded.name
                )

                st.session_state.source_hash = (
                    current_hash
                )

                # Clear previous editor state.
                if "status_editor" in st.session_state:
                    del st.session_state[
                        "status_editor"
                    ]

    with col_b:

        if st.button(
            "🔄 Reset",
            use_container_width=True,
        ):

            reset_state()

            st.rerun()

    # -----------------------------------------------------------------------
    # Empty state
    # -----------------------------------------------------------------------

    if (
        st.session_state.working_df
        is None
    ):

        st.info(
            "Upload a CSV or Excel file to get started."
        )

        st.markdown(
            "**Required columns:** "
            + ", ".join(REQUIRED_COLUMNS)
        )

        st.markdown(
            """
            **Supported formats**

            - CSV (`.csv`)
            - Excel (`.xlsx`)
            - Excel 97–2003 (`.xls`)
            """
        )

        return

    # -----------------------------------------------------------------------
    # File information
    # -----------------------------------------------------------------------

    st.success(
        f"Loaded: **{st.session_state.source_name}**"
    )

    # -----------------------------------------------------------------------
    # Cleaning report
    # -----------------------------------------------------------------------

    display_cleaning_report(
        st.session_state.clean_report
    )

    # -----------------------------------------------------------------------
    # Cleaned dataset
    # -----------------------------------------------------------------------

    st.subheader(
        "Cleaned Dataset"
    )

    st.caption(
        "All fields except Status are read-only. "
        "Use the Status dropdown to Active/Debar students."
    )

    # -----------------------------------------------------------------------
    # Editable table
    # -----------------------------------------------------------------------

    editable_columns = [
        "Status",
        "Name",
        "Gender",
        "Grade",
        "Math",
        "Science",
        "English",
        "Total",
    ]

    edited_df = st.data_editor(
        st.session_state.working_df[
            editable_columns
        ],
        column_config={

            "Status":
                st.column_config.SelectboxColumn(
                    "Status",
                    options=[
                        "Active",
                        "Debarred",
                    ],
                    required=True,
                ),

            "Name":
                st.column_config.TextColumn(
                    "Name",
                    disabled=True,
                ),

            "Gender":
                st.column_config.TextColumn(
                    "Gender",
                    disabled=True,
                ),

            "Grade":
                st.column_config.NumberColumn(
                    "Grade",
                    disabled=True,
                ),

            "Math":
                st.column_config.NumberColumn(
                    "Math",
                    disabled=True,
                ),

            "Science":
                st.column_config.NumberColumn(
                    "Science",
                    disabled=True,
                ),

            "English":
                st.column_config.NumberColumn(
                    "English",
                    disabled=True,
                ),

            "Total":
                st.column_config.NumberColumn(
                    "Total",
                    disabled=True,
                ),
        },

        disabled=[
            "Name",
            "Gender",
            "Grade",
            "Math",
            "Science",
            "English",
            "Total",
        ],

        hide_index=True,

        use_container_width=True,

        height=360,

        key="status_editor",
    )

    # Persist status changes.
    st.session_state.working_df[
        "Status"
    ] = edited_df[
        "Status"
    ].values

    debarred_count = int(
        (
            st.session_state.working_df[
                "Status"
            ]
            == "Debarred"
        ).sum()
    )

    active_count = int(
        (
            st.session_state.working_df[
                "Status"
            ]
            == "Active"
        ).sum()
    )

    c1, c2 = st.columns(2)

    c1.metric(
        "Active students",
        active_count,
    )

    c2.metric(
        "Debarred students",
        debarred_count,
    )

    # -----------------------------------------------------------------------
    # Filtering
    # -----------------------------------------------------------------------

    st.divider()

    st.header(
        "2. Minimum Total Score Filter & Shortlist"
    )

    st.caption(
        "Only Active students are considered. "
        "Debarred students are automatically excluded."
    )

    active_df = (
        st.session_state.working_df[
            st.session_state.working_df[
                "Status"
            ]
            == "Active"
        ]
        .copy()
    )

    # -----------------------------------------------------------------------
    # Threshold
    # -----------------------------------------------------------------------

    min_total = int(
        st.session_state.working_df[
            "Total"
        ].min()
    )

    max_total = int(
        st.session_state.working_df[
            "Total"
        ].max()
    )

    if min_total == max_total:

        threshold = st.number_input(
            "Minimum total score",
            min_value=min_total,
            max_value=max_total,
            value=min_total,
            step=1,
        )

    else:

        threshold_slider = st.slider(
            "Minimum total score",
            min_value=min_total,
            max_value=max_total,
            value=min_total,
            step=1,
        )

        threshold_input = st.number_input(
            "Or type an exact threshold",
            min_value=min_total,
            max_value=max_total,
            value=threshold_slider,
            step=1,
        )

        threshold = threshold_input

    # -----------------------------------------------------------------------
    # Shortlist
    # -----------------------------------------------------------------------

    shortlist = (
        active_df[
            active_df["Total"]
            >= threshold
        ]
        .sort_values(
            "Total",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    # -----------------------------------------------------------------------
    # Statistics
    # -----------------------------------------------------------------------

    st.subheader(
        "Live Shortlist Statistics"
    )

    s1, s2, s3, s4 = st.columns(4)

    s1.metric(
        "Matched students",
        len(shortlist),
    )

    s2.metric(
        "Average Total",
        (
            f"{shortlist['Total'].mean():.1f}"
            if len(shortlist)
            else "—"
        ),
    )

    s3.metric(
        "Average Math",
        (
            f"{shortlist['Math'].mean():.1f}"
            if len(shortlist)
            else "—"
        ),
    )

    s4.metric(
        "Average Science / English",
        (
            f"{shortlist['Science'].mean():.1f} / "
            f"{shortlist['English'].mean():.1f}"
            if len(shortlist)
            else "—"
        ),
    )

    # -----------------------------------------------------------------------
    # Shortlist table
    # -----------------------------------------------------------------------

    st.subheader(
        "Live Shortlist"
    )

    if shortlist.empty:

        st.warning(
            "No active students meet the selected minimum Total score."
        )

    else:

        st.dataframe(
            shortlist.drop(
                columns=["Status"]
            ),
            use_container_width=True,
            height=300,
            hide_index=True,
        )

    # -----------------------------------------------------------------------
    # Export
    # -----------------------------------------------------------------------

    csv_bytes = (
        shortlist
        .drop(columns=["Status"])
        .to_csv(index=False)
        .encode("utf-8")
    )

    filename = (
        f"shortlist_min{int(threshold)}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    )

    st.download_button(
        "⬇️ Download Shortlist as CSV",
        data=csv_bytes,
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )

    # -----------------------------------------------------------------------
    # Footer
    # -----------------------------------------------------------------------

    st.divider()

    st.caption(
        "Student Data Pipeline • "
        "CSV / XLSX / XLS • "
        "Automatic cleaning • "
        "Real-time shortlist"
    )


if __name__ == "__main__":
    main()