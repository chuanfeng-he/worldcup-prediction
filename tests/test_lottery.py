import pytest

from wcmodel.data import load_seed_data
from wcmodel.lottery import (
    apply_lottery_sale,
    china_lottery_markets,
    estimate_slip,
    historical_success,
    top_daily_recommendations,
)
from wcmodel.pipeline import prediction_for_fixture


def test_china_lottery_markets_cover_core_football_modes():
    seed = load_seed_data()
    match = prediction_for_fixture(seed, seed.fixtures[0])

    markets = china_lottery_markets(match)

    assert set(markets) == {"spf", "rqspf", "bf", "jqs", "bqc"}
    assert markets["spf"]["name"] == "胜平负"
    assert markets["rqspf"]["name"] == "让球胜平负"
    assert markets["bf"]["name"] == "比分"
    assert markets["jqs"]["name"] == "总进球"
    assert markets["bqc"]["name"] == "半全场"
    for market in markets.values():
        assert market["pick"]["label"]
        assert 0.0 <= market["pick"]["prob"] <= 1.0
        assert market["options"]


def test_score_market_matches_china_lottery_score_menu():
    seed = load_seed_data()
    match = prediction_for_fixture(seed, seed.fixtures[0])

    options = china_lottery_markets(match)["bf"]["options"]
    labels = {item["label"] for item in options}

    assert len(options) == 31
    assert {"1:0", "2:1", "0:0", "3:3", "0:1", "2:5", "胜其他", "平其他", "负其他"}.issubset(labels)
    assert sum(float(item["prob"]) for item in options) == pytest.approx(1.0, abs=1e-6)


def test_daily_recommendations_are_limited_to_uncompleted_target_date():
    seed = load_seed_data()
    matches = [prediction_for_fixture(seed, fixture) for fixture in seed.fixtures]

    recommendations = top_daily_recommendations(matches, target_date="2026-07-04", limit=3)

    assert len(recommendations) == 3
    assert all(item["date"] == "2026-07-04" for item in recommendations)
    assert all(item["completed"] is False for item in recommendations)
    assert recommendations == sorted(recommendations, key=lambda item: item["model_score"], reverse=True)


def test_daily_recommendations_skip_closed_lottery_markets():
    seed = load_seed_data()
    match = prediction_for_fixture(seed, seed.fixtures[-1])
    for market in match["lottery"].values():
        market["sale"] = False

    recommendations = top_daily_recommendations([match], target_date=str(match["kickoff"])[:10], limit=3)

    assert recommendations == []


def test_missing_lottery_sale_snapshot_closes_markets_by_default():
    seed = load_seed_data()
    match = prediction_for_fixture(seed, seed.fixtures[0])

    markets = apply_lottery_sale(china_lottery_markets(match), {})

    assert all(market["sale"] is False for market in markets.values())
    assert all(market["supports_single"] is False for market in markets.values())
    assert all(market["supports_parlay"] is False for market in markets.values())


def test_historical_success_reports_hit_rate_for_resolvable_markets():
    seed = load_seed_data()
    matches = [prediction_for_fixture(seed, fixture) for fixture in seed.fixtures]

    history = historical_success(matches)

    assert history["sample_size"] >= 1
    assert history["markets"]["spf"]["settled"] >= 1
    assert 0.0 <= history["markets"]["spf"]["hit_rate"] <= 1.0
    assert history["markets"]["bqc"]["settled"] >= 1


def test_estimate_slip_multiplies_probability_and_odds():
    slip = estimate_slip(
        [
            {"prob": 0.6, "odds": 1.8},
            {"prob": 0.5, "odds": 2.1},
        ],
        stake=20,
    )

    assert slip["selection_count"] == 2
    assert slip["hit_probability"] == pytest.approx(0.3)
    assert slip["combined_odds"] == pytest.approx(3.78)
    assert slip["payout_if_hit"] == pytest.approx(75.6)
    assert slip["expected_return"] == pytest.approx(2.68)


def test_estimate_slip_groups_same_match_options_as_alternatives():
    slip = estimate_slip(
        [
            {"match_id": "R16-20260704-2", "prob": 0.234, "odds": 2.06},
            {"match_id": "R16-20260704-2", "prob": 0.182, "odds": 3.45},
            {"match_id": "R16-20260704-3", "prob": 0.243, "odds": 1.26},
            {"match_id": "R16-20260704-1", "prob": 0.083, "odds": 6.10},
            {"match_id": "R16-20260704-1", "prob": 0.136, "odds": 4.40},
            {"match_id": "R16-20260704-1", "prob": 0.087, "odds": 6.50},
        ],
        stake=2,
    )

    assert slip["selection_count"] == 6
    assert slip["match_count"] == 3
    assert slip["combination_count"] == 6
    assert slip["total_stake"] == pytest.approx(12.0)
    assert slip["hit_probability"] == pytest.approx((0.234 + 0.182) * 0.243 * (0.083 + 0.136 + 0.087))
    assert slip["max_payout_if_hit"] == pytest.approx(2 * 3.45 * 1.26 * 6.50)
    assert slip["payout_if_hit"] == pytest.approx(slip["max_payout_if_hit"])
