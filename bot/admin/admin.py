from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from bot.config import settings
from bot.dao.dao import ProductDao, OrderDao
from bot.admin.kbs import admin_kb, admin_kb_back,admin_managment_kb, product_management_kb, orders_management_kb

from bot.admin.category import catalog_admin_router
from bot.admin.subcategory import subcatalog_admin_router
from bot.admin.product import product_admin_router
from bot.admin.orders import order_admin_router
from bot.admin.admin_managment import admin_router as admin_managment_router
from loguru import logger


admin_router = Router()
admin_router.include_routers(
    catalog_admin_router,
    subcatalog_admin_router,
    product_admin_router,
    order_admin_router,
    admin_managment_router
)


@admin_router.callback_query(F.data == "admin_panel", F.from_user.id.in_(settings.ADMIN_IDS))
async def start_admin(call: CallbackQuery):
    await call.answer('Доступ в админ-панель разрешен!')
    try:
        await call.message.edit_text(
            text="Вам разрешен доступ в админ-панель. Выберите необходимое действие.",
            reply_markup=admin_kb()
        )
    except Exception as e:
        await call.message.answer(
            text="Вам разрешен доступ в админ-панель. Выберите необходимое действие.",
            reply_markup=admin_kb()
        )
        

# @admin_router.callback_query(F.data == 'statistic', F.from_user.id.in_(settings.ADMIN_IDS))
# async def admin_statistic(call: CallbackQuery, session_without_commit: AsyncSession):
#     await call.answer('Запрос на получение статистики...')
#     await call.answer('📊 Собираем статистику...')

#     # stats = await UserDAO.get_statistics(session=session_without_commit)
#     # total_summ = await PurchaseDao.get_full_summ(session=session_without_commit)
#     stats_message = (
#         "📈 Статистика пользователей:\n\n"
#         f"👥 Всего пользователей: {stats['total_users']}\n"
#         f"🆕 Новых за сегодня: {stats['new_today']}\n"
#         f"📅 Новых за неделю: {stats['new_week']}\n"
#         f"📆 Новых за месяц: {stats['new_month']}\n\n"
#         f"💰 Общая сумма заказов: {total_summ} руб.\n\n"
#         "🕒 Данные актуальны на текущий момент."
#     )
#     await call.message.edit_text(
#         text=stats_message,
#         reply_markup=admin_kb()
#     )

@admin_router.callback_query(F.data == "cancel", F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer('Отмена сценария добавления товара')
    await call.message.delete()
    await call.message.answer(
        text="Отмена добавления товара.",
        reply_markup=admin_kb_back()
    )

@admin_router.callback_query(F.data == 'process_products', F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_products(call: CallbackQuery, session_without_commit: AsyncSession):
    await call.answer('Режим управления товарами')
    all_products_count = await ProductDao.count(session=session_without_commit)
    await call.message.edit_text(
        text=f"На данный момент в базе данных {all_products_count} товаров. Что будем делать?",
        reply_markup=product_management_kb()
    )

@admin_router.callback_query(F.data == 'process_orders', F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_orders(call: CallbackQuery, session_without_commit: AsyncSession):
    await call.answer('Режим управления заказами')
    all_orders_count = await OrderDao.count(session=session_without_commit)
    await call.message.edit_text(
        text=f"На данный момент у вас {all_orders_count} заказов. Что будем делать?",
        reply_markup=orders_management_kb()
    )

@admin_router.callback_query(F.data == 'process_admins', F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_orders(call: CallbackQuery,state: FSMContext, session_without_commit: AsyncSession):
    await state.clear()
    await call.answer('Режим управления доступом')

    await call.message.edit_text(
        text=f"Вы вошли в режим управления доступом. Что будем делать?",
        reply_markup=admin_managment_kb()
    )




