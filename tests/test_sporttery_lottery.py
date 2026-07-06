import json
import urllib.error
from pathlib import Path
import argparse

from wcmodel.data import load_seed_data
from wcmodel.live_results import apply_live_results
from wcmodel.pipeline import generate_public_data
from wcmodel.sporttery_lottery import apply_sporttery_lottery, fetch_sporttery_calculator


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
                    {"homeAway": "home", "score": "0", "team": {"id": home_team_id, "abbreviation": home}},
                    {"homeAway": "away", "score": "0", "team": {"id": away_team_id, "abbreviation": away}},
                ],
            }
        ],
    }


def _sporttery_payload():
    return {
        "errorCode": "0",
        "success": True,
        "value": {
            "lastUpdateTime": "2026-07-04 21:34:09",
            "matchInfoList": [
                {
                    "businessDate": "2026-07-04",
                    "subMatchList": [
                        {
                            "matchNumStr": "周六089",
                            "competition": "世界杯",
                            "leagueAbbName": "世界杯",
                            "homeTeamAbbName": "加拿大",
                            "awayTeamAbbName": "摩洛哥",
                            "matchDate": "2026-07-05",
                            "matchTime": "01:00:00",
                            "poolList": [
                                {"poolCode": "HAD", "poolStatus": "Selling", "single": 1, "allUp": 1, "cbtValue": 1},
                                {"poolCode": "HHAD", "poolStatus": "Selling", "single": 0, "allUp": 1, "cbtValue": 1},
                                {"poolCode": "CRS", "poolStatus": "Selling", "single": 1, "allUp": 1, "cbtValue": 1},
                                {"poolCode": "TTG", "poolStatus": "Selling", "single": 1, "allUp": 1, "cbtValue": 1},
                                {"poolCode": "HAFU", "poolStatus": "Selling", "single": 1, "allUp": 1, "cbtValue": 1},
                            ],
                            "had": {"h": "5.60", "d": "3.58", "a": "1.49", "updateDate": "2026-07-04", "updateTime": "21:07:55"},
                            "hhad": {"goalLine": "+1", "h": "2.22", "d": "2.80", "a": "3.11", "updateDate": "2026-07-04", "updateTime": "21:07:41"},
                            "crs": {
                                "s01s00": "14.00", "s02s00": "32.00", "s02s01": "16.50", "s03s00": "100.0",
                                "s03s01": "65.00", "s03s02": "65.00", "s04s00": "350.0", "s04s01": "275.0",
                                "s04s02": "300.0", "s05s00": "800.0", "s05s01": "700.0", "s05s02": "800.0",
                                "s1sh": "400.0", "s00s00": "9.50", "s01s01": "5.45", "s02s02": "15.50",
                                "s03s03": "60.00", "s1sd": "400.0", "s00s01": "5.95", "s00s02": "6.00",
                                "s01s02": "4.85", "s00s03": "16.00", "s01s03": "11.50", "s02s03": "30.00",
                                "s00s04": "40.00", "s01s04": "45.00", "s02s04": "70.00", "s00s05": "125.0",
                                "s01s05": "125.0", "s02s05": "225.0", "s1sa": "100.0",
                            },
                            "ttg": {"s0": "9.50", "s1": "4.55", "s2": "2.70", "s3": "3.25", "s4": "7.25", "s5": "15.00", "s6": "35.00", "s7": "55.00"},
                            "hafu": {"hh": "10.50", "hd": "13.00", "ha": "18.00", "dh": "12.00", "dd": "5.40", "da": "3.65", "ah": "31.00", "ad": "13.00", "aa": "2.67"},
                        },
                        {
                            "matchNumStr": "周六090",
                            "leagueAbbName": "世界杯",
                            "homeTeamAbbName": "巴拉圭",
                            "awayTeamAbbName": "法国",
                            "matchDate": "2026-07-05",
                            "matchTime": "05:00:00",
                            "poolList": [
                                {"poolCode": "HHAD", "poolStatus": "Selling", "single": 1, "allUp": 1, "cbtValue": 1},
                                {"poolCode": "CRS", "poolStatus": "Selling", "single": 1, "allUp": 1, "cbtValue": 1},
                                {"poolCode": "TTG", "poolStatus": "Selling", "single": 1, "allUp": 1, "cbtValue": 1},
                                {"poolCode": "HAFU", "poolStatus": "Selling", "single": 1, "allUp": 1, "cbtValue": 1},
                            ],
                            "had": {},
                            "hhad": {"goalLine": "+2", "h": "2.35", "d": "3.33", "a": "2.48"},
                            "crs": {
                                "s01s00": "45.00", "s02s00": "125.0", "s02s01": "60.00", "s03s00": "400.0",
                                "s03s01": "250.0", "s03s02": "180.0", "s04s00": "1000", "s04s01": "800.0",
                                "s04s02": "800.0", "s05s00": "1000", "s05s01": "1000", "s05s02": "1000",
                                "s1sh": "700.0", "s00s00": "17.00", "s01s01": "14.00", "s02s02": "30.00",
                                "s03s03": "100.0", "s1sd": "600.0", "s00s01": "7.10", "s00s02": "4.65",
                                "s01s02": "7.75", "s00s03": "4.80", "s01s03": "7.40", "s02s03": "30.00",
                                "s00s04": "12.00", "s01s04": "17.00", "s02s04": "45.00", "s00s05": "21.00",
                                "s01s05": "40.00", "s02s05": "100.0", "s1sa": "17.00",
                            },
                            "ttg": {"s0": "17.00", "s1": "6.25", "s2": "3.95", "s3": "3.15", "s4": "4.20", "s5": "8.60", "s6": "16.00", "s7": "21.00"},
                            "hafu": {"hh": "34.00", "hd": "23.00", "ha": "21.00", "dh": "36.00", "dd": "11.00", "da": "3.95", "ah": "70.00", "ad": "23.00", "aa": "1.42"},
                        },
                    ],
                }
            ],
        },
    }


