import json

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.admin.kbs import order_management_kb
from bot.config import bot, settings
from bot.dao.dao import ProductDao, OrderDao
from bot.user.kbs import purchase_kb
from bot.user.schemas import OrderData

purchase_standart_router = Router()


class ConfirmPurchase(StatesGroup):
    confirm_purchase = State()
    process_buy = State()


@purchase_standart_router.callback_query(F.data.startswith("set_name_phone_"))
async def page_set_user_data(call: CallbackQuery, state: FSMContext, session_without_commit: AsyncSession):
    logger.debug(f"no username route: {call.data}")

    _, _, _, data = call.data.split('_')
    delivery_methotd = data.strip()

    await state.update_data(delivery_methotd=delivery_methotd)

    await call.answer(f"Укажите данные для обратной связи")
    await call.message.answer(
        text=f"Укажите свой номер телефона, имя и фамилию(через запятую) для обратной связи.\n Пример: +79991234567, Иван Иванов",
        reply_markup=purchase_kb()
    )
    await state.set_state(ConfirmPurchase.process_buy)


@purchase_standart_router.message(F.text, ConfirmPurchase.process_buy)
async def process_buy(message: Message, state: FSMContext, session_without_commit: AsyncSession):
    logger.debug(f'process_buy: {message.text}')
    data = await state.get_data()
    phone_name_data = message.text.strip()
    phone_number, full_name = phone_name_data.split(sep=",")
    logger.debug(f"fullname: {phone_number, full_name}")

    description_message = (
        f"Пожалуйста, завершите оплату в размере {data.get('price')}₽, с помощью перевода по номеру карты 0000 0000 0000 0000 или телефону +7 999 000 0000. \n"
        f'Затем пришлите скриншот оплаты'
    )
    await state.update_data(phone_number=phone_number)
    await state.update_data(full_name=full_name)
    await message.answer(
        text=description_message,
        reply_markup=purchase_kb()
    )
    await state.set_state(ConfirmPurchase.confirm_purchase)


@purchase_standart_router.message(F.photo, ConfirmPurchase.confirm_purchase)
async def process_confirm_purchase(message: Message, state: FSMContext, session_with_commit: AsyncSession):
    purchase_photo = message.photo[-1].file_id
    data = await state.get_data()
    await state.clear()
    product_id = data.get('product_id')
    price = data.get('price')
    size = data.get('size')
    delivery_methotd = data.get('delivery_methotd')

    try:
        phone_number = data.get('phone_number')
        user_name = data.get('full_name')
    except Exception as e:
        logger.debug(f'no phone or name was asked')

    logger.debug(f"product_id: {product_id}, price: {price}, size: {size}, del: {delivery_methotd}")
    logger.debug(f"purchase photo: {purchase_photo}, user name: {user_name}")

    product_data = await ProductDao.find_one_or_none_by_id(session=session_with_commit, data_id=int(product_id))
    username = message.from_user.username

    if username:
        payment_data = {
            'user_id': int(message.from_user.id),
            'username': f'@{message.from_user.username}',
            'user name': {user_name},
            'price': price,
            'product_id': int(product_id),
            'size': size,
            'phone': phone_number,
            'delivery_methotd': delivery_methotd,
        }
    else:
        payment_data = {
            'user_id': int(message.from_user.id),
            'username': f'None',
            'user name': user_name,
            'price': price,
            'product_id': int(product_id),
            'size': size,
            'phone': phone_number,
            'delivery_methotd': delivery_methotd,
        }

    user_info = f"@{username} ({message.from_user.id}), телефон: {phone_number}" if username else f"{user_name}c ID {message.from_user.id} и контактным телефоном {phone_number}"
    text = (
        f"💲 Пользователь {user_info} купил товар <b>{product_data.name}</b> (ID: {product_id})"
        f"за <b>{product_data.price} ₽</b>.\n\n"
        f"Payment data: {payment_data}"
    )
    orderData = OrderData(
        user_id=message.from_user.id,
        user_name='@' + username if username else "None",
        fio=user_name if user_name else "None",
        product_id=product_data.id,
        product_name=product_data.name,
        product_size=size,
        photo_confirm=purchase_photo,
        price=price,
        phone_number=phone_number if phone_number else "None",
        delivery_methotd=delivery_methotd,
    )
    await OrderDao.add(
        session=session_with_commit,
        values=orderData
    )
    order = await OrderDao.find_one_or_none(
        session=session_with_commit,
        filters=orderData
    )
    logger.debug(order)
    media_group = [InputMediaPhoto(media=purchase_photo)]
    for photo in json.loads(product_data.photos):
        if photo:
            media_group.append(InputMediaPhoto(media=photo))

    for admin_id in settings.ADMIN_IDS:
        try:

            await bot.send_media_group(
                chat_id=admin_id,
                media=media_group
            )
            await bot.send_message(
                chat_id=admin_id,
                text=text,
                reply_markup=order_management_kb(order_id=order.id)
            )

        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления администраторам: {e}")
    logger.info(text)
    answer_message = (
        f'{user_name}, с вами свяжется администратор для подтверждения оплаты.'
    )
    await message.answer(
        text=answer_message,
        reply_markup=purchase_kb()
    )
