import re

import pandas as pd


ASEAN_COUNTRIES = {
    "brunei": "Brunei",
    "brunei darussalam": "Brunei",
    "cambodia": "Cambodia",
    "indonesia": "Indonesia",
    "lao pdr": "Laos",
    "lao people's democratic republic": "Laos",
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
    "indicator",
    "indicators",
    "unit",
    "source",
    "source_link",
    "remarks",
    "description",
}


def clean_column_name(
    column_name: object,
) -> str:
    """
    Convert a column name into lowercase snake_case.
    """
    cleaned = str(column_name).strip().lower()
    cleaned = re.sub(
        r"[^a-z0-9]+",
        "_",
        cleaned,
    )

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

    return clean_column_name(file_stem)


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

    Examples:
        2004
        2004dpt
        2005_measles
        2010_rate
    """
    return [
        column
        for column in dataframe.columns
        if re.match(
            r"^\d{4}",
            str(column),
        )
    ]


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

    value_column = next(
        (
            column
            for column in VALUE_COLUMN_CANDIDATES
            if column in dataframe.columns
        ),
        None,
    )

    if year_column is not None and value_column is None:
        excluded_columns = (
            METADATA_COLUMNS
            | {year_column}
        )

        remaining_columns = [
            column
            for column in dataframe.columns
            if column not in excluded_columns
        ]

        numeric_candidates: list[str] = []

        for column in remaining_columns:
            numeric_values = pd.to_numeric(
                dataframe[column],
                errors="coerce",
            )

            if numeric_values.notna().any():
                numeric_candidates.append(column)

        if len(numeric_candidates) == 1:
            value_column = numeric_candidates[0]

    return year_column, value_column


def convert_wide_to_long(
    dataframe: pd.DataFrame,
    year_columns: list[str],
) -> pd.DataFrame:
    """
    Convert wide year columns into year-value rows.
    """
    melted = dataframe.melt(
        id_vars=["country"],
        value_vars=year_columns,
        var_name="source_year_column",
        value_name="value",
    )

    melted["year"] = (
        melted["source_year_column"]
        .astype(str)
        .str.extract(
            r"^(\d{4})",
            expand=False,
        )
    )

    return melted[
        [
            "country",
            "year",
            "value",
        ]
    ]


def convert_long_format(
    dataframe: pd.DataFrame,
    year_column: str,
    value_column: str,
) -> pd.DataFrame:
    """
    Standardize an existing long-format dataset.
    """
    converted = dataframe.rename(
        columns={
            year_column: "year",
            value_column: "value",
        }
    )

    return converted[
        [
            "country",
            "year",
            "value",
        ]
    ]


def transform_health_data(
    dataframe: pd.DataFrame,
    indicator_name: str,
) -> pd.DataFrame:
    """
    Transform one ASEAN health dataset into the common format.

    Output columns:
        country
        year
        indicator
        value
    """
    transformed = dataframe.copy()

    transformed.columns = [
        clean_column_name(column)
        for column in transformed.columns
    ]

    transformed = transformed.loc[
        :,
        ~transformed.columns.str.startswith(
            "unnamed"
        ),
    ]

    country_column = find_country_column(
        transformed
    )

    transformed = transformed.rename(
        columns={
            country_column: "country",
        }
    )

    transformed["country"] = (
        transformed["country"]
        .apply(standardize_country)
    )

    wide_year_columns = find_wide_year_columns(
        transformed
    )

    if wide_year_columns:
        transformed = convert_wide_to_long(
            dataframe=transformed,
            year_columns=wide_year_columns,
        )

    else:
        year_column, value_column = (
            find_long_format_columns(
                transformed
            )
        )

        if (
            year_column is None
            or value_column is None
        ):
            raise ValueError(
                "Dataset must contain either wide year "
                "columns or recognizable year and value "
                "columns. "
                f"Available columns: "
                f"{list(transformed.columns)}"
            )

        transformed = convert_long_format(
            dataframe=transformed,
            year_column=year_column,
            value_column=value_column,
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
                "value",
            ]
        )

    transformed["year"] = (
        transformed["year"]
        .astype(int)
    )

    transformed = transformed[
        transformed["country"].isin(
            ASEAN_COUNTRIES.values()
        )
    ]

    transformed = transformed[
        (
            transformed["year"] >= 1900
        )
        & (
            transformed["year"] <= 2100
        )
    ]

    transformed = transformed.drop_duplicates(
        subset=[
            "country",
            "year",
            "indicator",
        ]
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
        by=[
            "indicator",
            "country",
            "year",
        ]
    ).reset_index(drop=True)

    print(
        f"Transformed {indicator_name}: "
        f"{len(transformed)} clean records"
    )

    return transformed