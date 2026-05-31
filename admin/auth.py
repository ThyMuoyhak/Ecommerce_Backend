from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List
import jwt

from database import get_db
from models import User, UserRole
from schemas import UserResponse
from config import settings

router = APIRouter(prefix="/api/admin/auth", tags=["Admin Auth"])

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

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_from_token)
):
    """Get all users (Admin only)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return [UserResponse.model_validate(user) for user in users]

@router.get("/verify")
async def verify_admin(current_admin: User = Depends(get_current_admin_from_token)):
    """Verify admin access"""
    return {
        "authenticated": True,
        "user_id": current_admin.id,
        "user_email": current_admin.email,
        "user_role": current_admin.role.value
    }