import pandas as pd

from pipelines.transform import (
    clean_numeric_value,
    indicator_from_filename,
    standardize_country,
    transform_health_data,
)


def test_standardize_country_handles_known_variants():
    assert standardize_country("Brunei Darussalam*") == "Brunei"
    assert standardize_country("Brunnei Darussalam") == "Brunei"
    assert standardize_country("Lao's PDR") == "Laos"
    assert (
        standardize_country("Lao People's Democratic Republic")
        == "Laos"
    )
    assert standardize_country("Viet Nam") == "Vietnam"


def test_indicator_from_filename_corrects_known_typos():
    assert (
        indicator_from_filename(
            "goverment_expence_in_health.csv"
        )
        == "government_expenditure_in_health"
    )


def test_clean_numeric_value_handles_spaces_commas_and_less_than():
    assert clean_numeric_value("38 000 ") == "38000"
    assert clean_numeric_value("1,130.90") == "1130.90"
    assert clean_numeric_value("<500") == "500"
    assert clean_numeric_value("") is None


def test_transform_wide_year_columns_to_long_format():
    dataframe = pd.DataFrame(
        {
            "Countries and areas": ["Brunei Darussalam"],
            "Reference year(s)": ["2004-2005"],
            "2004": ["19.9"],
            "2005": ["18.7"],
        }
    )

    transformed = transform_health_data(
        dataframe=dataframe,
        indicator_name="crude_birth_ratio",
    )

    assert transformed[
        ["country", "year", "indicator", "value"]
    ].to_dict("records") == [
        {
            "country": "Brunei",
            "year": 2004,
            "indicator": "crude_birth_ratio",
            "value": 19.9,
        },
        {
            "country": "Brunei",
            "year": 2005,
            "indicator": "crude_birth_ratio",
            "value": 18.7,
        },
    ]


def test_transform_year_columns_with_indicator_suffixes():
    dataframe = pd.DataFrame(
        {
            "Countries and areas": ["Cambodia"],
            "2004DPT": ["91.7"],
            "2005DPT": ["99.7"],
        }
    )

    transformed = transform_health_data(
        dataframe=dataframe,
        indicator_name="immunization_dpt",
    )

    assert transformed["year"].tolist() == [2004, 2005]
    assert transformed["value"].tolist() == [91.7, 99.7]


def test_transform_life_expectancy_keeps_sex_dimension():
    dataframe = pd.DataFrame(
        {
            "Countries and areas": ["Brunei Darussalam"],
            "2004M": ["74.6"],
            "2004F": ["77.5"],
        }
    )

    transformed = transform_health_data(
        dataframe=dataframe,
        indicator_name="life_expentancy_rate",
    )

    assert transformed[
        ["country", "year", "sex", "value"]
    ].to_dict("records") == [
        {
            "country": "Brunei",
            "year": 2004,
            "sex": "Female",
            "value": 77.5,
        },
        {
            "country": "Brunei",
            "year": 2004,
            "sex": "Male",
            "value": 74.6,
        },
    ]


def test_transform_government_expenditure_keeps_sub_indicator_and_unit():
    dataframe = pd.DataFrame(
        {
            "Countries": ["Brunei Darussalam"],
            "Indicators": ["Capital health expenditure"],
            "Unit": ["in million current US$"],
            "2000": ["13.3"],
        }
    )

    transformed = transform_health_data(
        dataframe=dataframe,
        indicator_name="government_expenditure_in_health",
    )

    record = transformed.iloc[0].to_dict()

    assert record["indicator"] == "government_expenditure_in_health"
    assert record["sub_indicator"] == "Capital health expenditure"
    assert record["unit"] == "in million current US$"
    assert record["value"] == 13.3


def test_transform_already_long_dataset_detects_value_column():
    dataframe = pd.DataFrame(
        {
            "Country": ["Brunei Darussalam"],
            "Year": [2012],
            "Physicians density (per 1000 population)": [1.47],
        }
    )

    transformed = transform_health_data(
        dataframe=dataframe,
        indicator_name="physicans_density",
    )

    assert transformed[
        ["country", "year", "indicator", "value"]
    ].to_dict("records") == [
        {
            "country": "Brunei",
            "year": 2012,
            "indicator": "physicans_density",
            "value": 1.47,
        }
    ]


def test_transform_hiv_death_values_with_spaces_and_less_than():
    dataframe = pd.DataFrame(
        {
            "Country": [
                "Indonesia",
                "Lao People's Democratic Republic",
            ],
            "2016": ["38 000 ", "<500 "],
        }
    )

    transformed = transform_health_data(
        dataframe=dataframe,
        indicator_name="death_by_hiv_aids",
    )

    assert transformed[
        ["country", "year", "value"]
    ].to_dict("records") == [
        {
            "country": "Indonesia",
            "year": 2016,
            "value": 38000,
        },
        {
            "country": "Laos",
            "year": 2016,
            "value": 500,
        },
    ]
