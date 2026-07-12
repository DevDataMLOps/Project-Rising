import pandas as pd

from pipelines.transform import clean_column_name


INDICATOR_METADATA_ALIASES = {
    "crude_birth_ratio": ["crude_birth_ratio"],
    "crude_death_ratio": ["crude_death_ratio"],
    "infant_mortality_rate": ["infant_mortality_rate"],
    "under_5_mortality_rate": ["under_5_mortality_rate"],
    "maternal_mortality_rate_death_per_1000_live_births": [
        "maternal_mortality_rate",
    ],
    "life_expectancy_rate": ["life_expentancy_rate"],
    "children_under_5_moderately_or_severely_underweight_percentage": [
        "underweight_children",
    ],
    "undernourished_population": ["undernourished_population"],
    "immunization_against_measles_and_dpt_among_children_of_1_year_old_percentage": [
        "immunization_dpt",
        "immunization_measless",
    ],
    "prevalence_of_malaria_and_tb_percentage": [
        "malaria_prevalence",
        "tb_prevalence",
    ],
    "government_expenditure_in_health": [
        "government_expenditure_in_health",
    ],
    "medical_doctors_physicians_per_1_000_population": [
        "physicans_density",
    ],
    "nurses_and_widwives_per_1_000_population": [
        "nurses_midwife_density",
    ],
    "pharmaceutical_personnel_per_1_000_population": [
        "pharmaceutical_worker_density",
    ],
    "prevalence_of_hiv_among_adults_aged_15_to_49": [
        "hiv_prevalence",
    ],
    "deaths_due_to_hiv_aids": ["death_by_hiv_aids"],
}


def transform_sdg3_metadata(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Transform SDG3 summary metadata into indicator-level records.
    """
    metadata = dataframe.copy()

    metadata.columns = [
        clean_column_name(column)
        for column in metadata.columns
    ]

    metadata = metadata.dropna(
        axis="columns",
        how="all",
    )

    metadata = metadata.rename(
        columns={
            "cleansed_data": "indicator_label",
            "source_link": "source_url",
            "link_to_issue": "issue_url",
            "cleansed": "is_cleansed",
            "combine": "should_combine",
        }
    )

    required_columns = {
        "indicator_label",
        "description",
        "source_url",
    }

    missing_columns = required_columns.difference(
        metadata.columns
    )

    if missing_columns:
        raise ValueError(
            "Missing metadata columns: "
            f"{sorted(missing_columns)}"
        )

    metadata = metadata.dropna(
        subset=["indicator_label"],
    )

    metadata["metadata_key"] = metadata[
        "indicator_label"
    ].apply(clean_column_name)

    metadata["indicator"] = metadata[
        "metadata_key"
    ].apply(
        lambda key: INDICATOR_METADATA_ALIASES.get(
            key,
            [key],
        )
    )

    metadata = metadata.explode(
        "indicator",
        ignore_index=True,
    )

    optional_columns = [
        "raw_data",
        "issue_url",
        "is_cleansed",
        "should_combine",
        "remarks",
    ]

    for column in optional_columns:
        if column not in metadata.columns:
            metadata[column] = pd.NA

    metadata = metadata[
        [
            "indicator",
            "indicator_label",
            "description",
            "source_url",
            "raw_data",
            "issue_url",
            "is_cleansed",
            "should_combine",
            "remarks",
        ]
    ]

    metadata = metadata.drop_duplicates(
        subset=["indicator"],
    )

    metadata = metadata.sort_values(
        by=["indicator"],
    ).reset_index(drop=True)

    return metadata
