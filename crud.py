from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from models import User, Product, Category, Order, OrderItem, ProductSize, ProductColor, ProductImage
from schemas import UserCreate, ProductCreate, OrderCreate
from utils import get_password_hash, generate_order_number
from datetime import datetime
from typing import Optional, List

# ========== User CRUD ==========
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_phone(db: Session, phone: str):
    return db.query(User).filter(User.phone_number == phone).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        full_name=user.full_name,
        gender=user.gender,
        phone_number=user.phone_number,
        email=user.email,
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ========== Category CRUD ==========
def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Category).offset(skip).limit(limit).all()

def get_category_by_id(db: Session, category_id: int):
    return db.query(Category).filter(Category.id == category_id).first()

def get_category_by_name(db: Session, name: str):
    return db.query(Category).filter(Category.name == name).first()

def create_category(db: Session, name: str, description: str = None):
    db_category = Category(name=name, description=description)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def update_category(db: Session, category_id: int, name: str = None, description: str = None):
    category = get_category_by_id(db, category_id)
    if category:
        if name:
            category.name = name
        if description is not None:
            category.description = description
        db.commit()
        db.refresh(category)
    return category

def delete_category(db: Session, category_id: int):
    category = get_category_by_id(db, category_id)
    if category:
        db.delete(category)
        db.commit()
        return True
    return False

# ========== Product CRUD ==========
def get_products(db: Session, skip: int = 0, limit: int = 100, category_id: int = None, search: str = None):
    query = db.query(Product).filter(Product.is_active == True)
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    if search:
        query = query.filter(Product.title.contains(search))
    
    return query.offset(skip).limit(limit).all()

def get_all_products_admin(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Product).offset(skip).limit(limit).all()

def get_product_by_id(db: Session, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()

def create_product(db: Session, product: ProductCreate, main_image: str):
    # Create product
    db_product = Product(
        title=product.title,
        original_price=product.original_price,
        discount_price=product.discount_price,
        description=product.description,
        category_id=product.category_id,
        stock_quantity=product.stock_quantity,
        main_image=main_image
    )
    db.add(db_product)
    db.flush()
    
    # Add sizes
    for size_data in product.sizes:
        db_size = ProductSize(
            product_id=db_product.id,
            size=size_data.size,
            stock=size_data.stock
        )
        db.add(db_size)
    
    # Add colors
    for color_data in product.colors:
        db_color = ProductColor(
            product_id=db_product.id,
            color=color_data.color,
            color_code=color_data.color_code
        )
        db.add(db_color)
    
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, product_data: dict):
    product = get_product_by_id(db, product_id)
    if product:
        for key, value in product_data.items():
            if hasattr(product, key) and value is not None:
                setattr(product, key, value)
        db.commit()
        db.refresh(product)
    return product

def delete_product(db: Session, product_id: int):
    product = get_product_by_id(db, product_id)
    if product:
        db.delete(product)
        db.commit()
        return True
    return False

def add_product_image(db: Session, product_id: int, image_url: str, is_main: bool = False):
    db_image = ProductImage(
        product_id=product_id,
        image_url=image_url,
        is_main=is_main
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

# ========== Order CRUD ==========
def get_orders_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

def get_all_orders(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Order).order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

def get_order_by_id(db: Session, order_id: int):
    return db.query(Order).filter(Order.id == order_id).first()

def get_order_by_number(db: Session, order_number: str):
    return db.query(Order).filter(Order.order_number == order_number).first()

def create_order(db: Session, user_id: int, order_data: OrderCreate):
    # Calculate total amount
    total_amount = 0
    order_items_data = []
    
    for item in order_data.items:
        product = get_product_by_id(db, item.product_id)
        if not product:
            raise ValueError(f"Product {item.product_id} not found")
        
        unit_price = product.discount_price if product.discount_price else product.original_price
        total_price = unit_price * item.quantity
        total_amount += total_price
        
        order_items_data.append({
            "product_id": item.product_id,
            "product_name": product.title,
            "product_size": item.size,
            "product_color": item.color,
            "quantity": item.quantity,
            "unit_price": unit_price,
            "total_price": total_price
        })
    
    # Apply any discount (you can implement coupon logic here)
    discount_amount = 0
    final_amount = total_amount - discount_amount
    
    # Create order
    order_number = generate_order_number()
    db_order = Order(
        order_number=order_number,
        user_id=user_id,
        total_amount=total_amount,
        discount_amount=discount_amount,
        final_amount=final_amount,
        shipping_address=order_data.shipping_address,
        phone_number=order_data.phone_number,
        notes=order_data.notes
    )
    db.add(db_order)
    db.flush()
    
    # Create order items
    for item_data in order_items_data:
        db_item = OrderItem(
            order_id=db_order.id,
            **item_data
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_order)
    return db_order

def update_order_status(db: Session, order_id: int, status: str):
    order = get_order_by_id(db, order_id)
    if order:
        order.status = status
        db.commit()
        db.refresh(order)
    return order

def update_payment_status(db: Session, order_id: int, payment_status: str, transaction_id: str = None):
    order = get_order_by_id(db, order_id)
    if order:
        order.payment_status = payment_status
        if transaction_id:
            order.payment_transaction_id = transaction_id
        if payment_status == "success":
            order.status = "paid"
        db.commit()
        db.refresh(order)
    return order