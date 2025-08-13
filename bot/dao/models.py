from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Text, ForeignKey
from bot.dao.database import Base


class Subcategory(Base):
    __tablename__ = 'subcategories'

    subcategory_name: Mapped[str] = mapped_column(Text, nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'))
    category: Mapped["Subcategory"] = relationship("Category", back_populates="subcategories")
    products: Mapped[List["Product"]] = relationship(
        "Product",
        back_populates="subcategory",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Subcategory(id={self.id}, name='{self.subcategory_name}')>"


class Category(Base):
    __tablename__ = 'categories'

    category_name: Mapped[str] = mapped_column(Text, nullable=False)
    subcategories: Mapped[List[Subcategory]] = relationship(
        "Subcategory",
        back_populates="category",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.category_name}')>"


class Product(Base):
    __tablename__ = 'products'
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    sizes: Mapped[str | None] = mapped_column(Text)
    # color: Mapped[List[str]| None] = mapped_column(Text)
    price: Mapped[int]
    photos: Mapped[str | None] = mapped_column(Text)
    subcategory_id: Mapped[int] = mapped_column(ForeignKey('subcategories.id'))
    subcategory: Mapped["Subcategory"] = relationship("Subcategory", back_populates="products")

    # purchases: Mapped[List['Purchase']] = relationship(
    #     "Purchase",
    #     back_populates="product",
    #     cascade="all, delete-orphan"
    # )

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price})>"


class Order(Base):
    __tablename__ = "orders"
    user_id: Mapped[int] = mapped_column(Text)
    user_name: Mapped[Optional[str]] = mapped_column(Text)
    fio: Mapped[str] = mapped_column(Text)
    product_id: Mapped[int] = mapped_column(Text)
    product_name: Mapped[str] = mapped_column(Text)
    product_size: Mapped[str | None] = mapped_column(Text)
    price: Mapped[int]
    photo_confirm: Mapped[str] = mapped_column(Text)
    phone_number: Mapped[str] = mapped_column(Text, default="None")
    delivery_methotd: Mapped[str] = mapped_column(Text, nullable=True)
    confirmed: Mapped[bool] = mapped_column(default=False)


class Admin(Base):
    __tablename__ = "admins"
    username: Mapped[str] = mapped_column(Text)


class User(Base):
    __tablename__ = "users"
    username: Mapped[str] = mapped_column(Text)

