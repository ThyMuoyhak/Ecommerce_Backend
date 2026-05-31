# create_admin.py
import sqlite3
import bcrypt

def create_admin():
    conn = sqlite3.connect('instance/ecommerce.db')
    cursor = conn.cursor()
    
    # Check if admin exists
    cursor.execute("SELECT * FROM users WHERE email = 'admin@example.com'")
    admin = cursor.fetchone()
    
    if not admin:
        # Hash password
        password = 'admin123'
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Insert admin
        cursor.execute('''
            INSERT INTO users (full_name, gender, phone_number, email, password_hash, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('Admin User', 'Male', '0999999999', 'admin@example.com', hashed.decode('utf-8'), 'admin', 1))
        
        conn.commit()
        print("Admin user created successfully!")
    else:
        print("Admin user already exists")
    
    conn.close()

if __name__ == '__main__':
    create_admin()