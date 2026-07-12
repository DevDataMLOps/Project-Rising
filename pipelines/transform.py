import re

import pandas as pd


ASEAN_COUNTRIES = {
    "brunei": "Brunei",
    "brunei darussalam": "Brunei",
    "cambodia": "Cambodia",
    "indonesia": "Indonesia",
    "lao pdr": "Laos",
    "laos": "Laos",
    "malaysia": "Malaysia",
    "myanmar": "Myanmar",
    "philippines": "Philippines",
    "singapore": "Singapore",
    "thailand": "Thailand",
    "timor-leste": "Timor-Leste",
    "viet nam": "Vietnam",
    "vietnam": "Vietnam",
}


def clean_column_name(column_name: object) -> str:
    """
    Convert a column name into lowercase snake_case.
    """
    cleaned = str(column_name).strip().lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned)

    return cleaned.strip("_")


def standardize_country(country: object) -> str | None:
    """
    Convert country-name variations into standard names.
    """
    if pd.isna(country):
        return None

    cleaned = str(country).strip().lower()

    return ASEAN_COUNTRIES.get(
        cleaned,
        str(country).strip(),
    )


def indicator_from_filename(file_name: str) -> str:
    """
    Convert a CSV filename into an indicator name.
    """
    indicator = file_name.lower().replace(".csv", "")
    indicator = clean_column_name(indicator)

    return indicator


def find_country_column(
    dataframe: pd.DataFrame,
) -> str:
    """
    Find the column that contains country names.
    """
    candidates = [
        "country",
        "country_name",
        "countries_and_areas",
        "location",
        "member_state",
        "economy",
    ]

    for candidate in candidates:
        if candidate in dataframe.columns:
            return candidate

    raise ValueError(
        "No country column was found. "
        f"Available columns: {list(dataframe.columns)}"
    )


def transform_health_data(
    dataframe: pd.DataFrame,
    indicator_name: str,
) -> pd.DataFrame:
    """
    Transform one dataset into a standard long format.
    """
    transformed = dataframe.copy()

    transformed.columns = [
        clean_column_name(column)
        for column in transformed.columns
    ]

    country_column = find_country_column(transformed)

    transformed = transformed.rename(
        columns={country_column: "country"}
    )

    transformed["country"] = transformed[
        "country"
    ].apply(standardize_country)

    year_columns = [
        column
        for column in transformed.columns
        if str(column).isdigit()
    ]

    if year_columns:
        transformed = transformed.melt(
            id_vars=["country"],
            value_vars=year_columns,
            var_name="year",
            value_name="value",
        )

    required_columns = {
        "country",
        "year",
        "value",
    }

    if not required_columns.issubset(
        transformed.columns
    ):
        raise ValueError(
            "Dataset must contain country, year, "
            "and value information. "
            f"Available columns: "
            f"{list(transformed.columns)}"
        )

    transformed["year"] = pd.to_numeric(
        transformed["year"],
        errors="coerce",
    )

    transformed["value"] = pd.to_numeric(
        transformed["value"],
        errors="coerce",
    )

    transformed["indicator"] = indicator_name

    transformed = transformed.dropna(
        subset=["country", "year", "value"]
    )

    transformed["year"] = transformed[
        "year"
    ].astype(int)

    transformed = transformed.drop_duplicates(
        subset=["country", "year", "indicator"]
    )

    transformed = transformed[
        [
            "country",
            "year",
            "indicator",
            "value",
        ]
    ]

    transformed = transformed.sort_values(
        by=["indicator", "country", "year"]
    ).reset_index(drop=True)

    return transformed