import os
import uuid
from fastapi import UploadFile, HTTPException
from PIL import Image
from config import settings

async def save_product_image(upload_file: UploadFile) -> str:
    """
    Save product image to: static/uploads/products/
    """
    print(f"[IMAGE_UTILS] Saving image: {upload_file.filename}")
    
    # Validate file extension
    file_extension = os.path.splitext(upload_file.filename)[1].lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File extension {file_extension} not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Read file content
    content = await upload_file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE // 1024 // 1024}MB"
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    
    # Save to: static/uploads/products/
    upload_dir = os.path.join(settings.UPLOAD_DIR, "products")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, unique_filename)
    print(f"[IMAGE_UTILS] Saving to: {file_path}")
    
    # Write file
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Optimize image
    try:
        with Image.open(file_path) as img:
            if img.mode in ('RGBA', 'P'):
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                else:
                    img = img.convert('RGB')
            
            if max(img.size) > 1200:
                img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
            
            if file_extension in ['.jpg', '.jpeg']:
                img.save(file_path, 'JPEG', quality=85, optimize=True)
            else:
                img.save(file_path, 'PNG', optimize=True)
            print(f"[IMAGE_UTILS] Image optimized")
    except Exception as e:
        print(f"[IMAGE_UTILS] Optimization skipped: {e}")
    
    # Return clean URL path
    url = f"/static/uploads/products/{unique_filename}"
    print(f"[IMAGE_UTILS] Returning URL: {url}")
    return url