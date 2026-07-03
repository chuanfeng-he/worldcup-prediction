const state = {
  lang: localStorage.getItem("wc26-lang") === "en" ? "en" : "zh",
  track: "accuracy",
  status: null,
  matches: [],
  daily: null,
  champion: null,
  history: null,
  query: "",
  selections: new Map(),
  slipMatchId: "",
  slipMarketKey: "spf",
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

const marketOrder = ["spf", "rqspf", "bf", "jqs", "bqc"];
const marketShort = {
  zh: {
    spf: "胜平负",
    rqspf: "让球",
    bf: "比分",
    jqs: "总进球",
    bqc: "半全",
  },
  en: {
    spf: "1X2",
    rqspf: "Handicap",
    bf: "Score",
    jqs: "Goals",
    bqc: "HT/FT",
  },
};

const marketNames = {
  zh: {
    spf: "胜平负",
    rqspf: "让球胜平负",
    bf: "比分",
    jqs: "总进球",
    bqc: "半全场",
  },
  en: {
    spf: "1X2",
    rqspf: "Handicap 1X2",
    bf: "Correct score",
    jqs: "Total goals",
    bqc: "Half-time / full-time",
  },
};

const outcomeLabels = {
  home: "主胜",
  draw: "平局",
  away: "客胜",
};

const outcomeCodes = {
  home: "3",
  draw: "1",
  away: "0",
};

const trackMeta = {
  accuracy: {
    zhTitle: "综合轨",
    enTitle: "Blended Track",
    zhDesc: "独立模型先给出基础概率，再用市场快照做有限校准；更适合看临场综合判断。",
    enDesc: "Starts from the independent model, then applies a bounded calibration from market snapshots for a match-day view.",
  },
  independent: {
    zhTitle: "独立轨",
    enTitle: "Independent Track",
    zhDesc: "只使用 Elo、阵容强度、主客和进球分布，不读取市场概率；更适合看模型原始判断。",
    enDesc: "Uses Elo, squad strength, home/away context and goal distribution only, without market probabilities.",
  },
};

const flags = {
  MEX: "🇲🇽",
  RSA: "🇿🇦",
  KOR: "🇰🇷",
  CZE: "🇨🇿",
  CAN: "🇨🇦",
  QAT: "🇶🇦",
  SUI: "🇨🇭",
  BIH: "🇧🇦",
  BRA: "🇧🇷",
  MAR: "🇲🇦",
  HAI: "🇭🇹",
  SCO: "🏴",
  USA: "🇺🇸",
  PAR: "🇵🇾",
  AUS: "🇦🇺",
  TUR: "🇹🇷",
  GER: "🇩🇪",
  CUW: "🇨🇼",
  CIV: "🇨🇮",
  ECU: "🇪🇨",
  NED: "🇳🇱",
  JPN: "🇯🇵",
  SWE: "🇸🇪",
  TUN: "🇹🇳",
  ESP: "🇪🇸",
  CPV: "🇨🇻",
  KSA: "🇸🇦",
  URU: "🇺🇾",
  BEL: "🇧🇪",
  EGY: "🇪🇬",
  IRN: "🇮🇷",
  NZL: "🇳🇿",
  FRA: "🇫🇷",
  SEN: "🇸🇳",
  IRQ: "🇮🇶",
  NOR: "🇳🇴",
  ARG: "🇦🇷",
  ALG: "🇩🇿",
  AUT: "🇦🇹",
  JOR: "🇯🇴",
  ENG: "🏴",
  CRO: "🇭🇷",
  GHA: "🇬🇭",
  PAN: "🇵🇦",
  POR: "🇵🇹",
  COD: "🇨🇩",
  UZB: "🇺🇿",
  COL: "🇨🇴",
};

const teamNamesEn = {
  MEX: "Mexico",
  RSA: "South Africa",
  KOR: "South Korea",
  CZE: "Czech Republic",
  CAN: "Canada",
  QAT: "Qatar",
  SUI: "Switzerland",
  BIH: "Bosnia & Herzegovina",
  BRA: "Brazil",
  MAR: "Morocco",
  HAI: "Haiti",
  SCO: "Scotland",
  USA: "United States",
  PAR: "Paraguay",
  AUS: "Australia",
  TUR: "Turkey",
  GER: "Germany",
  CUW: "Curacao",
  CIV: "Ivory Coast",
  ECU: "Ecuador",
  NED: "Netherlands",
  JPN: "Japan",
  SWE: "Sweden",
  TUN: "Tunisia",
  ESP: "Spain",
  CPV: "Cape Verde",
  KSA: "Saudi Arabia",
  URU: "Uruguay",
  BEL: "Belgium",
  EGY: "Egypt",
  IRN: "Iran",
  NZL: "New Zealand",
  FRA: "France",
  SEN: "Senegal",
  IRQ: "Iraq",
  NOR: "Norway",
  ARG: "Argentina",
  ALG: "Algeria",
  AUT: "Austria",
  JOR: "Jordan",
  ENG: "England",
  CRO: "Croatia",
  GHA: "Ghana",
  PAN: "Panama",
  POR: "Portugal",
  COD: "DR Congo",
  UZB: "Uzbekistan",
  COL: "Colombia",
};

const teamNamesZhToEn = {
  墨西哥: "Mexico",
  南非: "South Africa",
  韩国: "South Korea",
  捷克: "Czech Republic",
  加拿大: "Canada",
  卡塔尔: "Qatar",
  瑞士: "Switzerland",
  波黑: "Bosnia & Herzegovina",
  巴西: "Brazil",
  摩洛哥: "Morocco",
  海地: "Haiti",
  苏格兰: "Scotland",
  美国: "United States",
  巴拉圭: "Paraguay",
  澳大利亚: "Australia",
  土耳其: "Turkey",
  德国: "Germany",
  库拉索: "Curacao",
  科特迪瓦: "Ivory Coast",
  厄瓜多尔: "Ecuador",
  荷兰: "Netherlands",
  日本: "Japan",
  瑞典: "Sweden",
  突尼斯: "Tunisia",
  西班牙: "Spain",
  佛得角: "Cape Verde",
  沙特阿拉伯: "Saudi Arabia",
  乌拉圭: "Uruguay",
  比利时: "Belgium",
  埃及: "Egypt",
  伊朗: "Iran",
  新西兰: "New Zealand",
  法国: "France",
  塞内加尔: "Senegal",
  伊拉克: "Iraq",
  挪威: "Norway",
  阿根廷: "Argentina",
  阿尔及利亚: "Algeria",
  奥地利: "Austria",
  约旦: "Jordan",
  英格兰: "England",
  克罗地亚: "Croatia",
  加纳: "Ghana",
  巴拿马: "Panama",
  葡萄牙: "Portugal",
  刚果民主共和国: "DR Congo",
  乌兹别克斯坦: "Uzbekistan",
  哥伦比亚: "Colombia",
};

const optionLabelEn = {
  主胜: "Home",
  平局: "Draw",
  客胜: "Away",
  胜其他: "Home other",
  平其他: "Draw other",
  负其他: "Away other",
  "主胜 / 主胜": "Home / Home",
  "主胜 / 平局": "Home / Draw",
  "主胜 / 客胜": "Home / Away",
  "平局 / 主胜": "Draw / Home",
  "平局 / 平局": "Draw / Draw",
  "平局 / 客胜": "Draw / Away",
  "客胜 / 主胜": "Away / Home",
  "客胜 / 平局": "Away / Draw",
  "客胜 / 客胜": "Away / Away",
};

const i18n = {
  zh: {
    appName: "绿茵神噜",
    appKicker: "竞彩复盘与过关测算",
    headCopy: "北京时间赛程、体彩销售快照、赛果复盘和混合过关收益测算。",
    loading: "加载数据中",
    loadingShort: "加载中",
    todayTicketKicker: "今日比赛 · 北京时间",
    todayLoading: "今日未赛比赛加载中",
    trackKicker: "模型轨选择",
    trackAccuracyTitle: "综合轨",
    trackIndependentTitle: "独立轨",
    researchOnly: "研究用途，不构成投注建议",
    todayReviewTitle: "今日赛果复盘",
    pendingTitle: "待赛比赛预测",
    manualKicker: "人工选择",
    calculatorTitle: "独立玩法计算器",
    stakePerBet: "单注金额",
    pendingMatch: "未赛比赛",
    selectionEmptyShort: "在上方选择未赛比赛和玩法后，这里会计算命中概率和预计收益。",
    selectionEmpty: "在上方选择未赛比赛、玩法和具体投注项后，这里会计算命中概率和预计收益。",
    betCount: "注数",
    matchCount: "场次数",
    hitRate: "成功率",
    totalStake: "总本金",
    maxReturn: "最高返还",
    expectedProfit: "预计收益",
    betMode: "投注方式",
    notSelected: "未选择",
    slipNote: "注数按各场选项数相乘；总本金 = 单注金额 × 注数；最高返还取所有组合里可能固定奖金最高的一注；预计收益按组合概率加权估算。",
    scheduleKicker: "赛程纵览",
    allMatches: "全部比赛",
    searchLabel: "检索",
    searchPlaceholder: "球队、小组、日期",
    allScheduleTitle: "全部赛程（北京时间）",
    historyTitle: "历史命中率",
    championTitle: "冠军概率",
    footerDisclaimer: "模型输出仅用于研究复盘，不保证赛果，不构成投注建议。",
    footerData: "数据包含模型生成结果和手工录入的体彩销售快照。",
    statusDate: "北京日期",
    statusReview: "今日复盘",
    statusPending: "待赛",
    statusNext: "下一场",
    statusNoPending: "暂无待赛",
    statusSnapshot: "销售快照",
    statusModel: "模型",
    todayCompleted: "今日",
    completedMatches: "场已完赛",
    noUpcoming: "暂无未赛比赛",
    candidates: "三项候选",
    versus: "对",
    lowRisk: "低风险",
    risk: "风险",
    completed: "完赛",
    prematchPick: "模型赛前首选",
    hit: "命中",
    missActual: "未命中，实际",
    actual: "实际",
    missingData: "数据缺失",
    unsettled: "未结算",
    notHit: "未中",
    prediction: "预测",
    primaryPick: "首选",
    calculatorAllMarkets: "计算器可选全部玩法",
    pendingMarketPrediction: "待赛玩法预测",
    marketList: "胜平负 / 让球 / 比分 / 总进球 / 半全场",
    fairOdds: "公平赔率",
    listedOdds: "体彩赔率",
    displayOnly: "仅展示",
    saleUnavailable: "未开售",
    handicap: "让球",
    currentMarketClosed: "当前玩法未开售",
    switchOtherMarket: "游戏未开售，请切换其他玩法。",
    probability: "概率",
    successRate: "成功率",
    oddsInput: "票面赔率",
    single: "单场",
    nonSingle: "非单场",
    parlay: "过关",
    noParlay: "不可过关",
    sameMatchBackup: "单场 / 同场备选",
    needParlay: "需过关",
    mixedParlay: "混合过关",
    noMatch: "没有匹配比赛",
    simulations: "次模拟",
    settledMatches: "场已结算",
    matchesUnit: "场",
    noDailyCompleted: "今日暂无已完赛比赛",
    noPendingMatches: "暂无待赛比赛",
    noSelectablePending: "当前没有可选择的未赛比赛。",
    loadFailed: "数据加载失败",
    choose: "选择",
    selected: "已选择",
    completedStatus: "已完赛",
    pendingStatus: "未赛",
    nextMatchday: "下一待赛日",
    todayPending: "今日待赛",
  },
  en: {
    appName: "Green Pitch Luloo",
    appKicker: "Match Review & Parlay Lab",
    headCopy: "Beijing-time fixtures, lottery snapshots, result review and mixed-parlay return estimates.",
    loading: "Loading data",
    loadingShort: "Loading",
    todayTicketKicker: "Today · Beijing Time",
    todayLoading: "Loading today's match view",
    trackKicker: "Model Track",
    trackAccuracyTitle: "Blended Track",
    trackIndependentTitle: "Independent Track",
    researchOnly: "Research output, not betting advice",
    todayReviewTitle: "Today's Result Review",
    pendingTitle: "Pending Match Predictions",
    manualKicker: "Manual Picks",
    calculatorTitle: "Standalone Play Calculator",
    stakePerBet: "Stake per bet",
    pendingMatch: "Pending match",
    selectionEmptyShort: "Choose a pending match and market above to estimate hit probability and return.",
    selectionEmpty: "Choose a pending match, market and selections above to estimate hit probability and return.",
    betCount: "Bets",
    matchCount: "Matches",
    hitRate: "Hit rate",
    totalStake: "Stake",
    maxReturn: "Max return",
    expectedProfit: "Expected profit",
    betMode: "Bet mode",
    notSelected: "Not selected",
    slipNote: "Bet count multiplies selections across matches. Total stake = stake per bet x bet count. Max return uses the highest fixed-prize combination. Expected profit is probability-weighted.",
    scheduleKicker: "Schedule",
    allMatches: "All Matches",
    searchLabel: "Search",
    searchPlaceholder: "Team, group, date",
    allScheduleTitle: "Full Schedule (Beijing Time)",
    historyTitle: "Historical Hit Rate",
    championTitle: "Champion Probability",
    footerDisclaimer: "Model output is for research and review only. It does not guarantee results or provide betting advice.",
    footerData: "Data includes generated model output and manually entered lottery sales snapshots.",
    statusDate: "Beijing date",
    statusReview: "Reviewed today",
    statusPending: "Pending",
    statusNext: "Next",
    statusNoPending: "No pending match",
    statusSnapshot: "Sale snapshot",
    statusModel: "Model",
    todayCompleted: "Today",
    completedMatches: "completed",
    noUpcoming: "No pending matches",
    candidates: "Top Candidates",
    versus: "vs",
    lowRisk: "Low risk",
    risk: "risk",
    completed: "Final",
    prematchPick: "Pre-match top pick",
    hit: "Hit",
    missActual: "Miss, actual",
    actual: "Actual",
    missingData: "Missing data",
    unsettled: "Unsettled",
    notHit: "Miss",
    prediction: "Prediction",
    primaryPick: "top pick",
    calculatorAllMarkets: "all markets available in calculator",
    pendingMarketPrediction: "Market predictions",
    marketList: "1X2 / handicap / score / goals / HT-FT",
    fairOdds: "fair odds",
    listedOdds: "listed odds",
    displayOnly: "Display only",
    saleUnavailable: "Not on sale",
    handicap: "Handicap",
    currentMarketClosed: "This market is not on sale",
    switchOtherMarket: "is not on sale. Switch to another market.",
    probability: "probability",
    successRate: "success rate",
    oddsInput: "Ticket odds",
    single: "single",
    nonSingle: "not single",
    parlay: "parlay",
    noParlay: "no parlay",
    sameMatchBackup: "Single / same-match alternatives",
    needParlay: "Parlay required",
    mixedParlay: "Mixed parlay",
    noMatch: "No matching matches",
    simulations: "simulations",
    settledMatches: "settled matches",
    matchesUnit: "matches",
    noDailyCompleted: "No completed matches today",
    noPendingMatches: "No pending matches",
    noSelectablePending: "No selectable pending matches right now.",
    loadFailed: "Data load failed",
    choose: "Choose",
    selected: "Selected",
    completedStatus: "Completed",
    pendingStatus: "Pending",
    nextMatchday: "Next Matchday",
    todayPending: "Today",
  },
};

function pct(value, digits = 1) {
  return `${(Number(value || 0) * 100).toFixed(digits)}%`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function t(key) {
  return i18n[state.lang]?.[key] || i18n.zh[key] || key;
}

function localizedMeta(trackKey) {
  const meta = trackMeta[trackKey];
  return {
    title: state.lang === "en" ? meta.enTitle : meta.zhTitle,
    desc: state.lang === "en" ? meta.enDesc : meta.zhDesc,
  };
}

function marketLabel(key) {
  return marketNames[state.lang]?.[key] || marketNames.zh[key] || key;
}

function marketShortLabel(key) {
  return marketShort[state.lang]?.[key] || marketShort.zh[key] || key;
}

function optionLabel(label) {
  return state.lang === "en" ? optionLabelEn[label] || label : label;
}

function teamName(team) {
  if (!team) return "";
  return state.lang === "en" ? teamNamesEn[team.team_id] || team.name : team.name;
}

function teamText(name) {
  return state.lang === "en" ? teamNamesZhToEn[name] || name : name;
}

function targetLabelText() {
  const label = state.daily?.target_label || "";
  if (state.lang === "zh") return label || "待赛日";
  if (label === "今日待赛") return t("todayPending");
  return t("nextMatchday");
}

function stageLabel(match) {
  if (state.lang === "zh") return match.stage === "group" ? `${match.group}组` : match.stage;
  if (match.stage === "group") return `Group ${match.group}`;
  if (match.stage === "32强") return "Round of 32";
  if (match.stage === "16强") return "Round of 16";
  return match.stage;
}

function flagFor(team) {
  return flags[team.team_id] || "⚽";
}

function timeLabel(kickoff) {
  return String(kickoff).slice(11, 16);
}

function addDays(dateText, days) {
  const [year, month, day] = dateText.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day + days));
  return date.toISOString().slice(0, 10);
}

