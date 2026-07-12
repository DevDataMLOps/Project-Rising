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
    "lao people's democratic republic": "Laos",
    "laos": "Laos",
    "malaysia": "Malaysia",
    "myanmar": "Myanmar",
    "philippines": "Philippines",
    "singapore": "Singapore",
    "thailand": "Thailand",
    "timor-leste": "Timor-Leste",
    "timor leste": "Timor-Leste",
    "viet nam": "Vietnam",
    "vietnam": "Vietnam",
}


INDICATOR_NAME_ALIASES = {
    "goverment_expence_in_health": "government_expenditure_in_health",
}


COUNTRY_COLUMN_CANDIDATES = [
    "country",
    "countries",
    "country_name",
    "countries_and_areas",
    "countries_areas",
    "location",
    "member_state",
    "economy",
    "area",
]


YEAR_COLUMN_CANDIDATES = [
    "year",
    "reference_year",
    "reference_year_s",
    "date",
]


VALUE_COLUMN_CANDIDATES = [
    "value",
    "indicator_value",
    "rate",
    "amount",
    "percentage",
    "percent",
    "density",
    "prevalence",
]


METADATA_COLUMNS = {
    "country",
    "year",
    "indicator",
    "indicators",
    "sub_indicator",
    "sex",
    "unit",
    "source",
    "source_link",
    "remarks",
    "description",
    "reference_year_s",
}


def clean_column_name(
    column_name: object,
) -> str:
    """
    Convert a column name into lowercase snake_case.
    """
    cleaned = str(column_name).strip().lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned)

    return cleaned.strip("_")


def standardize_country(
    country: object,
) -> str | None:
    """
    Standardize ASEAN country names.
    """
    if pd.isna(country):
        return None

    original_name = str(country).strip()
    cleaned_name = original_name.lower()
    cleaned_name = cleaned_name.rstrip("*").strip()
    cleaned_name = re.sub(r"[^a-z0-9]+", " ", cleaned_name)
    cleaned_name = re.sub(r"\s+", " ", cleaned_name).strip()

    return ASEAN_COUNTRIES.get(
        cleaned_name,
        original_name,
    )


def indicator_from_filename(
    file_name: str,
) -> str:
    """
    Convert a filename into a normalized indicator name.
    """
    file_stem = file_name.rsplit(
        ".",
        maxsplit=1,
    )[0]

    indicator = clean_column_name(file_stem)

    return INDICATOR_NAME_ALIASES.get(
        indicator,
        indicator,
    )


def extract_year_from_column(
    column_name: object,
) -> int | None:
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


def extract_sex_from_column(
    column_name: object,
) -> str | None:
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


def clean_numeric_value(
    value: object,
) -> str | None:
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
    for candidate in COUNTRY_COLUMN_CANDIDATES:
        if candidate in dataframe.columns:
            return candidate

    raise ValueError(
        "No country column was found. "
        f"Available columns: {list(dataframe.columns)}"
    )


def find_wide_year_columns(
    dataframe: pd.DataFrame,
) -> list[str]:
    """
    Find columns that begin with a four-digit year.
    """
    return [
        column
        for column in dataframe.columns
        if extract_year_from_column(column) is not None
    ]


def find_value_column(
    dataframe: pd.DataFrame,
) -> str:
    """
    Find the value column in an already-long dataset.
    """
    for candidate in VALUE_COLUMN_CANDIDATES:
        if candidate in dataframe.columns:
            return candidate

    candidate_columns = [
        column
        for column in dataframe.columns
        if column not in METADATA_COLUMNS
    ]

    numeric_candidates = [
        column
        for column in candidate_columns
        if pd.to_numeric(
            dataframe[column].apply(clean_numeric_value),
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


def find_long_format_columns(
    dataframe: pd.DataFrame,
) -> tuple[str | None, str | None]:
    """
    Detect year and value columns in a long-format dataset.
    """
    year_column = next(
        (
            column
            for column in YEAR_COLUMN_CANDIDATES
            if column in dataframe.columns
        ),
        None,
    )

    if year_column is None:
        return None, None

    return year_column, find_value_column(dataframe)


def metadata_columns_for_melt(
    dataframe: pd.DataFrame,
) -> list[str]:
    """
    Keep source metadata columns during wide-to-long conversion.
    """
    return [
        column
        for column in [
            "indicators",
            "unit",
            "source",
        ]
        if column in dataframe.columns
    ]


def add_optional_output_columns(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add optional output columns used by richer datasets.
    """
    transformed = dataframe.copy()

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
    elif "sub_indicator" not in transformed.columns:
        transformed["sub_indicator"] = None

    if "unit" not in transformed.columns:
        transformed["unit"] = None

    if "sex" not in transformed.columns:
        transformed["sex"] = None

    return transformed


def transform_health_data(
    dataframe: pd.DataFrame,
    indicator_name: str,
) -> pd.DataFrame:
    """
    Transform one ASEAN health dataset into the common format.
    """
    transformed = dataframe.copy()

    transformed.columns = [
        clean_column_name(column)
        for column in transformed.columns
    ]

    transformed = transformed.loc[
        :,
        ~transformed.columns.str.startswith("unnamed"),
    ]

    country_column = find_country_column(transformed)

    transformed = transformed.rename(
        columns={country_column: "country"}
    )

    transformed["country"] = transformed[
        "country"
    ].apply(standardize_country)

    wide_year_columns = find_wide_year_columns(transformed)

    if wide_year_columns:
        metadata_columns = metadata_columns_for_melt(
            transformed
        )

        transformed = transformed.melt(
            id_vars=["country", *metadata_columns],
            value_vars=wide_year_columns,
            var_name="year_column",
            value_name="value",
        )

        transformed["sex"] = transformed[
            "year_column"
        ].apply(extract_sex_from_column)

        transformed["year"] = transformed[
            "year_column"
        ].apply(extract_year_from_column)

    else:
        year_column, value_column = find_long_format_columns(
            transformed
        )

        if year_column is None or value_column is None:
            raise ValueError(
                "Dataset must contain either wide year "
                "columns or recognizable year and value "
                "columns. "
                f"Available columns: {list(transformed.columns)}"
            )

        transformed = transformed.rename(
            columns={
                year_column: "year",
                value_column: "value",
            }
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
    transformed = add_optional_output_columns(transformed)

    transformed = transformed.dropna(
        subset=[
            "country",
            "year",
            "value",
        ]
    )

    if transformed.empty:
        return pd.DataFrame(
            columns=[
                "country",
                "year",
                "indicator",
                "sub_indicator",
                "sex",
                "unit",
                "value",
            ]
        )

    transformed["year"] = transformed["year"].astype(int)

    transformed = transformed[
        transformed["country"].isin(ASEAN_COUNTRIES.values())
    ]

    transformed = transformed[
        (transformed["year"] >= 1900)
        & (transformed["year"] <= 2100)
    ]

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

    print(
        f"Transformed {indicator_name}: "
        f"{len(transformed)} clean records"
    )

    return transformed
