"""Admin commands handler."""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import config
from app.services import PromoService, AdminService, UserService
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = Router()


class AdminStates(StatesGroup):
    """States for admin operations."""
    waiting_for_admin_id = State()
    waiting_for_codes = State()


async def is_admin(user_id: int, session: AsyncSession) -> bool:
    """Check if user is admin."""
    # Check if user is in the initial admin list
    if user_id == 854825784:
        return True
    # Check if user is in the database
    return await AdminService.is_admin(session, user_id)


@router.message(Command("stats"))
async def cmd_stats(message: Message, session: AsyncSession) -> None:
    """
    Show promo codes statistics (admin only).

    Args:
        message: Telegram message
        session: Database session
    """
    if not await is_admin(message.from_user.id, session):
        logger.warning(
            "Non-admin tried to access stats",
            telegram_id=message.from_user.id,
        )
        return

    try:
        stats = await PromoService.get_codes_stats(session)

        response = (
            "📊 <b>Статистика промокодов:</b>\n\n"
            f"Всего: {stats['total']}\n"
            f"Доступно: {stats['available']}\n"
            f"Выдано: {stats['assigned']}\n"
        )

        await message.answer(response, parse_mode="HTML")

        logger.info(
            "Stats requested by admin",
            telegram_id=message.from_user.id,
            stats=stats,
        )

    except Exception as e:
        logger.error(
            "Error getting stats",
            telegram_id=message.from_user.id,
            error=str(e),
        )
        await message.answer("Ошибка при получении статистики")


