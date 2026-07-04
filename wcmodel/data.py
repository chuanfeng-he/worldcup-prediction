from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from wcmodel.model import TeamRating, decimal_odds_to_probs


@dataclass(frozen=True)
class SeedData:
    teams: Dict[str, TeamRating]
    groups: Dict[str, List[str]]
    fixtures: List[Dict[str, object]]
    market_probs: Dict[str, Dict[str, float]]
    lottery_sales: Dict[str, Dict[str, object]]
    as_of: str


TEAM_ROWS = [
    ("MEX", "墨西哥", 1825, 0.74, 245, True),
    ("RSA", "南非", 1520, -0.28, 88, False),
    ("KOR", "韩国", 1730, 0.44, 190, False),
    ("CZE", "捷克", 1570, 0.08, 170, False),
    ("CAN", "加拿大", 1700, 0.50, 210, True),
    ("QAT", "卡塔尔", 1630, -0.08, 105, False),
    ("SUI", "瑞士", 1825, 0.82, 355, False),
    ("BIH", "波黑", 1545, 0.02, 145, False),
    ("BRA", "巴西", 2045, 1.45, 920, False),
    ("MAR", "摩洛哥", 1840, 0.88, 360, False),
    ("HAI", "海地", 1380, -0.56, 42, False),
    ("SCO", "苏格兰", 1610, 0.15, 210, False),
    ("USA", "美国", 1830, 0.70, 310, True),
    ("PAR", "巴拉圭", 1595, 0.10, 130, False),
    ("AUS", "澳大利亚", 1735, 0.42, 160, False),
    ("TUR", "土耳其", 1765, 0.55, 335, False),
    ("GER", "德国", 1945, 1.12, 760, False),
    ("CUW", "库拉索", 1390, -0.48, 46, False),
    ("CIV", "科特迪瓦", 1655, 0.36, 260, False),
    ("ECU", "厄瓜多尔", 1760, 0.50, 220, False),
    ("NED", "荷兰", 1965, 1.20, 740, False),
    ("JPN", "日本", 1810, 0.78, 295, False),
    ("SWE", "瑞典", 1780, 0.62, 280, False),
    ("TUN", "突尼斯", 1655, 0.22, 115, False),
    ("ESP", "西班牙", 2055, 1.38, 930, False),
    ("CPV", "佛得角", 1450, -0.18, 62, False),
    ("KSA", "沙特阿拉伯", 1640, 0.02, 120, False),
    ("URU", "乌拉圭", 1875, 0.82, 390, False),
    ("BEL", "比利时", 1925, 0.95, 560, False),
    ("EGY", "埃及", 1620, 0.30, 220, False),
    ("IRN", "伊朗", 1720, 0.42, 150, False),
    ("NZL", "新西兰", 1495, -0.20, 58, False),
    ("FRA", "法国", 2065, 1.48, 1050, False),
    ("SEN", "塞内加尔", 1795, 0.65, 310, False),
    ("IRQ", "伊拉克", 1510, -0.12, 70, False),
    ("NOR", "挪威", 1815, 0.76, 440, False),
    ("ARG", "阿根廷", 2085, 1.52, 900, False),
    ("ALG", "阿尔及利亚", 1615, 0.28, 230, False),
    ("AUT", "奥地利", 1790, 0.64, 330, False),
    ("JOR", "约旦", 1420, -0.36, 48, False),
    ("ENG", "英格兰", 2000, 1.28, 980, False),
    ("CRO", "克罗地亚", 1870, 0.92, 375, False),
    ("GHA", "加纳", 1665, 0.34, 245, False),
    ("PAN", "巴拿马", 1480, -0.18, 72, False),
    ("POR", "葡萄牙", 1980, 1.26, 890, False),
    ("COD", "刚果民主共和国", 1540, 0.05, 150, False),
    ("UZB", "乌兹别克斯坦", 1515, -0.02, 82, False),
    ("COL", "哥伦比亚", 1890, 0.90, 420, False),
]


GROUPS = {
    "A": ["MEX", "RSA", "KOR", "CZE"],
    "B": ["CAN", "QAT", "SUI", "BIH"],
    "C": ["BRA", "MAR", "HAI", "SCO"],
    "D": ["USA", "PAR", "AUS", "TUR"],
    "E": ["GER", "CUW", "CIV", "ECU"],
    "F": ["NED", "JPN", "SWE", "TUN"],
    "G": ["ESP", "CPV", "KSA", "URU"],
    "H": ["BEL", "EGY", "IRN", "NZL"],
    "I": ["FRA", "SEN", "IRQ", "NOR"],
    "J": ["ARG", "ALG", "AUT", "JOR"],
    "K": ["ENG", "CRO", "GHA", "PAN"],
    "L": ["POR", "COD", "UZB", "COL"],
}


