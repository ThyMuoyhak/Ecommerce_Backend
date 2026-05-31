from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from database import engine, Base
from config import settings
from routes import auth, products, categories, orders, payment
from admin import auth as admin_auth, products as admin_products, orders as admin_orders
from middleware import AuthMiddleware

# Create database tables
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
    
    # Create default admin user if not exists
    from sqlalchemy.orm import Session
    from models import User, UserRole
    from utils import get_password_hash
    
    db = Session(bind=engine)
    try:
        admin_email = "admin@example.com"
        admin_user = db.query(User).filter(User.email == admin_email).first()
        if not admin_user:
            admin_user = User(
                full_name="Admin User",
                gender="Male",
                phone_number="0999999999",
                email=admin_email,
                password_hash=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print("Default admin user created: admin@example.com / admin123")
        else:
            print(f"Admin user already exists: {admin_user.email}")
    except Exception as e:
        print(f"Error creating admin user: {e}")
    finally:
        db.close()
    
    yield
    
    # Shutdown
    print("Shutting down...")

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="E-commerce Clothing API with KHQR Payment Integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add Auth Middleware FIRST (before CORS for better security)
app.add_middleware(AuthMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
# User routes
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(categories.router)
app.include_router(orders.router)
app.include_router(payment.router)

# Admin routes
app.include_router(admin_auth.router)
app.include_router(admin_products.router)
app.include_router(admin_orders.router)

# Print all routes for debugging
print("\n=== Registered Routes ===")
for route in app.routes:
    if hasattr(route, "methods"):
        print(f"{route.methods} {route.path}")
print("========================\n")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to E-commerce Clothing API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "admin": "/api/admin",
            "auth": "/api/auth",
            "products": "/api/products",
            "categories": "/api/categories",
            "orders": "/api/orders",
            "payment": "/api/payment"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )