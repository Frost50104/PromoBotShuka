"""Start command handler."""

from datetime import datetime

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession
import pytz

from app.config import config
from app.services import UserService, PromoService, QRService
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = Router()


def is_promo_active() -> bool:
    """Check if promo period is active."""
    now = datetime.now(pytz.UTC)
    return config.PROMO_START <= now <= config.PROMO_END


@router.message(Command("my_id"))
async def cmd_my_id(message: Message) -> None:
    """
    Show user's Telegram ID.

    Args:
        message: Telegram message
    """
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

    logger.info(
        "User requested their ID",
        telegram_id=user_id,
        username=username,
    )


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    """
    Handle /start command.

    Args:
        message: Telegram message
        session: Database session
    """
    user_telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    logger.info(
        "User started bot",
        telegram_id=user_telegram_id,
        username=username,
    )

    # Check if promo is active
    if not is_promo_active():
        await message.answer(
            "К сожалению, акция в данный момент неактивна. "
            "Следите за нашими новостями, чтобы не пропустить следующую акцию!"
        )
        logger.info(
            "Promo not active, user notified",
            telegram_id=user_telegram_id,
        )
        return

    try:
        # Get or create user
        user, is_new = await UserService.get_or_create_user(
            session=session,
            telegram_id=user_telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )

        # Check if user already has a code
        has_code = await PromoService.user_has_code(session, user)
        if has_code:
            await message.answer("Вы уже получили подарок")
            logger.info(
                "User already has code",
                telegram_id=user_telegram_id,
                user_id=user.id,
            )
            return

        # Get available code
        promo_code = await PromoService.get_available_code(session, user)

        if not promo_code:
            await message.answer(
                "К сожалению, все подарки уже разобрали. "
                "Спасибо за интерес к UPPETIT!"
            )
            logger.warning(
                "No codes available",
                telegram_id=user_telegram_id,
                user_id=user.id,
            )
            return

        # Send welcome message
        await message.answer(
            "Привет, Друг! Хотим тебя порадовать подарком. "
            "Заходи в любой магазин UPPETIT и получи 1 бесплатный дрип-пакет нашего кофе. "
            "Просто покажи QR код на кассе"
        )

        # Generate and send QR code
        qr_buffer = QRService.generate_qr_code(promo_code.raw_code)

        qr_file = BufferedInputFile(
            qr_buffer.read(),
            filename="qr_code.png"
        )

        await message.answer_photo(
            photo=qr_file,
            caption=f"Ваш промокод: {promo_code.raw_code}"
        )

        logger.info(
            "QR code sent to user",
            telegram_id=user_telegram_id,
            user_id=user.id,
            code_id=promo_code.id,
            raw_code=promo_code.raw_code,
        )

    except Exception as e:
        logger.error(
            "Error processing start command",
            telegram_id=user_telegram_id,
            error=str(e),
            error_type=type(e).__name__,
        )
        await message.answer(
            "Произошла ошибка. Пожалуйста, попробуйте позже."
        )
