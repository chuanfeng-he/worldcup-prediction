from __future__ import annotations

import copy
import json
import urllib.error
import urllib.request
from dataclasses import replace
from datetime import datetime, timezone
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from wcmodel.data import SeedData
from wcmodel.model import decimal_odds_to_probs

SPORTTERY_CALCULATOR_URL = (
    "https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry"
    "?channel=c&poolCode=hhad,had,crs,ttg,hafu"
)
BEIJING_SUFFIX = "+08:00"

SportteryFetcher = Callable[[], Dict[str, object]]

SCORE_ODDS_FIELDS = {
    "1:0": "s01s00",
    "2:0": "s02s00",
    "2:1": "s02s01",
    "3:0": "s03s00",
    "3:1": "s03s01",
    "3:2": "s03s02",
    "4:0": "s04s00",
    "4:1": "s04s01",
    "4:2": "s04s02",
    "5:0": "s05s00",
    "5:1": "s05s01",
    "5:2": "s05s02",
    "胜其他": "s1sh",
    "0:0": "s00s00",
    "1:1": "s01s01",
    "2:2": "s02s02",
    "3:3": "s03s03",
    "平其他": "s1sd",
    "0:1": "s00s01",
    "0:2": "s00s02",
    "1:2": "s01s02",
    "0:3": "s00s03",
    "1:3": "s01s03",
    "2:3": "s02s03",
    "0:4": "s00s04",
    "1:4": "s01s04",
    "2:4": "s02s04",
    "0:5": "s00s05",
    "1:5": "s01s05",
    "2:5": "s02s05",
    "负其他": "s1sa",
}

TOTAL_GOAL_FIELDS = {
    "0": "s0",
    "1": "s1",
    "2": "s2",
    "3": "s3",
    "4": "s4",
    "5": "s5",
    "6": "s6",
    "7+": "s7",
}

HALF_FULL_FIELDS = {
    "主胜 / 主胜": "hh",
    "主胜 / 平局": "hd",
    "主胜 / 客胜": "ha",
    "平局 / 主胜": "dh",
    "平局 / 平局": "dd",
    "平局 / 客胜": "da",
    "客胜 / 主胜": "ah",
    "客胜 / 平局": "ad",
    "客胜 / 客胜": "aa",
}