FIXTURE_ROWS = [
    ("R32-20260701-1", "32强", "32强", "BRA", "MAR", "2026-07-01T20:00:00+08:00", True, 2, 1, 1, 0),
    ("R32-20260701-2", "32强", "32强", "GER", "CUW", "2026-07-01T23:00:00+08:00", True, 3, 0, 1, 0),
    ("R32-20260702-1", "32强", "32强", "MEX", "CZE", "2026-07-02T20:00:00+08:00", True, 1, 1, 0, 1),
    ("R32-20260702-2", "32强", "32强", "BIH", "QAT", "2026-07-02T23:00:00+08:00", True, 2, 0, 1, 0),
    ("R32-20260703-1", "32强", "32强", "ESP", "AUT", "2026-07-03T20:00:00+08:00", True, 3, 0, 1, 0),
    ("R32-20260703-2", "32强", "32强", "POR", "CRO", "2026-07-03T23:00:00+08:00", True, 2, 1, 0, 0),
    ("R32-20260703-3", "32强", "32强", "SUI", "ALG", "2026-07-03T23:59:00+08:00", True, 2, 0, 1, 0),
    ("R16-20260704-1", "16强", "16强", "AUS", "EGY", "2026-07-04T02:00:00+08:00", False, None, None, None, None),
    ("R16-20260704-2", "16强", "16强", "ARG", "CPV", "2026-07-04T06:00:00+08:00", False, None, None, None, None),
    ("R16-20260704-3", "16强", "16强", "COL", "GHA", "2026-07-04T09:30:00+08:00", False, None, None, None, None),
]


def _fixtures() -> List[Dict[str, object]]:
    fixtures = []
    for match_id, group, stage, home, away, kickoff, completed, hg, ag, hhg, ahg in FIXTURE_ROWS:
        fixtures.append(
            {
                "match_id": match_id,
                "group": group,
                "stage": stage,
                "home": home,
                "away": away,
                "neutral": True,
                "kickoff": kickoff,
                "completed": completed,
                "home_goals": hg,
                "away_goals": ag,
                "home_ht_goals": hhg,
                "away_ht_goals": ahg,
                "available_at": kickoff,
            }
        )
    return fixtures


def _market_snapshots() -> Dict[str, Dict[str, float]]:
    return {
        "R32-20260701-1": decimal_odds_to_probs(1.90, 3.35, 4.10),
        "R32-20260701-2": decimal_odds_to_probs(1.30, 5.20, 10.50),
        "R32-20260702-1": decimal_odds_to_probs(2.05, 3.15, 3.95),
        "R32-20260702-2": decimal_odds_to_probs(2.20, 3.10, 3.55),
        "R32-20260703-1": decimal_odds_to_probs(1.52, 4.10, 6.80),
        "R32-20260703-2": decimal_odds_to_probs(2.02, 3.25, 3.92),
        "R32-20260703-3": decimal_odds_to_probs(1.82, 3.40, 4.75),
        "R16-20260704-1": decimal_odds_to_probs(2.35, 3.05, 3.25),
        "R16-20260704-2": decimal_odds_to_probs(1.28, 5.50, 12.00),
        "R16-20260704-3": decimal_odds_to_probs(1.88, 3.35, 4.45),
        "ESPN-760502": decimal_odds_to_probs(5.60, 3.58, 1.49),
    }


