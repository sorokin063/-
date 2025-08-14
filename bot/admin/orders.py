
import pandas as pd
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, FSInputFile
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.admin.kbs import cancel_kb_inline, order_management_kb, order_confirmed_management_kb
from bot.admin.schemas import OrderUsernameModel, OrderData, OrderIdModel, OrderUserIdModel
from bot.config import settings
from bot.dao.dao import OrderDao, ProductDao

order_admin_router = Router()
class OrderStatus(StatesGroup):
    username = State()

@order_admin_router.callback_query(F.data == 'process_status', F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_order_status_by_name(call: CallbackQuery, session_without_commit: AsyncSession, state: FSMContext):
    await call.message.edit_text(
        text=f"Введите id пользователя, наприер 1345678915648",
        reply_markup=cancel_kb_inline()
    )
    await state.set_state(OrderStatus.username)

@order_admin_router.message(F.text, F.from_user.id.in_(settings.ADMIN_IDS), OrderStatus.username)
async def order_status_process_name(message:Message, state: FSMContext, session_without_commit: AsyncSession):
    user_id = message.text.strip()
    logger.debug(user_id)
    orders = await OrderDao.find_all(
        session=session_without_commit,
        filters= OrderUserIdModel(user_id=int(user_id))
    )
    
    logger.debug(orders)
    await message.delete()
    if orders:
        for order in orders: 
            payment_data = {
                'user_id': int(order.user_id),
                'username': f'@{order.user_name}',
                'user name': {order.fio},
                'price': order.price,
                'product_id': int(order.product_id),
                'product_name': order.product_name,
                'size': order.product_size,
                'phone_number': order.phone_number,
                'delivery_methotd': order.delivery_methotd,
                'Confirmed': order.confirmed
                }

            payment_info = (
                f"user_id: <b>{int(order.user_id)}</b>,\n"
                f"username: <b>@{order.user_name},</b>\n"
                f"FIO: <b>{order.fio}</b>,\n"
                # f"'payment_id': <b>{payment_info.telegram_payment_charge_id}</b>,\n"
                f"'price': <b>{order.price}</b>,\n"
                f"'product_id': <b>{int(order.product_id)}</b>,\n"
                f"product_name: <b>{order.product_name}</b>,\n"
                f"'size': <b>{order.product_size}</b>,\n"
                f"'delivery': <b>{order.delivery_methotd}</b>,\n"
                f"'phone_number': <b>{order.phone_number}</b>,\n"
                # f"'full_name': <b>{payment_info.order_info.name}</b>,\n"
                # f"'ucassa_charge_id': <b>{message.successful_payment.provider_payment_charge_id}</b>\n"
                f"Confirmed: {order.confirmed}"
            )

            try:

                if order.confirmed:
                    await message.answer_photo(
                    photo=order.photo_confirm,
                    caption=f"{payment_info}",
                    reply_markup=order_confirmed_management_kb(order_id=order.id)
                )
                else:
                    await message.answer_photo(
                        photo=order.photo_confirm,
                        caption=f"{payment_info}",
                        reply_markup=order_management_kb(order_id=order.id)
                    )
            except Exception as e:
                logger.info(f"{e}\n\n order Ucassa")
                product_data = await ProductDao.find_one_or_none_by_id(
                    session=session_without_commit,
                    data_id=int(order.product_id)
                )
                if order.confirmed:
                    await message.answer(
                        text=f"{payment_info}",
                        reply_markup=order_confirmed_management_kb(order_id = order.id)
                    )
                else:
                    await message.answer(
                        text=f"{payment_info}",
                        reply_markup=order_management_kb(order_id=order.id)
                    )
            
    else:
        await message.answer(
            text=f"Пользователь {user_id} не заказывал товары",
            reply_markup=cancel_kb_inline()
        )
    await state.clear()

@order_admin_router.callback_query(F.data.startswith('confirm_order_'), F.from_user.id.in_(settings.ADMIN_IDS))
async def confirm_order(call: CallbackQuery, session_with_commit: AsyncSession):
    logger.debug('admin confirm order')
    _, _, order_id = call.data.split('_')
    order = await OrderDao.find_one_or_none_by_id(data_id=order_id, session=session_with_commit)
    logger.debug(order)
    if order.confirmed:
        await call.answer(text="Товар уже подтвержден")
    else:
        new_order = OrderData(
            user_id=order.user_id,
            user_name=order.user_name,
            fio=order.fio,
            product_id=order.product_id,
            product_name=order.product_name,
            product_size=order.product_size,
            price=order.price,
            phone_number=order.phone_number,
            delivery_methotd = order.delivery_methotd,
            confirmed=True
        )
        await OrderDao.update(values=new_order,filters= OrderIdModel(id=order_id) , session= session_with_commit)
        await call.answer(text="Товар подтвержден")

@order_admin_router.callback_query(F.data.startswith('order_delete_'), F.from_user.id.in_(settings.ADMIN_IDS))
async def confirm_order(call: CallbackQuery, session_with_commit: AsyncSession):
    logger.debug(call.data.split('_'))
    _,_, order_id = call.data.split('_')
    logger.debug(order_id)

    order = await OrderDao.find_one_or_none_by_id(
        data_id=int(order_id),
        session=session_with_commit
        )
    
    await OrderDao.delete(
        session=session_with_commit, 
        filters= OrderIdModel(id = int(order_id))
        )
    logger.info(f"Заказ {order} был доставлен покупателю и удален из Базы данных")
    await call.message.delete()
    await call.answer(text= "Товар доставлен или отменен и удален из БД")

@order_admin_router.callback_query(F.data == "get_orders_excel" ,  F.from_user.id.in_(settings.ADMIN_IDS))
async def get_orders_excel(call: CallbackQuery, session_without_commit: AsyncSession):

    
    orders = await OrderDao.find_all(session=session_without_commit)
    id = []
    user_id =[]
    user_name= []
    fio = []
    product_id =[]
    product_name =[]
    product_size= []
    price =[]
    phone_number=[]
    delivery_methotd = []
    confirmed =[]
    for order in orders:
        id.append(order.id)
        user_id.append(order.user_id)
        user_name.append(order.user_name)
        fio.append(order.fio)
        product_id.append(order.product_id)
        product_name.append(order.product_name)
        product_size.append(order.product_size)
        price.append(order.price)
        phone_number.append(order.phone_number)
        delivery_methotd.append(order.delivery_methotd)
        confirmed.append(order.confirmed)
    data = {
        'id': id,
        'user_id': user_id,
        'user_name': user_name,
        'fio': fio,
        'product_id': product_id,
        'product_name': product_name,
        'product_size': product_size,
        'price': price,
        'phone_number': phone_number,
        'delivery_methotd': delivery_methotd,
        'confirmed': confirmed,
    }
    df = pd.DataFrame(data)
    logger.debug(df)
    df.to_excel("Orders.xlsx")
    await call.message.answer_document(FSInputFile("Orders.xlsx"), reply_markup=cancel_kb_inline())
