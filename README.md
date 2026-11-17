# Energy CRM — Telegram Web App

CRM for an energy company, run as a Telegram Web App. Each object («Обʼєкт») moves through the stages of its business process (СЕС, АСКОЕ, standard, non-standard, ІП, commerce).

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
│   │   │   ├── deal.py          # Objects (deals), stages, stage visits, stage threads
│   │   │   ├── audit.py         # Audit log
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
│   │   │   ├── bot.py           # Telegram bot (access requests, pushes)
│   │   │   └── seed.py          # Admin and dev seed data
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

On startup the app creates the admin from `ADMIN_TELEGRAM_ID` in an empty database and seeds the
stage catalog of every process. In development mode it also creates a dev worker (telegram_id: 987654321).

## API Endpoints

| Method  | Path                                      | Description                    | Auth    |
|---------|-------------------------------------------|--------------------------------|---------|
| GET     | `/api/auth/me`                            | Current user info              | Any     |
| GET     | `/api/deals/stages?process_type=…`        | Stage catalog of a process     | Any     |
| GET     | `/api/deals/`                             | All objects                    | Any     |
| POST    | `/api/deals/`                             | Create an object               | Any     |
| GET     | `/api/deals/{id}`                         | Object with its stages         | Any     |
| POST    | `/api/deals/{id}/advance`                 | Complete the current stage     | Any     |
| GET     | `/api/users/`                             | Colleagues                     | Any     |
| GET     | `/api/admin/users`                        | List all users                 | Admin   |
| POST    | `/api/admin/users`                        | Register user                  | Admin   |
| PATCH   | `/api/admin/users/{id}/toggle-active`     | Activate/deactivate user       | Admin   |
| GET     | `/api/notifications/`                     | My notifications               | Any     |
| GET     | `/api/notifications/unread-count`         | Unread count                   | Any     |
| PATCH   | `/api/notifications/{id}/read`            | Mark read                      | Any     |
| PATCH   | `/api/notifications/read-all`             | Mark all read                  | Any     |

## Deployment

Branches, the test and live stacks and the release flow are described in [DEPLOY.md](DEPLOY.md).

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

1. The admin registers employees by Telegram ID (or grants access from the bot).
2. An employee opens the Web App and creates an object, choosing its process.
3. Any active employee completes the current stage; decision stages ask «Так/Ні».
4. The object opens on its stage in work and finishes as completed or closed.
5. Notifications appear in the app and as Telegram pushes.
