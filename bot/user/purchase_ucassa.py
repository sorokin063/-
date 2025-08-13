import json

from aiogram import Router, F
from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, InputMediaPhoto
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import bot, settings
from bot.dao.dao import ProductDao, OrderDao
from bot.user.kbs import main_user_kb, get_product_buy_kb
from bot.user.schemas import OrderData

purchase_ucassa_router = Router()


@purchase_ucassa_router.callback_query(F.data.startswith("buy_"))
async def process_about(call: CallbackQuery, state: FSMContext, session_without_commit: AsyncSession):
    _, data = call.data.split('_')
    delivery_methotd = data.strip()
    data = await state.get_data()
    product_id = data.get('product_id')
    price = data.get('price')
    size = data.get('size')

    logger.info(f"prod_id = {product_id}, price = {price}, size = {size}, del_meth = {delivery_methotd}")

    await bot.send_invoice(
        chat_id=call.from_user.id,
        title=f'Оплата 👉 {price}₽',
        description=f'Пожалуйста, завершите оплату в размере {price}₽, чтобы открыть доступ к выбранному товару.',
        payload=f"{call.from_user.id}_{product_id}_{size}_{delivery_methotd}",
        provider_token=settings.PAYMENT_PROVIDER_TOKEN,
        currency='rub',
        prices=[LabeledPrice(
            label=f'Оплата {price}',
            amount=int(price) * 100
        )],
        need_name=True,
        need_phone_number=True,
        reply_markup=get_product_buy_kb(price),

    )
    await call.message.delete()


@purchase_ucassa_router.pre_checkout_query(lambda query: True)
async def pre_checkout_query(pre_checkout_q: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


@purchase_ucassa_router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: Message, session_with_commit: AsyncSession):
    payment_info = message.successful_payment
    user_id, product_id, size, delivery_methotd = payment_info.invoice_payload.split('_')
    payment_data = {
        'user_id': int(user_id),
        'payment_id': payment_info.telegram_payment_charge_id,
        'price': payment_info.total_amount / 100,
        'product_id': int(product_id),
        'size': size,
        'delivery': delivery_methotd,
        'phone_number': payment_info.order_info.phone_number,
        'full_name': payment_info.order_info.name,
        'ucassa_charge_id': message.successful_payment.provider_payment_charge_id
    }

    product_data = await ProductDao.find_one_or_none_by_id(session=session_with_commit, data_id=int(product_id))
    username = message.from_user.username

    orderData = OrderData(
        user_id=message.from_user.id,
        user_name='@' + username if username else "None",
        fio=payment_info.order_info.name,
        product_id=product_data.id,
        product_name=product_data.name,
        product_size=size,
        photo_confirm="Ucassa",
        price=payment_info.total_amount * 100,
        phone_number=payment_info.order_info.phone_number,
        delivery_methotd=delivery_methotd,
    )
    await OrderDao.add(
        session=session_with_commit,
        values=orderData
    )

    media_group = []
    # media_group.append(InputMediaPhoto(media=purchase_photo))
    for photo in json.loads(product_data.photos):
        if photo:
            media_group.append(InputMediaPhoto(media=photo))
    # Формируем уведомление администраторам
    for admin_id in settings.ADMIN_IDS:
        try:
            username = message.from_user.username
            user_info = f"@{username} ({message.from_user.id})" if username else f"c ID {message.from_user.id}"
            await bot.send_media_group(
                chat_id=admin_id,
                media=media_group,
            )
            await bot.send_message(
                chat_id=admin_id,
                text=(
                    f"💲 Пользователь {user_info} купил товар <b>{product_data.name}</b> (ID: {product_id}) "
                    f"за <b>{product_data.price} ₽</b>."
                    f"Payment data: {payment_data}"
                )
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления администраторам: {e}")
            await bot.send_message(
                chat_id=admin_id,
                text=(
                    f"💲 Пользователь {user_info} купил товар <b>{product_data.name}</b> (ID: {product_id}) "
                    f"за <b>{product_data.price} ₽</b>."
                    f"Payment data: {payment_data}"
                )
            )

    # текст для пользователя
    product_text = (
        f"🎉 <b>Спасибо за покупку!</b>\n\n"
        f"🛒 <b>Информация о вашем товаре:</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🔹 <b>Название:</b> <b>{product_data.name}</b>\n"
        f"🔹 <b>Описание:</b>\n<i>{product_data.description}</i>\n"
        f"🔹 <b>Цена:</b> <b>{product_data.price} ₽</b>\n"
        f"🔹 <b>Размер</b>\n<i>{size}</i>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"В скором времени администрация свяжится с вами\n"
    )

    # Отправляем информацию о товаре пользователю
    if product_data.name:
        await message.answer(
            text=product_text,
            reply_markup=main_user_kb(message.from_user.id)
        )
    else:
        await message.answer(
            text=product_text,
            reply_markup=main_user_kb(message.from_user.id)
        )
