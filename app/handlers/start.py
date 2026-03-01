"""Start command handler."""

from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from sqlalchemy.ext.asyncio import AsyncSession
import pytz

from app.config import config
from app.services import UserService, PromoService, QRService
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = Router()

SUBSCRIBE_CALLBACK = "check_subscription"


def is_promo_active() -> bool:
    """Check if promo period is active."""
    now = datetime.now(pytz.UTC)
    return config.PROMO_START <= now <= config.PROMO_END


async def is_subscribed_to_channel(bot: Bot, user_id: int) -> bool:
    """Check if user is subscribed to the required channel."""
    try:
        member = await bot.get_chat_member(
            chat_id=config.CHANNEL_USERNAME,
            user_id=user_id,
        )
        return member.status not in ("left", "kicked", "banned")
    except Exception as e:
        logger.warning(
            "Could not check channel subscription",
            error=str(e),
            channel=config.CHANNEL_USERNAME,
            user_id=user_id,
        )
        return True  # fail open — не блокируем пользователей при ошибке API


def get_subscribe_keyboard() -> InlineKeyboardMarkup:
    channel = config.CHANNEL_USERNAME.lstrip("@")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Подписаться на канал", url=f"https://t.me/{channel}")],
            [InlineKeyboardButton(text="Я подписался ✅", callback_data=SUBSCRIBE_CALLBACK)],
        ]
    )


async def send_gift(
    message: Message,
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
) -> None:
    """Get or create user and send promo gift."""
    user, _ = await UserService.get_or_create_user(
        session=session,
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
    )

    has_code = await PromoService.user_has_code(session, user)
    if has_code:
        if not user.extra_gift_allowed:
            await message.answer("Вы уже получили подарок")
            logger.info("User already has code", telegram_id=telegram_id, user_id=user.id)
            return
        # Extra gift granted by admin — use dedicated method
        promo_code = await PromoService.get_extra_code(session, user)
    else:
        promo_code = await PromoService.get_available_code(session, user)
    if not promo_code:
        await message.answer(
            "К сожалению, все подарки уже разобрали. "
            "Спасибо за интерес к UPPETIT!"
        )
        logger.warning("No codes available", telegram_id=telegram_id, user_id=user.id)
        return

    await message.answer(
        "Привет, Друг! Хотим тебя порадовать подарком. "
        "Заходи в любой магазин UPPETIT и получи 1 бесплатный дрип-пакет нашего кофе. "
        "Просто покажи QR код на кассе"
    )

    qr_buffer = QRService.generate_qr_code(promo_code.raw_code)
    qr_file = BufferedInputFile(qr_buffer.read(), filename="qr_code.png")
    await message.answer_photo(
        photo=qr_file,
        caption=f"Ваш промокод: {promo_code.raw_code}",
    )

    logger.info(
        "QR code sent to user",
        telegram_id=telegram_id,
        user_id=user.id,
        code_id=promo_code.id,
        raw_code=promo_code.raw_code,
    )


@router.message(Command("my_id"))
async def cmd_my_id(message: Message) -> None:
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    response = (
        f"👤 <b>Ваша информация:</b>\n\n"
        f"├ ID: <code>{user_id}</code>\n"
        f"├ Имя: {first_name}\n"
    )

    if username:
        response += f"└ Username: @{username}"
    else:
        response = response.rstrip("\n")
        response += "└ Username: не установлен"

    await message.answer(response, parse_mode="HTML")

    logger.info("User requested their ID", telegram_id=user_id, username=username)


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    user_telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    logger.info("User started bot", telegram_id=user_telegram_id, username=username)

    if not is_promo_active():
        await message.answer(
            "К сожалению, акция в данный момент неактивна. "
            "Следите за нашими новостями, чтобы не пропустить следующую акцию!"
        )
        logger.info("Promo not active, user notified", telegram_id=user_telegram_id)
        return

    subscribed = await is_subscribed_to_channel(message.bot, user_telegram_id)
    if not subscribed:
        await message.answer(
            f"Для получения подарка необходимо подписаться на наш канал!\n\n"
            f"Подпишитесь на {config.CHANNEL_USERNAME} и нажмите кнопку «Я подписался ✅».",
            reply_markup=get_subscribe_keyboard(),
        )
        logger.info(
            "User not subscribed to channel",
            telegram_id=user_telegram_id,
            channel=config.CHANNEL_USERNAME,
        )
        return

    try:
        await send_gift(message, session, user_telegram_id, username, first_name, last_name)
    except Exception as e:
        logger.error(
            "Error processing start command",
            telegram_id=user_telegram_id,
            error=str(e),
            error_type=type(e).__name__,
        )
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")


@router.callback_query(F.data == SUBSCRIBE_CALLBACK)
async def check_subscription_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user_telegram_id = callback.from_user.id
    username = callback.from_user.username
    first_name = callback.from_user.first_name
    last_name = callback.from_user.last_name

    logger.info(
        "User pressed 'I subscribed' button",
        telegram_id=user_telegram_id,
    )

    if not is_promo_active():
        await callback.answer("Акция в данный момент неактивна.", show_alert=True)
        return

    subscribed = await is_subscribed_to_channel(callback.bot, user_telegram_id)
    if not subscribed:
        await callback.answer(
            "Вы ещё не подписались на канал. Подпишитесь и попробуйте снова.",
            show_alert=True,
        )
        logger.info(
            "User confirmed but still not subscribed",
            telegram_id=user_telegram_id,
        )
        return

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    try:
        await send_gift(
            callback.message, session, user_telegram_id, username, first_name, last_name
        )
    except Exception as e:
        logger.error(
            "Error processing subscription callback",
            telegram_id=user_telegram_id,
            error=str(e),
            error_type=type(e).__name__,
        )
        await callback.message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
