from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Order, OrderStatus, PaymentStatus
from schemas import OrderResponse, OrderCreate
from crud import create_order, get_orders_by_user, get_order_by_id, update_order_status
from routes.auth import get_current_user, get_current_admin
from utils import notify_new_order

router = APIRouter(prefix="/api/orders", tags=["Orders"])

# User endpoints
@router.post("/", response_model=OrderResponse)
async def create_new_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create new order"""
    try:
        order = create_order(db, current_user.id, order_data)
        
        # Send notification
        order_dict = {
            "order_number": order.order_number,
            "customer_name": current_user.full_name,
            "final_amount": order.final_amount
        }
        await notify_new_order(order_dict)
        
        return OrderResponse.model_validate(order)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[OrderResponse])
async def list_my_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get current user's orders"""
    orders = get_orders_by_user(db, current_user.id, skip, limit)
    return [OrderResponse.model_validate(order) for order in orders]

@router.get("/{order_id}")
async def get_order_details(
    order_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get order details with product images"""
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if order belongs to user or user is admin
    if order.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Manual serialization to include product images
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
            "email": order.user.email,
            "phone_number": order.user.phone_number
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
    
    return order_dict

@router.put("/{order_id}/cancel")
async def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Cancel order (only if pending)"""
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if order.status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Cannot cancel order that is already processed")
    
    # Restore stock if needed
    if order.payment_status == PaymentStatus.SUCCESS:
        for item in order.items:
            if item.product:
                item.product.stock_quantity += item.quantity
                # Also restore size stock if applicable
                for size in item.product.sizes:
                    if size.size == item.product_size:
                        size.stock += item.quantity
                        break
    
    updated_order = update_order_status(db, order_id, OrderStatus.CANCELLED)
    return {"message": "Order cancelled successfully"}

# Admin endpoints
@router.get("/admin/orders")
async def admin_get_all_orders(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get all orders (Admin only)"""
    query = db.query(Order)
    
    if status:
        query = query.filter(Order.status == status)
    
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    
    # Manual serialization to include product images
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

@router.put("/admin/orders/{order_id}/status")
async def admin_update_order_status(
    order_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Update order status (Admin only)"""
    if status not in [s.value for s in OrderStatus]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # If status is being changed to PAID, decrease stock
    if status == OrderStatus.PAID.value and order.payment_status != PaymentStatus.SUCCESS:
        order.payment_status = PaymentStatus.SUCCESS
        for item in order.items:
            if item.product:
                item.product.stock_quantity -= item.quantity
                # Decrease size stock
                for size in item.product.sizes:
                    if size.size == item.product_size:
                        size.stock -= item.quantity
                        break
    
    # If status is being changed to CANCELLED, restore stock
    if status == OrderStatus.CANCELLED.value and order.payment_status == PaymentStatus.SUCCESS:
        for item in order.items:
            if item.product:
                item.product.stock_quantity += item.quantity
                for size in item.product.sizes:
                    if size.size == item.product_size:
                        size.stock += item.quantity
                        break
    
    order.status = OrderStatus(status)
    db.commit()
    db.refresh(order)
    
    return {"message": f"Order status updated to {status}"}