import asyncio
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, InputMediaPhoto, InputMedia
from sqlalchemy.ext.asyncio import AsyncSession
import json
from bot.config import settings, bot
from bot.dao.dao import ProductDao, CategoryDao, SubcategoryDao
from bot.admin.kbs import admin_kb, cancel_kb_inline, catalog_admin_kb, subcatalog_admin_kb, \
    admin_confirm_product_kb, dell_product_kb
from bot.admin.schemas import ProductModel, ProductIDModel, SubcategoryCategoryIDModel
from bot.admin.utils import process_dell_text_msg
from loguru import logger

product_admin_router = Router()


class AddProduct(StatesGroup):
    name = State()
    description = State()
    price = State()
    photos = State()
    category_id = State()
    subcategory_id = State()
    sizes = State()
    confirm_add_media = State()
    confirm_add_photo = State()


@product_admin_router.callback_query(F.data == 'delete_product', F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_start_dell(call: CallbackQuery, session_without_commit: AsyncSession):
    await call.answer('Режим удаления товаров')
    all_products = await ProductDao.find_all(session=session_without_commit)

    await call.message.edit_text(
        text=f"На данный момент в базе данных {len(all_products)} товаров. Для удаления нажмите на кнопку ниже"
    )
    for product_data in all_products:
        photos = json.loads(product_data.photos)
        media = []
        product_text = (f'🛒 Описание товара:\n\n'
                        f'🔹 <b>Название товара:</b> <b>{product_data.name}</b>\n'
                        f'🔹 <b>Описание:</b>\n\n<b>{product_data.description}</b>\n\n'
                        f'🔹 <b>Цена:</b> <b>{product_data.price} ₽</b>\n')
        if len(list(photos)) > 1:
            for photo in photos:
                media.append(InputMediaPhoto(media=photo))

            await call.message.answer_media_group(media=media)
            await call.message.answer(text=product_text, reply_markup=dell_product_kb(product_data.id))

        else:
            await call.message.answer_photo(photo=photos[0], caption=product_text,
                                            reply_markup=dell_product_kb(product_data.id))
        # if file_id:
        #     await call.message.answer_photo(photo=file_id, caption=product_text,
        #                                        reply_markup=dell_product_kb(product_data.id))
        # else:
        #     await call.message.answer(text=product_text,
        #                                        reply_markup=dell_product_kb(product_data.id))


@product_admin_router.callback_query(F.data.startswith('dellproduct_'), F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_start_dell(call: CallbackQuery, session_with_commit: AsyncSession):
    product_id = int(call.data.split('_')[-1])
    product = await ProductDao.find_one_or_none_by_id(
        data_id=ProductIDModel(id=product_id),
        session=session_with_commit
    )
    logger.info(f"Product delete prod_id: {product.id}, prod_name: {product.name}")
    await ProductDao.delete(session=session_with_commit, filters=ProductIDModel(id=product_id))
    await call.answer(f"Товар с ID {product_id} удален!", show_alert=True)
    await call.message.delete()


@product_admin_router.callback_query(F.data == 'add_product', F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_add_product(call: CallbackQuery, state: FSMContext):
    await call.answer('Запущен сценарий добавления товара.')
    await call.message.delete()
    msg = await call.message.answer(text="Для начала укажите имя товара: ", reply_markup=cancel_kb_inline())
    await state.update_data(last_msg_id=msg.message_id)
    await state.set_state(AddProduct.name)


@product_admin_router.message(F.text, F.from_user.id.in_(settings.ADMIN_IDS), AddProduct.name)
async def admin_process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await process_dell_text_msg(message, state)
    msg = await message.answer(text="Теперь дайте короткое описание товару: ", reply_markup=cancel_kb_inline())
    await state.update_data(last_msg_id=msg.message_id)
    logger.debug(f"State name: {state}\n State Data: {await state.get_data()}")
    await state.set_state(AddProduct.description)


@product_admin_router.message(F.text, F.from_user.id.in_(settings.ADMIN_IDS), AddProduct.description)
async def admin_process_description(message: Message, state: FSMContext, session_without_commit: AsyncSession):
    await state.update_data(description=message.html_text)
    await process_dell_text_msg(message, state)
    catalog_data = await CategoryDao.find_all(session=session_without_commit)
    msg = await message.answer(text="Теперь выберите категорию товара: ", reply_markup=catalog_admin_kb(catalog_data))
    await state.update_data(last_msg_id=msg.message_id)
    logger.debug(f"State description: {state}\n State Data: {await state.get_data()}")
    await state.set_state(AddProduct.category_id)


@product_admin_router.callback_query(F.data.startswith("add_category_"),
                                     F.from_user.id.in_(settings.ADMIN_IDS),
                                     AddProduct.category_id)
async def admin_process_category(call: CallbackQuery, state: FSMContext, session_without_commit: AsyncSession):
    category_id = int(call.data.split("_")[-1])
    await state.update_data(category_id=category_id)
    subCatalog_data = await SubcategoryDao.find_all(session_without_commit,
                                                    SubcategoryCategoryIDModel(category_id=category_id))
    logger.debug(f"subCatalog_data: {subCatalog_data}")
    await call.answer('Категория товара успешно выбрана.')
    msg = await call.message.edit_text(text="Выберите подкатегорию: ",
                                       reply_markup=subcatalog_admin_kb(subCatalog_data))
    await state.update_data(last_msg_id=msg.message_id)
    logger.debug(f"State category: {state}\n State Data: {await state.get_data()}")
    await state.set_state(AddProduct.subcategory_id)


@product_admin_router.callback_query(F.data.startswith("add_category_"),
                                     F.from_user.id.in_(settings.ADMIN_IDS),
                                     AddProduct.subcategory_id)
async def admin_process_subcategory(call: CallbackQuery, state: FSMContext):
    category_id = int(call.data.split("_")[-1])
    await state.update_data(subcategory_id=category_id)
    await call.answer('Подкатегория товара успешно выбрана.')
    msg = await call.message.edit_text(text="Введите цену товара: ", reply_markup=cancel_kb_inline())
    await state.update_data(last_msg_id=msg.message_id)
    logger.debug(f"State category: {state}\n State Data: {await state.get_data()}")
    await state.set_state(AddProduct.price)


@product_admin_router.message(F.text, F.from_user.id.in_(settings.ADMIN_IDS), AddProduct.price)
async def admin_process_price(message: Message, state: FSMContext):
    try:
        price = int(message.text)
        await state.update_data(price=price)
        await process_dell_text_msg(message, state)
        msg = await message.answer(
            text="Добавте доступные размеры",
            reply_markup=cancel_kb_inline()
        )
        await state.update_data(last_msg_id=msg.message_id)
        logger.debug(f"State price: {state}\n State Data: {await state.get_data()}")
        await state.set_state(AddProduct.sizes)
    except ValueError:
        await message.answer(text="Ошибка! Необходимо ввести числовое значение для цены.")
        return


@product_admin_router.message(F.text, F.from_user.id.in_(settings.ADMIN_IDS), AddProduct.sizes)
async def admin_process_sizes(message: Message, state: FSMContext):
    sizes = message.text.replace(" ", "").split(",")
    await state.update_data(sizes=json.dumps(sizes))
    await process_dell_text_msg(message, state)
    msg = await message.answer(
        text="Теперь отправьте фото товара",
        reply_markup=cancel_kb_inline())
    await state.update_data(last_msg_id=msg.message_id)
    logger.debug(f"State sizes: {state}\n State Data: {await state.get_data()}")
    await state.set_state(AddProduct.photos)


@product_admin_router.message(F.photo, F.from_user.id.in_(settings.ADMIN_IDS), AddProduct.photos)
async def admin_process_photos(message: Message, state: FSMContext, session_without_commit: AsyncSession,
                               album: list[Message] = None):
    media_group = []
    media_data = []
    logger.debug(f"album: {album}")

    product_data = await state.get_data()

    category_info = await CategoryDao.find_one_or_none_by_id(session=session_without_commit,
                                                             data_id=product_data.get("category_id"))
    subcategory_info = await SubcategoryDao.find_one_or_none_by_id(session=session_without_commit,
                                                                   data_id=product_data.get("subcategory_id"))
    sizes = ''.join(str(size) for size in product_data["sizes"])
    product_text = (f'🛒 Проверьте, все ли корректно:\n\n'
                    f'🔹 <b>Название товара:</b> <b>{product_data["name"]}</b>\n'
                    f'🔹 <b>Описание:</b>\n\n<b>{product_data["description"]}</b>\n\n'
                    f'🔹 <b>Цена:</b> <b>{product_data["price"]} ₽</b>\n'
                    f'🔹 <b>Описание (закрытое): {sizes} </b>\n\n<b></b>\n\n'
                    f'🔹 <b>Категория:</b> <b>{category_info.category_name} (ID: {category_info.id})</b>\n\n'
                    f'🔹 <b>Категория:</b> <b>{subcategory_info.subcategory_name} (ID: {subcategory_info.id})</b>\n\n')
    if album:
        for num in range(len(album)):
            if album[num]:
                logger.debug(f"photo: {album[num].photo[-1].file_id}")
                file_id = album[num].photo[-1].file_id
                media_data.append(file_id)
                media_group.append(InputMediaPhoto(media=file_id))
            else:
                obj_dict = album[num].dict()
                file_id = obj_dict[album[num].content_type]['file_id']
                media_group.append(InputMedia(media=file_id))
    else:
        file_id = message.photo[-1].file_id
        media_data.append(file_id)
        media_group.append(InputMediaPhoto(media=file_id))

    logger.debug(f"photos sent: {message.photo}")
    await state.update_data(photos=json.dumps(media_data))
    logger.debug(f"state: {state}\n message photo: {message.photo} \n photo id: {message.photo[-1].file_id}")

    file_id = product_data.get("photos")

    await process_dell_text_msg(message, state)
    mediamsg = await message.answer_media_group(media=media_group, )  # reply_markup=admin_confirm_product_kb()
    await state.update_data(mediamsg=mediamsg[0].message_id)
    msg = await message.answer(text=product_text, reply_markup=admin_confirm_product_kb())
    await state.update_data(last_msg_id=msg.message_id)
    logger.debug(f"State photo: {state}\n State Data: {await state.get_data()}")
    await state.set_state(AddProduct.confirm_add_media)


@product_admin_router.callback_query(F.data == "confirm_add", F.from_user.id.in_(settings.ADMIN_IDS),
                                     AddProduct.confirm_add_media)
async def admin_process_confirm_add(call: CallbackQuery, state: FSMContext, session_with_commit: AsyncSession):
    await call.answer('Приступаю к сохранению файла!')
    product_data = await state.get_data()
    await state.clear()
    logger.debug(f"product data: {product_data}")
    await bot.delete_message(chat_id=call.from_user.id, message_id=product_data["mediamsg"])
    await bot.delete_message(chat_id=call.from_user.id, message_id=product_data["last_msg_id"])
    del product_data["last_msg_id"]
    del product_data["category_id"]
    logger.info(f"Product add: {product_data}")
    await ProductDao.add(session=session_with_commit, values=ProductModel(**product_data))
    await call.message.answer(text="Товар успешно добавлен в базу данных!", reply_markup=admin_kb())

