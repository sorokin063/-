import json

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.dao.dao import CategoryDao, ProductDao, SubcategoryDao
from bot.user.kbs import catalog_kb, product_kb, subcatalog_kb, choose_size_kb2, delivery_kb, delivery_kb2
from bot.user.purchase_standart import purchase_standart_router
from bot.user.purchase_ucassa import purchase_ucassa_router
from bot.user.schemas import ProductCategoryIDModel, SubcategoryIDModel

catalog_router = Router()
catalog_router.include_routers(
    purchase_ucassa_router,
    purchase_standart_router,
)


@catalog_router.callback_query(F.data == "catalog")
async def page_catalog(call: CallbackQuery, state: FSMContext, session_without_commit: AsyncSession):
    await state.clear()
    await call.answer("Загрузка каталога...")
    catalog_data = await CategoryDao.find_all(session=session_without_commit)
    logger.debug(f"Load Catalog {catalog_data}")

    try:
        await call.message.edit_text(
            text="Выберите категорию товаров:",
            reply_markup=catalog_kb(catalog_data)
        )
    except Exception as e:
        logger.error(f"Catalog message edit: {e}")
        await call.message.answer(
            text="Выберите категорию товаров:",
            reply_markup=catalog_kb(catalog_data)
        )

@catalog_router.callback_query(F.data.startswith("category_"))
async def page_catalog_subcatalog(call: CallbackQuery, session_without_commit: AsyncSession):
    category_id = int(call.data.split("_")[-1])
    subcatigories = await SubcategoryDao.find_all(session=session_without_commit,
                                                  filters=SubcategoryIDModel(category_id=category_id))
    logger.debug(f"Load SubCatalog {subcatigories}")
    count_subcategories = len(subcatigories)

    if count_subcategories:
        await call.message.edit_text(
            text="Выберите категорию товаров:",
            reply_markup=subcatalog_kb(subcatigories)
        )
    else:
        await call.answer("В данной категории нет товаров.")

    

@catalog_router.callback_query(F.data.startswith("subcategory_"))
async def page_subcatalog_products(call: CallbackQuery, session_without_commit: AsyncSession):
    subcategory_id = int(call.data.split("_")[-1])
    products_category = await ProductDao.find_all(session=session_without_commit,
                                                  filters=ProductCategoryIDModel(subcategory_id=subcategory_id))
    
    count_products = len(products_category)
    if count_products:
        await call.message.delete()
        await call.answer(f"В данной категории {count_products} товаров.")
        for product in products_category:
            sizes = str(json.loads(product.sizes))
            logger.debug(f"sizes: {sizes}")
            media_group = []
            product_text = (
                f"📦 <b>Название товара:</b> {product.name}\n\n"
                f"💰 <b>Цена:</b> {product.price} руб.\n\n"
                f"📝 <b>Описание:</b>\n<i>{product.description}</i>\n\n"
                f"📝 <b>Описание:</b>\n<i>{sizes}</i>\n\n"
                f"━━━━━━━━━━━━━━━━━━"
            )
            photos = json.loads(product.photos)
            for photo in photos:
                logger.debug(f"photo id: {photo}")
                media_group.append(InputMediaPhoto(media=photo))
            
            await call.message.answer_media_group(media=media_group)
            await call.message.answer( 
                text=product_text,
                reply_markup=product_kb(product.id)
            )
    else:
        await call.answer("В данной категории нет товаров.")

@catalog_router.callback_query(F.data.startswith("size_"))
async def page_products_size(call: CallbackQuery, session_without_commit: AsyncSession):
    logger.debug(f"prod sizes call data: {call.data}")
    _, prod_id = call.data.split("_")
    product = await ProductDao.find_one_or_none_by_id(data_id=prod_id, session=session_without_commit)

    sizes = list[str](json.loads(product.sizes))
    logger.debug(f"sizes: {sizes}")
    await call.answer(f"Выберите размер: ")

    await call.message.answer(
            text="Выберите размер",
            reply_markup=choose_size_kb2(prod_id, product.price, sizes=sizes)
            )
        

@catalog_router.callback_query(F.data.startswith("delivery_"))
async def set_delivery(call: CallbackQuery, state:FSMContext, session_without_commit: AsyncSession):
    logger.debug(f"delivery: {call.data}")

    _, data = call.data.split('_')
    product_id, price, size = data.replace("(","").replace(")","").replace("'","").split(',')
    product_id.strip()
    price.strip()
    size.strip()

    logger.debug(f"prod_id = {product_id}, price = {price}, size = {size}")

    await state.update_data(product_id = product_id)
    await state.update_data(price = price)
    await state.update_data(size = size)

    await call.answer(f'Выберите способ доставки')
    await call.message.answer(
        text= f'Выберете способ доставки. \n За доставку оплата производиться отдельно после подтверждения оплаты товара',
        reply_markup= delivery_kb2(),
    )
    

