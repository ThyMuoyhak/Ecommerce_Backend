# check_products.py
import sqlite3

conn = sqlite3.connect('instance/ecommerce.db')
cursor = conn.cursor()

# Check products table
cursor.execute("SELECT id, title, main_image FROM products")
print("=== PRODUCTS ===")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Title: {row[1]}")
    print(f"  Main Image: {row[2]}")
    print()

# Check product_images table
cursor.execute("SELECT id, product_id, image_url FROM product_images")
print("=== PRODUCT IMAGES ===")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Product ID: {row[1]}, URL: {row[2]}")

conn.close()