from datetime import datetime, UTC, timedelta
from typing import Optional, List, Dict

from loguru import logger
from sqlalchemy import select, func, case
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.dao.baseDao import BaseDAO
from bot.dao.models import Category, Product, Subcategory, Order, User, Admin


class CategoryDao(BaseDAO[Category]):
    model = Category


class SubcategoryDao(BaseDAO[Subcategory]):
    model = Subcategory


class ProductDao(BaseDAO[Product]):
    model = Product


class OrderDao(BaseDAO[Order]):
    model = Order


class AdminDao(BaseDAO[Admin]):
    model = Admin


class UserDao(BaseDAO[User]):
    model = User