async function loadJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) throw new Error(`${path} ${response.status}`);
  return response.json();
}

function probsFor(match) {
  const key = state.track === "independent" ? "independent_probs" : "accuracy_probs";
  return match.prediction[key];
}

function spfMarketForTrack(match) {
  const sourceByLabel = new Map((match.lottery.spf.options || []).map((option) => [option.label, option]));
  const options = Object.entries(probsFor(match))
    .map(([outcome, prob]) => ({
      code: outcomeCodes[outcome],
      label: outcomeLabels[outcome],
      prob,
      fair_odds: 1 / Math.max(prob, 0.0001),
      listed_odds: sourceByLabel.get(outcomeLabels[outcome])?.listed_odds,
    }))
    .sort((a, b) => b.prob - a.prob);
  return {
    ...match.lottery.spf,
    options,
    pick: options[0],
  };
}

function marketForTrack(match, key) {
  return key === "spf" ? spfMarketForTrack(match) : match.lottery[key];
}

function displayOdds(option) {
  return Number(option.listed_odds || option.fair_odds || 1);
}

function saleTags(market) {
  const tags = [];
  if (market.supports_single) tags.push(t("single"));
  if (market.supports_parlay) tags.push(t("parlay"));
  return tags;
}

function codeFor(match) {
  return match.lottery_meta?.code || match.match_id;
}

