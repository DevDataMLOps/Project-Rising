import pandas as pd


VALID_ASEAN_COUNTRIES = {
    "Brunei",
    "Cambodia",
    "Indonesia",
    "Laos",
    "Malaysia",
    "Myanmar",
    "Philippines",
    "Singapore",
    "Thailand",
    "Timor-Leste",
    "Vietnam",
}


def validate_health_data(
    dataframe: pd.DataFrame,
) -> list[str]:
    """
    Validate a transformed health dataset.

    Returns a list of validation warnings.
    """
    warnings: list[str] = []

    required_columns = {
        "country",
        "year",
        "indicator",
        "value",
    }

    missing_columns = required_columns.difference(
        dataframe.columns
    )

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            f"{sorted(missing_columns)}"
        )

    if dataframe.empty:
        raise ValueError(
            "Validation failed: dataset is empty."
        )

    if dataframe.isna().any().any():
        warnings.append(
            "Dataset contains missing values."
        )

    duplicate_count = dataframe.duplicated(
        subset=["country", "year", "indicator"]
    ).sum()

    if duplicate_count > 0:
        warnings.append(
            f"Dataset contains {duplicate_count} "
            "duplicate records."
        )

    invalid_years = dataframe[
        (dataframe["year"] < 1900)
        | (dataframe["year"] > 2100)
    ]

    if not invalid_years.empty:
        warnings.append(
            f"Dataset contains {len(invalid_years)} "
            "records with invalid years."
        )

    unsupported_countries = sorted(
        set(dataframe["country"])
        - VALID_ASEAN_COUNTRIES
    )

    if unsupported_countries:
        warnings.append(
            "Unsupported country names found: "
            + ", ".join(unsupported_countries)
        )

    return warnings