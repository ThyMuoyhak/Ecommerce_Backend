# cleanup_nested_folders.py
import os
import shutil
import sqlite3

def cleanup_nested_folders():
    base_path = "static/uploads"
    
    # Find and fix nested products folders
    for root, dirs, files in os.walk(base_path):
        for dir_name in dirs:
            if dir_name == "products" and root != base_path:
                nested_path = os.path.join(root, dir_name)
                target_path = os.path.join(base_path, "products")
                
                print(f"Found nested folder: {nested_path}")
                
                # Move files to correct location
                for file in os.listdir(nested_path):
                    src = os.path.join(nested_path, file)
                    dst = os.path.join(target_path, file)
                    if os.path.isfile(src):
                        shutil.move(src, dst)
                        print(f"  Moved: {file}")
                
                # Remove empty nested folder
                shutil.rmtree(nested_path)
                print(f"  Removed: {nested_path}")
    
    # Fix database paths
    db_path = 'instance/ecommerce.db'
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Fix all paths
        cursor.execute("UPDATE products SET main_image = REPLACE(main_image, '/static/uploads/products/products/', '/static/uploads/products/')")
        cursor.execute("UPDATE product_images SET image_url = REPLACE(image_url, '/static/uploads/products/products/', '/static/uploads/products/')")
        cursor.execute("UPDATE products SET main_image = REPLACE(main_image, '\\\\', '/')")
        cursor.execute("UPDATE product_images SET image_url = REPLACE(image_url, '\\\\', '/')")
        
        conn.commit()
        print("\nDatabase paths fixed!")
        conn.close()
    
    print("\nCleanup complete!")

if __name__ == "__main__":
    cleanup_nested_folders()