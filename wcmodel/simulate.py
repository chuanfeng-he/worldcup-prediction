from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

from wcmodel.data import SeedData
from wcmodel.model import MatchContext, TeamRating, match_prediction, normalize_probs, team_strength


@dataclass(frozen=True)
class SimulationResult:
    champion_probs: Dict[str, float]
    group_probs: Dict[str, Dict[str, float]]
    locked_results_applied: int
    n_sims: int
    bracket_mode: str


def _empty_row() -> Dict[str, int]:
    return {"pts": 0, "gf": 0, "ga": 0, "wins": 0}


def _apply_score(row_home: Dict[str, int], row_away: Dict[str, int], home_goals: int, away_goals: int) -> None:
    row_home["gf"] += home_goals
    row_home["ga"] += away_goals
    row_away["gf"] += away_goals
    row_away["ga"] += home_goals
    if home_goals > away_goals:
        row_home["pts"] += 3
        row_home["wins"] += 1
    elif home_goals < away_goals:
        row_away["pts"] += 3
        row_away["wins"] += 1
    else:
        row_home["pts"] += 1
        row_away["pts"] += 1


def _ranking_key(team_id: str, row: Dict[str, int], team: TeamRating) -> Tuple[int, int, int, float]:
    return (row["pts"], row["gf"] - row["ga"], row["gf"], team_strength(team))


def _sample_group_score(
    rng: random.Random,
    probs: Dict[str, float],
) -> Tuple[int, int]:
    draw_cut = probs["home"] + probs["draw"]
    roll = rng.random()
    if roll < probs["home"]:
        return 2, 1
    if roll < draw_cut:
        return 1, 1
    return 1, 2


def _simulate_group(
    seed_data: SeedData,
    group: str,
    rng: random.Random,
    group_prob_cache: Dict[str, Dict[str, float]],
) -> List[str]:
    standings = {team_id: _empty_row() for team_id in seed_data.groups[group]}
    fixtures = [fixture for fixture in seed_data.fixtures if fixture["group"] == group]
    for fixture in fixtures:
        home_id = str(fixture["home"])
        away_id = str(fixture["away"])
        if fixture["completed"]:
            home_goals = int(fixture["home_goals"])
            away_goals = int(fixture["away_goals"])
        else:
            home_goals, away_goals = _sample_group_score(rng, group_prob_cache[str(fixture["match_id"])])
        _apply_score(standings[home_id], standings[away_id], home_goals, away_goals)
    return sorted(
        standings,
        key=lambda team_id: _ranking_key(team_id, standings[team_id], seed_data.teams[team_id]),
        reverse=True,
    )


def _knockout_probs(home: TeamRating, away: TeamRating, seed_data: SeedData) -> Dict[str, float]:
    raw = match_prediction(
        home,
        away,
        MatchContext(stage="knockout", neutral=True, as_of=seed_data.as_of),
        market_probs=None,
    )["accuracy_probs"]
    probs = normalize_probs(raw)
    strength_home = team_strength(home)
    strength_away = team_strength(away)
    home_shootout_share = 1.0 / (1.0 + 10.0 ** ((strength_away - strength_home) / 2.0))
    return normalize_probs(
        {
            "home": probs["home"] + probs["draw"] * home_shootout_share,
            "draw": 0.0,
            "away": probs["away"] + probs["draw"] * (1.0 - home_shootout_share),
        }
    )


def _play_knockout_round(
    team_ids: List[str],
    seed_data: SeedData,
    rng: random.Random,
    knockout_cache: Dict[Tuple[str, str], Dict[str, float]],
) -> List[str]:
    winners: List[str] = []
    for i in range(0, len(team_ids), 2):
        home_id = team_ids[i]
        away_id = team_ids[i + 1]
        key = (home_id, away_id)
        if key not in knockout_cache:
            knockout_cache[key] = _knockout_probs(seed_data.teams[home_id], seed_data.teams[away_id], seed_data)
        probs = knockout_cache[key]
        winners.append(home_id if rng.random() < probs["home"] else away_id)
    return winners


def _make_seeded_bracket(qualified: List[str], seed_data: SeedData) -> List[str]:
    ranked = sorted(qualified, key=lambda team_id: team_strength(seed_data.teams[team_id]), reverse=True)
    bracket: List[str] = []
    for i in range(len(ranked) // 2):
        bracket.extend([ranked[i], ranked[-(i + 1)]])
    return bracket


def simulate_tournament(seed_data: SeedData, n_sims: int = 5000, seed: int = 2026) -> SimulationResult:
    rng = random.Random(seed)
    champion_counts = {team.name: 0 for team in seed_data.teams.values()}
    r32_counts = {team.name: 0 for team in seed_data.teams.values()}
    locked_results = sum(1 for fixture in seed_data.fixtures if fixture["completed"])
    group_prob_cache = {
        str(fixture["match_id"]): match_prediction(
            seed_data.teams[str(fixture["home"])],
            seed_data.teams[str(fixture["away"])],
            MatchContext(stage="group", neutral=bool(fixture["neutral"]), as_of=seed_data.as_of),
            market_probs=seed_data.market_probs.get(str(fixture["match_id"])),
            market_max=0.25,
        )["accuracy_probs"]
        for fixture in seed_data.fixtures
        if not fixture["completed"]
    }
    knockout_cache: Dict[Tuple[str, str], Dict[str, float]] = {}

    for _ in range(n_sims):
        top_two: List[str] = []
        thirds: List[str] = []
        for group in sorted(seed_data.groups):
            ranking = _simulate_group(seed_data, group, rng, group_prob_cache)
            top_two.extend(ranking[:2])
            thirds.append(ranking[2])

        best_thirds = sorted(thirds, key=lambda team_id: team_strength(seed_data.teams[team_id]), reverse=True)[:8]
        qualified = top_two + best_thirds
        for team_id in qualified:
            r32_counts[seed_data.teams[team_id].name] += 1

        alive = _make_seeded_bracket(qualified, seed_data)
        while len(alive) > 1:
            alive = _play_knockout_round(alive, seed_data, rng, knockout_cache)
        champion_counts[seed_data.teams[alive[0]].name] += 1

    return SimulationResult(
        champion_probs={team: count / n_sims for team, count in sorted(champion_counts.items())},
        group_probs={
            team: {"round_of_32": count / n_sims}
            for team, count in sorted(r32_counts.items())
        },
        locked_results_applied=locked_results,
        n_sims=n_sims,
        bracket_mode="seeded_approximation_v1",
    )