function playableMatches() {
  return state.matches.filter((match) => !match.completed);
}

function ensureSlipDefaults() {
  const playable = playableMatches();
  if (!playable.length) {
    state.slipMatchId = "";
    return null;
  }
  if (!playable.some((match) => match.match_id === state.slipMatchId)) {
    state.slipMatchId = playable[0].match_id;
  }
  if (!marketOrder.includes(state.slipMarketKey)) {
    state.slipMarketKey = "spf";
  }
  return playable.find((match) => match.match_id === state.slipMatchId);
}

function renderStatus() {
  const pending = state.daily?.matches || [];
  const completed = state.daily?.today_completed || [];
  const nextMatch = pending[0];
  const saleCodes = pending.map(codeFor).join(" / ");
  $("#statusStrip").innerHTML = [
    `${t("statusDate")} ${state.daily?.as_of_date || state.status.data_available_at}`,
    `${t("statusReview")} ${completed.length} ${t("matchesUnit")}`,
    `${t("statusPending")} ${pending.length} ${t("matchesUnit")}`,
    nextMatch ? `${t("statusNext")} ${codeFor(nextMatch)} ${timeLabel(nextMatch.kickoff)}` : t("statusNoPending"),
    saleCodes ? `${t("statusSnapshot")} ${saleCodes}` : `${t("statusModel")} ${state.status.model_version}`,
  ]
    .map((item) => `<span class="pill">${escapeHtml(item)}</span>`)
    .join("");
}

