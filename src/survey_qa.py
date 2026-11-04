"""
GNSS Survey Data Quality-Control Tool

This script checks surveying coordinate data for:
- Missing required values
- Duplicate point identifiers
- Coordinates outside the expected project area
- Elevations outside the expected range
- Missing point codes
- Horizontal and vertical accuracy exceeding thresholds

The sample dataset included with this project is synthetic.
No confidential or client survey data is used.
"""

from pathlib import Path

import pandas as pd


INPUT_FILE = Path("sample_data/synthetic_survey_points.csv")
OUTPUT_DIRECTORY = Path("output")
CLEANED_FILE = OUTPUT_DIRECTORY / "cleaned_survey_points.csv"
QA_REPORT_FILE = OUTPUT_DIRECTORY / "qa_report.csv"
SUMMARY_FILE = OUTPUT_DIRECTORY / "qa_summary.txt"

REQUIRED_COLUMNS = [
    "Point_ID",
    "Easting",
    "Northing",
    "Elevation",
    "Point_Code",
    "Horizontal_Accuracy_m",
    "Vertical_Accuracy_m",
    "Survey_Method",
]

MIN_EASTING = 472000.0
MAX_EASTING = 473500.0
MIN_NORTHING = 1712000.0
MAX_NORTHING = 1713500.0
MIN_ELEVATION = 1000.0
MAX_ELEVATION = 1300.0
MAX_HORIZONTAL_ACCURACY = 0.10
MAX_VERTICAL_ACCURACY = 0.20


def validate_columns(dataframe):
    """Confirm that all required columns exist."""

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        missing_text = ", ".join(missing_columns)
        raise ValueError(f"Missing required columns: {missing_text}")


def add_issue(issues, row_number, point_id, issue_type, details):
    """Add one issue to the QA report."""

    issues.append(
        {
            "Row_Number": row_number,
            "Point_ID": point_id,
            "Issue_Type": issue_type,
            "Details": details,
        }
    )


def inspect_survey_data(dataframe):
    """Inspect every survey point and return a list of QA issues."""

    issues = []

    duplicated_ids = dataframe[
        dataframe["Point_ID"].duplicated(keep=False)
    ]["Point_ID"].dropna().unique()

    for dataframe_index, row in dataframe.iterrows():
        row_number = dataframe_index + 2
        point_id = row.get("Point_ID", "UNKNOWN")

        if pd.isna(point_id) or str(point_id).strip() == "":
            point_id = "UNKNOWN"
            add_issue(
                issues,
                row_number,
                point_id,
                "Missing Point ID",
                "Point_ID is blank.",
            )

        for field_name in REQUIRED_COLUMNS:
            field_value = row.get(field_name)

            if pd.isna(field_value) or str(field_value).strip() == "":
                add_issue(
                    issues,
                    row_number,
                    point_id,
                    "Missing Required Value",
                    f"{field_name} is missing.",
                )

        if point_id in duplicated_ids:
            add_issue(
                issues,
                row_number,
                point_id,
                "Duplicate Point ID",
                f"Point_ID {point_id} appears more than once.",
            )

        easting = row.get("Easting")
        if pd.notna(easting):
            if not MIN_EASTING <= easting <= MAX_EASTING:
                add_issue(
                    issues,
                    row_number,
                    point_id,
                    "Easting Outside Expected Range",
                    (
                        f"Easting {easting} is outside "
                        f"{MIN_EASTING} to {MAX_EASTING}."
                    ),
                )

        northing = row.get("Northing")
        if pd.notna(northing):
            if not MIN_NORTHING <= northing <= MAX_NORTHING:
                add_issue(
                    issues,
                    row_number,
                    point_id,
                    "Northing Outside Expected Range",
                    (
                        f"Northing {northing} is outside "
                        f"{MIN_NORTHING} to {MAX_NORTHING}."
                    ),
                )

        elevation = row.get("Elevation")
        if pd.notna(elevation):
            if not MIN_ELEVATION <= elevation <= MAX_ELEVATION:
                add_issue(
                    issues,
                    row_number,
                    point_id,
                    "Elevation Outside Expected Range",
                    (
                        f"Elevation {elevation} is outside "
                        f"{MIN_ELEVATION} to {MAX_ELEVATION}."
                    ),
                )

        horizontal_accuracy = row.get("Horizontal_Accuracy_m")
        if pd.notna(horizontal_accuracy):
            if horizontal_accuracy > MAX_HORIZONTAL_ACCURACY:
                add_issue(
                    issues,
                    row_number,
                    point_id,
                    "Horizontal Accuracy Exceeds Threshold",
                    (
                        f"Reported horizontal accuracy is "
                        f"{horizontal_accuracy} m; maximum allowed is "
                        f"{MAX_HORIZONTAL_ACCURACY} m."
                    ),
                )

        vertical_accuracy = row.get("Vertical_Accuracy_m")
        if pd.notna(vertical_accuracy):
            if vertical_accuracy > MAX_VERTICAL_ACCURACY:
                add_issue(
                    issues,
                    row_number,
                    point_id,
                    "Vertical Accuracy Exceeds Threshold",
                    (
                        f"Reported vertical accuracy is "
                        f"{vertical_accuracy} m; maximum allowed is "
                        f"{MAX_VERTICAL_ACCURACY} m."
                    ),
                )

    return issues


