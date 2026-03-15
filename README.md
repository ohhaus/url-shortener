# url-shortener
```
 ██╗   ██╗██████╗ ██╗         ███████╗██╗  ██╗ ██████╗ ██████╗ ████████╗███████╗███╗   ██╗███████╗██████╗
 ██║   ██║██╔══██╗██║         ██╔════╝██║  ██║██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝████╗  ██║██╔════╝██╔══██╗
 ██║   ██║██████╔╝██║         ███████╗███████║██║   ██║██████╔╝   ██║   █████╗  ██╔██╗ ██║█████╗  ██████╔╝
 ██║   ██║██╔══██╗██║         ╚════██║██╔══██║██║   ██║██╔══██╗   ██║   ██╔══╝  ██║╚██╗██║██╔══╝  ██╔══██╗
 ╚██████╔╝██║  ██║███████╗    ███████║██║  ██║╚██████╔╝██║  ██║   ██║   ███████╗██║ ╚████║███████╗██║  ██║
  ╚═════╝ ╚═╝  ╚═╝╚══════╝    ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
```

> Высокопроизводительный асинхронный сервис сокращения URL  
> на FastAPI + PostgreSQL + Redis + ARQ

---

## Stack
```
┌─────────────────────────────────────────────────────────┐
│                        CLIENT                           │
└───────────────────────────┬─────────────────────────────┘
                            │ HTTP
┌───────────────────────────▼─────────────────────────────┐
│              FastAPI  (Gunicorn + Uvicorn)               │
│                                                         │
│  POST /             →  create short URL                 │
│  GET  /{code}       →  redirect (cache-first)           │
│  GET  /{code}/info  →  stats                            │
│  DELETE /{code}     →  delete                           │
└───────┬─────────────────────────┬───────────────────────┘
        │                         │
┌───────▼───────┐       ┌─────────▼─────────┐
│  PostgreSQL   │       │       Redis        │
│               │       │                   │
│  short_url    │       │  redirect:{code}  │  TTL 1h
│  ┌──────────┐ │       │  clicks:{code}    │  TTL 5m
│  │short_code│ │       │  rate_limit:{ip}  │  TTL 1m
│  │orig_url  │ │       └─────────┬─────────┘
│  │clicks    │ │                 │
│  │created_at│ │       ┌─────────▼─────────┐
│  └──────────┘ │       │    ARQ Worker      │
└───────────────┘       │                   │
                        │  record_click()   │
                        │  max_tries=3      │
                        └───────────────────┘
```

---

## Quick Start (Docker)
```bash
# 1. Клонировать репозиторий
git clone https://github.com/your-org/url-shortener
cd url-shortener

# 2. Создать .env
cp .env.example .env

# 3. Собрать образы
make build

# 4. Применить миграции
make migrate

# 5. Запустить все сервисы
make up

# 6. Проверить статус
docker compose ps

# 7. Smoke test
curl -X POST http://localhost:8000/ \
     -H "Content-Type: application/json" \
     -d '{"original_url": "https://example.com"}'
```

---

## Development (локально)
```bash
# Установить зависимости
pip install -e ".[dev]"

# Поднять только инфраструктуру
make dev          # запускает db + redis + uvicorn --reload

# В отдельном терминале — воркер
make worker-dev

# Создать миграцию
make migrate-create m=add_user_table

# Применить миграции
make migrate
```

---

## Project Structure
```
url-shortener/
├── src/
│   ├── main.py                  # entrypoint, lifespan
│   ├── api.py                   # router registry
│   ├── config.py                # pydantic settings
│   ├── logging.py               # unified logging setup
│   │
│   ├── shortener/
│   │   ├── __init__.py          # exports shorten_router
│   │   ├── views.py             # HTTP handlers
│   │   ├── services.py          # business logic
│   │   ├── dependencies.py      # FastAPI DI
│   │   ├── models.py            # SQLAlchemy ORM
│   │   ├── schemas.py           # Pydantic I/O
│   │   ├── exceptions.py        # domain exceptions
│   │   └── decorators.py        # retry_on_integrity_error
│   │
│   ├── cache/
│   │   ├── redis.py             # RedisManager (singleton)
│   │   ├── services.py          # CacheService
│   │   ├── keys.py              # RedisKeys namespace
│   │   └── dependencies.py      # get_cache_service
│   │
│   ├── database/
│   │   ├── base.py              # DeclarativeBase + created_at
│   │   ├── engine.py            # async engine factory
│   │   └── sessions.py          # AsyncSessionLocal, get_async_session
│   │
│   └── worker/
│       ├── client.py            # ARQClient
│       ├── tasks.py             # record_click, WorkerSettings
│       └── worker.py            # entrypoint
│
├── tests/
│   ├── conftest.py              # fixtures, overrides
│   ├── utils/
│   │   ├── factories.py         # ShortURLFactory
│   │   └── mocks.py             # MockCacheService
│   ├── test_shortener.py        # API integration tests
│   ├── test_services.py         # service unit tests
│   ├── test_cache.py            # cache unit tests
│   ├── test_worker.py           # worker unit tests
│   ├── test_decorators.py       # decorator unit tests
│   ├── test_migrations.py       # schema tests
│   └── test_security.py         # security tests
│
├── alembic/
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── .coveragerc
├── .env.example
├── pyproject.toml
└── README.md
```

