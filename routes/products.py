from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import os

from database import get_db
from models import Product, ProductImage, ProductSize, ProductColor
from schemas import ProductCreate
from crud import get_product_by_id, delete_product
from routes.auth import get_current_user
from image_utils import save_product_image

router = APIRouter(prefix="/api/products", tags=["Products"])

# ==================== PUBLIC ENDPOINTS ====================

@router.get("/")
@router.get("")
async def list_products(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Product).filter(Product.is_active == True)
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    if search:
        query = query.filter(Product.title.contains(search))
    
    products = query.offset(skip).limit(limit).all()
    
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
            "category": {
                "id": product.category.id,
                "name": product.category.name,
            } if product.category else None,
            "sizes": [{"size": s.size, "stock": s.stock} for s in product.sizes] if product.sizes else [],
            "colors": [{"color": c.color, "color_code": c.color_code} for c in product.colors] if product.colors else [],
            "images": [{"image_url": i.image_url, "is_main": i.is_main} for i in product.images] if product.images else []
        })
    
    return result


@router.get("/{product_id}")
async def get_product(product_id: int, db: Session = Depends(get_db)):
    product = get_product_by_id(db, product_id)
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
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
        "category": {
            "id": product.category.id,
            "name": product.category.name,
        } if product.category else None,
        "sizes": [{"size": s.size, "stock": s.stock} for s in product.sizes] if product.sizes else [],
        "colors": [{"color": c.color, "color_code": c.color_code} for c in product.colors] if product.colors else [],
        "images": [{"image_url": i.image_url, "is_main": i.is_main} for i in product.images] if product.images else []
    }


# ==================== ADMIN ENDPOINTS ====================

