# Деплой и релизы

## Как устроено

| Ветка | Куда попадает | Бот | Адрес |
|---|---|---|---|
| `test` | тестовая копия | тестовый | `test.<домен>` |
| `main` | боевая копия | боевой | `app.<домен>` |

У каждой копии своя база и свой бот, данные не пересекаются.

## Обычная работа

1. Изменения пушатся в `test`. CI проверяет их и обновляет тестовую копию.
2. Проверяешь в тестовом боте.
3. Релиз: `gh pr create --base main --head test --title "Release"`, затем слияние этого Pull Request.
4. После слияния CI обновляет боевую копию.

Прямой пуш в `main` запрещён: попасть туда можно только через Pull Request с зелёными проверками.

## Первичная настройка сервера (один раз)

Нужны Linux-VPS, домен с двумя A-записями (`test` и `app`) на его IP и два бота от @BotFather.

1. Установить Docker и Caddy.
2. Создать пользователя `deploy`, добавить его в группу `docker`.
3. Склонировать код:

   ```bash
   sudo mkdir -p /opt/energy && sudo chown deploy /opt/energy
   git clone https://github.com/Shatilov789/energy-tg-webapp.git /opt/energy/test
   git clone https://github.com/Shatilov789/energy-tg-webapp.git /opt/energy/production
   ```

4. В каждой папке: `cp .env.deploy.example .env.deploy` и заполнить. Для боевой копии `APP_ENV=production`, `WEB_PORT=8080`.
5. Прописать домены в `/etc/caddy/Caddyfile` по образцу `deploy/Caddyfile.example`, выполнить `sudo systemctl reload caddy`.
6. Создать ключ только для деплоя: `ssh-keygen -t ed25519 -f deploy_key -N ""`, а `deploy_key.pub` добавить в `~deploy/.ssh/authorized_keys`.

## Настройка GitHub (один раз)

В Settings → Secrets and variables → Actions:

| Тип | Имя | Значение |
|---|---|---|
| Secret | `DEPLOY_HOST` | IP сервера |
| Secret | `DEPLOY_USER` | `deploy` |
| Secret | `DEPLOY_SSH_KEY` | содержимое `deploy_key` |
| Secret | `DEPLOY_KNOWN_HOSTS` | вывод `ssh-keyscan <IP>` |
| Variable | `DEPLOY_ENABLED` | `true` |

До установки `DEPLOY_ENABLED` CI работает, а шаг деплоя пропускается.

В @BotFather у каждого бота указать адрес его копии как URL Web App.
