import json

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

import bot.strings as s
from bot.dao.dao import UserDao, OrderDao, ProductDao
from bot.user.kbs import main_user_kb
from bot.user.schemas import UserIdModel, UserModel, OrderUserIdModel

user_router = Router()

# /start
@user_router.message(CommandStart())
async def cmd_start(message: Message, session_with_commit: AsyncSession):
    user_id = message.from_user.id
    username = message.from_user.username
    firstname = message.from_user.first_name
    logger.info(f"user_id: {user_id}, username: @{username}")

    user = await UserDao.find_one_or_none(
        session=session_with_commit,
        filters=UserIdModel(id=user_id)
    )

    if user:
        if username:
            logger.debug(username)
            if user.username != '@'+username:
                await UserDao.update(
                    session=session_with_commit,
                    filters=UserIdModel(id=user.id),
                    values=UserModel(id=user.id, username='@'+username)
                )
        
    elif username: 
        await UserDao.add(
                session=session_with_commit,
                values=UserModel(
                    id=user_id,
                    username='@'+username
                )
            )
    else: 
        await UserDao.add(
                session=session_with_commit,
                values=UserModel(
                    id=user_id,
                    username='@'+"None"
                )
            )
    # user_info = await UserDAO.find_one_or_none(
    #     session=session_with_commit,
    #     filters=TelegramIDModel(telegram_id=user_id)
    # )

    # if user_info:
    #     return await message.answer(
    #         f"👋 Привет, {message.from_user.full_name}! Выберите необходимое действие",
    #         reply_markup=main_user_kb(user_id)
    #     )

    # values = UserModel(
    #     telegram_id=user_id,
    #     username=message.from_user.username,
    #     first_name=message.from_user.first_name,
    #     last_name=message.from_user.last_name,
    # )
    # await UserDAO.add(session=session_with_commit, values=values)
    if username:
        await message.answer(f"🎉 <b>Добро пожаловать @{username}</b>.",
                            reply_markup=main_user_kb(user_id))
    else:
        await message.answer(text=f"🎉 <b>Добро пожаловать {firstname}</b>.\n Просим обратить внимание, что для покупки вам необходимо установить <b>Telegramm Username</b> (например @Username) иначе администрация не сможет связаться с вами.",
                            reply_markup=main_user_kb(user_id))
    
@user_router.callback_query(F.data == "home")
async def page_home(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer("Главная страница")
    return await call.message.answer(
        f"👋 Привет, {call.from_user.full_name}! Выберите необходимое действие",
        reply_markup=main_user_kb(call.from_user.id)
    )

@user_router.callback_query(F.data == "about")
async def page_about(call: CallbackQuery):
    await call.answer("О магазине")
    await call.message.answer(
        text=(
            s.about_text
        ),
        reply_markup=call.message.reply_markup
    )


@user_router.callback_query(F.data =="my_orders")
async def page_my_orders(call: CallbackQuery, session_without_commit: AsyncSession):
    
    orders = await OrderDao.find_all(
        session=session_without_commit,
        filters=OrderUserIdModel(user_id=call.from_user.id)
    )
    products = await ProductDao.find_all(session=session_without_commit)
    

    if orders:
        await call.message.delete()
        for order in orders:
            for product in products:
                if int(product.id)==int(order.product_id):
                    media = []
                    for photo in json.loads(product.photos): 
                        media.append(InputMediaPhoto(media=photo))
                # product = await ProductDao.find_one_or_none(
                #     session=session_without_commit,
                #     filters=ProductIDModel(id=order.product_id)
                # )
                
                    text = (
                        f"📦 <b>Название товара:</b> {product.name}\n\n"
                        f"💰 <b>Цена:</b> {product.price} руб.\n\n"
                        f"📝 <b>Описание:</b>\n<i>{product.description}</i>\n\n"
                        f"📝 <b>Размер\Цвет:</b>\n<i>{order.product_size}</i>\n\n"
                        f"━━━━━━━━━━━━━━━━━━\n\n"
                        f"<b>Статус подтверждения оплаты:</b>\n<i>{ s.confirmed if order.confirmed else s.not_confirmed}</i>\n\n"
                    )
                    await call.message.answer_media_group(media= media)
                    await call.message.answer(
                        text=text 
                        )
        await call.message.answer(
            text="Ваши заказы загруженны выше",
            reply_markup=call.message.reply_markup
        )
    else:
        await call.answer(
            text= "В данный момент у вас нет заказов"
            )
        return

# @user_router.callback_query(F.data == "my_profile")
# async def page_about(call: CallbackQuery, session_without_commit: AsyncSession):
#     await call.answer("Профиль")

#     # Получаем статистику покупок пользователя
#     purchases = await UserDAO.get_purchase_statistics(session=session_without_commit, telegram_id=call.from_user.id)
#     total_amount = purchases.get("total_amount", 0)
#     total_purchases = purchases.get("total_purchases", 0)

#     # Формируем сообщение в зависимости от наличия покупок
#     if total_purchases == 0:
#         await call.message.answer(
#             text="🔍 <b>У вас пока нет покупок.</b>\n\n"
#                  "Откройте каталог и выберите что-нибудь интересное!",
#             reply_markup=main_user_kb(call.from_user.id)
#         )
#     else:
#         text = (
#             f"🛍 <b>Ваш профиль:</b>\n\n"
#             f"Количество покупок: <b>{total_purchases}</b>\n"
#             f"Общая сумма: <b>{total_amount}₽</b>\n\n"
#             "Хотите просмотреть детали ваших покупок?"
#         )
#         await call.message.answer(
#             text=text,
#             reply_markup=purchases_kb()
#         )

# @user_router.callback_query(F.data == "purchases")
# async def page_user_purchases(call: CallbackQuery, session_without_commit: AsyncSession):
#     await call.answer("Мои покупки")

#     # Получаем список покупок пользователя
#     purchases = await UserDAO.get_purchased_products(session=session_without_commit, telegram_id=call.from_user.id)

#     if not purchases:
#         await call.message.edit_text(
#             text=f"🔍 <b>У вас пока нет покупок.</b>\n\n"
#                  f"Откройте каталог и выберите что-нибудь интересное!",
#             reply_markup=main_user_kb(call.from_user.id)
#         )
#         return

    # # Для каждой покупки отправляем информацию
    # for purchase in purchases:
    #     product = purchase.product
    #     file_text = "📦 <b>Товар включает файл:</b>" if product.file_id else "📄 <b>Товар не включает файлы:</b>"

    #     product_text = (
    #         f"🛒 <b>Информация о вашем товаре:</b>\n"
    #         f"━━━━━━━━━━━━━━━━━━\n"
    #         f"🔹 <b>Название:</b> <i>{product.name}</i>\n"
    #         f"🔹 <b>Описание:</b>\n<i>{product.description}</i>\n"
    #         f"🔹 <b>Цена:</b> <b>{product.price} ₽</b>\n"
    #         f"🔹 <b>Закрытое описание:</b>\n<i>{product.hidden_content}</i>\n"
    #         f"━━━━━━━━━━━━━━━━━━\n"
    #         f"{file_text}\n"
    #     )

    #     if product.file_id:
    #         # Отправляем файл с текстом
    #         await call.message.answer_document(
    #             document=product.file_id,
    #             caption=product_text,
    #         )
    #     else:
    #         # Отправляем только текст
    #         await call.message.answer(
    #             text=product_text,
    #         )

    # await call.message.answer(
    #     text="🙏 Спасибо за доверие!",
    #     reply_markup=main_user_kb(call.from_user.id)
    # )