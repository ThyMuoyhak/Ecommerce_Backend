# fix_db_paths.py
import sqlite3

conn = sqlite3.connect('instance/ecommerce.db')
cursor = conn.cursor()

cursor.execute("UPDATE products SET main_image = REPLACE(main_image, '/static/uploads/products/products/', '/static/uploads/products/')")
cursor.execute("UPDATE product_images SET image_url = REPLACE(image_url, '/static/uploads/products/products/', '/static/uploads/products/')")
cursor.execute("UPDATE products SET main_image = REPLACE(main_image, '\\', '/')")
cursor.execute("UPDATE product_images SET image_url = REPLACE(image_url, '\\', '/')")

conn.commit()
print("Database paths fixed!")
conn.close()