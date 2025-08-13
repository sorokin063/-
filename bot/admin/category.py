from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.admin.kbs import admin_kb, cancel_kb_inline, admin_confirm_category_kb, dell_category_kb
from bot.admin.schemas import CategoryModel, SubcategoryIDModel, CategoryIDModel
from bot.admin.utils import process_dell_text_msg
from bot.config import settings, bot
from bot.dao.dao import ProductDao, CategoryDao, SubcategoryDao

catalog_admin_router = Router()

class AddCategory(StatesGroup):
    name = State()
    confirm_add = State()


@catalog_admin_router.callback_query(F.data == 'delete_category', F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_start_dell(call: CallbackQuery, session_without_commit: AsyncSession):
    await call.answer('Режим удаления категории')
    categories = await CategoryDao.find_all(session=session_without_commit)
    
    logger.debug("Load Catalog to delete {categories}")
    for category in categories:
        subcategories = await SubcategoryDao.find_all(session=session_without_commit,filters=CategoryIDModel(id = category.id))
        prodCount = 0
        for subcetegory in subcategories:
            prodCount += await ProductDao.count(session=session_without_commit, filters=SubcategoryIDModel(id = subcetegory.id))
        text=(
                f"Категория <b>{category.category_name}</b>\n\n"
                f"В данной категории находиться <b>{len(subcategories)}</b> подкатегорий и {prodCount} товаров."
            )
        await call.message.answer(
            text=text,
            reply_markup=dell_category_kb(category.id)
        )

@catalog_admin_router.callback_query(F.data.startswith('dellcategory_'), F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_start_dell(call: CallbackQuery, session_with_commit: AsyncSession):
    category_id = int(call.data.split('_')[-1])
    logger.info(f"Category delete category_id: {category_id}")
    await CategoryDao.delete(session=session_with_commit, filters=CategoryIDModel(id=category_id))
    await call.answer(f"Категория с ID {category_id} удалена!", show_alert=True)
    await call.message.delete()


@catalog_admin_router.callback_query(F.data == 'add_category', F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_category(call: CallbackQuery, state: FSMContext):
    await call.answer('Запущен сценарий добавления категории.')
    await call.message.delete()
    msg = await call.message.answer(text="Для начала укажите имя категории: ", reply_markup=cancel_kb_inline())
    await state.update_data(last_msg_id=msg.message_id)
    await state.set_state(AddCategory.name)


@catalog_admin_router.message(F.text, F.from_user.id.in_(settings.ADMIN_IDS), AddCategory.name)
async def admin_process_category_name(message: Message, state: FSMContext, session_without_commit: AsyncSession):
    await state.update_data(category_name=message.text)
    await process_dell_text_msg(message, state)
    logger.debug(f"state: {state}\n category name: {message.text}")

    product_data = await state.get_data()
    
    category_text = (f'🛒 Проверьте, все ли корректно:\n\n'
                    f'🔹 <b>Название категории:</b> <b>{product_data["category_name"]}</b>\n')
    msg = await message.answer(text=category_text, reply_markup=admin_confirm_category_kb())
    await state.update_data(last_msg_id=msg.message_id)
    logger.debug(f"State name: {state}\n State Data: {await state.get_data()}")
    await state.set_state(AddCategory.confirm_add)
    

@catalog_admin_router.callback_query(F.data == "confirm_category_add", F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_confirm_category_add(call: CallbackQuery, state: FSMContext, session_with_commit: AsyncSession):
    await call.answer('Приступаю к сохранению файла!')
    product_data = await state.get_data()
    logger.info(f"category add data: {product_data}")
    await bot.delete_message(chat_id=call.from_user.id, message_id=product_data["last_msg_id"])
    del product_data["last_msg_id"]
    await CategoryDao.add(session=session_with_commit, values=CategoryModel(**product_data))
    await call.message.answer(text="Товар успешно добавлен в базу данных!", reply_markup=admin_kb())