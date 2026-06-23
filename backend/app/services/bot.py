"""Telegram bot — регистрация сотрудников и отправка ID админу."""

import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

bot_app: Application | None = None


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка /start — показать ID и уведомить админа."""
    user = update.effective_user
    if not user:
        return

    # Сообщение сотруднику
    await update.message.reply_text(
        f"👋 Добро пожаловать в Energy CRM!\n\n"
        f"📋 Ваши данные:\n"
        f"• Telegram ID: {user.id}\n"
        f"• Имя: {user.first_name}\n"
        f"• Фамилия: {user.last_name or '—'}\n"
        f"• Username: @{user.username}\n\n"
        f"✅ Ваш ID отправлен администратору.\n"
        f"Ожидайте — вам назначат роль и объекты."
    )

    # Уведомление админу
    if settings.admin_telegram_id:
        try:
            await context.bot.send_message(
                chat_id=settings.admin_telegram_id,
                text=(
                    f"🆕 Новый сотрудник запросил доступ!\n\n"
                    f"• Telegram ID: {user.id}\n"
                    f"• Имя: {user.first_name} {user.last_name or ''}\n"
                    f"• Username: @{user.username}\n\n"
                    f"Добавь сотрудника через админ-панель."
                ),
            )
        except Exception as e:
            logger.error("Не удалось отправить уведомление админу: %s", e)
    else:
        logger.warning("ADMIN_TELEGRAM_ID не задан — уведомление не отправлено")


async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка /myid — быстро показать свой ID."""
    user = update.effective_user
    if user:
        await update.message.reply_text(f"Ваш Telegram ID: `{user.id}`", parse_mode="Markdown")


async def start_bot() -> None:
    """Запуск бота (polling mode)."""
    global bot_app

    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN не задан — бот не запущен")
        return

    try:
        bot_app = (
            Application.builder()
            .token(settings.telegram_bot_token)
            .connect_timeout(30)
            .read_timeout(30)
            .write_timeout(30)
            .build()
        )

        bot_app.add_handler(CommandHandler("start", cmd_start))
        bot_app.add_handler(CommandHandler("myid", cmd_myid))

        await bot_app.initialize()
        await bot_app.start()
        await bot_app.updater.start_polling(drop_pending_updates=True)

        logger.info("Telegram бот запущен (polling)")
    except Exception as e:
        logger.error("Не удалось запустить бота: %s. Backend продолжит работу без бота.", e)
        bot_app = None


async def stop_bot() -> None:
    """Остановка бота."""
    global bot_app

    if bot_app:
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()
        bot_app = None
        logger.info("Telegram бот остановлен")
