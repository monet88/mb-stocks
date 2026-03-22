# System Architecture

> High-level architecture of the Daily Stock Analysis (DSA) system.

---

## Architecture Diagram

```mermaid
graph TD
    subgraph Entry["Entry Points"]
        CLI["main.py<br/>CLI / Scheduler"]
        API["server.py<br/>FastAPI"]
        BOT["bot/handler.py<br/>Chatbot Gateway"]
    end

    subgraph Core["Core Pipeline"]
        PIPE["StockAnalysisPipeline<br/>src/core/pipeline.py"]
        MR["MarketReview<br/>src/core/market_review.py"]
        TC["TradingCalendar<br/>src/core/trading_calendar.py"]
        BT["BacktestEngine<br/>src/core/backtest_engine.py"]
    end

    subgraph Data["Data Layer"]
        DFM["DataFetcherManager<br/>data_provider/base.py"]
        EF["efinance"]
        AK["akshare"]
        TU["tushare"]
        PTD["pytdx"]
        BS["baostock"]
        YF["yfinance"]
        TF["tickflow"]
        FA["FundamentalAdapter"]
    end

    subgraph AI["AI Layer"]
        GA["GeminiAnalyzer<br/>src/analyzer.py"]
        LLM["LiteLLM Router<br/>Multi-channel"]
        AGENT["Agent System<br/>src/agent/"]
    end

    subgraph Intel["Intelligence"]
        SS["SearchService<br/>Multi-engine news"]
        SOC["SocialSentiment<br/>US stocks"]
    end

    subgraph Output["Output Layer"]
        NS["NotificationService"]
        DB["SQLite Database"]
        FD["Feishu Cloud Docs"]
    end

    subgraph Frontend["Frontend"]
        WEB["dsa-web<br/>React + Vite"]
        DSK["dsa-desktop<br/>Electron"]
    end

    CLI --> PIPE
    CLI --> MR
    API --> PIPE
    BOT --> PIPE

    PIPE --> DFM
    PIPE --> GA
    PIPE --> SS
    PIPE --> SOC
    PIPE --> NS
    PIPE --> DB
    PIPE --> TC

    MR --> GA
    MR --> SS

    DFM --> EF
    DFM --> AK
    DFM --> TU
    DFM --> PTD
    DFM --> BS
    DFM --> YF
    DFM --> TF
    DFM --> FA

    GA --> LLM
    AGENT --> LLM

    WEB --> API
    DSK --> API
    BOT --> API
```

---

## Layer Description

### 1. Entry Layer

Three ways to enter the system:

| Entry | Mode | Description |
|-------|------|-------------|
| `main.py` | CLI | Parses args, runs one-shot or scheduled analysis |
| `server.py` | API | FastAPI ASGI server with REST endpoints |
| `bot/` | Chat | Message handler → command dispatcher → analysis |

The `main.py` supports combined modes: `--serve` starts API server in a background thread while still running analysis.

### 2. Core Pipeline (`src/core/`)

**`StockAnalysisPipeline`** is the central orchestrator (1475 lines):

```
For each stock in watchlist:
  1. fetch_and_save_stock_data() — DB cache check → DataFetcherManager
  2. analyze_stock() — 8-step analysis:
     a. Get realtime quote (with circuit breaker)
     b. Get chip distribution
     c. Get fundamental context (with timeout budget)
     d. Run trend analysis (MA alignment, buy signals)
     e. Search news intelligence (multi-dimensional)
     f. Get social sentiment (US only)
     g. Build enhanced context
     h. Call LLM analysis → AnalysisResult
  3. Notify — send results through configured channels
```

**Two analysis paths:**
- **Traditional path** — Direct LLM call with enhanced context
- **Agent path** — Multi-agent pipeline (intel → technical → risk → decision)

### 3. Data Provider Layer (`data_provider/`)

`DataFetcherManager` implements a **priority-ordered fallback chain**:

```
efinance (P0) → akshare (P1) → tushare (P2) → pytdx (P2) → baostock (P3) → yfinance (P4)
```

Each fetcher extends `BaseFetcher` with:
- `_fetch_raw_data()` — Provider-specific API call
- `_normalize_data()` — Standardize to `STANDARD_COLUMNS`

