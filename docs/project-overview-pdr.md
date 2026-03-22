# Project Overview — Daily Stock Analysis (DSA)

## Product Summary

**Daily Stock Analysis (DSA)** is an AI-powered stock analysis system covering **A-share (China), Hong Kong, and US markets**. It fetches multi-source market data, runs technical + fundamental analysis, generates LLM-powered decision dashboards, and delivers reports via 10+ notification channels.

The system operates in three modes:
1. **CLI batch** — one-shot or scheduled analysis of a watchlist
2. **FastAPI backend** — RESTful API serving a React Web UI and Electron desktop app
3. **Chatbot gateway** — interactive analysis via DingTalk, Feishu, Discord, Telegram, Slack

---

## Core Capabilities

| Capability | Description |
|------------|-------------|
| **Multi-source data** | 7 data providers with automatic fallback (efinance → akshare → tushare → pytdx → baostock → yfinance → tickflow) |
| **Real-time quotes** | Tencent, Sina, efinance, EastMoney, Tushare with circuit-breaker protection |
| **LLM analysis** | Unified via LiteLLM — Gemini, Claude, GPT, DeepSeek, Ollama with multi-channel routing |
| **Agent mode** | Multi-agent architecture (intel / technical / risk / decision / portfolio agents) with skill-based strategy system |
| **Technical indicators** | MA multi-alignment, volume analysis, chip distribution, bias rate, buy-signal scoring |
| **Fundamental pipeline** | Aggregated fundamental context with timeout/retry/cache protection |
| **News intelligence** | Multi-dimensional search (latest news, risk scan, earnings expectations) via Tavily, Bocha, Brave, SerpAPI, SearXNG |
| **Social sentiment** | Reddit/X/Polymarket sentiment for US stocks |
| **Report engine** | Simple / Full / Jinja2-rendered reports with integrity validation |
| **Notification** | WeChat, Feishu, Telegram, Email, Discord, Slack, PushPlus, Pushover, Server酱, custom webhook |
| **Backtest** | Automated backtest engine evaluating past analysis accuracy |
| **Portfolio** | Import, risk assessment, concentration alerts, FX conversion |
| **Market review** | Daily market summary for CN/US with configurable region |
| **Trading calendar** | Exchange-calendars integration for CN/HK/US trading day checks |
| **History comparison** | Compare current analysis with historical patterns |
| **Markdown-to-image** | Convert reports to images for channels without Markdown support |
| **Feishu Cloud Docs** | Auto-publish analysis to Feishu workspace |
| **i18n** | Report language: zh (Chinese), en (English) |

---

## Target Users

1. **Individual investors** tracking A-share / HK / US watchlists
2. **Trading groups** receiving automated daily analysis via chat bots
3. **Quantitative researchers** using backtest engine to validate AI signals
4. **Self-hosters** deploying via Docker on personal servers or cloud

---

## Product Development Requirements (PDR)

### P0 — Must Have (shipped)
- [x] Multi-source data fetching with fallback chain
- [x] LLM-powered stock analysis with decision dashboard
- [x] CLI batch + scheduled execution
- [x] 10+ notification channels
- [x] FastAPI REST API
- [x] React Web UI (dsa-web)
- [x] Electron desktop app (dsa-desktop)
- [x] Bot integrations (DingTalk, Feishu, Discord, Telegram, Slack)
- [x] Trading calendar per-market filtering
- [x] Agent mode with multi-agent architecture

### P1 — Important (shipped or in progress)
- [x] Backtest engine
- [x] Portfolio management with risk alerts
- [x] Social sentiment integration (US stocks)
- [x] Report integrity validation + retry
- [x] Multi-channel LLM config (LITELLM_CONFIG YAML)
- [x] Markdown-to-image for non-MD channels
- [ ] Vietnamese stock market integration (VN prefix convention, vnstock library)

### P2 — Nice to Have (planned)
- [ ] Strategy marketplace / community-contributed YAML strategies
- [ ] Real-time streaming analysis (WebSocket push)
- [ ] Mobile-native app (React Native)
- [ ] Multi-language Web UI (currently Chinese-only)
- [ ] Advanced charting in Web UI (candlestick, indicators overlay)

---

## Key Metrics

| Metric | Current |
|--------|---------|
| Python LOC | ~70K+ |
| Frontend LOC (TS/TSX) | ~20K+ |
| Data providers | 7 (with fallback chain) |
| Notification channels | 10+ |
| LLM providers supported | 6+ (via LiteLLM) |
| Agent skills (YAML strategies) | 11 |
| CI workflows | 10 |
| Test coverage | pytest + Playwright smoke |
