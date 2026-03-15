# url-shortener
```
 ██╗   ██╗██████╗ ██╗         ███████╗██╗  ██╗ ██████╗ ██████╗ ████████╗███████╗███╗   ██╗███████╗██████╗
 ██║   ██║██╔══██╗██║         ██╔════╝██║  ██║██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝████╗  ██║██╔════╝██╔══██╗
 ██║   ██║██████╔╝██║         ███████╗███████║██║   ██║██████╔╝   ██║   █████╗  ██╔██╗ ██║█████╗  ██████╔╝
 ██║   ██║██╔══██╗██║         ╚════██║██╔══██║██║   ██║██╔══██╗   ██║   ██╔══╝  ██║╚██╗██║██╔══╝  ██╔══██╗
 ╚██████╔╝██║  ██║███████╗    ███████║██║  ██║╚██████╔╝██║  ██║   ██║   ███████╗██║ ╚████║███████╗██║  ██║
  ╚═════╝ ╚═╝  ╚═╝╚══════╝    ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
```

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=flat-square&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white)
![Coverage](https://img.shields.io/badge/coverage-90.67%25-brightgreen?style=flat-square&logo=pytest)
![Tests](https://img.shields.io/badge/tests-83%20passed-brightgreen?style=flat-square&logo=pytest)
![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)

</div>

> Высокопроизводительный асинхронный сервис сокращения URL  
> FastAPI + PostgreSQL + Redis + ARQ + Loguru

---

## Stack
```
┌─────────────────────────────────────────────────────────┐
│                        CLIENT                           │
└───────────────────────────┬─────────────────────────────┘
                            │ HTTP
┌───────────────────────────▼─────────────────────────────┐
│         FastAPI  (Gunicorn + UvicornWorker)              │
│                                                         │
│  POST /             →  create short URL                 │
│  GET  /{code}       →  redirect (cache-first)           │
│  GET  /{code}/info  →  stats                            │
│  DELETE /{code}     →  delete                           │
│  GET  /health       →  health check                     │
└───────┬─────────────────────────┬───────────────────────┘
        │                         │
┌───────▼───────┐       ┌─────────▼─────────┐
│  PostgreSQL   │       │       Redis        │
│               │       │                   │
│  short_url    │       │  redirect:{code}  │  TTL 1h
│  ┌──────────┐ │       │  rate_limit:{ip}  │  TTL 1m
│  │short_code│ │       └─────────┬─────────┘
│  │orig_url  │ │                 │
│  │clicks    │ │       ┌─────────▼─────────┐
│  │created_at│ │       │    ARQ Worker      │
│  └──────────┘ │       │  record_click()   │
└───────────────┘       │  max_tries=3      │
                        └───────────────────┘
```

---

## Features

| Feature | Description |
|---|---|
| 🔗 Сокращение URL | `POST /` → уникальный 6-символьный код |
| ♻️ Дедупликация | `?deduplicate=true` — одна ссылка, один код |
| ⚡ Cache-first редирект | Redis → DB только при cache miss |
| 📊 Счётчик кликов | Асинхронно через ARQ worker |
| 🛡️ Rate limiting | 60 POST / мин по IP через Redis |
| 🔒 SSRF защита | Блокировка приватных IP-диапазонов |
| ❤️ Health check | `GET /health` → статус DB + Redis |
| 📋 Единые логи | Loguru — все сервисы в одном формате |
| ♾️ Бессрочные ссылки | Ссылки не истекают |

---

## Quick Start
```bash
# 1. Клонировать репозиторий
git clone https://github.com/your-org/url-shortener
cd url-shortener

# 2. Создать .env из примера
cp .env.example .env

# 3. Установить зависимости
make install

# 4. Собрать Docker образы
make build

# 5. Применить миграции
make migrate

# 6. Запустить все сервисы
make up

# 7. Smoke test
curl -X POST http://localhost:8000/ \
     -H "Content-Type: application/json" \
     -d '{"original_url": "https://example.com"}'
```

---

## Development
```bash
# 1. Установить зависимости (включая dev)
make install

# 2. Поднять инфраструктуру + запустить приложение локально
make dev

# 3. Воркер — в отдельном терминале
make worker-dev

# 4. Создать и применить миграцию
make migrate-create m=add_user_table
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
│   ├── logging.py               # loguru + InterceptHandler
│   ├── health.py                # GET /health
│   ├── middleware.py            # rate limit
│   │
│   ├── shortener/               # core domain
│   │   ├── views.py
│   │   ├── services.py
│   │   ├── dependencies.py
│   │   ├── models.py
│   │   ├── schemas.py           # + SSRF валидация
│   │   ├── exceptions.py
│   │   └── decorators.py
│   │
│   ├── cache/                   # redis abstraction
│   │   ├── redis.py
│   │   ├── services.py
│   │   ├── keys.py
│   │   └── dependencies.py
│   │
│   ├── database/                # sqlalchemy + alembic
│   │   ├── base.py
│   │   ├── engine.py
│   │   ├── sessions.py
│   │   └── revisions/
│   │
│   └── worker/                  # arq async tasks
│       ├── client.py
│       ├── tasks.py
│       └── worker.py
│
├── tests/
│   ├── conftest.py
│   ├── utils/
│   │   ├── factories.py
│   │   └── mocks.py
│   ├── test_shortener.py
│   ├── test_services.py
│   ├── test_cache.py
│   ├── test_worker.py
│   ├── test_decorators.py
│   ├── test_health.py
│   ├── test_middleware.py
│   ├── test_migrations.py
│   ├── test_schemas.py
│   └── test_security.py
│
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── .env.example
└── pyproject.toml
```

---

## Make Commands
```
Setup                       Database
──────────────────────────  ──────────────────────────────────
make install                make migrate
                            make migrate-create m=name
Infrastructure
──────────────────────────  Development
make build                  ──────────────────────────────────
make up                     make dev
make down                   make worker-dev
make restart
make logs                   Cleanup
make logs-app               ──────────────────────────────────
make logs-worker            make clean
make shell                  make prune

Testing & Quality
──────────────────────────
make test
make test-cov
make test-fast
make lint
make format
make check
```

---

## API Reference
```
POST   /
  Query:   ?deduplicate=true (default) | false
  Body:    { "original_url": "https://example.com" }
  201:     { "short_code": "aB3xYz", "original_url": "...", "clicks": 0 }
  409:     не удалось сгенерировать уникальный код
  422:     невалидный URL / SSRF / запрещённая схема

GET    /{short_code}
  302:     Redirect → original_url  (cache-first)
  404:     Not Found

GET    /{short_code}/info
  200:     { "short_code": "aB3xYz", "original_url": "...", "clicks": 42 }
  404:     Not Found

DELETE /{short_code}
  200:     { "status": "deleted", "short_code": "aB3xYz" }
  404:     Not Found

GET    /health
  200:     { "status": "ok",       "checks": { "database": "ok",          "redis": "ok"          } }
  200:     { "status": "degraded", "checks": { "database": "unavailable", "redis": "unavailable" } }
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

## Security

| Защита | Описание |
|---|---|
| SSRF | Блокировка `127.x`, `10.x`, `172.16.x`, `192.168.x`, `169.254.x` (AWS metadata), IPv6 private |
| Rate Limit | 60 POST / мин по IP → `429`. Сбой Redis → fail open |
| URL схема | Разрешены только `http` / `https`. `javascript:`, `data:`, `ftp:` → `422` |
| Swagger | Отключён в продакшне (`APP_DEBUG=False`) |

---

## Testing
```bash
make test          # все тесты
make test-cov      # тесты + htmlcov/index.html
make test-fast     # без slow/load маркеров
```

### Coverage — 91.95%

| Module | Stmts | Cover |
|---|---|---|
| `src/api.py` | 6 | ![100%](https://img.shields.io/badge/-100%25-brightgreen?style=flat-square) |
| `src/cache/keys.py` | 13 | ![100%](https://img.shields.io/badge/-100%25-brightgreen?style=flat-square) |
| `src/cache/redis.py` | 18 | ![100%](https://img.shields.io/badge/-100%25-brightgreen?style=flat-square) |
| `src/cache/services.py` | 17 | ![100%](https://img.shields.io/badge/-100%25-brightgreen?style=flat-square) |
| `src/middleware.py` | 27 | ![100%](https://img.shields.io/badge/-100%25-brightgreen?style=flat-square) |
| `src/shortener/services.py` | 65 | ![100%](https://img.shields.io/badge/-100%25-brightgreen?style=flat-square) |
| `src/shortener/dependencies.py` | 15 | ![100%](https://img.shields.io/badge/-100%25-brightgreen?style=flat-square) |
| `src/worker/client.py` | 25 | ![100%](https://img.shields.io/badge/-100%25-brightgreen?style=flat-square) |
| `src/worker/tasks.py` | 20 | ![100%](https://img.shields.io/badge/-100%25-brightgreen?style=flat-square) |
| `src/shortener/views.py` | 30 | ![93%](https://img.shields.io/badge/-93.33%25-green?style=flat-square) |
| `src/shortener/schemas.py` | 39 | ![88%](https://img.shields.io/badge/-88.24%25-green?style=flat-square) |
| `src/logging.py` | 32 | ![87%](https://img.shields.io/badge/-86.84%25-green?style=flat-square) |
| `src/health.py` | 24 | ![83%](https://img.shields.io/badge/-83.33%25-yellow?style=flat-square) |
| **TOTAL** | **415** | ![90.67%](https://img.shields.io/badge/-91.95%25-brightgreen?style=flat-square) |

### Test Suites

| Suite | Tests | Description |
|---|---|---|
| `test_shortener.py` | 12 | API integration — все эндпоинты |
| `test_services.py` | 13 | Business logic, дедупликация, retry |
| `test_cache.py` | 12 | RedisManager, CacheService, ключи |
| `test_worker.py` | 8 | ARQClient, record_click |
| `test_health.py` | 3 | Health check ok/degraded |
| `test_middleware.py` | 4 | Rate limit, fail open |
| `test_schemas.py` | 10 | SSRF валидация |
| `test_security.py` | 6 | SSRF + XSS через API |
| `test_decorators.py` | 4 | retry_on_integrity_error |
| `test_migrations.py` | 3 | DB schema |
| **Total** | **83** | **83 passed ✅** |

---

## Configuration

| Prefix | Class | Description |
|---|---|---|
| `APP_*` | `ApplicationSettings` | Приложение |
| `DATABASE_*` | `DatabaseSettings` | PostgreSQL |
| `REDIS_*` | `RedisSettings` | Redis |
| `WORKER_*` | `WorkerSettings` | ARQ Worker |
| `LOG_*` | `LoggingSettings` | Loguru |

---

## Production Checklist
```
[ ] Сменить все пароли из .env.example
[ ] APP_DEBUG=False           Swagger отключён
[ ] DATABASE_ECHO_SQL=False   SQL не логируется
[ ] APP_BASE_URL              Реальный домен
[ ] Reverse proxy             nginx / Caddy перед app
[ ] TLS                       HTTPS обязателен
[ ] Закрыть порты             db и redis не наружу
[ ] Log aggregation           Loki / Datadog / ELK
[ ] Алерты                    Worker queue lag
```

---

## License

MIT