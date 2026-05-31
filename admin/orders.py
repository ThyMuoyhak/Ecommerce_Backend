from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
import jwt

from database import get_db
from models import Order, OrderStatus, Product, User
from schemas import OrderResponse
from config import settings

router = APIRouter(prefix="/api/admin/orders", tags=["Admin Orders"])

def get_current_admin_from_token(authorization: str = Header(None), db: Session = Depends(get_db)):
    """Extract and verify admin token from Authorization header"""
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
        
        token = parts[1]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        user_id = payload.get("sub")
        user_role = payload.get("role")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        if user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/", response_model=List[OrderResponse])
async def admin_get_all_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_from_token)
):
    """Get all orders (Admin only)"""
    query = db.query(Order)
    
    if status:
        query = query.filter(Order.status == status)
    
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return [OrderResponse.model_validate(order) for order in orders]

@router.put("/{order_id}/status")
async def admin_update_order_status(
    order_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_from_token)
):
    """Update order status (Admin only)"""
    if status not in [s.value for s in OrderStatus]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = status
    db.commit()
    db.refresh(order)
    
    return {"message": f"Order status updated to {status}"}

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_from_token)
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