# check_paths.py
import os

# Check what files are actually in the directory
upload_dir = "static/uploads/products"
full_path = os.path.abspath(upload_dir)
print(f"Full path: {full_path}")

if os.path.exists(full_path):
    files = os.listdir(full_path)
    print(f"\nFiles in directory ({len(files)}):")
    for f in files:
        file_path = os.path.join(full_path, f)
        size = os.path.getsize(file_path)
        print(f"  - {f} ({size} bytes)")
else:
    print(f"Directory does not exist: {full_path}")