def fetch_sporttery_calculator(timeout: int = 12) -> Dict[str, object]:
    request = urllib.request.Request(
        SPORTTERY_CALCULATOR_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
            "Accept": "application/json,text/plain,*/*",
            "Referer": "https://www.sporttery.cn/jc/jsq/zqspf/",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", "replace")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError as exc:
                content_type = response.headers.get("content-type", "")
                snippet = " ".join(body[:160].split())
                raise RuntimeError(
                    f"sporttery live lottery returned non-json response: "
                    f"status={response.status}, content_type={content_type}, body={snippet!r}"
                ) from exc
            if not isinstance(payload, dict):
                raise RuntimeError(f"sporttery live lottery returned unexpected payload type: {type(payload).__name__}")
            return payload
    except urllib.error.URLError as exc:
        raise RuntimeError(f"sporttery live lottery request failed: {exc}") from exc


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _norm(value: object) -> str:
    return str(value or "").strip().replace(" ", "")


def _float(value: object) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _odds(source: Dict[str, object], fields: Dict[str, str]) -> Dict[str, float]:
    odds: Dict[str, float] = {}
    for label, field in fields.items():
        value = _float(source.get(field))
        if value is not None:
            odds[label] = value
    return odds


def _pool_rows(match: Dict[str, object]) -> Dict[str, Dict[str, object]]:
    rows: Dict[str, Dict[str, object]] = {}
    for row in match.get("poolList") or []:
        code = str(row.get("poolCode") or "").lower()
        if code:
            rows[code] = row
    return rows


def _pool_config(pool_rows: Dict[str, Dict[str, object]], code: str, odds: Dict[str, float], extra: Optional[Dict[str, object]] = None) -> Dict[str, object]:
    row = pool_rows.get(code, {})
    sale = (
        bool(odds)
        and str(row.get("poolStatus") or "").lower() == "selling"
        and str(row.get("cbtValue") or "1") != "2"
    )
    config: Dict[str, object] = {
        "sale": sale,
        "supports_single": sale and str(row.get("single") or "0") == "1",
        "supports_parlay": sale and str(row.get("allUp") or row.get("bettingAllup") or "0") == "1",
        "odds": odds if sale else {},
    }
    if extra:
        config.update(extra)
    return config


def _handicap(value: object) -> Optional[int]:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _match_kickoff(match: Dict[str, object]) -> str:
    date = str(match.get("matchDate") or "")
    time = str(match.get("matchTime") or "00:00:00")
    if len(time) == 5:
        time = f"{time}:00"
    return f"{date}T{time}{BEIJING_SUFFIX}"


def _fixture_index(seed_data: SeedData) -> Dict[Tuple[str, str, str], str]:
    team_names = {team_id: _norm(team.name) for team_id, team in seed_data.teams.items()}
    rows: Dict[Tuple[str, str, str], str] = {}
    for fixture in seed_data.fixtures:
        kickoff_key = str(fixture["kickoff"])[:16]
        rows[(team_names[str(fixture["home"])], team_names[str(fixture["away"])], kickoff_key)] = str(fixture["match_id"])
    return rows


def _iter_matches(payload: Dict[str, object]) -> Iterable[Dict[str, object]]:
    value = payload.get("value") or {}
    for day in value.get("matchInfoList") or []:
        yield from day.get("subMatchList") or []


def _sale_from_match(match: Dict[str, object], source_updated_at: Optional[str]) -> Dict[str, object]:
    pool_rows = _pool_rows(match)
    had = match.get("had") or {}
    hhad = match.get("hhad") or {}
    crs = match.get("crs") or {}
    ttg = match.get("ttg") or {}
    hafu = match.get("hafu") or {}
    hhad_handicap = _handicap(hhad.get("goalLine"))
    markets = {
        "spf": _pool_config(pool_rows, "had", _odds(had, {"主胜": "h", "平局": "d", "客胜": "a"}), {"handicap_label": "-"}),
        "rqspf": _pool_config(
            pool_rows,
            "hhad",
            _odds(hhad, {"主胜": "h", "平局": "d", "客胜": "a"}),
            {
                "handicap": hhad_handicap,
                "handicap_label": str(hhad.get("goalLine") or ""),
            },
        ),
        "bf": _pool_config(pool_rows, "crs", _odds(crs, SCORE_ODDS_FIELDS)),
        "jqs": _pool_config(pool_rows, "ttg", _odds(ttg, TOTAL_GOAL_FIELDS)),
        "bqc": _pool_config(pool_rows, "hafu", _odds(hafu, HALF_FULL_FIELDS)),
    }
    return {
        "code": match.get("matchNumStr"),
        "competition": match.get("leagueAbbName") or match.get("leagueAllName") or "世界杯",
        "source": "中国竞彩网实时计算器",
        "source_updated_at": source_updated_at,
        "markets": markets,
    }


def apply_sporttery_lottery(
    seed_data: SeedData,
    fetcher: SportteryFetcher = fetch_sporttery_calculator,
) -> Tuple[SeedData, Dict[str, object]]:
    payload = fetcher()
    if str(payload.get("errorCode")) not in {"0", ""} or payload.get("success") is False:
        raise RuntimeError(f"sporttery live lottery fetch failed: {payload.get('errorMessage') or payload.get('errorCode')}")

    value = payload.get("value") or {}
    source_updated_at = value.get("lastUpdateTime")
    fixture_index = _fixture_index(seed_data)
    lottery_sales = copy.deepcopy(seed_data.lottery_sales)
    market_probs = copy.deepcopy(seed_data.market_probs)
    applied: List[str] = []
    unmatched: List[str] = []

    for match in _iter_matches(payload):
        home = _norm(match.get("homeTeamAbbName") or match.get("homeTeamAllName"))
        away = _norm(match.get("awayTeamAbbName") or match.get("awayTeamAllName"))
        kickoff_key = _match_kickoff(match)[:16]
        match_id = fixture_index.get((home, away, kickoff_key))
        if not match_id:
            unmatched.append(str(match.get("matchNumStr") or f"{home}-{away}-{kickoff_key}"))
            continue
        sale = _sale_from_match(match, str(source_updated_at) if source_updated_at else None)
        lottery_sales[match_id] = sale
        had_odds = sale["markets"]["spf"]["odds"]
        if sale["markets"]["spf"]["sale"] and all(label in had_odds for label in ("主胜", "平局", "客胜")):
            market_probs[match_id] = decimal_odds_to_probs(had_odds["主胜"], had_odds["平局"], had_odds["客胜"])
        applied.append(match_id)

    report = {
        "source": "sporttery",
        "fetched_at": _utc_iso(),
        "source_updated_at": source_updated_at,
        "applied_count": len(applied),
        "applied_match_ids": applied,
        "unmatched_count": len(unmatched),
        "unmatched": unmatched,
    }
    return replace(seed_data, lottery_sales=lottery_sales, market_probs=market_probs), report
