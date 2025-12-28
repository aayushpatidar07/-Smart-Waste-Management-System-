"""
Quick Database Setup Test
Test MySQL connection and create database
"""

import mysql.connector
from mysql.connector import Error

def test_connection():
    """Test different MySQL password combinations"""
    passwords = ['', 'root', 'admin', 'password', 'mysql', '123456', 'Root@123']
    
    print("🔍 Testing MySQL Connection...")
    print("=" * 50)
    
    for pwd in passwords:
        try:
            print(f"\nTrying password: '{pwd}'")
            connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password=pwd
            )
            
            if connection.is_connected():
                print(f"✅ SUCCESS! MySQL password is: '{pwd}'")
                
                # Create database
                cursor = connection.cursor()
                cursor.execute("CREATE DATABASE IF NOT EXISTS smart_waste_db")
                print("✅ Database 'smart_waste_db' created successfully")
                
                cursor.close()
                connection.close()
                
                print("\n" + "=" * 50)
                print(f"✅ Update your .env file:")
                print(f"DB_PASSWORD={pwd}")
                print("=" * 50)
                return pwd
                
        except Error as e:
            print(f"❌ Failed: {e}")
            continue
    
    print("\n❌ None of the common passwords worked.")
    print("📝 Please enter your MySQL root password manually.")
    print("   You can reset MySQL password if needed.")
    return None

if __name__ == "__main__":
    password = test_connection()
    if not password:
        print("\n💡 To reset MySQL password on Windows:")
        print("   1. Stop MySQL service")
        print("   2. Run: mysqld --init-file=<path to reset file>")
        print("   3. Or use MySQL Workbench to reset password")