function renderTrackInfo() {
  const meta = localizedMeta(state.track);
  $("#trackTitle").textContent = meta.title;
  $("#trackDesc").textContent = meta.desc;
}

function renderRecommendations() {
  $("#todayDate").textContent = state.daily.as_of_date || state.daily.target_date;
  const completedCount = state.daily.today_completed?.length || 0;
  const pendingText = state.daily.matches.length
    ? `${targetLabelText()} ${state.daily.target_date} · ${state.daily.matches.length} ${t("matchesUnit")}`
    : t("noUpcoming");
  $("#todaySummary").textContent = `${t("todayCompleted")} ${completedCount} ${t("completedMatches")}${state.lang === "zh" ? "，" : ", "}${pendingText}`;
  $("#recommendTitle").textContent = `${targetLabelText()}${state.lang === "zh" ? "" : " "}${t("candidates")}`;
  $("#recommendGrid").innerHTML = state.daily.top_recommendations
    .map(
      (item, index) => `
      <article class="recommend-card">
        <span class="ticket-rank">${index + 1}</span>
        <div>
          <strong>${escapeHtml(teamText(item.home))} ${t("versus")} ${escapeHtml(teamText(item.away))}</strong>
          <p>${escapeHtml(marketLabel(item.market_key))} · ${escapeHtml(optionLabel(item.selection))}</p>
        </div>
        <div class="ticket-metric">
          <span>${pct(item.prob)}</span>
          <em>${state.lang === "en" ? t("lowRisk") : `${escapeHtml(item.risk)}${t("risk")}`}</em>
        </div>
      </article>
    `,
    )
    .join("");
}

function renderDailyMatches() {
  const completed = state.daily.today_completed || [];
  $("#todayReviewSummary").textContent = completed.length
    ? `${state.daily.as_of_date} · ${completed.length} ${t("completedMatches")}`
    : `${state.daily.as_of_date || state.daily.target_date} ${t("noDailyCompleted")}`;
  $("#dailyGrid").innerHTML = completed.map(renderReviewCard).join("") || `
    <section class="empty-state">${t("noDailyCompleted")}</section>
  `;
}

function resultLabelFromGoals(homeGoals, awayGoals) {
  if (homeGoals > awayGoals) return "主胜";
  if (homeGoals < awayGoals) return "客胜";
  return "平局";
}

function renderReviewCard(match) {
  const probs = probsFor(match);
  const [pickLabel, pickValue] = topOutcome(probs);
  const actualLabel = resultLabelFromGoals(match.result.home_goals, match.result.away_goals);
  const hit = pickLabel === actualLabel;
  return `
    <article class="daily-card review-card">
      <header class="daily-card-head">
        <div>
          <span class="match-date">${escapeHtml(match.kickoff.slice(0, 10))} ${escapeHtml(timeLabel(match.kickoff))}</span>
          <h2>
            <span class="flag">${flagFor(match.home)}</span>${escapeHtml(teamName(match.home))}
            <small>${t("versus")}</small>
            <span class="flag">${flagFor(match.away)}</span>${escapeHtml(teamName(match.away))}
          </h2>
        </div>
        <div class="result-score">
          <span>${t("completed")}</span>
          <strong>${match.result.home_goals}-${match.result.away_goals}</strong>
        </div>
      </header>
      <div class="review-line ${hit ? "hit" : "miss"}">
        <span>${t("prematchPick")}：${escapeHtml(optionLabel(pickLabel))} ${pct(pickValue)}</span>
        <strong>${hit ? t("hit") : `${t("missActual")} ${optionLabel(actualLabel)}`}</strong>
      </div>
      <div class="baseline-grid">
        ${baseline(optionLabel("主胜"), probs.home, "home-fill")}
        ${baseline(optionLabel("平局"), probs.draw, "draw-fill")}
        ${baseline(optionLabel("客胜"), probs.away, "away-fill")}
      </div>
      <div class="review-market-grid">
        ${marketOrder.map((key) => renderReviewMarket(match.lottery_review[key], key)).join("")}
      </div>
    </article>
  `;
}