def prepare_cleaned_data(dataframe):
    """Create a cleaned copy while preserving the original observations."""

    cleaned_dataframe = dataframe.copy()

    text_columns = [
        "Point_ID",
        "Point_Code",
        "Survey_Method",
    ]

    for column in text_columns:
        cleaned_dataframe[column] = (
            cleaned_dataframe[column]
            .astype("string")
            .str.strip()
        )

    numeric_columns = [
        "Easting",
        "Northing",
        "Elevation",
        "Horizontal_Accuracy_m",
        "Vertical_Accuracy_m",
    ]

    for column in numeric_columns:
        cleaned_dataframe[column] = pd.to_numeric(
            cleaned_dataframe[column],
            errors="coerce",
        )

    return cleaned_dataframe


def write_summary(dataframe, issues):
    """Write a concise text summary of the QA inspection."""

    issue_dataframe = pd.DataFrame(issues)

    summary_lines = [
        "GNSS Survey Data QA Summary",
        "===========================",
        f"Input file: {INPUT_FILE}",
        f"Total survey records: {len(dataframe)}",
        f"Total QA issues: {len(issues)}",
        "",
        "QA thresholds:",
        (
            f"- Easting range: "
            f"{MIN_EASTING} to {MAX_EASTING}"
        ),
        (
            f"- Northing range: "
            f"{MIN_NORTHING} to {MAX_NORTHING}"
        ),
        (
            f"- Elevation range: "
            f"{MIN_ELEVATION} to {MAX_ELEVATION} m"
        ),
        (
            f"- Maximum horizontal accuracy value: "
            f"{MAX_HORIZONTAL_ACCURACY} m"
        ),
        (
            f"- Maximum vertical accuracy value: "
            f"{MAX_VERTICAL_ACCURACY} m"
        ),
        "",
        "Issue counts by type:",
    ]

    if issue_dataframe.empty:
        summary_lines.append("- No issues detected")
    else:
        issue_counts = (
            issue_dataframe["Issue_Type"]
            .value_counts()
            .sort_index()
        )

        for issue_type, issue_count in issue_counts.items():
            summary_lines.append(
                f"- {issue_type}: {issue_count}"
            )

    SUMMARY_FILE.write_text(
        "\n".join(summary_lines),
        encoding="utf-8",
    )


def main():
    """Run the complete survey-data QA workflow."""

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file was not found: {INPUT_FILE}"
        )

    survey_dataframe = pd.read_csv(INPUT_FILE)

    validate_columns(survey_dataframe)

    cleaned_dataframe = prepare_cleaned_data(
        survey_dataframe
    )

    issues = inspect_survey_data(
        cleaned_dataframe
    )

    qa_report_dataframe = pd.DataFrame(
        issues,
        columns=[
            "Row_Number",
            "Point_ID",
            "Issue_Type",
            "Details",
        ],
    )

    cleaned_dataframe.to_csv(
        CLEANED_FILE,
        index=False,
    )

    qa_report_dataframe.to_csv(
        QA_REPORT_FILE,
        index=False,
    )

    write_summary(
        cleaned_dataframe,
        issues,
    )

    print("GNSS survey-data QA completed successfully.")
    print(f"Records inspected: {len(cleaned_dataframe)}")
    print(f"QA issues detected: {len(issues)}")
    print(f"Cleaned data: {CLEANED_FILE}")
    print(f"QA report: {QA_REPORT_FILE}")
    print(f"Summary: {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
