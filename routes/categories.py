from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Category
from schemas import CategoryResponse, CategoryCreate
from crud import get_categories, get_category_by_id, get_category_by_name, create_category, update_category, delete_category
from routes.auth import get_current_user

router = APIRouter(prefix="/api/categories", tags=["Categories"])

@router.get("/", response_model=List[CategoryResponse])
async def list_categories(db: Session = Depends(get_db)):
    """Get all categories (public)"""
    categories = get_categories(db)
    
    # Manual serialization to avoid Pydantic issues
    result = []
    for cat in categories:
        result.append({
            "id": cat.id,
            "name": cat.name,
            "description": cat.description,
            "created_at": cat.created_at.isoformat() if cat.created_at else None,
            "product_count": len(cat.products) if cat.products else 0
        })
    
    return result

@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, db: Session = Depends(get_db)):
    """Get single category (public)"""
    category = get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return {
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "created_at": category.created_at.isoformat() if category.created_at else None,
        "product_count": len(category.products) if category.products else 0
    }

@router.post("/", response_model=CategoryResponse)
async def create_new_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create new category (Admin only)"""
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if category exists
    existing = get_category_by_name(db, category.name)
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    new_category = create_category(db, category.name, category.description)
    
    return {
        "id": new_category.id,
        "name": new_category.name,
        "description": new_category.description,
        "created_at": new_category.created_at.isoformat() if new_category.created_at else None,
        "product_count": 0
    }

@router.put("/{category_id}", response_model=CategoryResponse)
async def update_existing_category(
    category_id: int,
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update category (Admin only)"""
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    updated = update_category(db, category_id, category.name, category.description)
    if not updated:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return {
        "id": updated.id,
        "name": updated.name,
        "description": updated.description,
        "created_at": updated.created_at.isoformat() if updated.created_at else None,
        "product_count": len(updated.products) if updated.products else 0
    }

@router.delete("/{category_id}")
async def delete_existing_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete category (Admin only)"""
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    success = delete_category(db, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return {"message": "Category deleted successfully"}