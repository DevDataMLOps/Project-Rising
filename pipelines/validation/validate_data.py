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


REQUIRED_COLUMNS = {
    "country",
    "year",
    "indicator",
    "value",
}


def validate_health_data(
    dataframe: pd.DataFrame,
) -> list[str]:
    """
    Validate one transformed health dataset.

    Returns validation warnings.
    """
    warnings: list[str] = []

    missing_columns = REQUIRED_COLUMNS.difference(
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

    missing_values = int(
        dataframe[
            [
                "country",
                "year",
                "indicator",
                "value",
            ]
        ]
        .isna()
        .sum()
        .sum()
    )

    if missing_values > 0:
        warnings.append(
            f"Dataset contains {missing_values} "
            "missing required values."
        )

    duplicate_count = int(
        dataframe.duplicated(
            subset=[
                "country",
                "year",
                "indicator",
            ]
        ).sum()
    )

    if duplicate_count > 0:
        warnings.append(
            f"Dataset contains {duplicate_count} "
            "duplicate records."
        )

    invalid_year_count = len(
        dataframe[
            (dataframe["year"] < 1900)
            | (dataframe["year"] > 2100)
        ]
    )

    if invalid_year_count > 0:
        warnings.append(
            f"Dataset contains {invalid_year_count} "
            "invalid year records."
        )

    unsupported_countries = sorted(
        set(dataframe["country"])
        - VALID_ASEAN_COUNTRIES
    )

    if unsupported_countries:
        warnings.append(
            "Unsupported countries found: "
            + ", ".join(unsupported_countries)
        )

    return warnings