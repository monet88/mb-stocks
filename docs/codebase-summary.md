# Codebase Summary

> Auto-generated documentation — last updated from codebase analysis.

## Scale

| Area | Files | Approximate LOC |
|------|-------|-----------------|
| Python backend (`src/`, `data_provider/`, `api/`, `bot/`, `main.py`, `server.py`) | ~130 | ~70K |
| Web frontend (`apps/dsa-web/src/`) | ~125 TSX/TS | ~20K |
| Desktop shell (`apps/dsa-desktop/`) | ~10 | ~2K |
| Tests | ~30 | ~5K |
| Config / CI / Scripts | ~30 | ~3K |
| **Total** | **~325** | **~100K** |

---

## Directory Structure

```
mb-stocks/
├── main.py                    # CLI entry point (723 lines)
├── server.py                  # FastAPI ASGI bootstrapper (55 lines)
├── requirements.txt           # Python dependencies (65 lines)
├── .env.example               # Environment variable template
│
├── src/                       # Core Python application
│   ├── config.py              # Singleton Config dataclass (~2150 lines, all env vars)
│   ├── analyzer.py            # GeminiAnalyzer — LLM analysis engine
│   ├── stock_analyzer.py      # StockTrendAnalyzer — technical indicator engine
│   ├── notification.py        # NotificationService — multi-channel dispatcher
│   ├── search_service.py      # SearchService — multi-engine news intelligence
│   ├── storage.py             # SQLite database layer
│   ├── logging_config.py      # Structured logging setup
│   ├── enums.py               # Shared enumerations
│   ├── formatters.py          # Report formatting utilities
│   ├── md2img.py              # Markdown → image conversion
│   ├── market_analyzer.py     # Market-level analysis helper
│   ├── scheduler.py           # APScheduler-based cron
│   ├── report_language.py     # i18n helpers (zh/en)
│   ├── auth.py                # API authentication
│   ├── webui_frontend.py      # Static asset preparation
│   ├── feishu_doc.py          # Feishu Cloud Docs integration
│   │
│   ├── core/                  # Pipeline orchestration
│   │   ├── pipeline.py        # StockAnalysisPipeline (1475 lines) — main flow
│   │   ├── market_review.py   # Daily market summary
│   │   ├── market_strategy.py # Market regime detection
│   │   ├── market_profile.py  # Market profile builder
│   │   ├── config_manager.py  # Runtime config manager
│   │   ├── config_registry.py # Config registry
│   │   ├── trading_calendar.py# Exchange calendar (CN/HK/US/VN)
│   │   └── backtest_engine.py # Backtest evaluation engine
│   │
│   ├── services/              # Business service layer (19 files)
│   │   ├── stock_service.py          # Stock CRUD operations
│   │   ├── analysis_service.py       # Analysis orchestration for API
│   │   ├── history_service.py        # Analysis history queries
│   │   ├── history_comparison_service.py # Cross-time comparisons
│   │   ├── backtest_service.py       # Backtest coordination
│   │   ├── portfolio_service.py      # Portfolio management
│   │   ├── portfolio_import_service.py # Portfolio import (CSV/XLSX)
│   │   ├── portfolio_risk_service.py # Risk assessment & alerts
│   │   ├── stock_code_utils.py       # Stock code parsing & resolution
│   │   ├── name_to_code_resolver.py  # Natural language → stock code
│   │   ├── image_stock_extractor.py  # Vision-based stock extraction
│   │   ├── import_parser.py          # Import file parsing
│   │   ├── social_sentiment_service.py # Reddit/X sentiment (US)
│   │   ├── report_renderer.py        # Jinja2 report rendering
│   │   ├── task_queue.py             # Background task queue
│   │   ├── task_service.py           # Task management
│   │   ├── system_config_service.py  # System config API
│   │   └── agent_model_service.py    # Agent model management
│   │
│   ├── repositories/          # Data access layer (5 files)
│   │   ├── stock_repo.py      # Stock data repository
│   │   ├── analysis_repo.py   # Analysis history repository
│   │   ├── backtest_repo.py   # Backtest results repository
│   │   └── portfolio_repo.py  # Portfolio repository
│   │
│   ├── schemas/               # Pydantic / data models
│   │   └── report_schema.py   # Report structure definitions
│   │
│   ├── agent/                 # Multi-agent AI system (33 files)
│   │   ├── orchestrator.py    # Multi-agent orchestrator
│   │   ├── executor.py        # Agent execution engine
│   │   ├── runner.py          # Agent runner with retry
│   │   ├── factory.py         # Agent builder factory
│   │   ├── llm_adapter.py     # LiteLLM adapter
│   │   ├── memory.py          # Agent memory system
│   │   ├── conversation.py    # Conversation management
│   │   ├── protocols.py       # Agent protocols & contracts
│   │   ├── agents/            # Specialized agents
│   │   │   ├── intel_agent.py      # News & intelligence
│   │   │   ├── technical_agent.py  # Technical analysis
│   │   │   ├── risk_agent.py       # Risk assessment
│   │   │   ├── decision_agent.py   # Final decision
│   │   │   ├── portfolio_agent.py  # Portfolio analysis
│   │   │   └── base_agent.py       # Agent base class
│   │   ├── skills/            # Skill framework
│   │   │   ├── skill_agent.py # Skill-driven agent
│   │   │   ├── router.py      # Skill routing (auto/manual)
│   │   │   ├── aggregator.py  # Skill result aggregation
│   │   │   ├── defaults.py    # Default skill configs
│   │   │   └── base.py        # Skill base class
│   │   ├── strategies/        # Strategy framework
│   │   │   ├── strategy_agent.py  # Strategy execution
│   │   │   ├── router.py      # Strategy routing
│   │   │   └── aggregator.py  # Strategy aggregation
│   │   └── tools/             # Agent tool registry
│   │       ├── registry.py    # Tool registration
│   │       ├── analysis_tools.py   # Analysis tools
│   │       ├── data_tools.py       # Data fetching tools
│   │       ├── market_tools.py     # Market data tools
│   │       ├── search_tools.py     # Search tools
│   │       └── backtest_tools.py   # Backtest tools
│   │
│   ├── notification_sender/   # Channel-specific senders (12 files)
│   │   ├── telegram_sender.py
│   │   ├── email_sender.py
│   │   ├── discord_sender.py
│   │   ├── slack_sender.py
│   │   ├── feishu_sender.py
│   │   ├── wechat_sender.py
│   │   ├── pushover_sender.py
│   │   ├── pushplus_sender.py
│   │   ├── serverchan3_sender.py
│   │   ├── custom_webhook_sender.py
│   │   └── astrbot_sender.py
│   │
│   └── data/                  # Static data mappings
│       └── stock_mapping.py   # Stock code → name mapping
│
├── data_provider/             # Market data fetcher subsystem (12 files)
│   ├── base.py                # DataFetcherManager + BaseFetcher (~900 lines)
│   ├── akshare_fetcher.py     # AkShare (EastMoney scraper)
│   ├── efinance_fetcher.py    # efinance (EastMoney API)
│   ├── tushare_fetcher.py     # Tushare Pro
│   ├── baostock_fetcher.py    # BaoStock
│   ├── pytdx_fetcher.py       # pytdx (TDX protocol)
│   ├── yfinance_fetcher.py    # Yahoo Finance
│   ├── tickflow_fetcher.py    # TickFlow SDK
│   ├── fundamental_adapter.py # Fundamental data aggregator
│   ├── realtime_types.py      # Realtime data type definitions
│   └── us_index_mapping.py    # US stock/index identification
│
├── strategies/                # YAML strategy definitions (11 files)
│   ├── shrink_pullback.yaml   # Volume shrink pullback
│   ├── bull_trend.yaml        # Bull trend
│   ├── ma_golden_cross.yaml   # MA golden cross
│   ├── volume_breakout.yaml   # Volume breakout
│   ├── chan_theory.yaml        # Chan theory
│   └── ... (6 more)
│
├── api/                       # FastAPI REST API (8 files)
│   ├── app.py                 # FastAPI application factory
│   ├── deps.py                # Dependency injection
│   ├── v1/router.py           # API v1 route definitions
│   └── middlewares/           # Auth + error handling middleware
│
├── bot/                       # Chatbot integrations (19 files)
│   ├── handler.py             # Message handler
│   ├── dispatcher.py          # Command dispatcher
│   ├── commands/              # Bot commands (analyze, chat, market, etc.)
│   └── platforms/             # Platform adapters (DingTalk, Discord, Feishu)
│
├── apps/
│   ├── dsa-web/               # React + Vite Web UI
│   │   ├── src/
│   │   │   ├── App.tsx        # Root component with routing
│   │   │   ├── api/           # API client layer (12 files)
│   │   │   ├── components/    # UI components (~80 files)
│   │   │   ├── pages/         # Page components
│   │   │   ├── contexts/      # React contexts (Auth)
│   │   │   ├── stores/        # Zustand stores
│   │   │   └── hooks/         # Custom hooks
│   │   └── package.json       # React 19, Vite 7, TailwindCSS 4
│   │
│   └── dsa-desktop/           # Electron desktop wrapper
│       └── (Electron main process + build scripts)
│
├── .github/
│   ├── workflows/             # CI/CD (10 workflows)
│   │   ├── ci.yml             # Main CI: ai-governance + backend-gate + web-gate + docker
│   │   ├── daily_analysis.yml # Scheduled daily analysis
│   │   ├── pr-review.yml      # PR review automation
│   │   └── ... (7 more)
│   └── scripts/               # GitHub automation scripts
│
├── docker/                    # Docker configs
├── scripts/                   # Utility scripts (build, deploy, CI)
├── tests/                     # pytest tests
├── templates/                 # Jinja2 report templates
└── docs/                      # Documentation (this directory)
```

