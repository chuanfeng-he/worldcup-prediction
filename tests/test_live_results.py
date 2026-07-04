from __future__ import annotations

import argparse
import json

from wcmodel.data import load_seed_data
from wcmodel.live_results import apply_live_results
from wcmodel.pipeline import generate_public_data


def _competitor(team_id, abbreviation, home_away, score, winner=False, advance=False, shootout_score=None):
    payload = {
        "id": team_id,
        "homeAway": home_away,
        "winner": winner,
        "advance": advance,
        "score": str(score),
        "team": {"id": team_id, "abbreviation": abbreviation, "displayName": abbreviation},
    }
    if shootout_score is not None:
        payload["shootoutScore"] = shootout_score
    return payload


def _goal(team_id, minute, display):
    return {
        "type": {"text": "Goal"},
        "clock": {"value": minute * 60, "displayValue": display},
        "team": {"id": team_id},
        "scoreValue": 1,
        "scoringPlay": True,
        "shootout": False,
    }


def _scheduled_event(event_id, date, home_team_id, home, away_team_id, away):
    return {
        "id": event_id,
        "date": date,
        "season": {"slug": "round-of-16"},
        "competitions": [
            {
                "status": {
                    "type": {
                        "name": "STATUS_SCHEDULED",
                        "completed": False,
                        "shortDetail": "Scheduled",
                    }
                },
                "competitors": [
                    _competitor(home_team_id, home, "home", 0),
                    _competitor(away_team_id, away, "away", 0),
                ],
            }
        ],
    }


def test_apply_live_results_uses_regulation_score_for_lottery_settlement():
    seed = load_seed_data()
    payload = {
        "events": [
            {
                "id": "760499",
                "date": "2026-07-03T18:00Z",
                "competitions": [
                    {
                        "status": {
                            "type": {
                                "name": "STATUS_FINAL_PEN",
                                "completed": True,
                                "shortDetail": "FT-Pens",
                            }
                        },
                        "competitors": [
                            _competitor("628", "AUS", "home", 1, shootout_score=2),
                            _competitor("2620", "EGY", "away", 1, winner=True, advance=True, shootout_score=4),
                        ],
                        "details": [
                            _goal("2620", 13, "13'"),
                            _goal("628", 55, "55'"),
                        ],
                    }
                ],
            },
            {
                "id": "760500",
                "date": "2026-07-03T22:00Z",
                "competitions": [
                    {
                        "status": {
                            "type": {
                                "name": "STATUS_FINAL_AET",
                                "completed": True,
                                "shortDetail": "AET",
                            }
                        },
                        "competitors": [
                            _competitor("202", "ARG", "home", 3, winner=True, advance=True),
                            _competitor("2597", "CPV", "away", 2),
                        ],
                        "details": [
                            _goal("202", 29, "29'"),
                            _goal("2597", 59, "59'"),
                            _goal("202", 92, "92'"),
                            _goal("2597", 103, "103'"),
                            _goal("202", 111, "111'"),
                        ],
                    }
                ],
            },
        ]
    }

    updated, report = apply_live_results(seed, fetcher=lambda date: payload, now_iso="2026-07-04T02:00:00Z")

    australia = next(item for item in updated.fixtures if item["match_id"] == "R16-20260704-1")
    argentina = next(item for item in updated.fixtures if item["match_id"] == "R16-20260704-2")

    assert report["applied_count"] == 2
    assert updated.as_of == "2026-07-04T10:00:00+08:00"
    assert australia["completed"] is True
    assert australia["home_goals"] == 1
    assert australia["away_goals"] == 1
    assert australia["home_ht_goals"] == 0
    assert australia["away_ht_goals"] == 1
    assert australia["live_result"]["status_detail"] == "FT-Pens"
    assert australia["live_result"]["shootout_score"] == {"home_goals": 2, "away_goals": 4}
    assert australia["live_result"]["advance"] == "EGY"

    assert argentina["completed"] is True
    assert argentina["home_goals"] == 1
    assert argentina["away_goals"] == 1
    assert argentina["home_ht_goals"] == 1
    assert argentina["away_ht_goals"] == 0
    assert argentina["live_result"]["settlement_basis"] == "regulation_90"
    assert argentina["live_result"]["final_score"] == {"home_goals": 3, "away_goals": 2}
    assert argentina["live_result"]["advance"] == "ARG"


