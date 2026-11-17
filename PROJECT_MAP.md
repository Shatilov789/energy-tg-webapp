# PROJECT MAP

A map of the project by area, so a change can start from the right files without reading everything.

---

## 1. Auth & users

Telegram Web App auth, roles (admin / worker), user management.

- `backend/app/core/security.py` — `initData` check, dev header (development only), `get_current_user`, `require_admin`
- `backend/app/models/user.py` — `User` (telegram_id, role, is_active, soft delete)
- `backend/app/schemas/user.py` — `UserResponse`, `UserCreate`, `UserBriefResponse`
- `backend/app/api/endpoints/auth.py` — `GET /api/auth/me`
- `backend/app/api/endpoints/users.py` — `GET /api/users/` (colleagues)
- `backend/app/api/endpoints/admin.py` — `GET/POST /api/admin/users`, `PATCH .../toggle-active`
- `backend/app/services/seed.py` — admin from `ADMIN_TELEGRAM_ID`, dev worker
- `frontend/src/api/client.js` — auth headers, `getMe`

---

## 2. Objects and business processes

An object («Обʼєкт», `Deal` in code) moves through the stages of its process.

- `backend/app/processes/definition.py` — stage and transition format
- `backend/app/processes/<name>.py` — one file per process (`ses`, `askoe`, `standard`, `nonstandard`, `ip`, `commerce`)
- `backend/app/processes/registry.py` — all known processes
- `backend/app/processes/catalog.py` — syncs the stage catalog into the DB at startup
- `backend/app/processes/engine.py` — starts objects and advances stages (row lock against double taps)
- `backend/app/models/deal.py` — `Deal`, `Stage`, `DealStageProgress` (one visit to a stage), `DealStageComment`
- `backend/app/schemas/deal.py`
- `backend/app/api/endpoints/deals.py` — `/api/deals/…`
- `frontend/src/pages/HomePage.jsx` — object list
- `frontend/src/pages/NewDealPage.jsx` — create an object
- `frontend/src/pages/DealPage.jsx` — an object and its stages, «Далі», «Так/Ні»
- `frontend/src/processes.js` — process labels and icons
- `backend/tests/test_deals.py`, `backend/tests/test_processes.py`

---

## 3. Admin panel

- `frontend/src/pages/AdminPage.jsx` — user management
- `frontend/src/components/admin/UsersTab.jsx`, `CreateUserModal.jsx`
- `backend/tests/test_admin.py`

---

## 4. Notifications

An in-app record plus a Telegram push, sent only after the transaction commits.
A notification points at an object (`deal_id`) and optionally a stage visit (`progress_id`).

- `backend/app/services/notifications.py` — `notify()`
- `backend/app/models/notification.py` — `Notification`, `NotificationType` (stored as a string)
- `backend/app/api/endpoints/notifications.py` — list, unread count, mark read
- `frontend/src/pages/NotificationsPage.jsx` — list; the action opens `/deals/:id`
- `backend/tests/test_notifications.py`, `backend/tests/test_notify.py`

---

## 5. Infrastructure

- `docker-compose.yml` (local), `docker-compose.deploy.yml` (server), `DEPLOY.md`
- `backend/Dockerfile`, `frontend/Dockerfile`
- `backend/app/db/` — engine, session, `Base`, `SoftDeleteMixin`
- `backend/alembic/versions/` — migrations (`0003` dropped the old questionnaire section)
- `backend/app/services/bot.py` — Telegram bot: `/start`, access requests, `/myid`, pushes
- `backend/app/services/audit.py` — audit log
- `.github/workflows/` — CI (ruff, black, pytest, migrations, frontend build) and deploy

---

## 6. Styles

- `frontend/src/styles/global.css` — one file, dark theme

---

## Quick commands

```bash
docker compose up -d --build            # rebuild after changes
docker compose logs backend --tail=20   # backend logs
PYTHONPATH=. python -m pytest backend/tests
alembic -c backend/alembic.ini upgrade head
```
