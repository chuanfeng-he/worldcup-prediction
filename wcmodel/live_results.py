from __future__ import annotations

import copy
import json
import re
import urllib.request
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple

from wcmodel.data import SeedData

ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates={date}"
BEIJING_TZ = timezone(timedelta(hours=8))
STAGE_BY_SLUG = {
    "round-of-32": "32强",
    "round-of-16": "16强",
    "quarterfinals": "8强",
    "semifinals": "半决赛",
    "third-place": "三四名决赛",
    "final": "决赛",
}

ScoreboardFetcher = Callable[[str], Dict[str, object]]


def fetch_espn_scoreboard(date_text: str, timeout: int = 12) -> Dict[str, object]:
    request = urllib.request.Request(
        ESPN_SCOREBOARD_URL.format(date=date_text),
        headers={"User-Agent": "wc26-forecast-web/0.1"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _parse_iso_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _utc_iso(now_iso: Optional[str]) -> str:
    if now_iso:
        value = _parse_iso_datetime(now_iso)
    else:
        value = datetime.now(timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _beijing_iso(value: str) -> str:
    return _parse_iso_datetime(value).astimezone(BEIJING_TZ).replace(microsecond=0).isoformat()


def _scoreboard_dates(fixtures: Iterable[Dict[str, object]], now_iso: Optional[str] = None, lookahead_days: int = 3) -> List[str]:
    dates: Set[str] = set()
    for fixture in fixtures:
        kickoff = _parse_iso_datetime(str(fixture["kickoff"]))
        utc_kickoff = kickoff.astimezone(timezone.utc)
        for candidate in (kickoff, kickoff - timedelta(days=1), utc_kickoff, utc_kickoff - timedelta(days=1)):
            dates.add(candidate.strftime("%Y%m%d"))
    now = _parse_iso_datetime(_utc_iso(now_iso))
    for day_offset in range(-1, lookahead_days + 1):
        candidate = now + timedelta(days=day_offset)
        dates.add(candidate.strftime("%Y%m%d"))
        dates.add(candidate.astimezone(BEIJING_TZ).strftime("%Y%m%d"))
    return sorted(dates)


def _team_ids(competition: Dict[str, object]) -> Dict[str, str]:
    teams: Dict[str, str] = {}
    for competitor in competition.get("competitors", []):
        team = competitor.get("team", {})
        abbreviation = team.get("abbreviation")
        espn_id = team.get("id") or competitor.get("id")
        if abbreviation and espn_id:
            teams[str(abbreviation)] = str(espn_id)
    return teams


def _competitors_by_local_id(competition: Dict[str, object]) -> Dict[str, Dict[str, object]]:
    rows: Dict[str, Dict[str, object]] = {}
    for competitor in competition.get("competitors", []):
        team = competitor.get("team", {})
        abbreviation = team.get("abbreviation")
        if abbreviation:
            rows[str(abbreviation)] = competitor
    return rows


def _clock_minute(display_value: object) -> Optional[int]:
    match = re.match(r"^(\d+)'", str(display_value or ""))
    if not match:
        return None
    return int(match.group(1))


def _is_first_half(clock: Dict[str, object]) -> bool:
    display = str(clock.get("displayValue") or "")
    minute = _clock_minute(display)
    if minute is None:
        value = clock.get("value")
        return isinstance(value, (int, float)) and float(value) <= 2700
    return minute < 45 or minute == 45


def _is_regulation(clock: Dict[str, object]) -> bool:
    display = str(clock.get("displayValue") or "")
    minute = _clock_minute(display)
    if minute is None:
        value = clock.get("value")
        return isinstance(value, (int, float)) and float(value) <= 5400
    if minute < 90 or minute == 90:
        return True
    return display.startswith("90'+")


def _score_from_details(
    competition: Dict[str, object],
    espn_to_local: Dict[str, str],
    predicate: Callable[[Dict[str, object]], bool],
) -> Optional[Dict[str, int]]:
    scores = {local_id: 0 for local_id in espn_to_local.values()}
    saw_scoring_detail = False
    for detail in competition.get("details", []):
        if not detail.get("scoringPlay") or detail.get("shootout"):
            continue
        team = detail.get("team") or {}
        local_id = espn_to_local.get(str(team.get("id")))
        if not local_id:
            continue
        saw_scoring_detail = True
        if predicate(detail.get("clock") or {}):
            scores[local_id] += int(detail.get("scoreValue") or 1)
    return scores if saw_scoring_detail else None


def _goals_for_fixture(score_by_team: Optional[Dict[str, int]], home_id: str, away_id: str) -> Optional[Dict[str, int]]:
    if score_by_team is None:
        return None
    return {"home_goals": int(score_by_team.get(home_id, 0)), "away_goals": int(score_by_team.get(away_id, 0))}


def _final_score(competitors: Dict[str, Dict[str, object]], home_id: str, away_id: str) -> Dict[str, int]:
    return {
        "home_goals": int(competitors[home_id].get("score") or 0),
        "away_goals": int(competitors[away_id].get("score") or 0),
    }


def _shootout_score(competitors: Dict[str, Dict[str, object]], home_id: str, away_id: str) -> Optional[Dict[str, int]]:
    home = competitors[home_id].get("shootoutScore")
    away = competitors[away_id].get("shootoutScore")
    if home is None and away is None:
        return None
    return {"home_goals": int(home or 0), "away_goals": int(away or 0)}


def _advance(competitors: Dict[str, Dict[str, object]]) -> Optional[str]:
    for team_id, competitor in competitors.items():
        if competitor.get("advance") or competitor.get("winner"):
            return team_id
    return None


def _live_result_for_fixture(fixture: Dict[str, object], event: Dict[str, object]) -> Optional[Dict[str, object]]:
    competitions = event.get("competitions") or []
    if not competitions:
        return None
    competition = competitions[0]
    status = competition.get("status", {}).get("type", {})
    if not status.get("completed"):
        return None

    home_id = str(fixture["home"])
    away_id = str(fixture["away"])
    competitors = _competitors_by_local_id(competition)
    if home_id not in competitors or away_id not in competitors:
        return None

    espn_ids = _team_ids(competition)
    espn_to_local = {espn_id: local_id for local_id, espn_id in espn_ids.items()}
    final_score = _final_score(competitors, home_id, away_id)
    regulation_score = _goals_for_fixture(_score_from_details(competition, espn_to_local, _is_regulation), home_id, away_id)
    halftime_score = _goals_for_fixture(_score_from_details(competition, espn_to_local, _is_first_half), home_id, away_id)
    settlement_score = regulation_score or final_score

    return {
        "source": "espn",
        "source_event_id": str(event.get("id") or ""),
        "status": str(status.get("name") or ""),
        "status_detail": str(status.get("shortDetail") or status.get("detail") or status.get("description") or ""),
        "settlement_basis": "regulation_90" if regulation_score else "final_score_fallback",
        "settlement_score": settlement_score,
        "final_score": final_score,
        "halftime_score": halftime_score,
        "shootout_score": _shootout_score(competitors, home_id, away_id),
        "advance": _advance(competitors),
    }


def _event_index(payloads: Iterable[Dict[str, object]]) -> Dict[frozenset, Dict[str, object]]:
    events: Dict[frozenset, Dict[str, object]] = {}
    for payload in payloads:
        for event in payload.get("events", []):
            competitions = event.get("competitions") or []
            if not competitions:
                continue
            local_ids = {
                str(competitor.get("team", {}).get("abbreviation"))
                for competitor in competitions[0].get("competitors", [])
                if competitor.get("team", {}).get("abbreviation")
            }
            if len(local_ids) == 2:
                events[frozenset(local_ids)] = event
    return events


def _events(payloads: Iterable[Dict[str, object]]) -> Iterable[Dict[str, object]]:
    for payload in payloads:
        yield from payload.get("events", [])


def _stage_for_event(event: Dict[str, object]) -> str:
    slug = str((event.get("season") or {}).get("slug") or "")
    return STAGE_BY_SLUG.get(slug, slug or "淘汰赛")


def _kickoff_beijing(event: Dict[str, object]) -> str:
    return _parse_iso_datetime(str(event["date"])).astimezone(BEIJING_TZ).replace(microsecond=0).isoformat()


def _fixture_from_event(event: Dict[str, object], known_team_ids: Set[str], fetched_at: str) -> Optional[Dict[str, object]]:
    competitions = event.get("competitions") or []
    if not competitions:
        return None
    competition = competitions[0]
    status = competition.get("status", {}).get("type", {})
    competitors = _competitors_by_local_id(competition)
    home_ids = [
        team_id
        for team_id, competitor in competitors.items()
        if competitor.get("homeAway") == "home"
    ]
    away_ids = [
        team_id
        for team_id, competitor in competitors.items()
        if competitor.get("homeAway") == "away"
    ]
    if len(home_ids) != 1 or len(away_ids) != 1:
        return None
    home_id = home_ids[0]
    away_id = away_ids[0]
    if home_id not in known_team_ids or away_id not in known_team_ids:
        return None
    stage = _stage_for_event(event)
    kickoff = _kickoff_beijing(event)
    row = {
        "match_id": f"ESPN-{event.get('id')}",
        "group": stage,
        "stage": stage,
        "home": home_id,
        "away": away_id,
        "neutral": True,
        "kickoff": kickoff,
        "completed": False,
        "home_goals": None,
        "away_goals": None,
        "home_ht_goals": None,
        "away_ht_goals": None,
        "available_at": kickoff,
    }
    live_result = _live_result_for_fixture(row, event)
    if live_result:
        settlement = live_result["settlement_score"]
        halftime = live_result.get("halftime_score") or {}
        row["completed"] = True
        row["home_goals"] = settlement["home_goals"]
        row["away_goals"] = settlement["away_goals"]
        row["home_ht_goals"] = halftime.get("home_goals")
        row["away_ht_goals"] = halftime.get("away_goals")
        row["live_result"] = {**live_result, "source_updated_at": fetched_at}
    else:
        row["live_schedule"] = {
            "source": "espn",
            "source_event_id": str(event.get("id") or ""),
            "status": str(status.get("name") or ""),
            "status_detail": str(status.get("shortDetail") or status.get("detail") or status.get("description") or ""),
        }
    return row


def apply_live_results(
    seed_data: SeedData,
    fetcher: ScoreboardFetcher = fetch_espn_scoreboard,
    now_iso: Optional[str] = None,
) -> Tuple[SeedData, Dict[str, object]]:
    fetched_dates = _scoreboard_dates(seed_data.fixtures, now_iso=now_iso)
    payloads: List[Dict[str, object]] = []
    failed_dates: List[Dict[str, str]] = []
    for date_text in fetched_dates:
        try:
            payloads.append(fetcher(date_text))
        except Exception as exc:
            failed_dates.append({"date": date_text, "error": str(exc)})
    events = _event_index(payloads)
    updated_fixtures: List[Dict[str, object]] = []
    applied: List[str] = []
    appended: List[str] = []
    fetched_at = _utc_iso(now_iso)

    for fixture in seed_data.fixtures:
        row = copy.deepcopy(fixture)
        event = events.get(frozenset({str(row["home"]), str(row["away"])}))
        live_result = _live_result_for_fixture(row, event) if event else None
        if live_result:
            settlement = live_result["settlement_score"]
            halftime = live_result.get("halftime_score") or {}
            row["completed"] = True
            row["home_goals"] = settlement["home_goals"]
            row["away_goals"] = settlement["away_goals"]
            row["home_ht_goals"] = halftime.get("home_goals")
            row["away_ht_goals"] = halftime.get("away_goals")
            row["live_result"] = {**live_result, "source_updated_at": fetched_at}
            applied.append(str(row["match_id"]))
        updated_fixtures.append(row)

    existing_pairs = {frozenset({str(row["home"]), str(row["away"])}) for row in updated_fixtures}
    known_team_ids = set(seed_data.teams)
    for event in _events(payloads):
        fixture = _fixture_from_event(event, known_team_ids, fetched_at)
        if not fixture:
            continue
        pair = frozenset({str(fixture["home"]), str(fixture["away"])})
        if pair in existing_pairs:
            continue
        updated_fixtures.append(fixture)
        existing_pairs.add(pair)
        appended.append(str(fixture["match_id"]))

    updated_fixtures.sort(key=lambda item: str(item["kickoff"]))
    report = {
        "source": "espn",
        "fetched_at": fetched_at,
        "fetched_dates": fetched_dates,
        "applied_count": len(applied),
        "applied_match_ids": applied,
        "appended_count": len(appended),
        "appended_match_ids": appended,
        "failed_dates": failed_dates,
    }
    return replace(seed_data, fixtures=updated_fixtures, as_of=_beijing_iso(fetched_at)), report
