import sqlite3
from datetime import datetime

def update_database():
    conn = sqlite3.connect('instance/ecommerce.db')
    cursor = conn.cursor()
    
    # For SQLite, we need to recreate the table to change column nullability
    # But a simpler approach is to update NULL values
    
    print("Updating database...")
    
    # Update products table
    cursor.execute("UPDATE products SET updated_at = created_at WHERE updated_at IS NULL")
    products_updated = cursor.rowcount
    print(f"Updated {products_updated} products")
    
    # Update orders table
    cursor.execute("UPDATE orders SET updated_at = created_at WHERE updated_at IS NULL")
    orders_updated = cursor.rowcount
    print(f"Updated {orders_updated} orders")
    
    # Update users table
    cursor.execute("UPDATE users SET updated_at = created_at WHERE updated_at IS NULL")
    users_updated = cursor.rowcount
    print(f"Updated {users_updated} users")
    
    conn.commit()
    conn.close()
    print("Database update completed!")

if __name__ == "__main__":
    update_database()