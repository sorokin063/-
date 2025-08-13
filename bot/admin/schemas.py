from pydantic import BaseModel, ConfigDict, Field


class ProductIDModel(BaseModel):
    id: int


class CategoryIDModel(BaseModel):
    id: int


class SubcategoryIDModel(BaseModel):
    id: int


class SubcategoryCategoryIDModel(BaseModel):
    category_id: int


class CategoryModel(BaseModel):
    category_name: str = Field(..., min_length=3)


class SubcategoryModel(BaseModel):
    subcategory_name: str = Field(..., min_length=3)
    category_id: int = Field(..., gt=0)


class ProductModel(BaseModel):
    name: str = Field(..., min_length=5)
    description: str = Field(..., min_length=5)
    price: int = Field(..., gt=0)
    subcategory_id: int = Field(..., gt=0)
    photos: str | None = None
    sizes: str | None = None


class OrderIdModel(BaseModel):
    id: int


class OrderData(BaseModel):
    user_id: int
    user_name: str
    fio: str
    product_id: int
    product_name: str
    product_size: str
    price: int
    phone_number: str
    delivery_methotd: str
    confirmed: bool = False


class OrderUsernameModel(BaseModel):
    user_name: str


class OrderUserIdModel(BaseModel):
    user_id: int

class AdminIdModel(BaseModel):
    id: int


class AdminUsernameModel(BaseModel):
    username: str


class AdminModel(BaseModel):
    id: int
    username: str
