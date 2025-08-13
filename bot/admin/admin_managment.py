from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession
from bot.config import settings
from bot.dao.dao import AdminDao, UserDao
from bot.admin.kbs import cancel_kb_inline, admin_managment_kb
from bot.admin.schemas import AdminUsernameModel, AdminModel
from bot.admin.utils import process_dell_text_msg
from loguru import logger
import pandas as pd


admin_router = Router()

class AdminManagment(StatesGroup):
    delete_admin = State()
    add_admin = State()


@admin_router.callback_query(F.data == 'delete_admin', F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_admin_dell(call:CallbackQuery, state: FSMContext, session_without_commit: AsyncSession):
    await call.answer('Режим удаления админа')
    
    try:
        msg = await call.message.edit_text(
            text="Введите username админа (например @username) для удаления",
            reply_markup=cancel_kb_inline(cancel_callback_data='process_admins')
            )
        await state.update_data(last_msg_id = msg.message_id)
        await state.set_state(AdminManagment.delete_admin)
    except Exception as e:
        logger.debug(e)
        await call.message.delete()
        msg = await call.message.answer(
            text="Введите username админа (например @username) для удаления",
            reply_markup=cancel_kb_inline(cancel_callback_data='process_admins')
            )
        await state.update_data(last_msg_id = msg.message_id)
        await state.set_state(AdminManagment.delete_admin)

@admin_router.message(F.text, F.from_user.id.in_(settings.ADMIN_IDS), AdminManagment.delete_admin)
async def admin_process_name(message: Message, state: FSMContext, session_with_commit: AsyncSession):
    
    admin_username: str
    if message.text.strip():
        admin_username = message.text.strip()
        admin = await AdminDao.find_one_or_none(
              session=session_with_commit,
              filters= AdminUsernameModel(username=admin_username)
            )
        if admin:
            await AdminDao.delete(session=session_with_commit, filters=AdminUsernameModel(username=admin_username))
            logger.info(f"Admin delete: {admin_username}")

            try:
                settings.ADMIN_IDS.remove(admin.id)
                
            except Exception as e:
                logger.error(e)

            await process_dell_text_msg(message=message, state=state)
            await state.clear()
            await message.answer(
                text=f"Пользователь с id {admin.id} и Username {admin.username} был удален",
                reply_markup=admin_managment_kb()
            )
        else:
            await process_dell_text_msg(message=message, state=state)
            await state.clear()
            await message.answer(
                text=f"Пользователь с id {admin_username} не числиться как админ",
                reply_markup=admin_managment_kb()
            )
    else:
        await message.answer(
            text=f"id должен состоять из цифр. Попробуйте снова",
            reply_markup=cancel_kb_inline('process_admins')
        )
        await process_dell_text_msg(message, state)

@admin_router.callback_query(F.data == 'add_admin', F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_admin_add(call:CallbackQuery, state: FSMContext, session_without_commit: AsyncSession):
    await call.answer(f"Режим добавления Админа")

    try: 
        msg = await call.message.edit_text(
            text="Введите username админа для добавления (например @username).\n\n Обратите внимание что для добавления пользователя как админа, он должен хотя бы раз начать работу с ботом",
            reply_markup=cancel_kb_inline(cancel_callback_data='process_admins')
            )
        await state.update_data(last_msg_id = msg.message_id)
        await state.set_state(AdminManagment.add_admin)

    except Exception as e:
        logger.debug(e)
        await call.message.delete()
        msg = await call.message.answer(
            text="Введите username админа для добавления (например @username).\n\n Обратите внимание что для добавления пользователя как админа, он должен хотя бы раз начать работу с ботом",
            reply_markup=cancel_kb_inline(cancel_callback_data='process_admins')
            )
        await state.update_data(last_msg_id = msg.message_id)
        await state.set_state(AdminManagment.add_admin)
    
    

@admin_router.message(F.text, F.from_user.id.in_(settings.ADMIN_IDS), AdminManagment.add_admin)
async def admin_process_name(message: Message, state: FSMContext, session_with_commit: AsyncSession):
    
    username = message.text.strip()
    logger.debug(username)
    user = await UserDao.find_one_or_none(
        session=session_with_commit,
        filters=AdminUsernameModel(username=username)
        )
    logger.debug(f"{user.id}, {user.username}")
    if user:
        admin = await AdminDao.add(
            session=session_with_commit,
            values= AdminModel(
                id=user.id,
                username=user.username
            )  
        )
        logger.info(f"Add new admin: {admin.id}, {admin.username}")
        await process_dell_text_msg(message=message, state=state)
        await state.clear()

        await message.answer(
            text=f"Пользователь с id {admin.id} и Username {admin.username} был повышен до Админа",
            reply_markup=admin_managment_kb()
        )
    else:
        await process_dell_text_msg(message=message, state=state)
        await state.clear()
        await message.answer(
            text=f"Ошибка добавления пользователя.\n\n Пользователь {username}, ниразу не общался с ботом, или уже является админом",
            reply_markup=admin_managment_kb()
        )


@admin_router.callback_query(F.data == 'get_admin_list', F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_get_admin_list(call:CallbackQuery, session_without_commit: AsyncSession):
    admins = await AdminDao.find_all(
        session=session_without_commit
    )
    id =[]
    username = []
    for admin in admins:
        id.append(admin.id)
        username.append(admin.username)
    data = {
        'id': id,
        'username': username
    }
    df = pd.DataFrame(data)
    df.to_excel("Admins.xlsx")

    await call.message.delete()
    await call.message.answer_document(
        document=FSInputFile("Admins.xlsx"),
        reply_markup=admin_managment_kb()
    )


@admin_router.callback_query(F.data == 'get_user_list', F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_get_user_list(call:CallbackQuery, session_without_commit: AsyncSession):
    pass

@admin_router.callback_query(F.data == 'update_admins', F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_update_admins(call:CallbackQuery, session_without_commit: AsyncSession):
    admins = await AdminDao.find_all(session=session_without_commit)
    for admin in admins:
        if settings.ADMIN_IDS.count(admin.id) == 0:
            settings.ADMIN_IDS.append(admin.id)
            logger.info(f"Update admin list {settings.ADMIN_IDS}")
            
    await call.answer(f"Список админов обновлен")
