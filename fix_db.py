# fix_db.py
import sqlite3
import os

def fix_database():
    # Connect to database
    db_path = 'instance/ecommerce.db'
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Fix products table
    cursor.execute("UPDATE products SET main_image = REPLACE(main_image, '/static/uploads/products/products/', '/static/uploads/products/')")
    products_updated = cursor.rowcount
    print(f"Updated {products_updated} products")
    
    # Fix product_images table
    cursor.execute("UPDATE product_images SET image_url = REPLACE(image_url, '/static/uploads/products/products/', '/static/uploads/products/')")
    images_updated = cursor.rowcount
    print(f"Updated {images_updated} product images")
    
    # Commit changes
    conn.commit()
    
    # Verify the fixes
    print("\n=== Updated Products ===")
    cursor.execute("SELECT id, title, main_image FROM products")
    for row in cursor.fetchall():
        print(f"ID: {row[0]}, Title: {row[1]}, Image: {row[2]}")
    
    conn.close()
    print("\nDatabase fixed successfully!")

if __name__ == "__main__":
    fix_database()