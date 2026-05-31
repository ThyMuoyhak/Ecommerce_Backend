from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional
import httpx
import hashlib
import uuid
import time

from database import get_db
from models import Order, PaymentStatus, OrderStatus, Product, ProductSize
from schemas import PaymentRequest, PaymentResponse, PaymentVerification
from crud import get_order_by_id
from routes.auth import get_current_user
from config import settings
from utils import notify_payment_success

router = APIRouter(prefix="/api/payment", tags=["Payment"])

def decrease_product_stock(db: Session, order: Order):
    """Decrease stock for all items in the order"""
    for item in order.items:
        # Decrease main product stock
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.stock_quantity -= item.quantity
            print(f"Decreased stock for product {product.id}: new stock = {product.stock_quantity}")
        
        # Decrease specific size stock
        size_stock = db.query(ProductSize).filter(
            ProductSize.product_id == item.product_id,
            ProductSize.size == item.product_size
        ).first()
        if size_stock:
            size_stock.stock -= item.quantity
            print(f"Decreased size stock for {item.product_size}: new stock = {size_stock.stock}")

def generate_khqr_hash(transaction_id: str, amount: float, success_url: str, remark: str = "") -> str:
    """Generate SHA1 hash for KHQR payment"""
    amount_str = f"{amount:.2f}"
    raw_string = f"{settings.KHQR_SECRET_KEY}{transaction_id}{amount_str}{success_url}{remark}"
    hash_value = hashlib.sha1(raw_string.encode()).hexdigest()
    return hash_value

def generate_verification_hash(transaction_id: str) -> str:
    """Generate SHA1 hash for verification"""
    raw_string = f"{settings.KHQR_PROFILE_KEY}{transaction_id}"
    hash_value = hashlib.sha1(raw_string.encode()).hexdigest()
    return hash_value

