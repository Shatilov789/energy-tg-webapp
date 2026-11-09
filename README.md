# Energy CRM — Telegram Web App

CRM-система для энергетической компании. Работники проходят пошаговые сценарии проверки объектов инфраструктуры (подстанции, кабельные линии, трансформаторы) через Telegram Web App.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  TG Web App     │────▶│  FastAPI Backend  │────▶│ PostgreSQL  │
│  (React + Vite) │     │  (async, REST)    │     └─────────────┘
└─────────────────┘     └──────────────────┘            │
                               │                   ┌────┴────┐
                               └──────────────────▶│  Redis  │
                                                   └─────────┘
```

## Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Frontend   | React 18, Vite, TG Web App SDK      |
| Backend    | FastAPI, SQLAlchemy 2.0 (async)     |
| Database   | PostgreSQL 16                       |
| Cache      | Redis 7                             |
| Migrations | Alembic                             |
| Container  | Docker, docker-compose              |

## Project Structure

```
energytgwebapp/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + lifespan
│   │   ├── core/
│   │   │   ├── config.py        # Settings (env vars)
│   │   │   └── security.py      # TG auth + RBAC
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── user.py          # Users (admin/worker)
│   │   │   ├── scenario.py      # Scenarios + steps
│   │   │   ├── object.py        # Inspection objects
│   │   │   ├── answer.py        # Step answers
│   │   │   ├── comment.py       # Admin comments
│   │   │   └── notification.py  # Notifications
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── api/
│   │   │   ├── router.py        # Central router
│   │   │   └── endpoints/       # Route handlers
│   │   ├── processes/           # Business processes
│   │   │   ├── definition.py    # Stage/transition format
│   │   │   ├── engine.py        # Starts and advances deals
│   │   │   ├── registry.py      # All known processes
│   │   │   ├── catalog.py       # Seeds stages into the DB
│   │   │   └── ses.py, askoe.py, standard.py, nonstandard.py, ip.py, commerce.py
│   │   ├── services/
│   │   │   ├── notifications.py # notify(): in-app record + push after commit
│   │   │   └── seed.py          # Dev seed data
│   │   └── db/
│   │       ├── base.py          # DeclarativeBase
│   │       └── session.py       # Async session factory
│   ├── alembic/                 # DB migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── main.jsx             # React entry
│   │   ├── App.jsx              # Router
│   │   ├── api/client.js        # API client
│   │   ├── pages/               # Page components
│   │   ├── components/          # Parts of the larger pages
│   │   ├── processes.js         # Process list and icons
│   │   └── styles/global.css    # Styles (dark theme)
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── .gitignore
```

## Quick Start

### 1. Clone & Configure

```bash
cp .env.example .env
# Edit .env — set TELEGRAM_BOT_TOKEN when available
```

### 2. Run with Docker

```bash
docker-compose up --build
```

Services:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### 3. Dev seed data

On first run in development mode, the app auto-creates:
- 5 stub scenarios (Подстанция, КЛ линия, Трансформатор, Ремонт, Проверка оборудования)
- Dev admin user (telegram_id: 123456789)
- Dev worker user (telegram_id: 987654321)

## API Endpoints

| Method  | Path                                      | Description                    | Auth    |
|---------|-------------------------------------------|--------------------------------|---------|
| GET     | `/api/auth/me`                            | Current user info              | Any     |
| GET     | `/api/scenarios/`                         | List scenarios                 | Any     |
| GET     | `/api/scenarios/{id}`                     | Scenario with steps            | Any     |
| POST    | `/api/scenarios/`                         | Create scenario                | Admin   |
| POST    | `/api/scenarios/{id}/steps`               | Add step to scenario           | Admin   |
| GET     | `/api/objects/`                           | My objects                     | Any     |
| GET     | `/api/objects/{id}`                       | Object detail                  | Owner   |
| POST    | `/api/objects/`                           | Create object                  | Any     |
| POST    | `/api/objects/{id}/share/{user_id}`       | Share object                   | Owner   |
| POST    | `/api/objects/{id}/steps/{step_id}/answer`| Submit answer                  | Worker  |
| PUT     | `/api/objects/{id}/steps/{step_id}/answer`| Update answer (if unlocked)    | Worker  |
| GET     | `/api/admin/users`                        | List all users                 | Admin   |
| POST    | `/api/admin/users`                        | Register user                  | Admin   |
| PATCH   | `/api/admin/users/{id}/toggle-active`     | Activate/deactivate user       | Admin   |
| GET     | `/api/admin/objects`                      | All objects (all workers)      | Admin   |
| POST    | `/api/admin/answers/{id}/comment`         | Comment on answer              | Admin   |
| PATCH   | `/api/admin/answers/{id}/unlock`          | Unlock answer for editing      | Admin   |
| GET     | `/api/notifications/`                     | My notifications               | Any     |
| GET     | `/api/notifications/unread-count`         | Unread count                   | Any     |
| PATCH   | `/api/notifications/{id}/read`            | Mark read                      | Any     |
| PATCH   | `/api/notifications/read-all`             | Mark all read                  | Any     |

## Database Migrations

With `APP_ENV=development` the backend creates tables from the models at startup. In every other
environment the schema comes from Alembic, so run this before starting the backend:

```bash
PYTHONPATH=. alembic -c backend/alembic.ini upgrade head
```

The stage catalog of each process is seeded automatically at startup in all environments.

## Adding a Business Process

1. Add `backend/app/processes/<name>.py` with `STAGES`, `TRANSITIONS` and `PROCESS`.
2. Register `PROCESS` in `backend/app/processes/registry.py`.
3. Add its label and icon to `frontend/src/processes.js`.

`backend/tests/test_processes.py` validates the new graph automatically.

## Business Flow

1. Admin registers workers by Telegram ID
2. Worker opens TG Web App → sees scenarios
3. Worker picks scenario → creates inspection object (name + comment)
4. Worker fills steps one by one (text answers, auto-saved)
5. Progress saved — worker can close and resume later
6. Answers stay editable until an admin locks them; a locked answer needs an admin unlock
7. Admin monitors all workers/objects, comments on answers
8. Objects can be shared between multiple workers
9. Reminders sent if a step stays unfilled for 2 days
