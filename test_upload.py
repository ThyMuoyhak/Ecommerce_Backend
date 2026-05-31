# test_upload.py
import requests
import os

# First, login to get token
login_response = requests.post(
    "http://localhost:8000/api/auth/login",
    data={"username": "admin@example.com", "password": "admin123"}
)

if login_response.status_code != 200:
    print(f"Login failed: {login_response.status_code}")
    print(login_response.text)
    exit()

token = login_response.json()["access_token"]
print(f"Login successful! Token: {token[:50]}...")

# Create a test image file if it doesn't exist
test_image_path = "test_image.jpg"
if not os.path.exists(test_image_path):
    # Create a simple red square image
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='red')
    img.save(test_image_path)
    print(f"Created test image: {test_image_path}")

# Test upload
with open(test_image_path, "rb") as img:
    files = {
        "main_image": ("test.jpg", img, "image/jpeg")
    }
    data = {
        "title": "Test Upload Product",
        "original_price": "29.99",
        "category_id": "1",
        "stock_quantity": "10",
        "sizes": '[{"size":"M","stock":10}]',
        "colors": '[{"color":"Black","color_code":"#000000"}]'
    }
    
    print("\nUploading product...")
    response = requests.post(
        "http://localhost:8000/api/products",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Product created successfully!")
        print(f"Product ID: {result['id']}")
        print(f"Image URL: {result['main_image']}")
        print(f"Full image URL: http://localhost:8000{result['main_image']}")
        
        # Check if file exists
        file_path = result['main_image'].replace('/static/', 'static/')
        if os.path.exists(file_path):
            print(f"\n✓ Image file exists at: {file_path}")
            print(f"  File size: {os.path.getsize(file_path)} bytes")
        else:
            print(f"\n✗ Image file NOT found at: {file_path}")
    else:
        print(f"Error: {response.text}")

# Clean up
if os.path.exists(test_image_path):
    os.remove(test_image_path)
    print(f"\nRemoved test image: {test_image_path}")