@router.message(Command("new_codes"))
async def cmd_new_codes(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """
    Start adding new promo codes (admin only).

    Args:
        message: Telegram message
        session: Database session
        state: FSM context
    """
    if not await is_admin(message.from_user.id, session):
        logger.warning(
            "Non-admin tried to add new codes",
            telegram_id=message.from_user.id,
        )
        return

    await state.set_state(AdminStates.waiting_for_codes)
    await message.answer(
        "📝 <b>Добавление новых промокодов</b>\n\n"
        "Отправьте промокоды построчно (по одному коду в строке).\n\n"
        "Пример:\n"
        "<code>987651527138080\n"
        "987652589596192\n"
        "987652691640275</code>\n\n"
        "Для отмены отправьте /cancel",
        parse_mode="HTML"
    )


@router.message(AdminStates.waiting_for_codes)
async def process_new_codes(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """
    Process new promo codes input.

    Args:
        message: Telegram message
        session: Database session
        state: FSM context
    """
    # Check for cancel command
    if message.text and message.text.strip().lower() == '/cancel':
        await state.clear()
        await message.answer("❌ Добавление кодов отменено")
        return

    # Get codes from message text
    text = message.text or ""
    lines = text.split("\n")

    # Parse codes (remove empty lines and whitespace)
    codes = [line.strip() for line in lines if line.strip()]

    if not codes:
        await message.answer(
            "❌ Не найдено ни одного кода.\n\n"
            "Пожалуйста, отправьте коды построчно или /cancel для отмены."
        )
        return

    try:
        # Add codes to database
        added, skipped = await PromoService.add_codes(session, codes)

        response = (
            "✅ <b>Коды успешно добавлены!</b>\n\n"
            f"📊 Статистика:\n"
            f"├ Добавлено новых: {added}\n"
            f"├ Пропущено (дубликаты): {skipped}\n"
            f"└ Всего в запросе: {len(codes)}"
        )

        await message.answer(response, parse_mode="HTML")

        logger.info(
            "New codes added via /new_codes",
            telegram_id=message.from_user.id,
            added=added,
            skipped=skipped,
            total=len(codes),
        )

    except Exception as e:
        logger.error(
            "Error adding new codes",
            telegram_id=message.from_user.id,
            error=str(e),
        )
        await message.answer("❌ Ошибка при добавлении кодов. Попробуйте позже.")

    await state.clear()


@router.message(Command("show_info"))
async def cmd_show_info(message: Message, session: AsyncSession) -> None:
    """
    Show detailed information (admin only).

    Args:
        message: Telegram message
        session: Database session
    """
    if not await is_admin(message.from_user.id, session):
        logger.warning(
            "Non-admin tried to access show_info",
            telegram_id=message.from_user.id,
        )
        return

    try:
        stats = await PromoService.get_codes_stats(session)
        unique_users = await AdminService.get_unique_users_count(session)

        response = (
            "📊 <b>Детальная информация:</b>\n\n"
            f"<b>Промокоды:</b>\n"
            f"├ Всего кодов: {stats['total']}\n"
            f"├ Выдано кодов: {stats['assigned']}\n"
            f"└ Кодов в запасе: {stats['available']}\n\n"
            f"<b>Пользователи:</b>\n"
            f"└ Уникальных пользователей: {unique_users}"
        )

        await message.answer(response, parse_mode="HTML")

        logger.info(
            "Show info requested by admin",
            telegram_id=message.from_user.id,
            stats=stats,
            unique_users=unique_users,
        )

    except Exception as e:
        logger.error(
            "Error getting detailed info",
            telegram_id=message.from_user.id,
            error=str(e),
        )
        await message.answer("Ошибка при получении информации")


@router.message(Command("show_users"))
async def cmd_show_users(message: Message, session: AsyncSession) -> None:
    """
    Show all bot users (admin only).

    Args:
        message: Telegram message
        session: Database session
    """
    if not await is_admin(message.from_user.id, session):
        logger.warning(
            "Non-admin tried to access show_users",
            telegram_id=message.from_user.id,
        )
        return

    try:
        users = await UserService.get_all_users(session)

        if not users:
            await message.answer("👥 Пользователей пока нет")
            return

        # Build response with user list
        response = f"👥 <b>Список пользователей ({len(users)}):</b>\n\n"

        for i, user in enumerate(users, 1):
            username_text = f"@{user.username}" if user.username else "нет"
            response += (
                f"{i}. <b>ID:</b> <code>{user.telegram_id}</code>\n"
                f"   <b>Имя:</b> {user.first_name or 'не указано'}\n"
                f"   <b>Username:</b> {username_text}\n"
                f"   <b>Дата регистрации:</b> {user.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            )

            # Telegram has message length limit, split if needed
            if len(response) > 3500:
                await message.answer(response, parse_mode="HTML")
                response = ""

        if response:
            await message.answer(response, parse_mode="HTML")

        logger.info(
            "Users list requested by admin",
            telegram_id=message.from_user.id,
            total_users=len(users),
        )

    except Exception as e:
        logger.error(
            "Error getting users list",
            telegram_id=message.from_user.id,
            error=str(e),
        )
        await message.answer("Ошибка при получении списка пользователей")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """
    Cancel current operation.

    Args:
        message: Telegram message
        state: FSM context
    """
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активных операций для отмены")
        return

    await state.clear()
    await message.answer("❌ Операция отменена")


@router.message(Command("add_admin"))
async def cmd_add_admin(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """
    Start adding new admin (admin only).

    Args:
        message: Telegram message
        session: Database session
        state: FSM context
    """
    if not await is_admin(message.from_user.id, session):
        logger.warning(
            "Non-admin tried to add admin",
            telegram_id=message.from_user.id,
        )
        return

    await state.set_state(AdminStates.waiting_for_admin_id)
    await message.answer(
        "👤 <b>Добавление нового админа</b>\n\n"
        "Отправьте Telegram ID нового админа:",
        parse_mode="HTML"
    )


@router.message(AdminStates.waiting_for_admin_id)
async def process_admin_id(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """
    Process admin ID input.

    Args:
        message: Telegram message
        session: Database session
        state: FSM context
    """
    try:
        new_admin_id = int(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Неверный формат ID. Пожалуйста, отправьте числовой ID.",
        )
        return

    success, msg = await AdminService.add_admin(session, new_admin_id)

    if success:
        await message.answer(f"✅ {msg}", parse_mode="HTML")
        logger.info(
            "New admin added",
            by_admin_id=message.from_user.id,
            new_admin_id=new_admin_id,
        )
    else:
        await message.answer(f"❌ {msg}", parse_mode="HTML")

    await state.clear()


@router.message(Command("delete_admin"))
async def cmd_delete_admin(message: Message, session: AsyncSession) -> None:
    """
    Delete admin (admin only).

    Args:
        message: Telegram message
        session: Database session
    """
    if not await is_admin(message.from_user.id, session):
        logger.warning(
            "Non-admin tried to delete admin",
            telegram_id=message.from_user.id,
        )
        return

    try:
        admins = await AdminService.get_all_admins(session)

        if not admins:
            await message.answer("❌ Нет админов для удаления")
            return

        # Create inline keyboard with admin buttons
        buttons = []
        for admin in admins:
            # Don't allow deleting the initial admin
            if admin.telegram_id == 854825784:
                continue

            button_text = admin.first_name or admin.username or f"ID: {admin.telegram_id}"
            buttons.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"delete_admin:{admin.telegram_id}"
                )
            ])

        if not buttons:
            await message.answer("❌ Нет админов доступных для удаления")
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await message.answer(
            "👥 <b>Выберите админа для удаления:</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(
            "Error getting admins list",
            telegram_id=message.from_user.id,
            error=str(e),
        )
        await message.answer("Ошибка при получении списка админов")


@router.callback_query(F.data.startswith("delete_admin:"))
async def process_delete_admin(callback: CallbackQuery, session: AsyncSession) -> None:
    """
    Process admin deletion.

    Args:
        callback: Callback query
        session: Database session
    """
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("У вас нет прав для этого действия", show_alert=True)
        return

    try:
        admin_id = int(callback.data.split(":")[1])

        # Don't allow deleting the initial admin
        if admin_id == 854825784:
            await callback.answer(
                "Невозможно удалить главного админа",
                show_alert=True
            )
            return

        success, msg = await AdminService.delete_admin(session, admin_id)

        if success:
            await callback.message.edit_text(f"✅ {msg}")
            await callback.answer()
            logger.info(
                "Admin deleted",
                by_admin_id=callback.from_user.id,
                deleted_admin_id=admin_id,
            )
        else:
            await callback.answer(f"❌ {msg}", show_alert=True)

    except Exception as e:
        logger.error(
            "Error deleting admin",
            telegram_id=callback.from_user.id,
            error=str(e),
        )
        await callback.answer("Ошибка при удалении админа", show_alert=True)