function renderReviewMarket(item, key) {
  const status = item.settled ? (item.hit ? t("hit") : t("notHit")) : t("unsettled");
  return `
    <section class="review-market ${item.hit ? "hit" : "miss"}">
      <span>${escapeHtml(marketShortLabel(key))}</span>
      <strong>${t("prediction")}：${escapeHtml(optionLabel(item.prediction))}</strong>
      <p>${t("actual")}：${escapeHtml(optionLabel(item.actual || t("missingData")))}</p>
      <em>${escapeHtml(status)}</em>
    </section>
  `;
}

function renderPredictionCard(match) {
  const probs = probsFor(match);
  const trackLabel = localizedMeta(state.track).title;
  const [pickLabel, pickValue] = topOutcome(probs);
  return `
    <article class="daily-card">
      <header class="daily-card-head">
        <div>
          <span class="match-date">${escapeHtml(match.kickoff.slice(0, 10))} ${escapeHtml(timeLabel(match.kickoff))}</span>
          <h2>
            <span class="flag">${flagFor(match.home)}</span>${escapeHtml(teamName(match.home))}
            <small>${t("versus")}</small>
            <span class="flag">${flagFor(match.away)}</span>${escapeHtml(teamName(match.away))}
          </h2>
        </div>
        <div class="card-badges">
          <strong class="track-badge">${escapeHtml(trackLabel)}</strong>
          <strong class="handicap">${t("handicap")} ${match.handicap > 0 ? "+" : ""}${match.handicap}</strong>
        </div>
      </header>
      <div class="card-subhead">
        <strong>${escapeHtml(trackLabel)}${state.lang === "zh" ? "" : " "}${t("primaryPick")}：${escapeHtml(optionLabel(pickLabel))} ${pct(pickValue)}</strong>
        <span>${escapeHtml(codeFor(match))} · ${t("calculatorAllMarkets")}</span>
      </div>
      <div class="baseline-grid">
        ${baseline(optionLabel("主胜"), probs.home, "home-fill")}
        ${baseline(optionLabel("平局"), probs.draw, "draw-fill")}
        ${baseline(optionLabel("客胜"), probs.away, "away-fill")}
      </div>
      <div class="market-title prediction-market-title">
        <strong>${t("pendingMarketPrediction")}</strong>
        <span>${t("marketList")}</span>
      </div>
      <div class="market-grid prediction-market-grid">
        ${marketOrder.map((key) => renderPredictionMarket(match, key)).join("")}
      </div>
    </article>
  `;
}

function renderPredictionMarket(match, key) {
  const market = marketForTrack(match, key);
  const pick = market.pick;
  const odds = displayOdds(pick);
  const status = market.sale ? saleTags(market).join(" / ") : t("saleUnavailable");
  const handicap = key === "rqspf" ? ` · ${t("handicap")} ${match.handicap > 0 ? "+" : ""}${match.handicap}` : "";
  return `
    <section class="market-card prediction-market ${market.sale ? "" : "unavailable"}">
      <span class="market-code">${escapeHtml(marketShortLabel(key))}</span>
      <strong>${t("prediction")}：${escapeHtml(optionLabel(pick.label))}</strong>
      <p>${pct(pick.prob)} · ${pick.listed_odds ? t("listedOdds") : t("fairOdds")} ${odds.toFixed(2)}${escapeHtml(handicap)}</p>
      <em>${escapeHtml(status || t("displayOnly"))}</em>
    </section>
  `;
}

function baseline(label, value, className) {
  return `
    <div class="baseline">
      <span>${label}</span>
      <strong>${pct(value)}</strong>
      <div class="bar-track"><div class="bar-fill ${className}" style="width:${pct(value, 3)}"></div></div>
    </div>
  `;
}

function selectionId(match, key) {
  return `${match.match_id}:${key}`;
}

function optionSelectionId(match, key, option) {
  return `${match.match_id}:${key}:${option.code}`;
}

function renderMarket(match, market, key) {
  const id = selectionId(match, key);
  const selected = state.selections.has(id);
  return `
    <section class="market-card ${selected ? "selected" : ""}">
      <span class="market-code">${escapeHtml(marketShortLabel(key))}</span>
      <strong>${t("prediction")}：${escapeHtml(optionLabel(market.pick.label))}</strong>
      <p>${pct(market.pick.prob)} · ${t("fairOdds")} ${Number(market.pick.fair_odds).toFixed(2)}</p>
      <button class="select-market" type="button"
        data-selection-id="${escapeHtml(id)}"
        data-match-id="${escapeHtml(match.match_id)}"
        data-market-key="${escapeHtml(key)}">
        ${selected ? t("selected") : t("choose")}
      </button>
    </section>
  `;
}

