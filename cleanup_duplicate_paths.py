# cleanup_duplicate_paths.py
import sqlite3

conn = sqlite3.connect('instance/ecommerce.db')
cursor = conn.cursor()

# Fix products table
cursor.execute("UPDATE products SET main_image = REPLACE(main_image, '/products/products/', '/products/')")
cursor.execute("UPDATE products SET main_image = REPLACE(main_image, '\\', '/')")
products_updated = cursor.rowcount
print(f"Updated {products_updated} products")

# Fix product_images table
cursor.execute("UPDATE product_images SET image_url = REPLACE(image_url, '/products/products/', '/products/')")
cursor.execute("UPDATE product_images SET image_url = REPLACE(image_url, '\\', '/')")
images_updated = cursor.rowcount
print(f"Updated {images_updated} product images")

conn.commit()
conn.close()
print("\nDuplicate paths cleaned up!")