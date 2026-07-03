from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_index_uses_cache_busted_frontend_assets():
    html = (ROOT / "web" / "index.html").read_text()

    assert "<title>绿茵神噜</title>" in html
    assert 'data-i18n="appName">绿茵神噜</h1>' in html
    assert '/assets/styles.css?v=' in html
    assert '/assets/app.js?v=' in html
    assert '/assets/football-terminal.svg?v=' in html


def test_frontend_exposes_chinese_english_language_switch():
    html = (ROOT / "web" / "index.html").read_text()
    app = (ROOT / "web" / "assets" / "app.js").read_text()

    assert 'data-lang="zh"' in html
    assert 'data-lang="en"' in html
    assert "const i18n" in app
    assert "function applyLanguage" in app
    assert 'localStorage.setItem("wc26-lang"' in app
    assert "teamNamesEn" in app


def test_index_no_longer_renders_round16_schedule_panel():
    html = (ROOT / "web" / "index.html").read_text()

    assert "16强赛程" not in html
    assert "round16Grid" not in html
    assert "round16-panel" not in html


def test_frontend_assets_include_side_mascot_decoration():
    styles = (ROOT / "web" / "assets" / "styles.css").read_text()
    mascot = ROOT / "web" / "assets" / "mascot-kicker.png"

    assert mascot.exists()
    assert "mascot-kicker.png?v=" in styles
    assert "body::before" in styles
    assert "body::after" in styles


def test_pending_prediction_cards_render_all_lottery_market_picks():
    app = (ROOT / "web" / "assets" / "app.js").read_text()

    assert "renderPredictionMarket(match, key)" in app
    assert "待赛玩法预测" in app
    assert "marketOrder.map((key) => renderPredictionMarket(match, key)).join" in app


def test_frontend_tolerates_stale_shell_without_optional_summary_nodes():
    app = (ROOT / "web" / "assets" / "app.js").read_text()

    assert 'const matchCount = $("#slipMatchCount");' in app
    assert "if (matchCount)" in app
