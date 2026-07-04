from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple

from wcmodel.model import OUTCOMES, dixon_coles_tau, normalize_probs, poisson_pmf

RESULT_LABELS = {"home": "主胜", "draw": "平局", "away": "客胜"}
RESULT_CODES = {"home": "3", "draw": "1", "away": "0"}
HALF_FULL_CODES = {
    ("home", "home"): "33",
    ("home", "draw"): "31",
    ("home", "away"): "30",
    ("draw", "home"): "13",
    ("draw", "draw"): "11",
    ("draw", "away"): "10",
    ("away", "home"): "03",
    ("away", "draw"): "01",
    ("away", "away"): "00",
}
RISK_WEIGHT = {
    "spf": 1.00,
    "rqspf": 0.94,
    "jqs": 0.78,
    "bqc": 0.58,
    "bf": 0.42,
}


def score_matrix(lambda_home: float, lambda_away: float, rho: float = -0.08, max_goals: int = 10) -> Dict[Tuple[int, int], float]:
    matrix: Dict[Tuple[int, int], float] = {}
    for home_goals in range(max_goals + 1):
        home_p = poisson_pmf(home_goals, lambda_home)
        for away_goals in range(max_goals + 1):
            tau = dixon_coles_tau(home_goals, away_goals, lambda_home, lambda_away, rho)
            matrix[(home_goals, away_goals)] = max(0.0, home_p * poisson_pmf(away_goals, lambda_away) * tau)
    total = sum(matrix.values())
    return {score: value / total for score, value in matrix.items()}


def _result(home_goals: int, away_goals: int) -> str:
    if home_goals > away_goals:
        return "home"
    if home_goals < away_goals:
        return "away"
    return "draw"


def _option(code: str, label: str, prob: float) -> Dict[str, object]:
    fair_odds = round(1.0 / max(prob, 0.0001), 2)
    return {"code": code, "label": label, "prob": prob, "fair_odds": fair_odds}


def _with_pick(name: str, options: List[Dict[str, object]], **extra: object) -> Dict[str, object]:
    ranked = sorted(options, key=lambda item: float(item["prob"]), reverse=True)
    payload = {"name": name, "options": options, "pick": ranked[0]}
    payload.update(extra)
    return payload


def _spf_options(probs: Dict[str, float]) -> List[Dict[str, object]]:
    return [
        _option(RESULT_CODES[outcome], RESULT_LABELS[outcome], probs[outcome])
        for outcome in OUTCOMES
    ]


def _rqspf_options(matrix: Dict[Tuple[int, int], float], handicap: int) -> List[Dict[str, object]]:
    aggregate = {outcome: 0.0 for outcome in OUTCOMES}
    for (home_goals, away_goals), prob in matrix.items():
        aggregate[_result(home_goals + handicap, away_goals)] += prob
    probs = normalize_probs(aggregate)
    return _spf_options(probs)


def _bf_options(matrix: Dict[Tuple[int, int], float]) -> List[Dict[str, object]]:
    exact_scores = [
        (1, 0), (2, 0), (2, 1), (3, 0), (3, 1), (3, 2),
        (4, 0), (4, 1), (4, 2), (5, 0), (5, 1), (5, 2),
        (0, 0), (1, 1), (2, 2), (3, 3),
        (0, 1), (0, 2), (1, 2), (0, 3), (1, 3), (2, 3),
        (0, 4), (1, 4), (2, 4), (0, 5), (1, 5), (2, 5),
    ]
    exact_set = set(exact_scores)
    aggregate = {f"{home}:{away}": 0.0 for home, away in exact_scores}
    aggregate.update({"胜其他": 0.0, "平其他": 0.0, "负其他": 0.0})

    for (home_goals, away_goals), prob in matrix.items():
        if (home_goals, away_goals) in exact_set:
            aggregate[f"{home_goals}:{away_goals}"] += prob
        elif home_goals > away_goals:
            aggregate["胜其他"] += prob
        elif home_goals == away_goals:
            aggregate["平其他"] += prob
        else:
            aggregate["负其他"] += prob

    return [
        _option(code, code, aggregate[code])
        for code in [*(f"{home}:{away}" for home, away in exact_scores[:12]), "胜其他",
                     *(f"{home}:{away}" for home, away in exact_scores[12:16]), "平其他",
                     *(f"{home}:{away}" for home, away in exact_scores[16:]), "负其他"]
    ]


def _jqs_options(matrix: Dict[Tuple[int, int], float]) -> List[Dict[str, object]]:
    aggregate = {str(i): 0.0 for i in range(7)}
    aggregate["7+"] = 0.0
    for (home_goals, away_goals), prob in matrix.items():
        total = home_goals + away_goals
        aggregate[str(total) if total < 7 else "7+"] += prob
    return [_option(code, code, prob) for code, prob in aggregate.items()]


