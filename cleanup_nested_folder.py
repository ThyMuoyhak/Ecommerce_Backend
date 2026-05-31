# cleanup_nested_folder.py
import os
import shutil

# Remove the nested products folder if it exists
nested_path = "static/uploads/products/products"
if os.path.exists(nested_path):
    print(f"Removing nested folder: {nested_path}")
    
    # Move any images from nested folder to parent
    if os.path.isdir(nested_path):
        for file in os.listdir(nested_path):
            src = os.path.join(nested_path, file)
            dst = os.path.join("static/uploads/products", file)
            if os.path.isfile(src):
                shutil.move(src, dst)
                print(f"  Moved: {file}")
    
    # Remove the empty nested folder
    shutil.rmtree(nested_path)
    print(f"Removed nested folder")

# Also check for any other nested issues
uploads_path = "static/uploads"
for root, dirs, files in os.walk(uploads_path):
    for dir_name in dirs:
        if dir_name == "products" and root != uploads_path:
            print(f"Warning: Found 'products' folder in unexpected location: {root}")