---

## Key Entry Points

| Entry | File | Purpose |
|-------|------|---------|
| CLI | `main.py` | Parse args → run_full_analysis / schedule / serve / backtest |
| API | `server.py` → `api/app.py` | FastAPI ASGI app |
| Pipeline | `src/core/pipeline.py` | `StockAnalysisPipeline.run()` → fetch → analyze → notify |
| Data | `data_provider/base.py` | `DataFetcherManager.get_daily_data()` with fallback |
| LLM | `src/analyzer.py` | `GeminiAnalyzer.analyze()` via LiteLLM |
| Agent | `src/agent/executor.py` | `AgentExecutor.run()` for multi-agent pipeline |
| Bot | `bot/handler.py` | `BotHandler.handle()` dispatches to commands |

---

## Technology Stack

### Backend
- **Language:** Python 3.10+
- **Framework:** FastAPI + Uvicorn
- **Database:** SQLite (via SQLAlchemy)
- **LLM:** LiteLLM (Gemini, Claude, GPT, DeepSeek, Ollama)
- **Data:** pandas, numpy, efinance, akshare, tushare, baostock, pytdx, yfinance, tickflow
- **Search:** Tavily, Bocha, Brave, SerpAPI, SearXNG
- **Notification:** 12 sender implementations

### Frontend (dsa-web)
- **Framework:** React 19 + TypeScript 5.9
- **Build:** Vite 7
- **Styling:** TailwindCSS 4
- **State:** Zustand 5
- **Routing:** React Router 7
- **Charts:** Recharts 3
- **Markdown:** react-markdown + remark-gfm
- **Testing:** Vitest + Playwright

### Desktop (dsa-desktop)
- **Shell:** Electron
- **Build:** Custom PowerShell/bash scripts
- **Release:** GitHub Actions desktop-release workflow

### CI/CD
- **Platform:** GitHub Actions
- **Checks:** ai-governance, backend-gate (ci_gate.sh), web-gate (lint+build), Docker build
- **Release:** Auto-tag (#patch/#minor/#major), Docker publish, desktop release

---

## Database Schema

SQLite database at `./data/stock_analysis.db` managed via SQLAlchemy:
- `daily_data` — Historical OHLCV bars
- `analysis_history` — LLM analysis results + context snapshots
- `news_intel` — Cached news intelligence
- `fundamental_snapshot` — Fundamental data snapshots
- `backtest_results` — Backtest evaluations
- `portfolio_*` — Portfolio tables (holdings, transactions, snapshots)
