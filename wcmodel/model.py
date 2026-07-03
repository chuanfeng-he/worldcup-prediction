from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Optional

from wcmodel import MODEL_VERSION

OUTCOMES = ("home", "draw", "away")


@dataclass(frozen=True)
class TeamRating:
    team_id: str
    name: str
    elo: float
    structural: float
    squad_value_eur_m: float
    host: bool = False


@dataclass(frozen=True)
class MatchContext:
    stage: str
    neutral: bool
    as_of: str
    home_advantage_goals: float = 0.18


def normalize_probs(probs: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(0.0, probs.get(outcome, 0.0)) for outcome in OUTCOMES)
    if total <= 0.0:
        return {outcome: 1.0 / 3.0 for outcome in OUTCOMES}
    return {outcome: max(0.0, probs.get(outcome, 0.0)) / total for outcome in OUTCOMES}


def poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0.0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def dixon_coles_tau(home_goals: int, away_goals: int, lambda_home: float, lambda_away: float, rho: float) -> float:
    if home_goals == 0 and away_goals == 0:
        return 1.0 - lambda_home * lambda_away * rho
    if home_goals == 0 and away_goals == 1:
        return 1.0 + lambda_home * rho
    if home_goals == 1 and away_goals == 0:
        return 1.0 + lambda_away * rho
    if home_goals == 1 and away_goals == 1:
        return 1.0 - rho
    return 1.0


def poisson_1x2(lambda_home: float, lambda_away: float, rho: float = -0.08, max_goals: int = 10) -> Dict[str, float]:
    probs = {"home": 0.0, "draw": 0.0, "away": 0.0}
    for home_goals in range(max_goals + 1):
        home_p = poisson_pmf(home_goals, lambda_home)
        for away_goals in range(max_goals + 1):
            tau = dixon_coles_tau(home_goals, away_goals, lambda_home, lambda_away, rho)
            p = max(0.0, home_p * poisson_pmf(away_goals, lambda_away) * tau)
            if home_goals > away_goals:
                probs["home"] += p
            elif home_goals < away_goals:
                probs["away"] += p
            else:
                probs["draw"] += p
    return normalize_probs(probs)


def decimal_odds_to_probs(home: float, draw: float, away: float) -> Dict[str, float]:
    if min(home, draw, away) <= 1.0:
        raise ValueError("decimal odds must be greater than 1.0")
    raw = {"home": 1.0 / home, "draw": 1.0 / draw, "away": 1.0 / away}
    return normalize_probs(raw)


def blend_with_market(independent: Dict[str, float], market: Dict[str, float], market_max: float) -> Dict[str, float]:
    weight = min(max(market_max, 0.0), 1.0)
    independent_n = normalize_probs(independent)
    market_n = normalize_probs(market)
    return normalize_probs(
        {
            outcome: independent_n[outcome] * (1.0 - weight) + market_n[outcome] * weight
            for outcome in OUTCOMES
        }
    )


def team_strength(team: TeamRating) -> float:
    elo_component = (team.elo - 1700.0) / 400.0
    squad_component = 0.18 * math.log10(max(team.squad_value_eur_m, 25.0) / 250.0)
    host_component = 0.12 if team.host else 0.0
    return 0.62 * elo_component + 0.30 * team.structural + squad_component + host_component


def expected_goals(home: TeamRating, away: TeamRating, context: MatchContext) -> Dict[str, float]:
    home_strength = team_strength(home)
    away_strength = team_strength(away)
    advantage = 0.0 if context.neutral else context.home_advantage_goals
    if home.host:
        advantage += 0.10
    if away.host:
        advantage -= 0.05
    diff = home_strength - away_strength
    base = 1.28
    return {
        "home": min(3.6, max(0.25, base + 0.42 * diff + advantage)),
        "away": min(3.6, max(0.25, base - 0.42 * diff - advantage * 0.45)),
    }


def match_prediction(
    home: TeamRating,
    away: TeamRating,
    context: MatchContext,
    market_probs: Optional[Dict[str, float]] = None,
    market_max: float = 0.25,
) -> Dict[str, object]:
    lambdas = expected_goals(home, away, context)
    independent = poisson_1x2(lambdas["home"], lambdas["away"], rho=-0.08)
    accuracy = blend_with_market(independent, market_probs, market_max) if market_probs else independent
    return {
        "model_version": MODEL_VERSION,
        "home_team": home.name,
        "away_team": away.name,
        "context": {
            "stage": context.stage,
            "neutral": context.neutral,
            "as_of": context.as_of,
        },
        "expected_goals": lambdas,
        "independent_probs": independent,
        "accuracy_probs": accuracy,
        "components": {
            "poisson_dc": independent,
            "market": market_probs,
        },
    }
