# Project Roadmap

> Planned features and improvements for Daily Stock Analysis (DSA).
> Updated based on codebase analysis and recent development activity.

---

## Current State (v3.9.0)

The system is a mature, feature-rich stock analysis platform with:
- ✅ Multi-source data (7 providers with fallback)
- ✅ LLM analysis via LiteLLM (Gemini, Claude, GPT, DeepSeek, Ollama)
- ✅ Multi-agent architecture with skill/strategy system
- ✅ 10+ notification channels
- ✅ FastAPI backend + React Web UI + Electron desktop
- ✅ Bot integrations (DingTalk, Feishu, Discord, Telegram, Slack)
- ✅ Backtest engine
- ✅ Portfolio management
- ✅ Trading calendar per-market filtering
- ✅ i18n report language (zh/en)
- ✅ Social sentiment (US stocks)

---

## Near-term (Next Release)

### Vietnamese Stock Market Integration
**Status:** Shipped (V1: PR #1, V2: PR #2)
- V1: Daily historical data via `VnstocksFetcher` (`VN:FPT` prefix convention)
- V2: Hybrid realtime quotes (intraday during trading hours, daily close fallback)
- V2: Dynamic stock names via `Listing().all_symbols()` with 24h TTL cache
- V2: VN trading calendar support (weekday-only, `Asia/Ho_Chi_Minh`)
- API key management via `VNSTOCK_API_KEY` env var
- 44 tests (16 V1 + 28 V2)

### Technical Debt
- **Config consolidation** — `src/config.py` at 2150 lines; consider splitting into domain-specific config modules
- **Pipeline decomposition** — `src/core/pipeline.py` at 1475 lines; extract agent path and notification logic
- **Test coverage** — Expand pytest coverage for data providers and agent system

---

## Mid-term (v4.x)

### Enhanced Analytics
- **Real-time streaming** — WebSocket push for live quote updates in Web UI
- **Advanced charting** — Candlestick charts with indicator overlays (MA, MACD, RSI)
- **Options flow** — Integration with options data for sentiment analysis
- **Sector rotation** — Cross-sector analysis and rotation signals

### Platform Improvements
- **Multi-language Web UI** — Currently Chinese-only; add English UI
- **Mobile app** — React Native or PWA for mobile access
- **API v2** — GraphQL endpoint for flexible data queries
- **Plugin system** — User-installable plugins for custom data sources and analysis

### Agent Enhancements
- **Strategy backtesting** — Automated testing of YAML strategies against historical data
- **Strategy marketplace** — Community-contributed strategy sharing
- **Agent memory persistence** — Cross-session agent learning
- **Event-driven alerts** — Real-time event monitoring with configurable rules

---

## Long-term (v5.x)

### Enterprise Features
- **Multi-tenant** — Separate user accounts with isolated portfolios
- **RBAC** — Role-based access control for team deployments
- **Audit trail** — Full audit logging for compliance
- **Webhook integrations** — Outbound webhooks for downstream systems

### Advanced AI
- **Fine-tuned models** — Domain-specific model fine-tuning on financial data
- **RAG pipeline** — Retrieval-augmented generation with company filings
- **Predictive models** — ML-based price prediction alongside LLM analysis
- **Multi-modal** — Image/chart analysis in reports

---

## Version History (Recent)

| Version | Highlights |
|---------|-----------|
| v3.9.0 | Slack notification, stock autocomplete, report language config |
| v3.8.x | Agent skill routing, portfolio risk alerts, fundamental pipeline |
| v3.7.x | Multi-agent architecture, trading calendar, backtest engine |
| v3.6.x | LiteLLM migration, multi-channel config, Electron desktop |

> Full changelog: [CHANGELOG.md](./CHANGELOG.md)
