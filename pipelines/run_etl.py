from pathlib import Path

import pandas as pd

from pipelines.extract import (
    discover_csv_files,
    extract_csv,
)
from pipelines.load import load_processed_csv
from pipelines.metadata import transform_sdg3_metadata
from pipelines.transform import (
    indicator_from_filename,
    transform_health_data,
)
from pipelines.validate import validate_health_data


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw"

EXCLUDED_RAW_FILES = {
    "SDG3_summary.csv",
}

METADATA_RAW_FILE = RAW_DATA_PATH / "SDG3_summary.csv"

PROCESSED_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "asean_health_indicators.csv"
)

METADATA_OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "indicator_metadata.csv"
)


def process_metadata() -> None:
    """
    Process SDG3 metadata into indicator-level documentation.
    """
    if not METADATA_RAW_FILE.exists():
        print(
            f"Skipped metadata: {METADATA_RAW_FILE.name} "
            "was not found."
        )
        return

    print(f"\nProcessing metadata {METADATA_RAW_FILE.name}")

    raw_metadata = extract_csv(METADATA_RAW_FILE)
    transformed_metadata = transform_sdg3_metadata(
        raw_metadata
    )

    load_processed_csv(
        dataframe=transformed_metadata,
        output_path=METADATA_OUTPUT_PATH,
    )


def run_pipeline() -> None:
    """
    Run the complete Project RISING ETL pipeline.
    """
    print("Starting Project RISING ETL pipeline...")

    csv_files = [
        csv_file
        for csv_file in discover_csv_files(RAW_DATA_PATH)
        if csv_file.name not in EXCLUDED_RAW_FILES
    ]

    processed_datasets: list[pd.DataFrame] = []

    for csv_file in csv_files:
        print(f"\nProcessing {csv_file.name}")

        raw_dataframe = extract_csv(csv_file)

        indicator_name = indicator_from_filename(
            csv_file.name
        )

        transformed_dataframe = (
            transform_health_data(
                dataframe=raw_dataframe,
                indicator_name=indicator_name,
            )
        )

        if transformed_dataframe.empty:
            print(
                f"Skipped {csv_file.name}: "
                "no usable country-year-value records were found."
            )
            continue

        warnings = validate_health_data(
            transformed_dataframe
        )

        if warnings:
            for warning in warnings:
                print(f"Validation warning: {warning}")
        else:
            print("Validation passed")

        processed_datasets.append(
            transformed_dataframe
        )

    combined_dataframe = pd.concat(
        processed_datasets,
        ignore_index=True,
    )

    combined_dataframe = (
        combined_dataframe
        .sort_values(
            by=[
                "indicator",
                "country",
                "year",
            ]
        )
        .reset_index(drop=True)
    )

    load_processed_csv(
        dataframe=combined_dataframe,
        output_path=PROCESSED_DATA_PATH,
    )

    process_metadata()

    print(
        "\nETL pipeline completed successfully."
    )

    print(
        f"Processed {len(csv_files)} datasets "
        f"and created {len(combined_dataframe)} "
        "combined records."
    )


if __name__ == "__main__":
    run_pipeline()
