from pydantic import BaseModel, ConfigDict, Field


class TelegramIDModel(BaseModel):
    telegram_id: int

    model_config = ConfigDict(from_attributes=True)


class UserModel(TelegramIDModel):
    username: str | None
    first_name: str | None
    last_name: str | None


class ProductIDModel(BaseModel):
    id: int


class ProductCategoryIDModel(BaseModel):
    subcategory_id: int

class SubcategoryIDModel(BaseModel):
    category_id: int

class PaymentData(BaseModel):
    user_id: int = Field(..., description="ID пользователя Telegram")
    payment_id: str = Field(..., max_length=255, description="Уникальный ID платежа")
    price: int = Field(..., description="Сумма платежа в рублях")
    product_id: int = Field(..., description="ID товара")

class OrderData(BaseModel):
    user_id: int 
    user_name: str
    fio: str
    product_id: int
    product_name: str
    product_size: str
    photo_confirm: str
    price: int
    phone_number: str
    delivery_methotd: str
    # confirmed: bool = False

class OrderUserIdModel(BaseModel):
    user_id: int

class UserIdModel(BaseModel):
    id: int

class UserModel(BaseModel):
    id: int
    username: str