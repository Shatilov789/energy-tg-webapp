"""Telegram bot: staff registration, sending a user their ID, and push notifications."""

import logging

from sqlalchemy import select
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from backend.app.core.config import settings
from backend.app.db.session import async_session
from backend.app.models.user import User, UserRole

logger = logging.getLogger(__name__)

bot_app: Application | None = None

# In-memory буфер запитів доступу, поки адмін не натисне кнопку (tg_id -> дані кандидата).
# Достатньо для MVP — переживає рестарт бекенду погано, але живе тестування це не блокує.
pending_access_requests: dict[int, dict] = {}


def _open_webapp_markup() -> InlineKeyboardMarkup | None:
    if not settings.webapp_url:
        return None
    return InlineKeyboardMarkup([[InlineKeyboardButton("Відкрити Energy CRM →", url=settings.webapp_url)]])


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start: show a registered user the login button, offer a new user an access request."""
    user = update.effective_user
    if not user or not update.message:
        return

    async with async_session() as session:
        db_user = (await session.execute(select(User).where(User.telegram_id == user.id))).scalar_one_or_none()

    if db_user and db_user.is_active:
        await update.message.reply_text(
            f"👋 З поверненням, {db_user.first_name}!",
            reply_markup=_open_webapp_markup(),
        )
        return

    await update.message.reply_text(
        f"👋 Ласкаво просимо в Energy CRM!\n\n"
        f"📋 Ваші дані:\n"
        f"• Telegram ID: {user.id}\n"
        f"• Ім'я: {user.first_name}\n"
        f"• Прізвище: {user.last_name or '—'}\n"
        f"• Username: @{user.username}\n\n"
        f"Ви ще не маєте доступу. Натисніть кнопку щоб запросити його в адміністратора.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔑 Запросити доступ", callback_data="request_access")]]
        ),
    )


async def on_request_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Кандидат натиснув 'Запросити доступ' — сповістити адміна кнопкою підтвердження."""
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return
    await query.answer()

    pending_access_requests[user.id] = {
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "username": user.username or "",
    }

    await query.edit_message_text("⏳ Запит надіслано адміністратору. Очікуйте на підтвердження.")

    if not settings.admin_telegram_id:
        logger.warning("ADMIN_TELEGRAM_ID is not set; access request notification not sent")
        return

    try:
        await context.bot.send_message(
            chat_id=settings.admin_telegram_id,
            text=(
                f"🆕 Запит на доступ!\n\n"
                f"• Telegram ID: {user.id}\n"
                f"• Ім'я: {user.first_name} {user.last_name or ''}\n"
                f"• Username: @{user.username}"
            ),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("✅ Дозволити доступ", callback_data=f"grant_access:{user.id}")]]
            ),
        )
    except Exception as e:
        logger.error("Failed to notify the admin: %s", e)


async def on_grant_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Адмін натиснув 'Дозволити доступ' — завести/реактивувати User (worker, без обмежень)."""
    query = update.callback_query
    admin_user = update.effective_user
    if not query or not admin_user:
        return

    if admin_user.id != settings.admin_telegram_id:
        await query.answer("Тільки адміністратор може підтверджувати доступ", show_alert=True)
        return
    await query.answer()

    tg_id = int(query.data.split(":", 1)[1])
    candidate = pending_access_requests.pop(tg_id, {})
    first_name = candidate.get("first_name") or "Співробітник"
    last_name = candidate.get("last_name") or None
    username = candidate.get("username") or None

    async with async_session() as session:
        db_user = (await session.execute(select(User).where(User.telegram_id == tg_id))).scalar_one_or_none()
        if db_user:
            db_user.is_active = True
        else:
            db_user = User(
                telegram_id=tg_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
                role=UserRole.WORKER,
            )
            session.add(db_user)
        await session.commit()

    await query.edit_message_text(f"✅ Доступ надано: {first_name} {last_name or ''} (tg_id={tg_id})")

    try:
        await context.bot.send_message(
            chat_id=tg_id,
            text="✅ Вам надано доступ до Energy CRM!",
            reply_markup=_open_webapp_markup(),
        )
    except Exception as e:
        logger.warning("Не вдалось сповістити кандидата (tg_id=%d): %s", tg_id, e)


async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /myid: quickly show the user their ID."""
    user = update.effective_user
    if user:
        await update.message.reply_text(f"Ваш Telegram ID: `{user.id}`", parse_mode="Markdown")


async def send_telegram_notification(telegram_id: int, text: str) -> None:
    """Send a Telegram push notification. Silently skipped when the bot is not running."""
    if not bot_app:
        return
    try:
        kwargs: dict = {"chat_id": telegram_id, "text": text}
        if settings.webapp_url:
            kwargs["reply_markup"] = InlineKeyboardMarkup(
                [[InlineKeyboardButton("Відкрити Energy CRM →", url=settings.webapp_url)]]
            )
        await bot_app.bot.send_message(**kwargs)
    except Exception as e:
        logger.warning("Telegram push not sent (user tg_id=%d): %s", telegram_id, e)


async def start_bot() -> None:
    """Start the bot (polling mode)."""
    global bot_app

    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN is not set; bot not started")
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
        bot_app.add_handler(CallbackQueryHandler(on_request_access, pattern="^request_access$"))
        bot_app.add_handler(CallbackQueryHandler(on_grant_access, pattern="^grant_access:"))

        await bot_app.initialize()
        await bot_app.start()
        await bot_app.updater.start_polling(drop_pending_updates=True)

        logger.info("Telegram bot started (polling)")
    except Exception as e:
        logger.error("Failed to start the bot: %s. The backend keeps running without it.", e)
        bot_app = None


async def stop_bot() -> None:
    """Stop the bot."""
    global bot_app

    if bot_app:
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()
        bot_app = None
        logger.info("Telegram bot stopped")
