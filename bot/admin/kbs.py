from typing import List, Optional, Union
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.dao.models import Category, Subcategory
import bot.strings as s


def catalog_admin_kb(catalog_data: List[Category]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for category in catalog_data:
        kb.button(text=category.category_name, callback_data=f"add_category_{category.id}")
    kb.button(text=s.cancel, callback_data="admin_panel")
    kb.adjust(2)
    return kb.as_markup()

def subcatalog_admin_kb(catalog_data: List[Subcategory]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for category in catalog_data:
        kb.button(text=category.subcategory_name, callback_data=f"add_category_{category.id}")
    kb.button(text=s.cancel, callback_data="admin_panel")
    kb.adjust(2)
    return kb.as_markup()


def admin_send_photo_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=s.cancel, callback_data="admin_panel")
    kb.adjust(2)
    return kb.as_markup()


def admin_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=s.manage_product, callback_data="process_products")
    kb.button(text=s.manage_orders, callback_data="process_orders")
    kb.button(text=s.manage_admins, callback_data="process_admins")
    kb.button(text=s.to_home, callback_data="home")
    kb.adjust(2,2)
    return kb.as_markup()

def admin_managment_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text=s.add_admin, callback_data="add_admin")
    kb.button(text=s.del_admin, callback_data="delete_admin")
    kb.button(text=s.get_admin_list, callback_data="get_admin_list")
    kb.button(text=s.update_admins, callback_data="update_admins")
    kb.button(text=s.back, callback_data="cancel")
    kb.button(text=s.to_home, callback_data="home")
    kb.adjust(2,2,2)
    return kb.as_markup()

def admin_kb_back() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=s.admin_panel, callback_data="admin_panel")
    kb.button(text=s.to_home, callback_data="home")
    kb.adjust(1)
    return kb.as_markup()


def dell_product_kb(product_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=s.delete, callback_data=f"dellproduct_{product_id}")
    kb.button(text=s.to_home, callback_data="home")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def dell_category_kb(category_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=s.delete, callback_data=f"dellcategory_{category_id}")
    kb.button(text=s.admin_panel, callback_data="admin_panel")
    kb.button(text=s.to_home, callback_data="home")
    kb.adjust(2, 2, 1)
    return kb.as_markup()

def dell_subcategory_kb(subcategory_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=s.delete, callback_data=f"dellsubcategory_{subcategory_id}")
    kb.button(text=s.admin_panel, callback_data="admin_panel")
    kb.button(text=s.to_home, callback_data="home")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def product_management_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=s.add_product, callback_data="add_product")
    kb.button(text=s.del_product, callback_data="delete_product")
    kb.button(text=s.add_category, callback_data="add_category")
    kb.button(text=s.del_category, callback_data="delete_category")
    kb.button(text=s.add_subcategory, callback_data="add_subcategory")
    kb.button(text=s.del_subcategory, callback_data="delete_subcategory")
    kb.button(text=s.admin_panel, callback_data="admin_panel")
    kb.button(text=s.to_home, callback_data="home")
    kb.adjust(2, 2, 2, 2)
    return kb.as_markup()


def cancel_kb_inline(cancel_callback_data: Optional[Union[str, CallbackData]] = "cancel") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=s.cancel, callback_data=cancel_callback_data)
    return kb.as_markup()


def admin_confirm_product_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=s.confirm, callback_data="confirm_add")
    kb.button(text=s.cancel, callback_data="admin_panel")
    kb.adjust(1)
    return kb.as_markup()


def admin_confirm_category_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=s.confirm, callback_data="confirm_category_add")
    kb.button(text=s.cancel, callback_data="admin_panel")
    kb.adjust(1)
    return kb.as_markup()


def admin_confirm_subctegory_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=s.confirm, callback_data="confirm_subcategory_add")
    kb.button(text=s.cancel, callback_data="admin_panel")
    kb.adjust(1)
    return kb.as_markup()

def orders_management_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=s.check_orders, callback_data="process_status")
    kb.button(text=s.get_excel, callback_data="get_orders_excel")
    kb.button(text=s.back, callback_data="admin_panel")
    kb.adjust(1)
    return kb.as_markup()

def order_management_kb(order_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=s.confirm_order, callback_data=f"confirm_order_{order_id}")
    kb.button(text=s.order_delivered, callback_data=f"order_delete_{order_id}")
    kb.button(text=s.cancel, callback_data="admin_panel")
    kb.adjust(1)
    return kb.as_markup()

def order_confirmed_management_kb(order_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=s.order_delivered, callback_data=f"order_delete_{order_id}")
    kb.button(text=s.cancel, callback_data="admin_panel")
    kb.adjust(1)
    return kb.as_markup()
