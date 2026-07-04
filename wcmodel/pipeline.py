from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from wcmodel import MODEL_VERSION
from wcmodel.data import SeedData
from wcmodel.lottery import (
    apply_lottery_sale,
    china_lottery_markets,
    handicap_for_match,
    historical_success,
    lottery_review,
    top_daily_recommendations,
)
from wcmodel.model import MatchContext, match_prediction
from wcmodel.simulate import simulate_tournament

CACHE_POLICY = {
    "html_ttl_seconds": 120,
    "public_json_ttl_seconds": 300,
    "static_asset_ttl_seconds": 604800,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _next_uncompleted_date(matches: List[Dict[str, object]], as_of_date: str) -> Optional[str]:
    dates = sorted({
        str(match["kickoff"])[:10]
        for match in matches
        if not match["completed"] and str(match["kickoff"])[:10] >= as_of_date
    })
    return dates[0] if dates else None


def prediction_for_fixture(seed_data: SeedData, fixture: Dict[str, object]) -> Dict[str, object]:
    home_id = str(fixture["home"])
    away_id = str(fixture["away"])
    match_id = str(fixture["match_id"])
    sale_snapshot = seed_data.lottery_sales.get(match_id, {})
    prediction = match_prediction(
        seed_data.teams[home_id],
        seed_data.teams[away_id],
        MatchContext(stage=str(fixture["stage"]), neutral=bool(fixture["neutral"]), as_of=seed_data.as_of),
        market_probs=seed_data.market_probs.get(str(fixture["match_id"])),
        market_max=0.25,
    )
    match = {
        "match_id": fixture["match_id"],
        "group": fixture["group"],
        "stage": fixture["stage"],
        "kickoff": fixture["kickoff"],
        "completed": fixture["completed"],
        "home": {
            "team_id": home_id,
            "name": seed_data.teams[home_id].name,
        },
        "away": {
            "team_id": away_id,
            "name": seed_data.teams[away_id].name,
        },
        "result": {
            "home_goals": fixture["home_goals"],
            "away_goals": fixture["away_goals"],
            "home_ht_goals": fixture.get("home_ht_goals"),
            "away_ht_goals": fixture.get("away_ht_goals"),
        }
        if fixture["completed"]
        else None,
        "prediction": prediction,
    }
    sale_markets = sale_snapshot.get("markets", {})
    official_handicap = sale_markets.get("rqspf", {}).get("handicap")
    match["handicap"] = int(official_handicap) if official_handicap is not None else handicap_for_match(match)
    match["lottery_meta"] = {
        "code": sale_snapshot.get("code"),
        "competition": sale_snapshot.get("competition"),
        "source": sale_snapshot.get("source"),
        "source_updated_at": sale_snapshot.get("source_updated_at"),
    }
    match["lottery"] = apply_lottery_sale(china_lottery_markets(match), sale_snapshot)
    if match["completed"]:
        match["lottery_review"] = lottery_review(match)
    if fixture.get("live_result"):
        match["live_result"] = fixture["live_result"]
    return match


def generate_public_data(
    seed_data: SeedData,
    output_dir: Path,
    n_sims: int = 5000,
    seed_value: int = 2026,
    live_result_report: Optional[Dict[str, object]] = None,
    live_lottery_report: Optional[Dict[str, object]] = None,
    **kwargs,
) -> Dict[str, object]:
    if "seed" in kwargs:
        seed_value = int(kwargs["seed"])
    if "live_result_report" in kwargs and live_result_report is None:
        live_result_report = kwargs["live_result_report"]

    generated_at = _now_iso()
    sim = simulate_tournament(seed_data, n_sims=n_sims, seed=seed_value)
    matches = [prediction_for_fixture(seed_data, fixture) for fixture in seed_data.fixtures]
    as_of_date = seed_data.as_of[:10]
    target_date = _next_uncompleted_date(matches, as_of_date) or as_of_date
    daily_matches = [
        match for match in matches
        if str(match["kickoff"])[:10] == target_date and not match["completed"]
    ]
    today_completed = [
        match for match in matches
        if str(match["kickoff"])[:10] == as_of_date and match["completed"]
    ]
    today_pending = [
        match for match in matches
        if str(match["kickoff"])[:10] == as_of_date and not match["completed"]
    ]
    today_status = "pending" if today_pending else "completed" if today_completed else "empty"
    target_label = "今日待赛" if target_date == as_of_date and daily_matches else "下一待赛日"

    files: List[str] = []
    status = {
        "model_version": MODEL_VERSION,
        "generated_at": generated_at,
        "data_available_at": seed_data.as_of,
        "mode": "offline_static_local_with_live_data" if live_result_report or live_lottery_report else "offline_static_local",
        "live_results": live_result_report,
        "live_lottery": live_lottery_report,
        "tracks": ["independent", "accuracy"],
        "cache_policy": CACHE_POLICY,
        "locked_results_applied": sim.locked_results_applied,
        "bracket_mode": sim.bracket_mode,
        "notes": [
            "Pages read precomputed JSON instead of triggering model runs.",
            "Market data only affects accuracy_probs; independent_probs remains market-free.",
        ],
    }
    payloads = {
        "model_status.json": status,
        "matches.json": {
            "generated_at": generated_at,
            "matches": matches,
        },
        "champion_probs.json": {
            "generated_at": generated_at,
            "n_sims": sim.n_sims,
            "bracket_mode": sim.bracket_mode,
            "champion_probs": sim.champion_probs,
        },
        "group_probs.json": {
            "generated_at": generated_at,
            "group_probs": sim.group_probs,
        },
        "daily_predictions.json": {
            "generated_at": generated_at,
            "as_of_date": as_of_date,
            "target_date": target_date,
            "target_label": target_label,
            "today_status": today_status,
            "today_completed": today_completed,
            "matches": daily_matches,
            "top_recommendations": top_daily_recommendations(matches, target_date=target_date, limit=3),
            "responsible_note": "模型价值候选仅用于研究复盘，不构成投注建议或收益承诺。",
        },
        "history.json": {
            "generated_at": generated_at,
            "history": historical_success(matches),
        },
    }

    for filename, payload in payloads.items():
        _write_json(output_dir / filename, payload)
        files.append(filename)
    return {"generated_at": generated_at, "files": sorted(files), "simulation": asdict(sim)}
