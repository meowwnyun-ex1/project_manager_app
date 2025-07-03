#!/usr/bin/env python3
"""
DENSO Project Manager Pro - Create Admin User Script
สคริปต์สำหรับสร้าง Admin User ใหม่
"""

import pyodbc
import bcrypt
import streamlit as st
from datetime import datetime
import sys


def get_database_connection():
    """เชื่อมต่อฐานข้อมูล"""
    try:
        # อ่านการตั้งค่าจาก secrets.toml
        db_config = st.secrets.database

        connection_string = (
            f"DRIVER={{{db_config.driver}}};"
            f"SERVER={db_config.server};"
            f"DATABASE={db_config.database};"
            f"UID={db_config.username};"
            f"PWD={db_config.password};"
            f"Encrypt={db_config.connection_options.encrypt};"
            f"TrustServerCertificate={db_config.connection_options.trust_server_certificate};"
        )

        conn = pyodbc.connect(connection_string)
        return conn

    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return None


def check_admin_exists(conn):
    """ตรวจสอบว่ามี admin user อยู่แล้วหรือไม่"""
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT UserID, Username, Email, Role FROM Users WHERE Username = 'admin'"
        )
        result = cursor.fetchone()

        if result:
            print(f"⚠️ Admin user already exists:")
            print(f"   UserID: {result[0]}")
            print(f"   Username: {result[1]}")
            print(f"   Email: {result[2]}")
            print(f"   Role: {result[3]}")
            return True
        else:
            print("🔍 No admin user found. Will create new one.")
            return False

    except Exception as e:
        print(f"❌ Error checking admin user: {str(e)}")
        return None


def hash_password(password: str) -> str:
    """สร้าง password hash"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def create_admin_user(
    conn, username="admin", password="admin123", email="admin@denso.com"
):
    """สร้าง admin user ใหม่"""
    try:
        # Hash password
        password_hash = hash_password(password)

        # SQL Insert
        insert_query = """
        INSERT INTO Users (
            Username, PasswordHash, Email, FirstName, LastName, 
            Role, Department, IsActive, CreatedDate, PasswordChangedDate
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        cursor = conn.cursor()
        cursor.execute(
            insert_query,
            (
                username,
                password_hash,
                email,
                "System",
                "Administrator",
                "Admin",
                "IT",
                1,  # IsActive
                datetime.now(),
                datetime.now(),
            ),
        )

        conn.commit()

        print("✅ Admin user created successfully!")
        print(f"📝 Login Details:")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"   Email: {email}")
        print("⚠️ Please change password immediately after first login!")

        return True

    except Exception as e:
        print(f"❌ Error creating admin user: {str(e)}")
        conn.rollback()
        return False


def create_additional_user(
    conn,
    username,
    password,
    email,
    first_name,
    last_name,
    role="User",
    department="General",
):
    """สร้าง user เพิ่มเติม"""
    try:
        # ตรวจสอบว่า username ซ้ำหรือไม่
        cursor = conn.cursor()
        cursor.execute("SELECT UserID FROM Users WHERE Username = ?", (username,))
        if cursor.fetchone():
            print(f"⚠️ Username '{username}' already exists!")
            return False

        # Hash password
        password_hash = hash_password(password)

        # SQL Insert
        insert_query = """
        INSERT INTO Users (
            Username, PasswordHash, Email, FirstName, LastName, 
            Role, Department, IsActive, CreatedDate, PasswordChangedDate
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        cursor.execute(
            insert_query,
            (
                username,
                password_hash,
                email,
                first_name,
                last_name,
                role,
                department,
                1,  # IsActive
                datetime.now(),
                datetime.now(),
            ),
        )

        conn.commit()

        print(f"✅ User '{username}' created successfully!")
        return True

    except Exception as e:
        print(f"❌ Error creating user '{username}': {str(e)}")
        conn.rollback()
        return False


def list_all_users(conn):
    """แสดงรายชื่อ users ทั้งหมด"""
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT UserID, Username, Email, FirstName, LastName, Role, Department, IsActive, CreatedDate
            FROM Users 
            ORDER BY CreatedDate DESC
        """
        )

        users = cursor.fetchall()

        print("\n👥 All Users in System:")
        print("-" * 80)
        print(
            f"{'ID':<4} {'Username':<15} {'Name':<20} {'Email':<25} {'Role':<10} {'Active'}"
        )
        print("-" * 80)

        for user in users:
            full_name = f"{user[3] or ''} {user[4] or ''}".strip()
            active_status = "✅" if user[7] else "❌"
            print(
                f"{user[0]:<4} {user[1]:<15} {full_name:<20} {user[2]:<25} {user[5]:<10} {active_status}"
            )

        print(f"\nTotal Users: {len(users)}")

    except Exception as e:
        print(f"❌ Error listing users: {str(e)}")


def main():
    """Main function"""
    print("🔐 DENSO Project Manager Pro - Admin User Creator")
    print("=" * 60)

    # เชื่อมต่อฐานข้อมูล
    conn = get_database_connection()
    if not conn:
        print("❌ Cannot connect to database. Please check your configuration.")
        sys.exit(1)

    try:
        # ตรวจสอบ command line arguments
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()

            if command == "create":
                # สร้าง admin user
                admin_exists = check_admin_exists(conn)
                if not admin_exists:
                    create_admin_user(conn)

            elif command == "force":
                # บังคับสร้าง admin user ใหม่
                print("🔄 Force creating new admin user...")
                create_admin_user(conn)

            elif command == "list":
                # แสดงรายชื่อ users
                list_all_users(conn)

            elif command == "user" and len(sys.argv) >= 6:
                # สร้าง user ใหม่
                username = sys.argv[2]
                password = sys.argv[3]
                email = sys.argv[4]
                first_name = sys.argv[5]
                last_name = sys.argv[6] if len(sys.argv) > 6 else ""
                role = sys.argv[7] if len(sys.argv) > 7 else "User"
                department = sys.argv[8] if len(sys.argv) > 8 else "General"

                create_additional_user(
                    conn,
                    username,
                    password,
                    email,
                    first_name,
                    last_name,
                    role,
                    department,
                )

            else:
                print("Available commands:")
                print(
                    "  python create_admin_user.py create                    # Create admin user if not exists"
                )
                print(
                    "  python create_admin_user.py force                     # Force create new admin user"
                )
                print(
                    "  python create_admin_user.py list                      # List all users"
                )
                print(
                    "  python create_admin_user.py user <username> <password> <email> <firstname> <lastname> [role] [department]"
                )
        else:
            # Default: ตรวจสอบและสร้าง admin หากจำเป็น
            admin_exists = check_admin_exists(conn)
            if admin_exists is False:
                create_admin_user(conn)

            # แสดงรายชื่อ users
            list_all_users(conn)

    finally:
        conn.close()
        print("\n🔐 Database connection closed.")


if __name__ == "__main__":
    main()
