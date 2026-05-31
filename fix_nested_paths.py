# fix_nested_paths.py
import sqlite3

conn = sqlite3.connect('instance/ecommerce.db')
cursor = conn.cursor()

# Fix main_image paths
cursor.execute("UPDATE products SET main_image = REPLACE(main_image, '/static/uploads/products/products/', '/static/uploads/products/')")
products_updated = cursor.rowcount
print(f"Updated {products_updated} products")

# Fix product_images paths
cursor.execute("UPDATE product_images SET image_url = REPLACE(image_url, '/static/uploads/products/products/', '/static/uploads/products/')")
images_updated = cursor.rowcount
print(f"Updated {images_updated} product images")

# Also fix any paths with backslashes
cursor.execute("UPDATE products SET main_image = REPLACE(main_image, '\\', '/')")
cursor.execute("UPDATE product_images SET image_url = REPLACE(image_url, '\\', '/')")

conn.commit()

# Verify the fixes
print("\nCurrent product images:")
cursor.execute("SELECT id, title, main_image FROM products")
for row in cursor.fetchall():
    print(f"  ID {row[0]}: {row[2]}")

print("\nCurrent sub images:")
cursor.execute("SELECT id, product_id, image_url FROM product_images")
for row in cursor.fetchall():
    print(f"  ID {row[0]}, Product {row[1]}: {row[2]}")

conn.close()