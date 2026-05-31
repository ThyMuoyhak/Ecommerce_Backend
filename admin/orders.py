# admin/orders.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta

from database import get_db
from models import Order, OrderStatus, Product, User
from schemas import OrderResponse
from routes.auth import get_current_admin

router = APIRouter(prefix="/api/admin/orders", tags=["Admin Orders"])

@router.get("/", response_model=List[OrderResponse])
async def admin_get_all_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get all orders (Admin only)"""
    query = db.query(Order)
    
    if status:
        query = query.filter(Order.status == status)
    
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    
    # Manual serialization
    result = []
    for order in orders:
        order_dict = {
            "id": order.id,
            "order_number": order.order_number,
            "user_id": order.user_id,
            "total_amount": order.total_amount,
            "discount_amount": order.discount_amount,
            "final_amount": order.final_amount,
            "status": order.status.value,
            "payment_status": order.payment_status.value,
            "shipping_address": order.shipping_address,
            "phone_number": order.phone_number,
            "notes": order.notes,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "user": {
                "id": order.user.id,
                "full_name": order.user.full_name,
                "email": order.user.email
            } if order.user else None,
            "items": []
        }
        
        for item in order.items:
            order_dict["items"].append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "product_size": item.product_size,
                "product_color": item.product_color,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "product_image": item.product.main_image if item.product else None
            })
        
        result.append(order_dict)
    
    return result

@router.put("/{order_id}/status")
async def admin_update_order_status(
    order_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Update order status (Admin only)"""
    if status not in [s.value for s in OrderStatus]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = OrderStatus(status)
    db.commit()
    db.refresh(order)
    
    return {"message": f"Order status updated to {status}"}

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get dashboard statistics (Admin only)"""
    
    # Total orders
    total_orders = db.query(Order).count()
    
    # Total revenue from paid orders
    total_revenue_result = db.query(func.sum(Order.final_amount)).filter(Order.payment_status == "success").scalar()
    total_revenue = float(total_revenue_result) if total_revenue_result else 0.0
    
    # Orders by status
    pending_orders = db.query(Order).filter(Order.status == OrderStatus.PENDING).count()
    processing_orders = db.query(Order).filter(Order.status == OrderStatus.PROCESSING).count()
    completed_orders = db.query(Order).filter(Order.status == OrderStatus.DELIVERED).count()
    
    # Recent orders (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_orders = db.query(Order).filter(Order.created_at >= week_ago).count()
    
    # Total products
    total_products = db.query(Product).count()
    
    # Total users
    total_users = db.query(User).count()
    
    return {
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "pending_orders": pending_orders,
        "processing_orders": processing_orders,
        "completed_orders": completed_orders,
        "recent_orders": recent_orders,
        "total_products": total_products,
        "total_users": total_users
    }