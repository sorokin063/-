from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.config import settings
from bot.dao.models import Category, Subcategory
import bot.strings as s


def main_user_kb(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=s.catalog, callback_data="catalog")
    kb.button(text=s.about, callback_data="about")
    kb.button(text=s.my_orders , callback_data="my_orders")
    if user_id in settings.ADMIN_IDS:
        kb.button(text=s.admin_panel, callback_data="admin_panel")
    kb.adjust(1)
    return kb.as_markup()


def catalog_kb(catalog_data: List[Category]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for category in catalog_data:
        kb.button(text=category.category_name, callback_data=f"category_{category.id}")
    kb.button(text=s.to_home, callback_data="home")
    kb.adjust(2)
    return kb.as_markup()

def subcatalog_kb(subcatalog_data: List[Subcategory]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for category in subcatalog_data:
        kb.button(text=category.subcategory_name, callback_data=f"subcategory_{category.id}")
    kb.button(text=s.to_home, callback_data="home")
    kb.button(text=s.back, callback_data="catalog")
    kb.adjust(2)
    return kb.as_markup()


def purchases_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🗑 Смотреть покупки", callback_data="purchases")
    kb.button(text="🏠 На главную", callback_data="home")
    kb.adjust(1)
    return kb.as_markup()


def product_kb(product_id ) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=s.buy, callback_data=f"size_{product_id}")
    kb.button(text=s.back, callback_data=f"catalog")
    kb.button(text=s.to_home, callback_data="home")
    kb.adjust(2)
    return kb.as_markup()

def choose_size_kb(product_id, price, sizes) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for size in sizes:
        kb.button(text=size, callback_data=f"buy_{product_id, price, size}")
    kb.button(text=s.to_home, callback_data="home")
    kb.adjust(3, 3, 3, 1)
    return kb.as_markup()

def choose_size_kb2(product_id, price, sizes) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for size in sizes:
        kb.button(text=size, callback_data=f"delivery_{product_id, price, size}")
    kb.button(text=s.to_home, callback_data="home")
    kb.adjust(3, 3, 3, 1)
    return kb.as_markup()

def delivery_kb():
    # standart route
    kb = InlineKeyboardBuilder()
    deliveries = ["ТомскПВЗ", "CDEK", "Деловые линии", "Boxberry",]

    for delvivery in deliveries:
        kb.button(text=delvivery, callback_data=f"set_name_phone_{delvivery}")
    
    kb.button(text=s.to_home, callback_data="home")
    kb.adjust(3)
    return kb.as_markup()

def delivery_kb2():
    # ucassa route
    kb = InlineKeyboardBuilder()
    deliveries = ["ТомскПВЗ", "CDEK", "Деловые линии", "Boxberry",]

    for delivery in deliveries:
        kb.button(text=delivery, callback_data=f"buy_{delivery}")
    
    kb.button(text=s.to_home, callback_data="home")
    kb.adjust(3)
    return kb.as_markup()

def purchase_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=s.back, callback_data="catalog")
    kb.button(text=s.to_home, callback_data="home")
    kb.adjust(2)
    return kb.as_markup()


def get_product_buy_kb(price) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f'Оплатить {price}₽', pay=True)],
        [InlineKeyboardButton(text='Отменить', callback_data='home')]
    ])