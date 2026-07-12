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


def process_metadata() -> bool:
    """
    Process SDG3 metadata into indicator-level documentation.
    """
    if not METADATA_RAW_FILE.exists():
        print(
            f"Skipped metadata: {METADATA_RAW_FILE.name} "
            "was not found."
        )
        return False

    print(f"\nProcessing metadata {METADATA_RAW_FILE.name}")

    raw_metadata = extract_csv(METADATA_RAW_FILE)
    transformed_metadata = transform_sdg3_metadata(
        raw_metadata
    )

    load_processed_csv(
        dataframe=transformed_metadata,
        output_path=METADATA_OUTPUT_PATH,
    )

    return True


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
    skipped_files: list[str] = []

    for csv_file in csv_files:
        print(f"\nProcessing {csv_file.name}")

        try:
            raw_dataframe = extract_csv(csv_file)

            indicator_name = indicator_from_filename(
                csv_file.name
            )

            transformed_dataframe = transform_health_data(
                dataframe=raw_dataframe,
                indicator_name=indicator_name,
            )

            if transformed_dataframe.empty:
                print(
                    f"Skipped {csv_file.name}: "
                    "no usable ASEAN country-year-value "
                    "records were found."
                )
                skipped_files.append(csv_file.name)
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

        except (
            ValueError,
            FileNotFoundError,
            NotADirectoryError,
        ) as error:
            print(f"Skipped {csv_file.name}: {error}")
            skipped_files.append(csv_file.name)
            continue

    if not processed_datasets:
        raise RuntimeError(
            "ETL failed: no datasets produced usable records."
        )

    combined_dataframe = pd.concat(
        processed_datasets,
        ignore_index=True,
    )

    duplicate_columns = [
        "country",
        "year",
        "indicator",
    ]

    for optional_column in [
        "sub_indicator",
        "sex",
    ]:
        if optional_column in combined_dataframe.columns:
            duplicate_columns.append(optional_column)

    combined_dataframe = (
        combined_dataframe
        .drop_duplicates(subset=duplicate_columns)
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

    metadata_processed = process_metadata()

    print("\nETL pipeline completed successfully.")
    print(f"CSV files discovered: {len(csv_files)}")
    print(f"Datasets processed: {len(processed_datasets)}")
    print(f"Datasets skipped: {len(skipped_files)}")
    print(
        f"Metadata processed: "
        f"{'yes' if metadata_processed else 'no'}"
    )
    print(
        f"Combined records created: "
        f"{len(combined_dataframe)}"
    )

    if skipped_files:
        print("\nSkipped files:")
        for skipped_file in skipped_files:
            print(f"- {skipped_file}")


if __name__ == "__main__":
    run_pipeline()