@router.post("/")
@router.post("")
async def create_new_product(
    title: str = Form(...),
    original_price: float = Form(...),
    discount_price: Optional[float] = Form(None),
    description: Optional[str] = Form(None),
    category_id: int = Form(...),
    stock_quantity: int = Form(0),
    main_image: UploadFile = File(...),
    sub_images: List[UploadFile] = File([]),
    sizes: str = Form("[]"),
    colors: str = Form("[]"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        print(f"=== CREATING PRODUCT ===")
        print(f"Title: {title}")
        
        main_image_path = await save_product_image(main_image)
        print(f"Main image saved: {main_image_path}")
        
        sizes_data = json.loads(sizes) if sizes else []
        colors_data = json.loads(colors) if colors else []
        
        new_product = Product(
            title=title,
            original_price=original_price,
            discount_price=discount_price,
            description=description,
            category_id=category_id,
            stock_quantity=stock_quantity,
            main_image=main_image_path,
            is_active=True
        )
        db.add(new_product)
        db.flush()
        
        for size_data in sizes_data:
            db.add(ProductSize(
                product_id=new_product.id,
                size=size_data['size'],
                stock=size_data['stock']
            ))
        
        for color_data in colors_data:
            db.add(ProductColor(
                product_id=new_product.id,
                color=color_data['color'],
                color_code=color_data.get('color_code')
            ))
        
        for idx, sub_image in enumerate(sub_images):
            if sub_image and sub_image.filename:
                sub_image_path = await save_product_image(sub_image)
                print(f"Sub image {idx + 1} saved: {sub_image_path}")
                db.add(ProductImage(
                    product_id=new_product.id,
                    image_url=sub_image_path,
                    is_main=False
                ))
        
        db.commit()
        db.refresh(new_product)
        print(f"Product {new_product.id} created successfully!")
        
        return {
            "id": new_product.id,
            "title": new_product.title,
            "original_price": new_product.original_price,
            "discount_price": new_product.discount_price,
            "description": new_product.description,
            "main_image": new_product.main_image,
            "category_id": new_product.category_id,
            "stock_quantity": new_product.stock_quantity,
            "is_active": new_product.is_active,
            "created_at": new_product.created_at.isoformat() if new_product.created_at else None,
            "updated_at": new_product.updated_at.isoformat() if new_product.updated_at else None,
            "category": {
                "id": new_product.category.id,
                "name": new_product.category.name,
            } if new_product.category else None,
            "sizes": [{"size": s.size, "stock": s.stock} for s in new_product.sizes] if new_product.sizes else [],
            "colors": [{"color": c.color, "color_code": c.color_code} for c in new_product.colors] if new_product.colors else [],
            "images": [{"image_url": i.image_url, "is_main": i.is_main} for i in new_product.images] if new_product.images else []
        }
        
    except Exception as e:
        db.rollback()
        print(f"Error creating product: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")


@router.put("/{product_id}")
async def update_existing_product(
    product_id: int,
    title: Optional[str] = Form(None),
    original_price: Optional[float] = Form(None),
    discount_price: Optional[float] = Form(None),
    description: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    stock_quantity: Optional[int] = Form(None),
    is_active: Optional[bool] = Form(None),
    sizes: Optional[str] = Form(None),
    colors: Optional[str] = Form(None),
    existing_main_image: Optional[str] = Form(None),
    existing_sub_images: Optional[str] = Form(None),
    main_image: Optional[UploadFile] = File(None),
    sub_images: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    try:
        print(f"=== UPDATING PRODUCT {product_id} ===")
        
        # Update basic fields
        if title is not None:
            product.title = title
        if original_price is not None:
            product.original_price = original_price
        if discount_price is not None:
            product.discount_price = discount_price
        if description is not None:
            product.description = description
        if category_id is not None:
            product.category_id = category_id
        if stock_quantity is not None:
            product.stock_quantity = stock_quantity
        if is_active is not None:
            product.is_active = is_active
        
        # Update main image if new one uploaded
        if main_image and main_image.filename:
            print(f"Updating main image: {main_image.filename}")
            
            # Delete old main image file
            if product.main_image:
                old_path = product.main_image.lstrip('/')  # /static/... → static/...
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                        print(f"Deleted old main image: {old_path}")
                    except Exception as e:
                        print(f"Error deleting old image: {e}")
            
            product.main_image = await save_product_image(main_image)
            print(f"New main image saved: {product.main_image}")
        
        # Update sizes
        if sizes is not None:
            sizes_data = json.loads(sizes)
            product.sizes.clear()
            for size_data in sizes_data:
                product.sizes.append(ProductSize(
                    size=size_data['size'],
                    stock=size_data['stock']
                ))
            print(f"Updated sizes: {len(sizes_data)} items")
        
        # Update colors
        if colors is not None:
            colors_data = json.loads(colors)
            product.colors.clear()
            for color_data in colors_data:
                product.colors.append(ProductColor(
                    color=color_data['color'],
                    color_code=color_data.get('color_code')
                ))
            print(f"Updated colors: {len(colors_data)} items")
        
        # Handle sub images
        keep_sub_images = []
        if existing_sub_images:
            keep_sub_images = json.loads(existing_sub_images)
            print(f"Keeping {len(keep_sub_images)} existing sub images")
        
        # Delete sub images not in keep list
        deleted_count = 0
        for img in product.images[:]:
            if img.image_url not in keep_sub_images:
                old_path = img.image_url.lstrip('/')  # ← FIXED (was .replace)
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                        print(f"Deleted sub image: {old_path}")
                    except Exception as e:
                        print(f"Error deleting sub image: {e}")
                db.delete(img)
                deleted_count += 1
        print(f"Deleted {deleted_count} sub images")
        
        # Add new sub images
        for idx, sub_image in enumerate(sub_images):
            if sub_image and sub_image.filename:
                sub_image_path = await save_product_image(sub_image)
                print(f"New sub image {idx + 1} saved: {sub_image_path}")
                db.add(ProductImage(
                    product_id=product.id,
                    image_url=sub_image_path,
                    is_main=False
                ))
        
        db.commit()
        db.refresh(product)
        print(f"Product {product_id} updated successfully!")
        
        return {
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
            "category": {
                "id": product.category.id,
                "name": product.category.name,
            } if product.category else None,
            "sizes": [{"size": s.size, "stock": s.stock} for s in product.sizes] if product.sizes else [],
            "colors": [{"color": c.color, "color_code": c.color_code} for c in product.colors] if product.colors else [],
            "images": [{"image_url": i.image_url, "is_main": i.is_main} for i in product.images] if product.images else []
        }
        
    except Exception as e:
        db.rollback()
        print(f"Error updating product: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to update product: {str(e)}")


@router.delete("/{product_id}")
async def delete_existing_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    print(f"=== DELETING PRODUCT {product_id} ===")
    
    # Delete main image file
    if product.main_image:
        main_image_path = product.main_image.lstrip('/')  # ← FIXED
        if os.path.exists(main_image_path):
            try:
                os.remove(main_image_path)
                print(f"Deleted main image: {main_image_path}")
            except Exception as e:
                print(f"Error deleting main image: {e}")
    
    # Delete sub image files
    for img in product.images:
        img_path = img.image_url.lstrip('/')  # ← FIXED
        if os.path.exists(img_path):
            try:
                os.remove(img_path)
                print(f"Deleted sub image: {img_path}")
            except Exception as e:
                print(f"Error deleting sub image: {e}")
    
    success = delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    
    print(f"Product {product_id} deleted successfully!")
    return {"message": "Product deleted successfully"}