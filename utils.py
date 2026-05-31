import os
import shutil
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from config import settings
import hashlib
import hmac
from fastapi import UploadFile, HTTPException
from PIL import Image
import uuid

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# JWT Token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

# Order utilities
def generate_order_number() -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4().hex[:8].upper())
    return f"ORD-{timestamp}-{unique_id}"

# File upload utilities - COMPLETELY FIXED - No duplicate folder creation
async def save_upload_file(upload_file: UploadFile, subfolder: str = "") -> str:
    """Save uploaded file and return the URL path"""
    
    print(f"=== SAVING FILE ===")
    print(f"Filename: {upload_file.filename}")
    print(f"Original subfolder parameter: '{subfolder}'")
    
    # CRITICAL FIX: Clean the subfolder parameter
    # Remove any leading/trailing slashes or backslashes
    subfolder_cleaned = ""
    if subfolder and subfolder.strip():
        subfolder_cleaned = subfolder.strip('/\\')
        # Remove any duplicate 'products' patterns
        while 'products/products' in subfolder_cleaned:
            subfolder_cleaned = subfolder_cleaned.replace('products/products', 'products')
        while 'products\\\\products' in subfolder_cleaned:
            subfolder_cleaned = subfolder_cleaned.replace('products\\\\products', 'products')
        while 'products//products' in subfolder_cleaned:
            subfolder_cleaned = subfolder_cleaned.replace('products//products', 'products')
    
    print(f"Cleaned subfolder: '{subfolder_cleaned}'")
    
    # Validate file extension
    file_extension = os.path.splitext(upload_file.filename)[1].lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File extension {file_extension} not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}")
    
    # Read file content
    content = await upload_file.read()
    print(f"File size: {len(content)} bytes")
    
    # Validate file size
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max size: {settings.MAX_FILE_SIZE // 1024 // 1024}MB")
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    print(f"Unique filename: {unique_filename}")
    
    # Build path - ALWAYS use the base upload directory
    upload_path = settings.UPLOAD_DIR
    
    # Only add subfolder if it's provided and not empty
    if subfolder_cleaned:
        upload_path = os.path.join(settings.UPLOAD_DIR, subfolder_cleaned)
    
    print(f"Upload path: {upload_path}")
    
    # Ensure directory exists
    os.makedirs(upload_path, exist_ok=True)
    
    file_path = os.path.join(upload_path, unique_filename)
    print(f"Full file path: {file_path}")
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            f.write(content)
        print(f"File saved successfully!")
        
        # Verify file was created
        if os.path.exists(file_path):
            print(f"File exists at: {file_path}")
            print(f"File size on disk: {os.path.getsize(file_path)} bytes")
        else:
            print(f"ERROR: File was not created at {file_path}")
            raise HTTPException(status_code=500, detail="File was not saved properly")
            
    except Exception as e:
        print(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Optimize image if it's an image file
    if file_extension in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
        try:
            with Image.open(file_path) as img:
                # Convert RGBA to RGB if needed
                if img.mode in ('RGBA', 'P'):
                    if img.mode == 'RGBA':
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[3])
                        img = background
                    else:
                        img = img.convert('RGB')
                
                # Resize if too large
                if max(img.size) > 1200:
                    img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                
                # Save based on format
                if file_extension in ['.jpg', '.jpeg']:
                    img.save(file_path, 'JPEG', quality=85, optimize=True)
                else:
                    img.save(file_path, 'PNG', optimize=True)
                print(f"Image optimized")
        except Exception as e:
            print(f"Image optimization skipped: {e}")
    
    # Return relative URL - use forward slashes for web
    if subfolder_cleaned:
        relative_path = f"/static/uploads/{subfolder_cleaned}/{unique_filename}"
    else:
        relative_path = f"/static/uploads/{unique_filename}"
    
    # Clean the path - replace backslashes and remove any duplicates
    relative_path = relative_path.replace('\\', '/')
    while '//' in relative_path:
        relative_path = relative_path.replace('//', '/')
    while '/products/products/' in relative_path:
        relative_path = relative_path.replace('/products/products/', '/products/')
    
    print(f"Returning URL: {relative_path}")
    print(f"=== SAVE COMPLETE ===")
    
    return relative_path

async def save_multiple_images(files: list[UploadFile], subfolder: str = "") -> list[str]:
    """Save multiple uploaded files and return their URLs"""
    saved_paths = []
    for file in files:
        if file and file.filename:
            path = await save_upload_file(file, subfolder)
            saved_paths.append(path)
    return saved_paths

# KHQR Payment utilities
def generate_khqr_hash(transaction_id: str, amount: float, success_url: str, remark: str = "") -> str:
    """Generate SHA1 hash for KHQR payment"""
    raw_string = settings.KHQR_SECRET_KEY + transaction_id + str(amount) + success_url + remark
    return hashlib.sha1(raw_string.encode()).hexdigest()

def generate_verification_hash(transaction_id: str) -> str:
    """Generate SHA1 hash for verification"""
    raw_string = settings.KHQR_PROFILE_KEY + transaction_id
    return hashlib.sha1(raw_string.encode()).hexdigest()

# Telegram Bot utilities
async def send_telegram_alert(message: str):
    """Send alert to Telegram bot"""
    try:
        from telegram import Bot
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=settings.TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        print(f"Telegram alert failed: {e}")

async def notify_new_order(order_data: dict):
    """Send new order notification"""
    message = f"""
🛍️ NEW ORDER RECEIVED!
━━━━━━━━━━━━━━━━━━━━━
📦 Order: {order_data.get('order_number')}
👤 Customer: {order_data.get('customer_name')}
💰 Total: ${order_data.get('final_amount')}
📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━
Status: Pending Payment
    """
    await send_telegram_alert(message)

async def notify_payment_success(order_data: dict):
    """Send payment success notification"""
    message = f"""
✅ PAYMENT CONFIRMED!
━━━━━━━━━━━━━━━━━━━━━
📦 Order: {order_data.get('order_number')}
💰 Amount: ${order_data.get('final_amount')}
💳 Transaction: {order_data.get('transaction_id')}
━━━━━━━━━━━━━━━━━━━━━
Status: Paid - Ready to Process
    """
    await send_telegram_alert(message)