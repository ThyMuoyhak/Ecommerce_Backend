from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List
from jose import jwt

from database import get_db
from models import User, UserRole
from schemas import UserResponse
from routes.auth import get_current_admin
from crud import get_user_by_id
from config import settings

router = APIRouter(prefix="/api/admin/auth", tags=["Admin Auth"])

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

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get all users (Admin only)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return [UserResponse.model_validate(user) for user in users]

@router.get("/verify")
async def verify_admin(current_admin = Depends(get_current_admin)):
    """Verify admin access"""
    return {
        "authenticated": True,
        "user_id": current_admin.id,
        "user_email": current_admin.email,
        "user_role": current_admin.role.value
    }

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Update user role (Admin only)"""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if role not in [UserRole.USER.value, UserRole.ADMIN.value]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    user.role = UserRole(role)
    db.commit()
    
    return {"message": f"User role updated to {role}"}

@router.put("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Activate/Deactivate user (Admin only)"""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = not user.is_active
    db.commit()
    
    status_text = "activated" if user.is_active else "deactivated"
    return {"message": f"User {status_text} successfully"}

@router.get("/test")
async def test_endpoint():
    """Test endpoint to check if admin routes are working"""
    return {"message": "Admin routes are working", "status": "ok"}