import pytest

from api.services.disease_risk_service import predict_disease_risk


def test_wetter_scenario_increases_risk() -> None:
    dry = predict_disease_risk(
        country="Philippines",
        disease="dengue",
        temperature_c=29.0,
        rainfall_mm=10.0,
        humidity_pct=55.0,
    )
    wet = predict_disease_risk(
        country="Philippines",
        disease="dengue",
        temperature_c=29.0,
        rainfall_mm=180.0,
        humidity_pct=85.0,
    )

    assert wet["risk_score"] > dry["risk_score"]


def test_prediction_is_case_insensitive_for_country() -> None:
    prediction = predict_disease_risk(
        country="philippines",
        disease="malaria",
        temperature_c=28.0,
        rainfall_mm=100.0,
        humidity_pct=75.0,
    )

    assert prediction["country"] == "Philippines"


def test_prediction_rejects_unknown_country() -> None:
    with pytest.raises(KeyError):
        predict_disease_risk(
            country="Atlantis",
            disease="dengue",
            temperature_c=28.0,
            rainfall_mm=100.0,
            humidity_pct=75.0,
        )