def _lottery_sales() -> Dict[str, Dict[str, object]]:
    return {
        "R16-20260704-1": {
            "code": "周五086",
            "competition": "世界杯",
            "source": "模拟试玩截图 2026-07-03 17:45",
            "markets": {
                "spf": {
                    "sale": True,
                    "handicap_label": "-",
                    "supports_single": True,
                    "supports_parlay": True,
                    "odds": {"主胜": 3.20, "平局": 2.76, "客胜": 2.20},
                },
                "rqspf": {
                    "sale": True,
                    "handicap": 1,
                    "handicap_label": "+1",
                    "supports_single": False,
                    "supports_parlay": True,
                    "odds": {"主胜": 1.52, "平局": 3.43, "客胜": 5.55},
                },
                "bf": {
                    "sale": True,
                    "supports_single": True,
                    "supports_parlay": True,
                    "odds": {
                        "1:0": 7.50, "2:0": 15.50, "2:1": 9.25, "3:0": 47.00,
                        "3:1": 35.00, "3:2": 55.00, "4:0": 200.00, "4:1": 150.00,
                        "4:2": 300.00, "5:0": 600.00, "5:1": 500.00, "5:2": 700.00,
                        "胜其他": 350.00, "0:0": 6.50, "1:1": 4.40, "2:2": 15.00,
                        "3:3": 90.00, "平其他": 600.00, "0:1": 6.10, "0:2": 10.00,
                        "1:2": 7.25, "0:3": 25.00, "1:3": 23.00, "2:3": 45.00,
                        "0:4": 80.00, "1:4": 90.00, "2:4": 175.00, "0:5": 350.00,
                        "1:5": 350.00, "2:5": 500.00, "负其他": 250.00,
                    },
                },
                "jqs": {
                    "sale": True,
                    "supports_single": True,
                    "supports_parlay": True,
                    "odds": {"0": 6.25, "1": 3.70, "2": 2.75, "3": 3.90, "4": 8.50, "5": 22.00, "6": 40.00, "7+": 65.00},
                },
                "bqc": {
                    "sale": True,
                    "supports_single": True,
                    "supports_parlay": True,
                    "odds": {
                        "主胜 / 主胜": 5.90, "主胜 / 平局": 13.00, "主胜 / 客胜": 24.00,
                        "平局 / 主胜": 7.00, "平局 / 平局": 3.90, "平局 / 客胜": 5.00,
                        "客胜 / 主胜": 25.00, "客胜 / 平局": 13.00, "客胜 / 客胜": 4.00,
                    },
                },
            },
        },
        "R16-20260704-2": {
            "code": "周五087",
            "competition": "世界杯",
            "source": "模拟试玩截图 2026-07-03 17:45",
            "markets": {
                "spf": {
                    "sale": False,
                    "handicap_label": "-",
                    "supports_single": False,
                    "supports_parlay": False,
                    "odds": {},
                },
                "rqspf": {
                    "sale": True,
                    "handicap": -2,
                    "handicap_label": "-2",
                    "supports_single": True,
                    "supports_parlay": True,
                    "odds": {"主胜": 2.06, "平局": 3.45, "客胜": 2.82},
                },
                "bf": {"sale": True, "supports_single": True, "supports_parlay": True, "odds": {}},
                "jqs": {"sale": True, "supports_single": True, "supports_parlay": True, "odds": {}},
                "bqc": {"sale": True, "supports_single": True, "supports_parlay": True, "odds": {}},
            },
        },
        "R16-20260704-3": {
            "code": "周五088",
            "competition": "世界杯",
            "source": "模拟试玩截图 2026-07-03 17:45",
            "markets": {
                "spf": {
                    "sale": True,
                    "handicap_label": "-",
                    "supports_single": True,
                    "supports_parlay": True,
                    "odds": {"主胜": 1.26, "平局": 4.50, "客胜": 8.80},
                },
                "rqspf": {
                    "sale": True,
                    "handicap": -1,
                    "handicap_label": "-1",
                    "supports_single": True,
                    "supports_parlay": True,
                    "odds": {"主胜": 2.17, "平局": 2.86, "客胜": 3.14},
                },
                "bf": {"sale": True, "supports_single": True, "supports_parlay": True, "odds": {}},
                "jqs": {"sale": True, "supports_single": True, "supports_parlay": True, "odds": {}},
                "bqc": {"sale": True, "supports_single": True, "supports_parlay": True, "odds": {}},
            },
        },
        "ESPN-760502": {
            "code": "周六089",
            "competition": "世界杯",
            "source": "用户提供体彩截图 2026-07-04",
            "markets": {
                "spf": {
                    "sale": True,
                    "handicap_label": "-",
                    "supports_single": True,
                    "supports_parlay": True,
                    "odds": {"主胜": 5.60, "平局": 3.58, "客胜": 1.49},
                },
                "rqspf": {
                    "sale": True,
                    "handicap": 1,
                    "handicap_label": "+1",
                    "supports_single": False,
                    "supports_parlay": True,
                    "odds": {"主胜": 2.22, "平局": 2.80, "客胜": 3.11},
                },
                "bf": {"sale": False, "supports_single": False, "supports_parlay": False, "odds": {}},
                "jqs": {"sale": False, "supports_single": False, "supports_parlay": False, "odds": {}},
                "bqc": {"sale": False, "supports_single": False, "supports_parlay": False, "odds": {}},
            },
        },
        "ESPN-760503": {
            "code": "周六090",
            "competition": "世界杯",
            "source": "用户提供体彩截图 2026-07-04",
            "markets": {
                "spf": {
                    "sale": False,
                    "handicap_label": "-",
                    "supports_single": False,
                    "supports_parlay": False,
                    "odds": {},
                },
                "rqspf": {
                    "sale": True,
                    "handicap": 2,
                    "handicap_label": "+2",
                    "supports_single": True,
                    "supports_parlay": True,
                    "odds": {"主胜": 2.35, "平局": 3.33, "客胜": 2.48},
                },
                "bf": {"sale": False, "supports_single": False, "supports_parlay": False, "odds": {}},
                "jqs": {"sale": False, "supports_single": False, "supports_parlay": False, "odds": {}},
                "bqc": {"sale": False, "supports_single": False, "supports_parlay": False, "odds": {}},
            },
        },
    }


def load_seed_data() -> SeedData:
    teams = {
        team_id: TeamRating(team_id, name, elo, structural, squad_value, host)
        for team_id, name, elo, structural, squad_value, host in TEAM_ROWS
    }
    return SeedData(
        teams=teams,
        groups=GROUPS,
        fixtures=_fixtures(),
        market_probs=_market_snapshots(),
        lottery_sales=_lottery_sales(),
        as_of="2026-07-03T23:59:59+08:00",
    )
