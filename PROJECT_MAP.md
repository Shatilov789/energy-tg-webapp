# PROJECT MAP — навигатор по секциям

Этот файл — карта проекта для быстрой работы с нужным блоком без перечитывания всего кода.
При работе с секцией: читай только файлы из неё + зависимости из списка.

---

## СЕКЦИЯ 1 — Auth & Users

**Что делает:** TG Web App auth, регистрация юзеров, роли (admin/worker).

**Файлы:**
- `backend/app/core/security.py` — TG initData верификация, dev-bypass, `get_current_user`, `require_admin`
- `backend/app/models/user.py` — модель User (telegram_id, role, is_active, SoftDelete)
- `backend/app/schemas/user.py` — UserResponse, UserCreate, UserBriefResponse
- `backend/app/api/endpoints/auth.py` — `GET /api/auth/me`
- `backend/app/api/endpoints/admin.py` (top) — `GET/POST /admin/users`, toggle-active
- `frontend/src/api/client.js` — `getMe`, заголовки auth
- `frontend/src/App.jsx` — роутинг, TG SDK init
- `backend/app/core/seed.py` — dev admin/worker seed

**Зависимости:** нет внешних (основа для всего остального)

---

## СЕКЦИЯ 2 — Сценарии (Scenarios)

**Что делает:** CRUD сценариев с шагами-вопросами.

**Файлы:**
- `backend/app/models/scenario.py` — Scenario, ScenarioStep
- `backend/app/schemas/scenario.py` — ScenarioResponse, ScenarioWithStepsResponse, StepResponse
- `backend/app/api/endpoints/scenarios.py` — `GET /api/scenarios/`, `GET /api/scenarios/{id}`
- `frontend/src/pages/ObjectsPage.jsx` — выбор сценария при создании объекта
- `frontend/src/scenarioIcons.js` — маппинг имя сценария → иконка

**Зависимости:** Секция 1 (auth)

---

## СЕКЦИЯ 3 — Объекты (Objects)

**Что делает:** Создание инспекционных объектов, назначение сотрудников, список.

**Файлы:**
- `backend/app/models/object.py` — Object, ObjectWorker, ObjectStatus
- `backend/app/schemas/object.py` — ObjectCreate, ObjectResponse, ObjectDetailResponse, ObjectListItemResponse, AdminObjectResponse
- `backend/app/api/endpoints/objects.py` — `GET/POST /api/objects/`, `GET /api/objects/{id}`, `POST .../share/{user_id}`
- `frontend/src/pages/HomePage.jsx` — список объектов, секции "В работе"/"Завершённые"
- `frontend/src/pages/ObjectsPage.jsx` — создание объекта, выбор сценария

**Зависимости:** Секции 1, 2

---

## СЕКЦИЯ 4 — Ответы на шаги (Step Answers)

**Что делает:** Сотрудник заполняет ответы на вопросы шагов; lock/unlock ответов.

**Файлы:**
- `backend/app/models/answer.py` — ObjectAnswer (answer_text, is_locked, SoftDelete)
- `backend/app/schemas/answer.py` — AnswerCreate, AnswerResponse
- `backend/app/api/endpoints/steps.py` — `POST/PUT /objects/{id}/steps/{id}/answer`
- `backend/app/api/endpoints/admin.py` (bottom) — `PATCH /admin/answers/{id}/lock`, `PATCH .../unlock`
- `frontend/src/pages/StepPage.jsx` — основная страница заполнения (qcard, textarea, saveAnswer)
- `frontend/src/api/client.js` — `submitAnswer`, `updateAnswer`, `lockAnswer`, `unlockAnswer`

**Зависимости:** Секции 1, 2, 3

**Важно:** Ответ создаётся с `is_locked=False`. Сотрудник может дополнять ответ до ручной блокировки админом.

---

## СЕКЦИЯ 5 — Обсуждение шага (Step Discussion)

**Что делает:** Тред-комментарии под каждым шагом; системные события; reply-цитаты.