def _bqc_options(lambda_home: float, lambda_away: float) -> List[Dict[str, object]]:
    half = score_matrix(lambda_home * 0.45, lambda_away * 0.45, rho=-0.05, max_goals=6)
    second = score_matrix(lambda_home * 0.55, lambda_away * 0.55, rho=-0.04, max_goals=7)
    aggregate = {key: 0.0 for key in HALF_FULL_CODES}
    for (half_home, half_away), half_prob in half.items():
        half_result = _result(half_home, half_away)
        for (second_home, second_away), second_prob in second.items():
            full_result = _result(half_home + second_home, half_away + second_away)
            aggregate[(half_result, full_result)] += half_prob * second_prob
    return [
        _option(code, f"{RESULT_LABELS[half]} / {RESULT_LABELS[full]}", prob)
        for (half, full), code in HALF_FULL_CODES.items()
        for prob in [aggregate[(half, full)]]
    ]


def handicap_for_match(match: Dict[str, object]) -> int:
    probs = match["prediction"]["accuracy_probs"]
    if probs["home"] >= 0.58:
        return -1
    if probs["away"] >= 0.58:
        return 1
    return 0


def china_lottery_markets(match: Dict[str, object]) -> Dict[str, Dict[str, object]]:
    expected = match["prediction"]["expected_goals"]
    matrix = score_matrix(expected["home"], expected["away"], rho=-0.08)
    handicap = int(match.get("handicap", handicap_for_match(match)))
    markets = {
        "spf": _with_pick("胜平负", _spf_options(match["prediction"]["accuracy_probs"]), code="SPF"),
        "rqspf": _with_pick("让球胜平负", _rqspf_options(matrix, handicap), code="RQSPF", handicap=handicap),
        "bf": _with_pick("比分", _bf_options(matrix), code="BF"),
        "jqs": _with_pick("总进球", _jqs_options(matrix), code="JQS"),
        "bqc": _with_pick("半全场", _bqc_options(expected["home"], expected["away"]), code="BQC"),
    }
    return markets


def _actual_spf(match: Dict[str, object]) -> Optional[str]:
    result = match.get("result")
    if not result:
        return None
    return RESULT_LABELS[_result(int(result["home_goals"]), int(result["away_goals"]))]


def _actual_rqspf(match: Dict[str, object]) -> Optional[str]:
    result = match.get("result")
    if not result:
        return None
    handicap = int(match.get("handicap", handicap_for_match(match)))
    return RESULT_LABELS[_result(int(result["home_goals"]) + handicap, int(result["away_goals"]))]


def _actual_bf(match: Dict[str, object]) -> Optional[str]:
    result = match.get("result")
    if not result:
        return None
    return f"{int(result['home_goals'])}:{int(result['away_goals'])}"


def _actual_jqs(match: Dict[str, object]) -> Optional[str]:
    result = match.get("result")
    if not result:
        return None
    total = int(result["home_goals"]) + int(result["away_goals"])
    return str(total) if total < 7 else "7+"


def _actual_bqc(match: Dict[str, object]) -> Optional[str]:
    result = match.get("result")
    if not result or result.get("home_ht_goals") is None or result.get("away_ht_goals") is None:
        return None
    half = _result(int(result["home_ht_goals"]), int(result["away_ht_goals"]))
    full = _result(int(result["home_goals"]), int(result["away_goals"]))
    return f"{RESULT_LABELS[half]} / {RESULT_LABELS[full]}"


ACTUAL_BY_MARKET = {
    "spf": _actual_spf,
    "rqspf": _actual_rqspf,
    "bf": _actual_bf,
    "jqs": _actual_jqs,
    "bqc": _actual_bqc,
}


def apply_lottery_sale(markets: Dict[str, Dict[str, object]], sale: Dict[str, object]) -> Dict[str, Dict[str, object]]:
    sale_markets = sale.get("markets", {}) if sale else {}
    for key, market in markets.items():
        config = sale_markets.get(key)
        if not config:
            market["sale"] = False
            market["supports_single"] = False
            market["supports_parlay"] = False
            continue
        market["sale"] = bool(config.get("sale", False))
        market["supports_single"] = bool(config.get("supports_single", False))
        market["supports_parlay"] = bool(config.get("supports_parlay", False))
        if "handicap_label" in config:
            market["handicap_label"] = config["handicap_label"]
        odds = config.get("odds", {})
        for option in market.get("options", []):
            listed = odds.get(option["label"], odds.get(option["code"]))
            if listed is not None:
                option["listed_odds"] = float(listed)
        pick_code = market.get("pick", {}).get("code")
        for option in market.get("options", []):
            if option.get("code") == pick_code:
                market["pick"] = option
                break
    return markets


