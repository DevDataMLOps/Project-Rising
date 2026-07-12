import re

import pandas as pd


ASEAN_COUNTRIES = {
    "brunei": "Brunei",
    "brunei darussalam": "Brunei",
    "brunnei darussalam": "Brunei",
    "cambodia": "Cambodia",
    "indonesia": "Indonesia",
    "lao pdr": "Laos",
    "laos pdr": "Laos",
    "lao s pdr": "Laos",
    "lao people s democratic republic": "Laos",
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


INDICATOR_NAME_ALIASES = {
    "goverment_expence_in_health": "government_expenditure_in_health",
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
    cleaned = cleaned.rstrip("*").strip()
    cleaned = re.sub(r"[^a-z0-9]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

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

    return INDICATOR_NAME_ALIASES.get(
        indicator,
        indicator,
    )


def extract_year_from_column(column_name: object) -> int | None:
    """
    Extract a four-digit year from the start of a column name.
    """
    match = re.match(
        r"^(19|20)\d{2}",
        str(column_name).strip(),
    )

    if match is None:
        return None

    return int(match.group(0))


def extract_sex_from_column(column_name: object) -> str | None:
    """
    Extract sex from year columns such as 2004M and 2004F.
    """
    cleaned = clean_column_name(column_name)
    match = re.match(
        r"^(19|20)\d{2}([mf])(?:_(\d+))?$",
        cleaned,
    )

    if match is None:
        return None

    sex_code = match.group(2)
    duplicate_suffix = match.group(3)

    if sex_code == "f" or duplicate_suffix == "1":
        return "Female"

    return "Male"


def clean_numeric_value(value: object) -> str | None:
    """
    Clean numeric strings such as 38 000, 1,130.90, and <500.
    """
    if pd.isna(value):
        return None

    cleaned = str(value).strip()

    if not cleaned:
        return None

    cleaned = cleaned.replace("<", "")
    cleaned = cleaned.replace(",", "")
    cleaned = re.sub(r"\s+", "", cleaned)

    return cleaned


def find_country_column(
    dataframe: pd.DataFrame,
) -> str:
    """
    Find the column that contains country names.
    """
    candidates = [
        "country",
        "countries",
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


def find_value_column(
    dataframe: pd.DataFrame,
) -> str:
    """
    Find the value column in an already-long dataset.
    """
    ignored_columns = {
        "country",
        "year",
        "indicator",
        "sex",
        "source",
        "unit",
        "reference_year_s",
    }

    candidate_columns = [
        column
        for column in dataframe.columns
        if column not in ignored_columns
    ]

    numeric_candidates = [
        column
        for column in candidate_columns
        if pd.to_numeric(
            dataframe[column],
            errors="coerce",
        ).notna().any()
    ]

    if len(numeric_candidates) == 1:
        return numeric_candidates[0]

    if not numeric_candidates:
        raise ValueError(
            "No value column was found. "
            f"Available columns: {list(dataframe.columns)}"
        )

    raise ValueError(
        "Multiple possible value columns were found: "
        f"{numeric_candidates}"
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
        if extract_year_from_column(column) is not None
    ]

    metadata_columns = [
        column
        for column in [
            "indicators",
            "unit",
            "source",
        ]
        if column in transformed.columns
    ]

    if year_columns:
        transformed = transformed.melt(
            id_vars=["country", *metadata_columns],
            value_vars=year_columns,
            var_name="year_column",
            value_name="value",
        )
        transformed["sex"] = transformed[
            "year_column"
        ].apply(extract_sex_from_column)
        transformed["year"] = transformed[
            "year_column"
        ].apply(extract_year_from_column)

    elif "year" in transformed.columns and "value" not in transformed.columns:
        value_column = find_value_column(transformed)
        transformed = transformed.rename(
            columns={value_column: "value"}
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
        transformed["value"].apply(clean_numeric_value),
        errors="coerce",
    )

    transformed["indicator"] = indicator_name

    if "indicators" in transformed.columns:
        transformed["sub_indicator"] = transformed[
            "indicators"
        ].apply(
            lambda value: (
                str(value).strip()
                if not pd.isna(value)
                else None
            )
        )
    else:
        transformed["sub_indicator"] = None

    if "unit" not in transformed.columns:
        transformed["unit"] = None

    if "sex" not in transformed.columns:
        transformed["sex"] = None

    transformed = transformed.dropna(
        subset=["country", "year", "value"]
    )

    transformed["year"] = transformed[
        "year"
    ].astype(int)

    transformed = transformed.drop_duplicates(
        subset=[
            "country",
            "year",
            "indicator",
            "sub_indicator",
            "sex",
        ]
    )

    transformed = transformed[
        [
            "country",
            "year",
            "indicator",
            "sub_indicator",
            "sex",
            "unit",
            "value",
        ]
    ]

    transformed = transformed.sort_values(
        by=[
            "indicator",
            "sub_indicator",
            "country",
            "year",
            "sex",
        ]
    ).reset_index(drop=True)

    return transformed
