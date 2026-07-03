from __future__ import annotations

import json

import pytest

from wcmodel.data import load_seed_data
from wcmodel.pipeline import generate_public_data
from wcmodel.simulate import simulate_tournament


def test_generate_public_data_writes_cache_friendly_json(tmp_path):
    seed = load_seed_data()

    summary = generate_public_data(seed, tmp_path, n_sims=200, seed=7)

    expected_files = {
        "daily_predictions.json",
        "history.json",
        "model_status.json",
        "matches.json",
        "champion_probs.json",
        "group_probs.json",
    }
    assert expected_files.issubset({path.name for path in tmp_path.iterdir()})
    assert summary["files"] == sorted(expected_files)

    status = json.loads((tmp_path / "model_status.json").read_text())
    assert "domain" not in status
    assert status["mode"] == "offline_static_local"
    assert status["cache_policy"]["public_json_ttl_seconds"] == 300
    assert status["tracks"] == ["independent", "accuracy"]


def test_seed_data_uses_chinese_names_and_completed_beijing_daily_results(tmp_path):
    seed = load_seed_data()

    assert seed.teams["ESP"].name == "西班牙"
    assert seed.teams["AUT"].name == "奥地利"
    assert seed.teams["ARG"].name == "阿根廷"
    assert seed.teams["CPV"].name == "佛得角"

    generate_public_data(seed, tmp_path, n_sims=50, seed=11)
    daily = json.loads((tmp_path / "daily_predictions.json").read_text())
    completed = {
        (item["home"]["name"], item["away"]["name"], item["result"]["home_goals"], item["result"]["away_goals"])
        for item in daily["today_completed"]
    }

    assert daily["as_of_date"] == "2026-07-03"
    assert daily["today_status"] == "completed"
    assert completed == {
        ("西班牙", "奥地利", 3, 0),
        ("葡萄牙", "克罗地亚", 2, 1),
        ("瑞士", "阿尔及利亚", 2, 0),
    }


def test_next_bettable_schedule_and_track_difference_are_visible(tmp_path):
    seed = load_seed_data()
    generate_public_data(seed, tmp_path, n_sims=50, seed=11)
    matches_payload = json.loads((tmp_path / "matches.json").read_text())
    daily = json.loads((tmp_path / "daily_predictions.json").read_text())
    matches = matches_payload["matches"]

    next_matches = {
        (item["home"]["name"], item["away"]["name"])
        for item in daily["matches"]
    }
    assert daily["target_date"] == "2026-07-04"
    assert daily["target_label"] == "下一待赛日"
    assert next_matches == {
        ("澳大利亚", "埃及"),
        ("阿根廷", "佛得角"),
        ("哥伦比亚", "加纳"),
    }

    argentina = next(item for item in matches if item["home"]["name"] == "阿根廷")
    assert argentina["prediction"]["accuracy_probs"] != argentina["prediction"]["independent_probs"]


def test_completed_daily_review_contains_all_lottery_settlements(tmp_path):
    seed = load_seed_data()
    generate_public_data(seed, tmp_path, n_sims=50, seed=11)
    daily = json.loads((tmp_path / "daily_predictions.json").read_text())

    for match in daily["today_completed"]:
        review = match["lottery_review"]
        assert set(review) == {"spf", "rqspf", "bf", "jqs", "bqc"}
        assert all(item["actual"] for item in review.values())
        assert review["bf"]["actual"] == f"{match['result']['home_goals']}:{match['result']['away_goals']}"


def test_lottery_sales_snapshot_tracks_daily_sale_rules(tmp_path):
    seed = load_seed_data()
    generate_public_data(seed, tmp_path, n_sims=50, seed=11)
    matches = json.loads((tmp_path / "matches.json").read_text())["matches"]

    australia = next(item for item in matches if item["home"]["name"] == "澳大利亚")
    argentina = next(item for item in matches if item["home"]["name"] == "阿根廷")
    colombia = next(item for item in matches if item["home"]["name"] == "哥伦比亚")

    assert australia["lottery_meta"]["code"] == "周五086"
    assert australia["kickoff"] == "2026-07-04T02:00:00+08:00"
    assert australia["handicap"] == 1
    assert australia["lottery"]["spf"]["sale"] is True
    assert australia["lottery"]["rqspf"]["supports_single"] is False
    assert australia["lottery"]["bf"]["options"][0]["listed_odds"] == 7.5
    bf_odds = {item["label"]: item.get("listed_odds") for item in australia["lottery"]["bf"]["options"]}
    assert bf_odds["0:1"] == 6.10
    assert bf_odds["1:1"] == 4.40
    assert bf_odds["0:0"] == 6.50

    assert argentina["lottery_meta"]["code"] == "周五087"
    assert argentina["lottery"]["spf"]["sale"] is False
    assert argentina["handicap"] == -2

    assert colombia["lottery_meta"]["code"] == "周五088"
    assert colombia["handicap"] == -1


def test_simulation_is_seed_reproducible_and_locks_completed_results():
    seed = load_seed_data()

    first = simulate_tournament(seed, n_sims=300, seed=42)
    second = simulate_tournament(seed, n_sims=300, seed=42)

    assert first == second
    assert first.champion_probs
    assert sum(first.champion_probs.values()) == pytest.approx(1.0, abs=1e-9)
    assert first.locked_results_applied >= 1
