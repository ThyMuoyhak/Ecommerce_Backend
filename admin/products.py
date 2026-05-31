from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from jose import jwt

from database import get_db
from models import Product, User
from config import settings

router = APIRouter(prefix="/api/admin/products", tags=["Admin Products"])

def verify_admin_token(authorization: str = Header(None), db: Session = Depends(get_db)):
    """Verify admin token and return user"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        user_role = payload.get("role")
        
        if not user_id or user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/all")
async def admin_get_all_products(
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_admin: User = Depends(verify_admin_token)
):
    """Get all products including inactive (Admin only)"""
    
    query = db.query(Product)
    if not include_inactive:
        query = query.filter(Product.is_active == True)
    
    products = query.offset(skip).limit(limit).all()
    
    # Manual serialization
    result = []
    for product in products:
        result.append({
            "id": product.id,
            "title": product.title,
            "original_price": product.original_price,
            "discount_price": product.discount_price,
            "description": product.description,
            "main_image": product.main_image,
            "category_id": product.category_id,
            "stock_quantity": product.stock_quantity,
            "is_active": product.is_active,
            "created_at": product.created_at.isoformat() if product.created_at else None,
            "updated_at": product.updated_at.isoformat() if product.updated_at else None,
            "discount_percentage": round(((product.original_price - product.discount_price) / product.original_price) * 100, 2) if product.discount_price else 0,
            "category": {
                "id": product.category.id,
                "name": product.category.name,
            } if product.category else None,
            "sizes": [{"size": s.size, "stock": s.stock} for s in product.sizes] if product.sizes else [],
            "colors": [{"color": c.color, "color_code": c.color_code} for c in product.colors] if product.colors else [],
            "images": [{"image_url": i.image_url, "is_main": i.is_main} for i in product.images] if product.images else []
        })
    
    return result

@router.get("/stats")
async def get_product_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(verify_admin_token)
):
    """Get product statistics (Admin only)"""
    
    total_products = db.query(Product).count()
    active_products = db.query(Product).filter(Product.is_active == True).count()
    inactive_products = db.query(Product).filter(Product.is_active == False).count()
    out_of_stock = db.query(Product).filter(Product.stock_quantity == 0).count()
    
    return {
        "total_products": total_products,
        "active_products": active_products,
        "inactive_products": inactive_products,
        "out_of_stock": out_of_stock
    }

@router.put("/{product_id}/toggle-status")
async def toggle_product_status(
    product_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(verify_admin_token)
):
    """Activate/Deactivate product (Admin only)"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.is_active = not product.is_active
    db.commit()
    
    return {
        "message": f"Product {'activated' if product.is_active else 'deactivated'} successfully",
        "is_active": product.is_active
    }

@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(verify_admin_token)
):
    """Delete product (Admin only)"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Delete image files
    if product.main_image:
        import os
        old_path = product.main_image.replace('/static/', 'static/')
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception:
                pass
    
    db.delete(product)
    db.commit()
    
    return {"message": "Product deleted successfully"}