def test_apply_live_results_appends_known_espn_scheduled_fixtures():
    seed = load_seed_data()
    payload = {
        "events": [
            _scheduled_event("760502", "2026-07-04T17:00Z", "206", "CAN", "2869", "MAR"),
            _scheduled_event("760503", "2026-07-04T21:00Z", "210", "PAR", "478", "FRA"),
        ]
    }

    updated, report = apply_live_results(seed, fetcher=lambda date: payload, now_iso="2026-07-04T02:00:00Z")

    canada = next(item for item in updated.fixtures if item["match_id"] == "ESPN-760502")
    france = next(item for item in updated.fixtures if item["match_id"] == "ESPN-760503")

    assert report["appended_count"] == 2
    assert canada["stage"] == "16强"
    assert canada["home"] == "CAN"
    assert canada["away"] == "MAR"
    assert canada["kickoff"] == "2026-07-05T01:00:00+08:00"
    assert canada["completed"] is False
    assert france["home"] == "PAR"
    assert france["away"] == "FRA"
    assert france["kickoff"] == "2026-07-05T05:00:00+08:00"


def test_apply_live_results_continues_when_one_scoreboard_date_fails():
    seed = load_seed_data()
    payload = {
        "events": [
            _scheduled_event("760502", "2026-07-04T17:00Z", "206", "CAN", "2869", "MAR"),
        ]
    }

    def fetcher(date_text):
        if date_text == "20260703":
            raise TimeoutError("temporary ESPN timeout")
        return payload

    updated, report = apply_live_results(seed, fetcher=fetcher, now_iso="2026-07-04T02:00:00Z")

    assert any(item["match_id"] == "ESPN-760502" for item in updated.fixtures)
    assert report["failed_dates"] == [{"date": "20260703", "error": "temporary ESPN timeout"}]


def test_generated_daily_predictions_use_appended_future_fixtures(tmp_path):
    seed = load_seed_data()
    payload = {
        "events": [
            {
                "id": "760499",
                "date": "2026-07-03T18:00Z",
                "competitions": [
                    {
                        "status": {"type": {"name": "STATUS_FINAL_PEN", "completed": True, "shortDetail": "FT-Pens"}},
                        "competitors": [
                            _competitor("628", "AUS", "home", 1, shootout_score=2),
                            _competitor("2620", "EGY", "away", 1, winner=True, advance=True, shootout_score=4),
                        ],
                        "details": [
                            _goal("2620", 13, "13'"),
                            _goal("628", 55, "55'"),
                        ],
                    }
                ],
            },
            {
                "id": "760500",
                "date": "2026-07-03T22:00Z",
                "competitions": [
                    {
                        "status": {"type": {"name": "STATUS_FINAL_AET", "completed": True, "shortDetail": "AET"}},
                        "competitors": [
                            _competitor("202", "ARG", "home", 3, winner=True, advance=True),
                            _competitor("2597", "CPV", "away", 2),
                        ],
                        "details": [
                            _goal("202", 29, "29'"),
                            _goal("2597", 59, "59'"),
                            _goal("202", 92, "92'"),
                            _goal("2597", 103, "103'"),
                            _goal("202", 111, "111'"),
                        ],
                    }
                ],
            },
            {
                "id": "760501",
                "date": "2026-07-04T01:30Z",
                "competitions": [
                    {
                        "status": {"type": {"name": "STATUS_FINAL", "completed": True, "shortDetail": "FT"}},
                        "competitors": [
                            _competitor("208", "COL", "home", 2, winner=True, advance=True),
                            _competitor("4469", "GHA", "away", 0),
                        ],
                        "details": [
                            _goal("208", 14, "14'"),
                            _goal("208", 74, "74'"),
                        ],
                    }
                ],
            },
            _scheduled_event("760502", "2026-07-04T17:00Z", "206", "CAN", "2869", "MAR"),
            _scheduled_event("760503", "2026-07-04T21:00Z", "210", "PAR", "478", "FRA"),
        ]
    }

    updated, report = apply_live_results(seed, fetcher=lambda date: payload, now_iso="2026-07-04T02:00:00Z")
    generate_public_data(updated, tmp_path, n_sims=50, seed=11, live_result_report=report)

    daily = json.loads((tmp_path / "daily_predictions.json").read_text())
    pairs = {(item["home"]["name"], item["away"]["name"]) for item in daily["matches"]}

    assert daily["as_of_date"] == "2026-07-04"
    assert daily["target_date"] == "2026-07-05"
    assert pairs == {("加拿大", "摩洛哥"), ("巴拉圭", "法国")}


