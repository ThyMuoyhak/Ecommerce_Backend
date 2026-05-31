import os
from decouple import config

class Settings:
    # App
    APP_NAME = "Ecommerce Clothing API"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY = config("SECRET_KEY", default="your-secret-key-change-this")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # Database - Will use Render's DATABASE_URL environment variable
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./instance/ecommerce.db")
    
    # File Upload
    UPLOAD_DIR = "static/uploads"
    MAX_FILE_SIZE = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    
    # KHQR Payment Gateway
    KHQR_GATEWAY_URL = "https://khqr.cc/api/payment/request"
    KHQR_PROFILE_ID = "6RV4SzQbqgFte0wiFse5Cqa6Ww8wriIa"
    KHQR_SECRET_KEY = config("KHQR_SECRET_KEY", default="YOUR_SECRET_KEY")
    KHQR_PROFILE_KEY = config("KHQR_PROFILE_KEY", default="YOUR_PROFILE_KEY")
    KHQR_VERIFY_URL = f"https://khqr.cc/api/{KHQR_PROFILE_ID}/payment-gateway/v1/payments/check-trans"
    
    # CORS
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://your-frontend.onrender.com",  # Add your frontend URL when deployed
    ]

settings = Settings()

# Create upload directories
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "products"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "temp"), exist_ok=True)