def lottery_review(match: Dict[str, object]) -> Dict[str, Dict[str, object]]:
    predictions = match.get("lottery") or china_lottery_markets(match)
    review: Dict[str, Dict[str, object]] = {}
    for key, actual_fn in ACTUAL_BY_MARKET.items():
        market = predictions[key]
        pick = market["pick"]
        actual = actual_fn(match)
        review[key] = {
            "name": market["name"],
            "prediction": pick["label"],
            "prediction_prob": pick["prob"],
            "actual": actual,
            "hit": actual is not None and pick["label"] == actual,
            "settled": actual is not None,
        }
    return review


def top_daily_recommendations(matches: Iterable[Dict[str, object]], target_date: str, limit: int = 3) -> List[Dict[str, object]]:
    candidates: List[Dict[str, object]] = []
    for match in matches:
        if str(match["kickoff"])[:10] != target_date or match["completed"]:
            continue
        markets = match.get("lottery") or china_lottery_markets(match)
        for key, market in markets.items():
            if not market.get("sale"):
                continue
            pick = market["pick"]
            score = float(pick["prob"]) * RISK_WEIGHT[key]
            candidates.append(
                {
                    "match_id": match["match_id"],
                    "date": str(match["kickoff"])[:10],
                    "completed": match["completed"],
                    "home": match["home"]["name"],
                    "away": match["away"]["name"],
                    "market_key": key,
                    "market": market["name"],
                    "selection": pick["label"],
                    "prob": pick["prob"],
                    "model_score": round(score, 6),
                    "risk": "低" if score >= 0.45 else "中" if score >= 0.28 else "高",
                    "reason": "概率集中度最高" if key in {"spf", "rqspf"} else "衍生玩法中排序靠前",
                }
            )
    return sorted(candidates, key=lambda item: item["model_score"], reverse=True)[:limit]


def historical_success(matches: Iterable[Dict[str, object]]) -> Dict[str, object]:
    rows = [match for match in matches if match.get("completed")]
    markets = {
        key: {"hit": 0, "settled": 0, "hit_rate": 0.0}
        for key in ("spf", "rqspf", "bf", "jqs", "bqc")
    }
    for match in rows:
        predictions = match.get("lottery") or china_lottery_markets(match)
        for key, actual_fn in ACTUAL_BY_MARKET.items():
            actual = actual_fn(match)
            if actual is None:
                continue
            markets[key]["settled"] += 1
            if predictions[key]["pick"]["label"] == actual:
                markets[key]["hit"] += 1
    for item in markets.values():
        if item["settled"]:
            item["hit_rate"] = item["hit"] / item["settled"]
    return {"sample_size": len(rows), "markets": markets}


def estimate_slip(selections: Iterable[Dict[str, float]], stake: float) -> Dict[str, float]:
    selected = list(selections)
    if stake < 0:
        raise ValueError("stake must be non-negative")

    groups: Dict[str, List[Dict[str, float]]] = {}
    for index, selection in enumerate(selected):
        group_key = str(selection.get("match_id") or f"selection-{index}")
        groups.setdefault(group_key, []).append(
            {
                "prob": min(max(float(selection["prob"]), 0.0), 1.0),
                "odds": max(float(selection["odds"]), 1.0),
            }
        )

    hit_probability = 0.0
    combination_count = 0
    max_combined_odds = 0.0
    expected_payout = 0.0
    if groups:
        hit_probability = 1.0
        combination_count = 1
        for options in groups.values():
            hit_probability *= min(sum(option["prob"] for option in options), 1.0)
            combination_count *= len(options)

        combinations = [({"prob": 1.0, "odds": 1.0})]
        for options in groups.values():
            combinations = [
                {"prob": combo["prob"] * option["prob"], "odds": combo["odds"] * option["odds"]}
                for combo in combinations
                for option in options
            ]
        max_combined_odds = max((combo["odds"] for combo in combinations), default=0.0)
        expected_payout = sum(combo["prob"] * stake * combo["odds"] for combo in combinations)

    total_stake = stake * combination_count if selected else 0.0
    max_payout_if_hit = stake * max_combined_odds if selected else 0.0
    expected_return = expected_payout - total_stake if selected else 0.0
    return {
        "selection_count": len(selected),
        "match_count": len(groups),
        "combination_count": combination_count,
        "hit_probability": hit_probability,
        "combined_odds": max_combined_odds,
        "stake": stake,
        "total_stake": total_stake,
        "max_payout_if_hit": max_payout_if_hit,
        "payout_if_hit": max_payout_if_hit,
        "expected_payout": expected_payout,
        "expected_return": expected_return,
        "expected_roi": expected_return / total_stake if total_stake > 0 else 0.0,
    }