function renderCalculator() {
  const match = ensureSlipDefaults();
  if (!match) {
    $("#slipMatchSelect").innerHTML = `<option>${t("noPendingMatches")}</option>`;
    $("#marketTabs").innerHTML = "";
    $("#optionGrid").innerHTML = `<p class="empty-state">${t("noSelectablePending")}</p>`;
    return;
  }
  $("#slipMatchSelect").innerHTML = playableMatches()
    .map(
      (item) => `
      <option value="${escapeHtml(item.match_id)}" ${item.match_id === state.slipMatchId ? "selected" : ""}>
        ${escapeHtml(codeFor(item))} · ${escapeHtml(item.kickoff.slice(5, 10))} ${escapeHtml(timeLabel(item.kickoff))} · ${escapeHtml(teamName(item.home))} ${t("versus")} ${escapeHtml(teamName(item.away))}
      </option>
    `,
    )
    .join("");
  $("#marketTabs").innerHTML = marketOrder
    .map(
      (key) => `
      <button class="market-tab ${key === state.slipMarketKey ? "active" : ""}" type="button" data-market-key="${escapeHtml(key)}">
        ${escapeHtml(marketShortLabel(key))}
      </button>
    `,
    )
    .join("");
  renderOptionGrid(match);
  bindCalculatorControls();
}

function renderOptionGrid(match) {
  const market = marketForTrack(match, state.slipMarketKey);
  const options = market.options || [];
  const tags = saleTags(market);
  if (!market.sale) {
    $("#optionGrid").innerHTML = `
      <div class="option-head">
        <strong>${escapeHtml(codeFor(match))} · ${escapeHtml(teamName(match.home))} ${t("versus")} ${escapeHtml(teamName(match.away))} · ${escapeHtml(marketLabel(state.slipMarketKey))}</strong>
        <span>${t("currentMarketClosed")}</span>
      </div>
      <p class="empty-state">${escapeHtml(marketLabel(state.slipMarketKey))} ${t("switchOtherMarket")}</p>
    `;
    return;
  }
  $("#optionGrid").innerHTML = `
    <div class="option-head">
      <strong>${escapeHtml(codeFor(match))} · ${escapeHtml(teamName(match.home))} ${t("versus")} ${escapeHtml(teamName(match.away))} · ${escapeHtml(marketLabel(state.slipMarketKey))}</strong>
      <span>${escapeHtml(localizedMeta(state.track).title)} ${t("probability")} · ${tags.join(" / ") || t("displayOnly")} · ${t("handicap")} ${match.handicap > 0 ? "+" : ""}${match.handicap}</span>
    </div>
    <div class="option-list ${state.slipMarketKey === "bf" ? "score-options" : ""}">
      ${options.map((option) => renderBetOption(match, market, option)).join("")}
    </div>
  `;
}

function renderBetOption(match, market, option) {
  const id = optionSelectionId(match, state.slipMarketKey, option);
  const selected = state.selections.has(id);
  const odds = displayOdds(option);
  return `
    <button class="bet-option ${selected ? "selected" : ""}" type="button"
      data-selection-id="${escapeHtml(id)}"
      data-match-id="${escapeHtml(match.match_id)}"
      data-market-key="${escapeHtml(state.slipMarketKey)}"
      data-option-code="${escapeHtml(option.code)}">
      <strong>${escapeHtml(optionLabel(option.label))}</strong>
      <span>${t("successRate")} ${pct(option.prob)}</span>
      <em>${t("listedOdds")} ${odds.toFixed(2)}</em>
      <small>${saleTags(market).join(" / ")}</small>
    </button>
  `;
}

function topOutcome(probs) {
  return [
    ["主胜", probs.home],
    ["平局", probs.draw],
    ["客胜", probs.away],
  ].sort((a, b) => b[1] - a[1])[0];
}

function renderTomorrow() {
  const upcoming = state.daily.matches || [];
  $("#tomorrowSummary").textContent = `${state.daily.target_date} · ${upcoming.length} ${t("matchesUnit")}`;
  $("#tomorrowGrid").innerHTML = upcoming.map(renderPredictionCard).join("") || `
    <p class="empty-state">${t("noPendingMatches")}</p>
  `;
}

function renderTomorrowCard(match) {
  const probs = probsFor(match);
  const [label, value] = topOutcome(probs);
  return `
    <article class="tomorrow-card">
      <div>
          <span class="match-date">${escapeHtml(timeLabel(match.kickoff))}</span>
          <h3>
          <span class="flag">${flagFor(match.home)}</span>${escapeHtml(teamName(match.home))}
          <small>${t("versus")}</small>
          <span class="flag">${flagFor(match.away)}</span>${escapeHtml(teamName(match.away))}
        </h3>
      </div>
      <div class="tomorrow-pick">
        <span>${escapeHtml(localizedMeta(state.track).title)} ${t("primaryPick")}</span>
        <strong>${escapeHtml(optionLabel(label))} ${pct(value)}</strong>
      </div>
    </article>
  `;
}

function renderCompactMatch(match) {
  const probs = probsFor(match);
  const result = match.result ? `${match.result.home_goals}-${match.result.away_goals}` : t("versus");
  return `
    <article class="match-row">
      <div class="match-meta">
        <strong>${escapeHtml(stageLabel(match))}</strong><br />
        ${escapeHtml(match.kickoff.slice(0, 10))}<br />
        ${match.completed ? t("completedStatus") : t("pendingStatus")}
      </div>
      <div class="teams">
        <div class="team-line"><span><span class="flag">${flagFor(match.home)}</span>${escapeHtml(teamName(match.home))}</span><span class="score">${escapeHtml(result)}</span></div>
        <div class="team-line"><span><span class="flag">${flagFor(match.away)}</span>${escapeHtml(teamName(match.away))}</span><span class="score">${t("handicap")} ${match.handicap > 0 ? "+" : ""}${match.handicap}</span></div>
      </div>
      <div class="prob-bars">
        ${miniBar(optionLabel("主胜"), probs.home, "home-fill")}
        ${miniBar(optionLabel("平局"), probs.draw, "draw-fill")}
        ${miniBar(optionLabel("客胜"), probs.away, "away-fill")}
      </div>
    </article>
  `;
}

function miniBar(label, value, className) {
  return `
    <div class="bar-line">
      <span>${label}</span>
      <span class="bar-track"><span class="bar-fill ${className}" style="width:${pct(value, 3)}"></span></span>
      <strong>${pct(value)}</strong>
    </div>
  `;
}

