# clean_db_paths.py
import sqlite3

conn = sqlite3.connect('instance/ecommerce.db')
cursor = conn.cursor()

# Fix any paths with duplicate 'products'
cursor.execute("UPDATE products SET main_image = REPLACE(main_image, '/static/uploads/products/products/', '/static/uploads/products/')")
cursor.execute("UPDATE product_images SET image_url = REPLACE(image_url, '/static/uploads/products/products/', '/static/uploads/products/')")

# Also fix any paths that might have double slashes
cursor.execute("UPDATE products SET main_image = REPLACE(main_image, '//', '/')")
cursor.execute("UPDATE product_images SET image_url = REPLACE(image_url, '//', '/')")

print(f"Fixed products: {cursor.rowcount}")

conn.commit()

# Show current paths
cursor.execute("SELECT id, title, main_image FROM products")
print("\nCurrent product images:")
for row in cursor.fetchall():
    print(f"  ID {row[0]}: {row[2]}")

conn.close()