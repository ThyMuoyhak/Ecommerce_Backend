# verify_fix.py
import sqlite3

conn = sqlite3.connect('instance/ecommerce.db')
cursor = conn.cursor()

print("=== UPDATED PRODUCTS ===")
cursor.execute("SELECT id, title, main_image FROM products")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Title: {row[1]}")
    print(f"  Main Image: {row[2]}")
    print()

print("=== PRODUCT IMAGES ===")
cursor.execute("SELECT id, product_id, image_url FROM product_images")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Product ID: {row[1]}, URL: {row[2]}")

if cursor.rowcount == 0:
    print("No sub images (clean)")

conn.close()