**Файлы:**
- `backend/app/models/comment.py` — StepComment (reply_to_id, is_system_event, event_type), AdminComment
- `backend/app/schemas/step_comment.py` — StepCommentCreate, StepCommentResponse, StepCommentBrief
- `backend/app/api/endpoints/steps.py` — `GET/POST /objects/{id}/steps/{id}/comments`
- `frontend/src/pages/StepPage.jsx` (discuss-block) — список сообщений, форма, reply-bar
- `frontend/src/styles/global.css` — `.discuss-*` классы (≈строки 640–760)
- `frontend/src/api/client.js` — `getStepComments`, `addStepComment`

**Зависимости:** Секции 1, 3, 4

**Системные события (is_system_event=true):**
- `lock` — admin заблокировал ответ
- `unlock` — admin разблокировал ответ
- `admin_comment` — admin оставил комментарий к ответу

---

## СЕКЦИЯ 6 — Admin Panel

**Что делает:** Дашборд метрик, обзор объектов, комментирование/блокировка ответов.

**Файлы:**
- `backend/app/api/endpoints/admin.py` — все admin-эндпоинты
- `frontend/src/pages/AdminPage.jsx` — дашборд, карточки объектов, lock/unlock/comment
- `frontend/src/styles/global.css` — `.adm-*`, `.dash-grid`, `.mc`, `.bdg-*` классы
- `frontend/src/api/client.js` — `getAdminObjects`, `getAdminUsers`, `addComment`, `lockAnswer`, `unlockAnswer`

**Зависимости:** Секции 1–5

---

## СЕКЦИЯ 7 — Уведомления (Notifications)

**Что делает:** Уведомления сотрудникам (разблокировка, комментарий админа, напоминание, шаринг).

**Файлы:**
- `backend/app/models/notification.py` — Notification, NotificationType
- `backend/app/api/endpoints/notifications.py` — `GET /notifications/`, mark-read, unread-count
- `frontend/src/pages/NotificationsPage.jsx` — список уведомлений, deep-links на шаг
- `frontend/src/api/client.js` — `getNotifications`, `getUnreadCount`, `markRead`, `markAllRead`

**Зависимости:** Секции 1, 3, 4

---

## СЕКЦИЯ 8 — Инфраструктура

**Что делает:** Docker, БД, Telegram Bot, CI/CD.

**Файлы:**
- `docker-compose.yml` — 4 контейнера (db, redis, backend, frontend)
- `backend/Dockerfile` + `frontend/Dockerfile`
- `.env` / `.env.example`
- `backend/app/db/session.py` — async engine, get_db
- `backend/app/db/base.py` — Base, metadata
- `backend/app/db/mixins.py` — SoftDeleteMixin
- `backend/bot.py` — Telegram polling bot (/start, /myid)
- `backend/app/services/scheduler.py` — APScheduler, check_unfilled_steps
- `.github/workflows/ci.yml` — ruff + black + pytest + frontend build
- `backend/tests/` — 44 теста (conftest, test_auth, test_scenarios, test_objects, test_answers, test_admin, test_notifications)

**Зависимости:** все секции

---

## СЕКЦИЯ 9 — Стили (CSS)

**Что делает:** Все UI-классы, тёмная тема, компоненты.

**Файлы:**
- `frontend/src/styles/global.css` — единый CSS файл (~800 строк)

**Навигация по блокам внутри global.css:**
- `:root` переменные — строки 1–30
- Базовые элементы (body, page, sc, btn) — 31–120
- Tabbar — 121–160
- HomePage компоненты (obj-card, ci, bdg) — 161–280
- ObjectsPage (scen-select) — 281–340
- StepPage (qhdr, qcard, qtextarea, qprog) — 341–480
- Admin (adm-*, dash-grid, mc) — 481–570
- Notifications — 571–620
- Discussion (discuss-*) — 621–760
- Утилиты (empty-state, loading, error) — 761–800

---

## Быстрые команды

```bash
# Пересборка после изменений
docker compose up -d --build

# Только бек (быстрее)
docker compose up -d --build backend

# Только фронт
docker compose up -d --build frontend

# Логи бека
docker compose logs backend --tail=20

# SQL миграция вручную
docker compose exec db psql -U postgres -d energy_crm -c "ALTER TABLE ..."
```