function renderMatches() {
  const query = state.query.trim().toLowerCase();
  const filtered = state.matches.filter((match) => {
    if (!query) return true;
    return [match.group, match.home.name, match.away.name, teamName(match.home), teamName(match.away), match.stage, stageLabel(match), match.kickoff.slice(0, 10)]
      .join(" ")
      .toLowerCase()
      .includes(query);
  });
  $("#matchCount").textContent = `${filtered.length} ${t("matchesUnit")}`;
  $("#matchList").innerHTML = filtered.slice(0, 24).map(renderCompactMatch).join("") || `<p class="error">${t("noMatch")}</p>`;
}

function renderChampions() {
  const entries = Object.entries(state.champion.champion_probs)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 14);
  $("#simMeta").textContent = `${state.champion.n_sims} ${t("simulations")}`;
  $("#championList").innerHTML = entries
    .map(
      ([team, value], index) => `
      <div class="champion-row">
        <span class="rank">${index + 1}</span>
        <span>${escapeHtml(teamText(team))}</span>
        <span class="prob">${pct(value)}</span>
      </div>
    `,
    )
    .join("");
}

function renderHistory() {
  const history = state.history.history;
  $("#historyMeta").textContent = `${history.sample_size} ${t("settledMatches")}`;
  $("#historyGrid").innerHTML = marketOrder
    .map((key) => {
      const item = history.markets[key];
      return `
        <div class="history-cell">
          <span>${escapeHtml(marketShortLabel(key))}</span>
          <strong>${pct(item.hit_rate)}</strong>
          <em>${item.hit}/${item.settled}</em>
        </div>
      `;
    })
    .join("");
}

function findMatch(matchId) {
  return state.matches.find((match) => match.match_id === matchId);
}

function findMarketOption(match, key, code) {
  const market = marketForTrack(match, key);
  return (market.options || []).find((option) => String(option.code) === String(code));
}

function toggleOption(button) {
  const match = findMatch(button.dataset.matchId);
  if (!match) return;
  const key = button.dataset.marketKey;
  const id = button.dataset.selectionId;
  const market = marketForTrack(match, key);
  const option = findMarketOption(match, key, button.dataset.optionCode);
  if (!option || !market.sale) return;
  const odds = displayOdds(option);
  if (state.selections.has(id)) {
    state.selections.delete(id);
  } else {
    state.selections.set(id, {
      id,
      matchId: match.match_id,
      marketKey: key,
      optionCode: option.code,
      home: match.home.name,
      away: match.away.name,
      market: state.slipMarketKey,
      selection: option.label,
      prob: option.prob,
      odds: odds.toFixed(2),
      supportsSingle: Boolean(market.supports_single),
      supportsParlay: Boolean(market.supports_parlay),
      userOdds: false,
    });
  }
  renderCalculator();
  renderSlip();
}

function renderSlip() {
  const selections = Array.from(state.selections.values());
  if (!selections.length) {
    $("#selectedList").innerHTML = `<p class="empty-state">${t("selectionEmpty")}</p>`;
    updateSlipSummary([]);
    return;
  }
  $("#selectedList").innerHTML = selections
    .map(
      (item) => `
      <article class="selected-item">
        <button class="remove-selection" type="button" data-selection-id="${escapeHtml(item.id)}">×</button>
        <div>
          <strong>${escapeHtml(teamText(item.home))} ${t("versus")} ${escapeHtml(teamText(item.away))}</strong>
          <p>${escapeHtml(marketLabel(item.market))} · ${escapeHtml(optionLabel(item.selection))} · ${pct(item.prob)} · ${item.supportsSingle ? t("single") : t("nonSingle")} / ${item.supportsParlay ? t("parlay") : t("noParlay")}</p>
        </div>
        <label>
          <span>${t("oddsInput")}</span>
          <input class="odds-input" data-selection-id="${escapeHtml(item.id)}" type="number" min="1" step="0.01" value="${escapeHtml(item.odds)}" />
        </label>
      </article>
    `,
    )
    .join("");
  bindSlipInputs();
  updateSlipSummary(selections);
}

function updateSlipSummary(selections) {
  const stake = Number($("#stakeInput").value || 0);
  const estimate = estimateSlip(selections, stake);
  $("#slipCount").textContent = String(estimate.combinationCount);
  const matchCount = $("#slipMatchCount");
  if (matchCount) matchCount.textContent = String(estimate.matchCount);
  $("#slipHitRate").textContent = pct(estimate.hitProbability);
  const stakeTotal = $("#slipStakeTotal");
  if (stakeTotal) stakeTotal.textContent = estimate.totalStake.toFixed(2);
  $("#slipPayout").textContent = estimate.maxPayoutIfHit.toFixed(2);
  $("#slipReturn").textContent = estimate.expectedReturn.toFixed(2);
  $("#slipMode").textContent = slipModeText(selections);
  $("#slipReturn").classList.toggle("negative", estimate.expectedReturn < 0);
  $("#slipReturn").classList.toggle("positive", estimate.expectedReturn > 0);
}