**Specialized subsystems:**
- **Realtime quotes** — Tencent → Sina → efinance → EastMoney with circuit breaker
- **Chip distribution** — Via DataFetcherManager with fuse protection
- **Fundamental pipeline** — Aggregated context with timeout/retry/cache

**Market routing:**
- US stocks (`^[A-Z]{1,5}$`) → `YfinanceFetcher` (early return, no fallback)
- HK stocks (`HK` prefix) → General chain
- A-share (6-digit) → General chain

### 4. AI Layer

**GeminiAnalyzer** (`src/analyzer.py`):
- Uses LiteLLM for unified model access
- Supports multi-channel configuration (YAML or env vars)
- Temperature, retry, and token limit controls
- Report integrity validation with placeholder fill

**Agent System** (`src/agent/`):
- **Architecture:** `single` (legacy) or `multi` (orchestrator)
- **Orchestrator modes:** quick / standard / full / specialist
- **Specialized agents:** intel, technical, risk, decision, portfolio
- **Skill system:** 11 YAML strategies (shrink_pullback, bull_trend, chan_theory, etc.)
- **Tool registry:** analysis, data, market, search, backtest tools

### 5. Intelligence Layer

**SearchService** — Multi-engine news search:
- Engines: Tavily, Bocha, Brave, SerpAPI, SearXNG (self-hosted + public)
- Multi-key load balancing per engine
- Multi-dimensional search: latest news + risk scan + earnings
- Configurable news window (ultra_short/short/medium/long)

**SocialSentimentService** — US stocks only:
- Reddit, X (Twitter), Polymarket data
- External API at api.adanos.org

### 6. Output Layer

**NotificationService** — 12 channels:
| Channel | Type |
|---------|------|
| WeChat Enterprise | Webhook |
| Feishu | Webhook |
| Telegram | Bot API |
| Email | SMTP |
| Discord | Bot / Webhook |
| Slack | Webhook / Bot |
| PushPlus | Token |
| Pushover | API |
| Server酱3 | SendKey |
| Custom Webhook | POST JSON |
| AstrBot | Token |
| Feishu Cloud Docs | API |

Features: batch splitting for length limits, markdown-to-image for non-MD channels, merged notification mode, stock-group email routing.

**Database** — SQLite via SQLAlchemy:
- Analysis history with context snapshots
- News intelligence cache
- Fundamental snapshots
- Backtest results
- Portfolio data

### 7. Frontend Layer

**dsa-web** (React 19 + Vite 7):
- Pages: Home (analysis), Chat (AI chat), Portfolio, Backtest, Settings
- Zustand state management
- Axios API client with auth context
- TailwindCSS 4 styling
- Motion animations
- Recharts for data visualization

**dsa-desktop** (Electron):
- Wraps dsa-web build output
- Platform-specific build scripts
- GitHub Actions release workflow

---

## Data Flow

```mermaid
sequenceDiagram
    participant U as User/Scheduler
    participant P as Pipeline
    participant D as DataFetcherManager
    participant DB as SQLite
    participant AI as LLM (LiteLLM)
    participant S as SearchService
    participant N as NotificationService

    U->>P: run(stock_codes)
    loop For each stock
        P->>DB: has_today_data?
        alt Cache hit
            DB-->>P: skip fetch
        else Cache miss
            P->>D: get_daily_data(code)
            D-->>P: DataFrame
            P->>DB: save_daily_data()
        end
        P->>D: get_realtime_quote(code)
        P->>D: get_chip_distribution(code)
        P->>D: get_fundamental_context(code)
        P->>P: trend_analysis(df)
        P->>S: search_comprehensive_intel(code)
        P->>AI: analyze(enhanced_context + news)
        AI-->>P: AnalysisResult
        P->>DB: save_analysis_history()
    end
    P->>N: send(results)
    N-->>U: Notifications delivered
```

---

## Configuration Architecture

All configuration flows through `src/config.py` → `Config` dataclass:

```
.env file → python-dotenv → os.getenv() → Config._load_from_env() → Config (singleton)
```

Config groups (~2150 lines):
- Stock list, Feishu docs, data source tokens
- AI/LLM: multi-channel, multi-key, temperature, retry
- Agent: mode, architecture, skills, orchestrator settings
- Search: 6 engine configs with multi-key support
- Notification: 12 channel configurations
- Backtest, portfolio, trading calendar
- WebUI, bot, flow control, logging
