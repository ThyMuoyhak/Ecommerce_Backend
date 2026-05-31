import os
from decouple import config

class Settings:
    # App
    APP_NAME = "Ecommerce Clothing API"
    DEBUG = True
    SECRET_KEY = config("SECRET_KEY", default="your-secret-key-change-this")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # Database
    DATABASE_URL = f"sqlite:///./instance/ecommerce.db"
    
    # File Upload
    UPLOAD_DIR = "static/uploads"
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    
    # KHQR Payment Gateway
    KHQR_GATEWAY_URL = "https://khqr.cc/api/payment/request"
    KHQR_PROFILE_ID = "6RV4SzQbqgFte0wiFse5Cqa6Ww8wriIa"
    
    # IMPORTANT: These should be different and provided by KHQR
    # The secret key is for generating payment hash
    KHQR_SECRET_KEY = config("KHQR_SECRET_KEY", default="VXt1QnJ2ExvW1esNp7fgDYFmt9ky9wWo")
    
    # The profile key is for verification (usually different from secret key)
    KHQR_PROFILE_KEY = config("KHQR_PROFILE_KEY", default="VXt1QnJ2ExvW1esNp7fgDYFmt9ky9wWo")
    
    # Update the verify URL to use your actual profile ID
    KHQR_VERIFY_URL = f"https://khqr.cc/api/{KHQR_PROFILE_ID}/payment-gateway/v1/payments/check-trans"
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN", default="YOUR_BOT_TOKEN")
    TELEGRAM_CHAT_ID = config("TELEGRAM_CHAT_ID", default="YOUR_CHAT_ID")
    
    # CORS
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]

settings = Settings()

# Create upload directories
os.makedirs(os.path.join(settings.UPLOAD_DIR, "products"), exist_ok=True)