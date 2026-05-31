# fix_image_paths.py
import sqlite3

def fix_image_paths():
    conn = sqlite3.connect('instance/ecommerce.db')
    cursor = conn.cursor()
    
    # Get all products
    cursor.execute("SELECT id, main_image FROM products")
    products = cursor.fetchall()
    
    updated_count = 0
    for product in products:
        product_id, image_path = product
        
        if image_path:
            # Fix the path: remove duplicates and fix slashes
            # Convert backslashes to forward slashes
            fixed_path = image_path.replace('\\', '/')
            
            # Remove duplicate 'products' folder
            if '/products/products/' in fixed_path:
                fixed_path = fixed_path.replace('/products/products/', '/products/')
            
            # Ensure it starts with /static/uploads
            if not fixed_path.startswith('/static/'):
                if fixed_path.startswith('/uploads/'):
                    fixed_path = '/static' + fixed_path
                elif not fixed_path.startswith('/'):
                    fixed_path = '/static/uploads/products/' + fixed_path
            
            if fixed_path != image_path:
                print(f"Fixing product {product_id}:")
                print(f"  Old: {image_path}")
                print(f"  New: {fixed_path}")
                cursor.execute("UPDATE products SET main_image = ? WHERE id = ?", (fixed_path, product_id))
                updated_count += 1
    
    # Also fix product_images table
    cursor.execute("SELECT id, image_url FROM product_images")
    images = cursor.fetchall()
    
    for image in images:
        image_id, image_url = image
        if image_url:
            fixed_url = image_url.replace('\\', '/')
            if '/products/products/' in fixed_url:
                fixed_url = fixed_url.replace('/products/products/', '/products/')
            if not fixed_url.startswith('/static/'):
                if fixed_url.startswith('/uploads/'):
                    fixed_url = '/static' + fixed_url
            
            if fixed_url != image_url:
                print(f"Fixing product_image {image_id}:")
                print(f"  Old: {image_url}")
                print(f"  New: {fixed_url}")
                cursor.execute("UPDATE product_images SET image_url = ? WHERE id = ?", (fixed_url, image_id))
                updated_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"\nTotal updated: {updated_count} records")

if __name__ == "__main__":
    fix_image_paths()