def test_sporttery_live_lottery_overrides_all_sold_markets_for_appended_matches(tmp_path):
    seed = load_seed_data()
    events = {
        "events": [
            _scheduled_event("760502", "2026-07-04T17:00Z", "206", "CAN", "2869", "MAR"),
            _scheduled_event("760503", "2026-07-04T21:00Z", "210", "PAR", "478", "FRA"),
        ]
    }
    seed, live_report = apply_live_results(seed, fetcher=lambda date: events, now_iso="2026-07-04T02:00:00Z")
    seed, lottery_report = apply_sporttery_lottery(seed, fetcher=_sporttery_payload)
    generate_public_data(seed, tmp_path, n_sims=50, seed=11, live_result_report=live_report, live_lottery_report=lottery_report)
    matches = json.loads((Path(tmp_path) / "matches.json").read_text())["matches"]

    canada = next(item for item in matches if item["match_id"] == "ESPN-760502")
    paraguay = next(item for item in matches if item["match_id"] == "ESPN-760503")

    assert canada["lottery_meta"]["source"] == "中国竞彩网实时计算器"
    assert canada["lottery"]["bf"]["sale"] is True
    assert canada["lottery"]["jqs"]["sale"] is True
    assert canada["lottery"]["bqc"]["sale"] is True
    assert {item["label"]: item.get("listed_odds") for item in canada["lottery"]["bf"]["options"]}["1:1"] == 5.45
    assert {item["label"]: item.get("listed_odds") for item in canada["lottery"]["jqs"]["options"]}["2"] == 2.70
    assert {item["label"]: item.get("listed_odds") for item in canada["lottery"]["bqc"]["options"]}["客胜 / 客胜"] == 2.67

    assert paraguay["lottery"]["spf"]["sale"] is False
    assert paraguay["lottery"]["rqspf"]["sale"] is True
    assert paraguay["handicap"] == 2
    assert {item["label"]: item.get("listed_odds") for item in paraguay["lottery"]["bf"]["options"]}["0:3"] == 4.80
    assert {item["label"]: item.get("listed_odds") for item in paraguay["lottery"]["jqs"]["options"]}["3"] == 3.15


def test_generate_cli_can_apply_sporttery_live_lottery(monkeypatch, tmp_path):
    from wcmodel import cli

    called = {"lottery": False}

    def fake_apply_sporttery_lottery(seed):
        called["lottery"] = True
        return seed, {"source": "sporttery", "applied_count": 0}

    monkeypatch.setattr(cli, "PUBLIC_ROOT", tmp_path / "public")
    monkeypatch.setattr(cli, "_copy_web_assets", lambda public_root: public_root.mkdir(parents=True, exist_ok=True))
    monkeypatch.setattr(cli, "apply_sporttery_lottery", fake_apply_sporttery_lottery)

    cli.generate(argparse.Namespace(sims=50, seed=11, live_results="none", live_lottery="sporttery"))

    status = json.loads((tmp_path / "public" / "data" / "model_status.json").read_text())
    assert called["lottery"] is True
    assert status["mode"] == "offline_static_local_with_live_data"
    assert status["live_lottery"]["source"] == "sporttery"


def test_generate_cli_degrades_when_sporttery_live_lottery_is_unavailable(monkeypatch, tmp_path):
    from wcmodel import cli

    def fake_apply_sporttery_lottery(seed):
        raise RuntimeError("sporttery live lottery returned non-json response: text/html")

    monkeypatch.setattr(cli, "PUBLIC_ROOT", tmp_path / "public")
    monkeypatch.setattr(cli, "_copy_web_assets", lambda public_root: public_root.mkdir(parents=True, exist_ok=True))
    monkeypatch.setattr(cli, "apply_sporttery_lottery", fake_apply_sporttery_lottery)

    cli.generate(argparse.Namespace(sims=50, seed=11, live_results="none", live_lottery="sporttery"))

    status = json.loads((tmp_path / "public" / "data" / "model_status.json").read_text())
    assert status["mode"] == "offline_static_local_with_live_data"
    assert status["live_lottery"]["source"] == "sporttery"
    assert status["live_lottery"]["applied_count"] == 0
    assert "non-json response" in status["live_lottery"]["error"]


def test_sporttery_fetcher_rejects_non_json_response(monkeypatch):
    class FakeHeaders:
        def get(self, key, default=None):
            return "text/html" if key == "content-type" else default

    class FakeResponse:
        status = 200
        headers = FakeHeaders()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b"        <script>var seqid = 'challenge';</script>"

    monkeypatch.setattr("urllib.request.urlopen", lambda request, timeout: FakeResponse())

    try:
        fetch_sporttery_calculator()
    except RuntimeError as exc:
        assert "non-json response" in str(exc)
        assert "text/html" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


def test_sporttery_fetcher_wraps_url_errors(monkeypatch):
    def raise_url_error(request, timeout):
        raise urllib.error.URLError("timed out")

    monkeypatch.setattr("urllib.request.urlopen", raise_url_error)

    try:
        fetch_sporttery_calculator()
    except RuntimeError as exc:
        assert "request failed" in str(exc)
        assert "timed out" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")
