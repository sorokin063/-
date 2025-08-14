from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.admin.kbs import admin_kb, cancel_kb_inline, catalog_admin_kb, admin_confirm_subctegory_kb, \
    dell_subcategory_kb
from bot.admin.schemas import SubcategoryModel, SubcategoryIDModel
from bot.admin.utils import process_dell_text_msg
from bot.config import settings, bot
from bot.dao.dao import ProductDao, CategoryDao, SubcategoryDao

subcatalog_admin_router = Router()


class AddSubcategory(StatesGroup):
    name = State()
    category_id = State()
    confirm_add = State()


@subcatalog_admin_router.callback_query(F.data == 'delete_subcategory', F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_start_dell(call: CallbackQuery, session_without_commit: AsyncSession):
    await call.answer('Режим удаления категории')
    subcategories = await SubcategoryDao.find_all(session=session_without_commit)
    logger.debug("Load SubCatalog to delete {subcategories}")
    for sub in subcategories:
        prodCount = await ProductDao.count(session=session_without_commit, filters=SubcategoryIDModel(id=sub.id))
        await call.message.answer(
            text=f"В данной категории находиться {prodCount} товаров.",
            reply_markup=dell_subcategory_kb(sub.id)
        )


@subcatalog_admin_router.callback_query(F.data.startswith('dellsubcategory_'), F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_start_dell(call: CallbackQuery, session_with_commit: AsyncSession):
    subcategory_id = int(call.data.split('_')[-1])
    logger.info(f"Category delete category_id: {subcategory_id}")
    await SubcategoryDao.delete(session=session_with_commit, filters=SubcategoryIDModel(id=subcategory_id))
    await call.answer(f"Подкатегория с ID {subcategory_id} удалена!", show_alert=True)
    await call.message.delete()


@subcatalog_admin_router.callback_query(F.data == 'add_subcategory', F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_add_subcategory(call: CallbackQuery, state: FSMContext):
    await call.answer('Запущен сценарий добавления подкатегории.')
    await call.message.delete()
    msg = await call.message.answer(text="Для начала укажите имя подкатегории: ", reply_markup=cancel_kb_inline())
    await state.update_data(last_msg_id=msg.message_id)
    await state.set_state(AddSubcategory.name)


@subcatalog_admin_router.message(F.text, F.from_user.id.in_(settings.ADMIN_IDS), AddSubcategory.name)
async def admin_process_subcategory_name(message: Message, state: FSMContext, session_without_commit: AsyncSession):
    await state.update_data(subcategory_name=message.text)
    await process_dell_text_msg(message, state)
    logger.debug(f"state: {state}\n subcategory name: {message.text}")

    catalog_data = await CategoryDao.find_all(session=session_without_commit)
    msg = await message.answer(text="Теперь выберите категорию товара: ", reply_markup=catalog_admin_kb(catalog_data))
    await state.update_data(last_msg_id=msg.message_id)
    logger.debug(f"State description: {state}\n State Data: {await state.get_data()}")
    await state.set_state(AddSubcategory.category_id)


@subcatalog_admin_router.callback_query(F.data.startswith("add_category_"),
                                        F.from_user.id.in_(settings.ADMIN_IDS),
                                        AddSubcategory.category_id)
async def admin_process_subcategory_category(call: CallbackQuery, state: FSMContext,
                                             session_without_commit: AsyncSession):
    message = call.message
    category_id = int(call.data.split("_")[-1])
    await state.update_data(category_id=category_id)
    await process_dell_text_msg(message, state)
    logger.debug(f"state: {state}\n message category_id: {category_id}")

    product_data = await state.get_data()
    category_info = await CategoryDao.find_one_or_none_by_id(session=session_without_commit,
                                                             data_id=product_data.get("category_id"))

    category_text = (f'🛒 Проверьте, все ли корректно:\n\n'
                     f'🔹 <b>Название подкатегории:</b> <b>{product_data["subcategory_name"]}</b>\n'
                     f'🔹 <b>Категория:</b> <b>{category_info.category_name} (ID: {category_info.id})</b>\n\n')
    msg = await message.answer(text=category_text, reply_markup=admin_confirm_subctegory_kb())
    await state.update_data(last_msg_id=msg.message_id)
    logger.info(f"State name: {state}\n State Data: {await state.get_data()}")
    await state.set_state(AddSubcategory.confirm_add)


@subcatalog_admin_router.callback_query(F.data == "confirm_subcategory_add", F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_confirm_subcategory_add(call: CallbackQuery, state: FSMContext,
                                                session_with_commit: AsyncSession):
    await call.answer('Приступаю к сохранению файла!')
    product_data = await state.get_data()
    logger.info(f"category add data: {product_data}")
    await bot.delete_message(chat_id=call.from_user.id, message_id=product_data["last_msg_id"])
    del product_data["last_msg_id"]
    await SubcategoryDao.add(session=session_with_commit, values=SubcategoryModel(**product_data))
    await call.message.answer(text="Подкатегория успешно добавлена в базу данных!", reply_markup=admin_kb())
