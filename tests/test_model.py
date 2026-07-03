from __future__ import annotations

import pytest

from wcmodel.model import (
    MatchContext,
    TeamRating,
    blend_with_market,
    decimal_odds_to_probs,
    match_prediction,
    poisson_1x2,
)


def assert_probability_vector(probs: dict[str, float]) -> None:
    assert set(probs) == {"home", "draw", "away"}
    assert all(0.0 <= value <= 1.0 for value in probs.values())
    assert sum(probs.values()) == pytest.approx(1.0, abs=1e-9)


def test_poisson_1x2_returns_normalized_probabilities():
    probs = poisson_1x2(lambda_home=1.55, lambda_away=1.05, rho=-0.08)

    assert_probability_vector(probs)
    assert probs["home"] > probs["away"]
    assert 0.15 <= probs["draw"] <= 0.35


def test_decimal_odds_to_probs_removes_bookmaker_margin():
    probs = decimal_odds_to_probs(home=1.80, draw=3.60, away=4.50)

    assert_probability_vector(probs)
    assert probs["home"] > probs["draw"] > probs["away"]


def test_market_blend_is_bounded_by_market_max():
    independent = {"home": 0.55, "draw": 0.25, "away": 0.20}
    market = {"home": 0.35, "draw": 0.30, "away": 0.35}

    blended = blend_with_market(independent, market, market_max=0.20)

    assert_probability_vector(blended)
    assert blended["home"] == pytest.approx(0.51)
    assert blended["away"] == pytest.approx(0.23)


def test_match_prediction_outputs_independent_and_accuracy_tracks():
    home = TeamRating(
        team_id="BRA",
        name="Brazil",
        elo=2040,
        structural=1.45,
        squad_value_eur_m=920,
        host=False,
    )
    away = TeamRating(
        team_id="MAR",
        name="Morocco",
        elo=1840,
        structural=0.85,
        squad_value_eur_m=320,
        host=False,
    )
    context = MatchContext(stage="group", neutral=True, as_of="2026-06-10T12:00:00Z")
    market = {"home": 0.46, "draw": 0.30, "away": 0.24}

    prediction = match_prediction(home, away, context, market_probs=market, market_max=0.25)

    assert prediction["home_team"] == "Brazil"
    assert prediction["away_team"] == "Morocco"
    assert_probability_vector(prediction["independent_probs"])
    assert_probability_vector(prediction["accuracy_probs"])
    assert prediction["accuracy_probs"]["home"] < prediction["independent_probs"]["home"]
    assert prediction["components"]["market"] == market
    assert prediction["model_version"].startswith("wc26-offline-")
