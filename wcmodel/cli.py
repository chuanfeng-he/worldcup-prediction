from __future__ import annotations

import argparse
import json
import shutil
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional, Sequence

from wcmodel.data import load_seed_data
from wcmodel.live_results import apply_live_results
from wcmodel.model import MatchContext, match_prediction
from wcmodel.pipeline import generate_public_data
from wcmodel.sporttery_lottery import apply_sporttery_lottery

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = PROJECT_ROOT / "web"
PUBLIC_ROOT = PROJECT_ROOT / "public"


def _copy_web_assets(public_root: Path) -> None:
    public_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(WEB_ROOT, public_root, dirs_exist_ok=True)


def generate(args: argparse.Namespace) -> None:
    seed = load_seed_data()
    live_result_report = None
    live_lottery_report = None
    live_results = getattr(args, "live_results", "none")
    if live_results == "espn":
        seed, live_result_report = apply_live_results(seed)
    live_lottery = getattr(args, "live_lottery", "none")
    if live_lottery == "sporttery":
        seed, live_lottery_report = apply_sporttery_lottery(seed)
    _copy_web_assets(PUBLIC_ROOT)
    data_dir = PUBLIC_ROOT / "data"
    summary = generate_public_data(
        seed,
        data_dir,
        n_sims=args.sims,
        seed_value=args.seed,
        live_result_report=live_result_report,
        live_lottery_report=live_lottery_report,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


def predict(args: argparse.Namespace) -> None:
    seed = load_seed_data()
    teams_by_name = {team.name.lower(): team for team in seed.teams.values()}
    try:
        home = teams_by_name[args.home.lower()]
        away = teams_by_name[args.away.lower()]
    except KeyError as exc:
        raise SystemExit(f"unknown team: {exc.args[0]}") from exc
    payload = match_prediction(
        home,
        away,
        MatchContext(stage=args.stage, neutral=args.neutral, as_of=seed.as_of),
        market_probs=None,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def serve(args: argparse.Namespace) -> None:
    if not (PUBLIC_ROOT / "index.html").exists():
        generate(argparse.Namespace(sims=args.sims, seed=args.seed, live_results=args.live_results, live_lottery=args.live_lottery))
    handler = partial(SimpleHTTPRequestHandler, directory=str(PUBLIC_ROOT))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving http://{args.host}:{args.port} from {PUBLIC_ROOT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wcmodel", description="Offline-first World Cup forecast worker")
    sub = parser.add_subparsers(dest="command", required=True)

    generate_cmd = sub.add_parser("generate", help="Generate static JSON and copy web assets")
    generate_cmd.add_argument("--sims", type=int, default=5000)
    generate_cmd.add_argument("--seed", type=int, default=2026)
    generate_cmd.add_argument("--live-results", choices=("none", "espn"), default="none")
    generate_cmd.add_argument("--live-lottery", choices=("none", "sporttery"), default="none")
    generate_cmd.set_defaults(func=generate)

    predict_cmd = sub.add_parser("predict-match", help="Predict a single match by team name")
    predict_cmd.add_argument("--home", required=True)
    predict_cmd.add_argument("--away", required=True)
    predict_cmd.add_argument("--stage", default="group")
    predict_cmd.add_argument("--neutral", action="store_true")
    predict_cmd.set_defaults(func=predict)

    serve_cmd = sub.add_parser("serve", help="Serve the generated static site locally")
    serve_cmd.add_argument("--host", default="127.0.0.1")
    serve_cmd.add_argument("--port", type=int, default=8080)
    serve_cmd.add_argument("--sims", type=int, default=2000)
    serve_cmd.add_argument("--seed", type=int, default=2026)
    serve_cmd.add_argument("--live-results", choices=("none", "espn"), default="none")
    serve_cmd.add_argument("--live-lottery", choices=("none", "sporttery"), default="none")
    serve_cmd.set_defaults(func=serve)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
