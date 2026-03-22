# Code Standards

> Conventions, patterns, and quality rules observed in the mb-stocks codebase.

---

## Language & Formatting

| Rule | Standard |
|------|----------|
| Python version | 3.10+ (type hints, `|` union syntax avoided for 3.10 compat) |
| TypeScript version | 5.9 (strict mode) |
| Encoding | UTF-8, `# -*- coding: utf-8 -*-` header on Python files |
| Line endings | CRLF (Windows development, Git normalizes) |
| Indentation | 4 spaces (Python), 2 spaces (TypeScript/CSS) |
| Max line length | Soft 120 (no hard enforcement via linter config) |
| Docstrings | Chinese comments dominant; public APIs have Chinese docstrings |
| File header | Module-level docstring with `===` banner, responsibility list |

---

## Python Conventions

### Naming
- **Files:** `snake_case.py`, descriptive names (`stock_trend_analyzer.py`, `social_sentiment_service.py`)
- **Classes:** `PascalCase` (`StockAnalysisPipeline`, `DataFetcherManager`)
- **Functions:** `snake_case` (`get_daily_data`, `run_full_analysis`)
- **Constants:** `UPPER_SNAKE_CASE` (`STANDARD_COLUMNS`, `_US_STOCK_PATTERN`)
- **Private:** Leading underscore (`_is_us_market`, `_enhance_context`)

### Architecture Patterns
1. **Singleton Config** — `Config.get_instance()` with `@dataclass` and `_load_from_env()` class method
2. **Manager + Fetcher** — `DataFetcherManager` orchestrates multiple `BaseFetcher` subclasses with priority-ordered fallback
3. **Pipeline** — `StockAnalysisPipeline` coordinates fetch → analyze → notify in a step-by-step flow
4. **Service layer** — `src/services/` provides business logic consumed by API routes and CLI
5. **Repository layer** — `src/repositories/` encapsulates database queries (SQLAlchemy)
6. **Agent framework** — Factory-built `AgentExecutor` with tool registry, skill router, and specialized agents
7. **Channel senders** — Each notification channel has its own `*_sender.py` implementing a common interface

### Error Handling
- **Fail-open by default** — Individual stock failure doesn't stop batch; individual notification channel failure doesn't block others
- **Try/except with logging** — Most external calls wrapped in try/except with `logger.warning()`
- **Circuit breaker** — Realtime data sources use circuit breaker with configurable cooldown
- **Graceful degradation** — Missing features (no API key, no search service) degrade gracefully

### Configuration
- **All config from env vars** — Single `Config` dataclass (~2150 lines) reads everything from `os.getenv()`
- **`.env` file** — `python-dotenv` loads `.env`; `.env.example` is the source of truth for available vars
- **Parse helpers** — `parse_env_bool()`, `parse_env_int()`, `parse_env_float()` with fallback + warning
- **No hardcoded values** — Secrets, URLs, API keys, model names are never hardcoded

### Import Style
```python
# stdlib first, then third-party, then local — standard Python convention
import os
import logging

import pandas as pd
from fastapi import FastAPI

from src.config import get_config, Config
from data_provider.base import DataFetcherManager
```

### Logging
- `logging.getLogger(__name__)` at module level
- Chinese log messages for operational logs (targeted at Chinese users)
- `f-string` formatting in log messages (not % formatting)
- Log levels: `INFO` for flow milestones, `WARNING` for recoverable errors, `ERROR` for failures, `DEBUG` for data dumps

---

## TypeScript / React Conventions (dsa-web)

### Naming
- **Files:** `PascalCase.tsx` for components, `camelCase.ts` for utilities
- **Components:** Functional components with `React.FC` type annotation
- **Stores:** Zustand stores in `stores/` directory with `use*Store` naming

### Patterns
- **React 19** with React Compiler (babel plugin)
- **Zustand** for global state (not Redux)
- **React Router 7** with `<Shell>` layout component
- **Axios** for API calls with centralized error handling
- **TailwindCSS 4** with `tailwind-merge` for conditional classes
- **Motion** (Framer Motion) for animations
- **Lucide + Remix Icons** for iconography

### Component Structure
```
components/
├── common/          # Reusable UI primitives (Button, Card, Input, etc.)
├── layout/          # Shell, ShellHeader, SidebarNav
├── report/          # Report display components
├── history/         # Analysis history list
└── StockAutocomplete/  # Feature-specific component group
```

---

## Data Provider Standards

### Adding a New Fetcher
1. Create `data_provider/new_fetcher.py` extending `BaseFetcher`
2. Implement `_fetch_raw_data(stock_code, start_date, end_date)` → `pd.DataFrame`
3. Implement `_normalize_data(df, stock_code)` → standardized columns
4. Standard columns: `['date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'pct_chg']`
5. Register in `DataFetcherManager._init_default_fetchers()` with try/except import
6. Wrap import in try/except so missing dependency doesn't break startup

### Market Routing
- US stocks matched by regex `^[A-Z]{1,5}(\.[A-Z])?$` → `YfinanceFetcher`
- HK stocks identified by `HK` prefix → routed through general fetcher chain
- A-share stocks: 6-digit codes → general fetcher chain with priority fallback

---

## CI / Quality Gates

| Gate | Tool | Blocking |
|------|------|----------|
| `ai-governance` | `scripts/check_ai_assets.py` | Yes |
| `backend-gate` | `scripts/ci_gate.sh` (flake8 + pytest + py_compile) | Yes |
| `web-gate` | `npm run lint && npm run build` | Yes (when web changed) |
| `docker-build` | Docker build + import smoke | Yes |
| `network-smoke` | `pytest -m network` | No (observational) |
| `pr-review` | AI review + labels | No (advisory) |

### Commit Convention
- English commit messages
- Conventional format: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`, `test:`
- Issue references: `(#NNN)` or `(Issue #NNN)`
- Auto-tag triggered only by `#patch`, `#minor`, `#major` in commit title

---

## Security Rules

- No hardcoded secrets, keys, paths, model names, or port numbers
- API keys via env vars only
- `.env` never committed (in `.gitignore`)
- Webhook SSL verification on by default (`webhook_verify_ssl: True`)
- Auth middleware for API endpoints (configurable)
- Rate limiting for bot commands