function estimateSlip(selections, stake) {
  const groups = new Map();
  selections.forEach((item, index) => {
    const key = item.matchId || `selection-${index}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push({
      prob: Math.min(Math.max(Number(item.prob || 0), 0), 1),
      odds: Math.max(Number(item.odds || 1), 1),
    });
  });

  if (!selections.length || stake <= 0) {
    const combinationCount = selections.length
      ? Array.from(groups.values()).reduce((total, group) => total * group.length, 1)
      : 0;
    return {
      combinationCount,
      matchCount: groups.size,
      hitProbability: selections.length ? Array.from(groups.values()).reduce((hit, group) => hit * Math.min(group.reduce((sum, item) => sum + item.prob, 0), 1), 1) : 0,
      totalStake: selections.length && stake > 0 ? stake * combinationCount : 0,
      maxPayoutIfHit: 0,
      expectedReturn: 0,
    };
  }

  let combinationCount = 1;
  let hitProbability = 1;
  let combinations = [{ prob: 1, odds: 1 }];
  groups.forEach((group) => {
    combinationCount *= group.length;
    hitProbability *= Math.min(group.reduce((sum, item) => sum + item.prob, 0), 1);
    combinations = combinations.flatMap((combo) =>
      group.map((item) => ({
        prob: combo.prob * item.prob,
        odds: combo.odds * item.odds,
      })),
    );
  });

  const totalStake = stake * combinationCount;
  const maxPayoutIfHit = Math.max(...combinations.map((combo) => stake * combo.odds), 0);
  const expectedPayout = combinations.reduce((sum, combo) => sum + combo.prob * stake * combo.odds, 0);
  return {
    combinationCount,
    matchCount: groups.size,
    hitProbability,
    totalStake,
    maxPayoutIfHit,
    expectedReturn: expectedPayout - totalStake,
  };
}

function slipModeText(selections) {
  if (!selections.length) return t("notSelected");
  const uniqueMatches = new Set(selections.map((item) => item.matchId)).size;
  if (uniqueMatches === 1) {
    return selections.some((item) => item.supportsSingle) ? t("sameMatchBackup") : t("needParlay");
  }
  if (!selections.every((item) => item.supportsParlay)) {
    return t("noParlay");
  }
  return t("mixedParlay");
}

function applyLanguage() {
  document.documentElement.lang = state.lang === "en" ? "en" : "zh-CN";
  document.title = t("appName");
  $$("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  $$("[data-i18n-placeholder]").forEach((element) => {
    element.setAttribute("placeholder", t(element.dataset.i18nPlaceholder));
  });
  $$("[data-lang]").forEach((button) => {
    button.classList.toggle("active", button.dataset.lang === state.lang);
  });
}

function renderAll() {
  if (!state.status || !state.daily || !state.champion || !state.history) return;
  renderStatus();
  renderTrackInfo();
  renderRecommendations();
  renderDailyMatches();
  renderTomorrow();
  renderMatches();
  renderHistory();
  renderChampions();
  renderCalculator();
  renderSlip();
}

function refreshSelectionsForTrack() {
  state.selections.forEach((item, id) => {
    const match = findMatch(item.matchId);
    const option = match ? findMarketOption(match, item.marketKey, item.optionCode) : null;
    if (!match || !option) {
      state.selections.delete(id);
      return;
    }
    item.prob = option.prob;
    const market = marketForTrack(match, item.marketKey);
    item.supportsSingle = Boolean(market.supports_single);
    item.supportsParlay = Boolean(market.supports_parlay);
    if (!item.userOdds) {
      item.odds = displayOdds(option).toFixed(2);
    }
  });
}

function bindCalculatorControls() {
  $("#slipMatchSelect").addEventListener("change", (event) => {
    state.slipMatchId = event.target.value;
    renderCalculator();
  });
  $$(".market-tab").forEach((button) => {
    button.addEventListener("click", () => {
      state.slipMarketKey = button.dataset.marketKey;
      renderCalculator();
    });
  });
  $$(".bet-option").forEach((button) => {
    button.addEventListener("click", () => toggleOption(button));
  });
}

function bindPredictionButtons() {
  $$(".open-slip").forEach((button) => {
    button.addEventListener("click", () => {
      state.slipMatchId = button.dataset.matchId;
      renderCalculator();
      document.querySelector("#slipPanel")?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}

function bindSlipInputs() {
  $$(".remove-selection").forEach((button) => {
    button.addEventListener("click", () => {
      state.selections.delete(button.dataset.selectionId);
      renderCalculator();
      renderSlip();
    });
  });
  $$(".odds-input").forEach((input) => {
    input.addEventListener("input", () => {
      const item = state.selections.get(input.dataset.selectionId);
      if (!item) return;
      item.odds = input.value;
      item.userOdds = true;
      updateSlipSummary(Array.from(state.selections.values()));
    });
  });
}

function bindControls() {
  $$("[data-lang]").forEach((button) => {
    button.addEventListener("click", () => {
      state.lang = button.dataset.lang === "en" ? "en" : "zh";
      localStorage.setItem("wc26-lang", state.lang);
      applyLanguage();
      renderAll();
    });
  });
  $$(".segmented button").forEach((button) => {
    button.addEventListener("click", () => {
      state.track = button.dataset.track;
      $$(".segmented button").forEach((item) => item.classList.toggle("active", item === button));
      refreshSelectionsForTrack();
      renderTrackInfo();
      renderDailyMatches();
      renderTomorrow();
      bindPredictionButtons();
      renderCalculator();
      renderSlip();
      renderMatches();
    });
  });
  $("#matchSearch").addEventListener("input", (event) => {
    state.query = event.target.value;
    renderMatches();
  });
  $("#stakeInput").addEventListener("input", () => {
    updateSlipSummary(Array.from(state.selections.values()));
  });
  bindPredictionButtons();
}

async function main() {
  applyLanguage();
  try {
    const [status, matches, daily, champion, history] = await Promise.all([
      loadJson("/data/model_status.json"),
      loadJson("/data/matches.json"),
      loadJson("/data/daily_predictions.json"),
      loadJson("/data/champion_probs.json"),
      loadJson("/data/history.json"),
    ]);
    state.status = status;
    state.matches = matches.matches;
    state.daily = daily;
    state.champion = champion;
    state.history = history;
    applyLanguage();
    renderAll();
    bindControls();
  } catch (error) {
    const statusStrip = $("#statusStrip");
    if (statusStrip) statusStrip.innerHTML = `<span class="pill">${t("loadFailed")}</span>`;
    const dailyGrid = $("#dailyGrid");
    if (dailyGrid && !dailyGrid.innerHTML.trim()) {
      dailyGrid.innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`;
    }
    console.error(error);
  }
}

main();
