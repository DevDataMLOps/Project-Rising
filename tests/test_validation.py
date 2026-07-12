import pandas as pd
import pytest

from pipelines.validate import validate_health_data


def test_validate_health_data_accepts_valid_dataset():
    dataframe = pd.DataFrame(
        {
            "country": ["Brunei"],
            "year": [2020],
            "indicator": ["crude_birth_ratio"],
            "value": [12.5],
        }
    )

    assert validate_health_data(dataframe) == []


def test_validate_health_data_raises_for_missing_required_columns():
    dataframe = pd.DataFrame(
        {
            "country": ["Brunei"],
            "year": [2020],
            "value": [12.5],
        }
    )

    with pytest.raises(ValueError, match="Missing required columns"):
        validate_health_data(dataframe)


def test_validate_health_data_warns_for_invalid_years():
    dataframe = pd.DataFrame(
        {
            "country": ["Brunei"],
            "year": [1800],
            "indicator": ["crude_birth_ratio"],
            "value": [12.5],
        }
    )

    warnings = validate_health_data(dataframe)

    assert "records with invalid years" in warnings[0]


def test_validate_health_data_warns_for_unsupported_country():
    dataframe = pd.DataFrame(
        {
            "country": ["Atlantis"],
            "year": [2020],
            "indicator": ["crude_birth_ratio"],
            "value": [12.5],
        }
    )

    warnings = validate_health_data(dataframe)

    assert warnings == [
        "Unsupported country names found: Atlantis",
    ]


def test_validate_health_data_uses_sex_in_duplicate_key():
    dataframe = pd.DataFrame(
        {
            "country": ["Brunei", "Brunei"],
            "year": [2004, 2004],
            "indicator": [
                "life_expentancy_rate",
                "life_expentancy_rate",
            ],
            "sex": ["Male", "Female"],
            "value": [74.6, 77.5],
        }
    )

    assert validate_health_data(dataframe) == []


def test_validate_health_data_uses_sub_indicator_in_duplicate_key():
    dataframe = pd.DataFrame(
        {
            "country": ["Brunei", "Brunei"],
            "year": [2004, 2004],
            "indicator": [
                "government_expenditure_in_health",
                "government_expenditure_in_health",
            ],
            "sub_indicator": [
                "Capital health expenditure",
                "Current health expenditure",
            ],
            "value": [13.6, 14.1],
        }
    )

    assert validate_health_data(dataframe) == []


def test_validate_health_data_warns_for_true_duplicates():
    dataframe = pd.DataFrame(
        {
            "country": ["Brunei", "Brunei"],
            "year": [2020, 2020],
            "indicator": [
                "crude_birth_ratio",
                "crude_birth_ratio",
            ],
            "value": [12.5, 12.5],
        }
    )

    warnings = validate_health_data(dataframe)

    assert warnings == [
        "Dataset contains 1 duplicate records.",
    ]
