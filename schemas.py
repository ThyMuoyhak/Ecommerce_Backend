from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

# ========== User Schemas ==========
class UserRoleEnum(str, Enum):
    USER = "user"
    ADMIN = "admin"

class UserBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    gender: str = Field(..., pattern="^(Male|Female|Other)$")
    phone_number: str = Field(..., pattern="^[0-9]{9,15}$")
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    full_name: str
    gender: str
    phone_number: str
    email: str
    role: UserRoleEnum
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# ========== Category Schemas ==========
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    product_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

# ========== Product Schemas ==========
class ProductSizeBase(BaseModel):
    size: str = Field(..., pattern="^(XS|S|M|L|XL|XXL|XXXL)$")
    stock: int = Field(..., ge=0)

class ProductColorBase(BaseModel):
    color: str = Field(..., min_length=2, max_length=30)
    color_code: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")

class ProductImageBase(BaseModel):
    image_url: str
    is_main: bool = False

class ProductBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    original_price: float = Field(..., gt=0)
    discount_price: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    category_id: int
    stock_quantity: int = Field(0, ge=0)

class ProductCreate(ProductBase):
    sizes: List[ProductSizeBase] = []
    colors: List[ProductColorBase] = []

class ProductUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    original_price: Optional[float] = Field(None, gt=0)
    discount_price: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    category_id: Optional[int] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    id: int
    main_image: str
    discount_percentage: Optional[float] = 0
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None  # Change this line - make it Optional
    category: CategoryResponse
    sizes: List[ProductSizeBase]
    colors: List[ProductColorBase]
    images: List[ProductImageBase]
    
    class Config:
        from_attributes = True
    
    @validator('discount_percentage', always=True)
    def calculate_discount(cls, v, values):
        if 'original_price' in values and 'discount_price' in values:
            if values.get('discount_price'):
                return round(((values['original_price'] - values['discount_price']) / values['original_price']) * 100, 2)
        return 0
    
# ========== Order Schemas ==========
class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)
    size: str
    color: str

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    shipping_address: str = Field(..., min_length=5)
    phone_number: str = Field(..., pattern="^[0-9]{9,15}$")
    notes: Optional[str] = None

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_size: str
    product_color: str
    quantity: int
    unit_price: float
    total_price: float
    
    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    order_number: str
    user_id: int
    total_amount: float
    discount_amount: float
    final_amount: float
    status: OrderStatusEnum
    payment_status: str
    shipping_address: str
    phone_number: str
    notes: Optional[str]
    created_at: datetime
    items: List[OrderItemResponse]
    
    class Config:
        from_attributes = True

# ========== Payment Schemas ==========
class PaymentRequest(BaseModel):
    order_id: int

class PaymentResponse(BaseModel):
    payment_url: str
    transaction_id: str
    amount: float

class PaymentVerification(BaseModel):
    transaction_id: str

class PaymentCallback(BaseModel):
    transaction_id: str
    status: str
    amount: float
    payment_date: Optional[str] = None