---

## Make Commands
```
Infrastructure
─────────────────────────────────────────
make build          Build all images
make up             Start all services
make down           Stop all services
make restart        Restart app + worker
make logs           Follow logs (all)
make logs-app       Follow app logs
make logs-worker    Follow worker logs
make shell          Shell inside app container

Database
─────────────────────────────────────────
make migrate                Apply migrations
make migrate-create m=name  Create new migration

Development
─────────────────────────────────────────
make dev            Start infra + run app locally
make worker-dev     Run worker locally

Testing & Quality
─────────────────────────────────────────
make test           Run all tests
make test-cov       Run tests with HTML coverage report
make test-fast      Run tests, skip slow
make lint           Run ruff lint
make format         Run ruff format
make check          lint + format check (CI)

Cleanup
─────────────────────────────────────────
make clean          Remove .pyc / __pycache__
make prune          Remove stopped containers + volumes
```

---

## API Reference
```
POST   /
────────────────────────────────────────────────────────
Body:    { "original_url": "https://example.com" }
Returns: { "short_code": "aB3xYz", "original_url": "...", "clicks": 0 }
Status:  201 Created
         409 Conflict  — не удалось сгенерировать уникальный код
         422            — невалидный URL

GET    /{short_code}
────────────────────────────────────────────────────────
Returns: 302 Redirect → original_url   (cache-first)
         404 Not Found

GET    /{short_code}/info
────────────────────────────────────────────────────────
Returns: { "short_code": "aB3xYz", "original_url": "...", "clicks": 42 }
Status:  200 OK
         404 Not Found

DELETE /{short_code}
────────────────────────────────────────────────────────
Returns: { "status": "deleted", "short_code": "aB3xYz" }
Status:  200 OK
         404 Not Found
```

---

## Configuration

Все настройки через переменные окружения. Префиксы:
```
APP_*        →  ApplicationSettings
DATABASE_*   →  DatabaseSettings
REDIS_*      →  RedisSettings
WORKER_*     →  WorkerSettings
LOG_*        →  LoggingSettings
```

---

## Redirect Flow
```
GET /{code}
     │
     ▼
Redis.get("redirect:{code}")
     │
     ├── HIT ──────────────────────────► 302 Redirect
     │                                       │
     └── MISS                           enqueue_click()
          │                                  │
          ▼                             ARQ Worker
     PostgreSQL.select(ShortURL)             │
          │                            UPDATE clicks += 1
          ├── NOT FOUND ───────────► 404
          │
          └── FOUND
               │
               ▼
          Redis.setex("redirect:{code}", TTL=3600)
               │
               ▼
          302 Redirect
```

---

## Testing
```bash
# Все тесты
make test

# С HTML отчётом покрытия
make test-cov
# → открыть htmlcov/index.html

# Быстрый прогон (без slow/load)
make test-fast
```

Тесты используют SQLite in-memory — внешние зависимости не нужны.
```
tests/test_cache.py          ████████████  12 passed
tests/test_decorators.py     ████████████   4 passed
tests/test_migrations.py     ████████████   3 passed
tests/test_security.py       ████████████   4 passed
tests/test_services.py       ████████████  13 passed
tests/test_shortener.py      ████████████  12 passed
tests/test_worker.py         ████████████   8 passed
─────────────────────────────────────────────────────
TOTAL                                      56 passed
```

---

## Production Checklist
```
[ ] Сменить все пароли из .env.example
[ ] APP_ENVIRONMENT=production
[ ] APP_DEBUG=False
[ ] DATABASE_ECHO_SQL=False
[ ] Настроить APP_BASE_URL под реальный домен
[ ] Поставить reverse proxy (nginx / Caddy) перед app
[ ] Настроить TLS
[ ] Ограничить порты db и redis — не открывать наружу
[ ] Настроить log aggregation (Loki / Datadog / ELK)
[ ] Настроить алерты на worker queue lag
```

---

## License

MIT