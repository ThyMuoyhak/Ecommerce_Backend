import os
from decouple import config

class Settings:
    # App
    APP_NAME = "Ecommerce Clothing API"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY = config("SECRET_KEY", default="your-secret-key-change-this")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # Database
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
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN", default="")
    TELEGRAM_CHAT_ID = config("TELEGRAM_CHAT_ID", default="")
    
    # CORS - Updated with your Netlify URLs
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "https://charming-licorice-c0e6f2.netlify.app",      # frontend_user
        "https://glittering-lollipop-73b279.netlify.app",    # frontend_admin
    ]

settings = Settings()

# Create upload directories
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "products"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "temp"), exist_ok=True)