def test_completed_auto_appended_espn_fixture_stays_in_daily_review(tmp_path):
    seed = load_seed_data()
    payload = {
        "events": [
            {
                "id": "760502",
                "date": "2026-07-04T17:00Z",
                "season": {"slug": "round-of-16"},
                "competitions": [
                    {
                        "status": {"type": {"name": "STATUS_FINAL", "completed": True, "shortDetail": "FT"}},
                        "competitors": [
                            _competitor("206", "CAN", "home", 1, winner=True, advance=True),
                            _competitor("2869", "MAR", "away", 0),
                        ],
                        "details": [
                            _goal("206", 31, "31'"),
                        ],
                    }
                ],
            }
        ]
    }

    updated, report = apply_live_results(seed, fetcher=lambda date: payload, now_iso="2026-07-04T18:30:00Z")
    generate_public_data(updated, tmp_path, n_sims=50, seed=11, live_result_report=report)

    daily = json.loads((tmp_path / "daily_predictions.json").read_text())
    canada = next(item for item in daily["today_completed"] if item["match_id"] == "ESPN-760502")

    assert daily["as_of_date"] == "2026-07-05"
    assert canada["home"]["name"] == "加拿大"
    assert canada["away"]["name"] == "摩洛哥"
    assert canada["result"]["home_goals"] == 1
    assert canada["result"]["away_goals"] == 0
    assert canada["live_result"]["settlement_basis"] == "regulation_90"


def test_generated_json_exposes_live_final_score_and_settlement_score(tmp_path):
    seed = load_seed_data()
    payload = {
        "events": [
            {
                "id": "760500",
                "date": "2026-07-03T22:00Z",
                "competitions": [
                    {
                        "status": {"type": {"name": "STATUS_FINAL_AET", "completed": True, "shortDetail": "AET"}},
                        "competitors": [
                            _competitor("202", "ARG", "home", 3, winner=True, advance=True),
                            _competitor("2597", "CPV", "away", 2),
                        ],
                        "details": [
                            _goal("202", 29, "29'"),
                            _goal("2597", 59, "59'"),
                            _goal("202", 92, "92'"),
                            _goal("2597", 103, "103'"),
                            _goal("202", 111, "111'"),
                        ],
                    }
                ],
            }
        ]
    }

    updated, _ = apply_live_results(seed, fetcher=lambda date: payload, now_iso="2026-07-04T02:00:00Z")
    generate_public_data(updated, tmp_path, n_sims=50, seed=11, live_result_report={"source": "espn"})

    matches = json.loads((tmp_path / "matches.json").read_text())["matches"]
    argentina = next(item for item in matches if item["match_id"] == "R16-20260704-2")

    assert argentina["completed"] is True
    assert argentina["result"]["home_goals"] == 1
    assert argentina["result"]["away_goals"] == 1
    assert argentina["live_result"]["final_score"] == {"home_goals": 3, "away_goals": 2}
    assert argentina["live_result"]["settlement_basis"] == "regulation_90"


def test_generate_cli_can_apply_espn_live_results(monkeypatch, tmp_path):
    from wcmodel import cli

    called = {"live": False}

    def fake_apply_live_results(seed):
        called["live"] = True
        return seed, {"source": "espn", "applied_count": 0, "fetched_dates": ["20260703"]}

    monkeypatch.setattr(cli, "PUBLIC_ROOT", tmp_path / "public")
    monkeypatch.setattr(cli, "_copy_web_assets", lambda public_root: public_root.mkdir(parents=True, exist_ok=True))
    monkeypatch.setattr(cli, "apply_live_results", fake_apply_live_results)

    cli.generate(argparse.Namespace(sims=50, seed=11, live_results="espn", live_lottery="none"))

    status = json.loads((tmp_path / "public" / "data" / "model_status.json").read_text())
    assert called["live"] is True
    assert status["mode"] == "offline_static_local_with_live_data"
    assert status["live_results"]["source"] == "espn"