@router.post("/initiate", response_model=PaymentResponse)
async def initiate_payment(
    payment_request: PaymentRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Initiate KHQR payment for an order"""
    
    # Get order
    order = get_order_by_id(db, payment_request.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Verify order belongs to user
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if already paid
    if order.payment_status == PaymentStatus.SUCCESS:
        raise HTTPException(status_code=400, detail="Order already paid")
    
    # Generate a unique transaction ID for this payment attempt
    transaction_id = f"{order.id}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    
    # Success URL
    success_url = f"http://localhost:3000/payment/success?order_id={order.id}&transaction_id={transaction_id}"
    
    # Remark
    remark = f"Order {order.order_number}"
    
    # Generate hash
    hash_value = generate_khqr_hash(
        transaction_id=transaction_id,
        amount=order.final_amount,
        success_url=success_url,
        remark=remark
    )
    
    # Build payment URL
    from urllib.parse import urlencode
    payment_params = {
        "transaction_id": transaction_id,
        "amount": f"{order.final_amount:.2f}",
        "success_url": success_url,
        "remark": remark,
        "hash": hash_value
    }
    
    query_string = urlencode(payment_params)
    payment_url = f"{settings.KHQR_GATEWAY_URL}/{settings.KHQR_PROFILE_ID}?{query_string}"
    
    return PaymentResponse(
        payment_url=payment_url,
        transaction_id=transaction_id,
        amount=order.final_amount
    )

@router.post("/verify")
async def verify_payment(
    verification: PaymentVerification,
    db: Session = Depends(get_db)
):
    """Verify payment status with KHQR gateway and update stock"""
    
    print(f"=== PAYMENT VERIFICATION ===")
    print(f"Transaction ID: {verification.transaction_id}")
    
    # Generate verification hash
    hash_value = generate_verification_hash(verification.transaction_id)
    
    # Prepare POST data
    post_data = {
        "transaction_id": verification.transaction_id,
        "hash": hash_value
    }
    
    # Send verification request
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                settings.KHQR_VERIFY_URL,
                data=post_data,
                timeout=30.0
            )
            result = response.json()
            print(f"Verification response: {result}")
            
            # Check if payment is successful
            is_paid = (
                result.get('responseCode') == 0 and
                result.get('data', {}).get('status', '').lower() == 'success'
            )
            
            if is_paid:
                # Extract the original order ID from transaction_id
                order_id = int(verification.transaction_id.split('_')[0])
                order = get_order_by_id(db, order_id)
                
                if order and order.payment_status != PaymentStatus.SUCCESS:
                    print(f"Updating order {order_id} to PAID")
                    
                    # Update payment status
                    order.payment_status = PaymentStatus.SUCCESS
                    order.payment_transaction_id = verification.transaction_id
                    
                    # Update order status to PAID
                    order.status = OrderStatus.PAID
                    
                    # Decrease stock
                    decrease_product_stock(db, order)
                    
                    db.commit()
                    db.refresh(order)
                    
                    # Send notification
                    order_dict = {
                        "order_number": order.order_number,
                        "final_amount": order.final_amount,
                        "transaction_id": verification.transaction_id
                    }
                    await notify_payment_success(order_dict)
                    
                    return {
                        "verified": True,
                        "message": "Payment verified successfully, stock decreased",
                        "order_status": order.status.value,
                        "payment_status": order.payment_status.value
                    }
            
            return {
                "verified": False,
                "message": "Payment not verified",
                "response": result
            }
            
        except httpx.RequestError as e:
            print(f"Verification error: {e}")
            raise HTTPException(status_code=500, detail=f"Payment verification failed: {str(e)}")

@router.post("/test-verify")
async def test_verify_payment(
    verification: PaymentVerification,
    db: Session = Depends(get_db)
):
    """Test endpoint to verify payment - SKIPS KHQR verification"""
    
    print(f"=== TEST PAYMENT VERIFICATION (BYPASS) ===")
    print(f"Transaction ID: {verification.transaction_id}")
    
    try:
        # Extract order ID from transaction_id
        order_id = int(verification.transaction_id.split('_')[0])
        order = get_order_by_id(db, order_id)
        
        if order and order.payment_status != PaymentStatus.SUCCESS:
            print(f"Updating order {order_id} to PAID (TEST MODE)")
            
            # Update payment status
            order.payment_status = PaymentStatus.SUCCESS
            order.payment_transaction_id = verification.transaction_id
            
            # Update order status to PAID
            order.status = OrderStatus.PAID
            
            # Decrease stock
            decrease_product_stock(db, order)
            
            db.commit()
            db.refresh(order)
            
            print(f"Order {order_id} updated: status={order.status.value}")
            
            # Send notification
            order_dict = {
                "order_number": order.order_number,
                "final_amount": order.final_amount,
                "transaction_id": verification.transaction_id
            }
            await notify_payment_success(order_dict)
            
            return {
                "verified": True,
                "message": "Payment verified successfully (TEST MODE), stock decreased",
                "order_status": order.status.value,
                "payment_status": order.payment_status.value
            }
        else:
            return {"verified": False, "message": "Order already paid or not found"}
            
    except Exception as e:
        print(f"Test verification error: {e}")
        return {"verified": False, "message": str(e)}

@router.post("/webhook")
async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle payment webhook from KHQR"""
    
    try:
        data = await request.json()
        print(f"Webhook received: {data}")
        
        transaction_id = data.get('transaction_id')
        status = data.get('status', '').lower()
        
        if status == 'success' and transaction_id:
            order_id = int(transaction_id.split('_')[0])
            order = get_order_by_id(db, order_id)
            
            if order and order.payment_status != PaymentStatus.SUCCESS:
                print(f"Webhook: Updating order {order_id}")
                
                order.payment_status = PaymentStatus.SUCCESS
                order.payment_transaction_id = transaction_id
                order.status = OrderStatus.PAID
                
                # Decrease stock
                decrease_product_stock(db, order)
                
                db.commit()
                db.refresh(order)
                
                # Send notification
                order_dict = {
                    "order_number": order.order_number,
                    "final_amount": order.final_amount,
                    "transaction_id": transaction_id
                }
                await notify_payment_success(order_dict)
                
                return {"status": "ok", "message": "Order updated and stock decreased"}
        
        return {"status": "ok", "message": "No action taken"}
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}