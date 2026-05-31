# migrate_to_postgres.py
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os

# SQLite connection (your local database)
sqlite_conn = sqlite3.connect('instance/ecommerce.db')
sqlite_cursor = sqlite_conn.cursor()

# PostgreSQL connection (Render database)
pg_conn = psycopg2.connect(
    host="dpg-d8480kbeo5us73e3elt0-a.virginia-postgres.render.com",
    port=5432,
    database="testdb_uq0y",
    user="testdb_uq0y_user",
    password="pCKmJ10PokZLC9R1IiFfTly4VA8kje99",
    sslmode="require"
)
pg_cursor = pg_conn.cursor()

def migrate_table(table_name, columns):
    """Migrate data from SQLite to PostgreSQL"""
    print(f"Migrating {table_name}...")
    
    # Get data from SQLite
    sqlite_cursor.execute(f"SELECT {', '.join(columns)} FROM {table_name}")
    rows = sqlite_cursor.fetchall()
    
    if rows:
        # Insert into PostgreSQL
        placeholders = ','.join(['%s'] * len(columns))
        insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        for row in rows:
            try:
                pg_cursor.execute(insert_query, row)
            except Exception as e:
                print(f"Error inserting row {row}: {e}")
        
        pg_conn.commit()
        print(f"  Migrated {len(rows)} rows")
    else:
        print(f"  No data to migrate")

# Get all tables from SQLite
sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
tables = sqlite_cursor.fetchall()

for table in tables:
    table_name = table[0]
    
    # Get column names
    sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in sqlite_cursor.fetchall()]
    
    migrate_table(table_name, columns)

# Close connections
sqlite_conn.close()
pg_cursor.close()
pg_conn.close()

print("\nMigration complete!")