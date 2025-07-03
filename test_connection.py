#!/usr/bin/env python3
"""
Database Connection Diagnostic Tool
เครื่องมือวินิจฉัยการเชื่อมต่อฐานข้อมูล
"""

import pyodbc
import sys
import time


def test_sql_server_connection():
    """ทดสอบการเชื่อมต่อ SQL Server แบบครบถ้วน"""

    print("🔍 SQL Server Connection Diagnostic")
    print("=" * 50)

    # Test configurations
    configs = [
        {
            "name": "Production Server",
            "server": "10.73.148.27",
            "database": "ProjectManagerDB",
            "username": "TS00029",
            "password": "Thammaphon@TS00029",
            "driver": "ODBC Driver 17 for SQL Server",
        },
        {
            "name": "LocalDB",
            "server": "(localdb)\\MSSQLLocalDB",
            "database": "ProjectManagerDB",
            "username": "",
            "password": "",
            "driver": "ODBC Driver 17 for SQL Server",
        },
    ]

    for config in configs:
        print(f"\n🧪 Testing: {config['name']}")
        print("-" * 30)

        # Test 1: Server connectivity
        success = test_server_connection(config)
        if not success:
            continue

        # Test 2: Database connection
        success = test_database_connection(config)
        if not success:
            continue

        # Test 3: Basic query
        test_basic_query(config)


def test_server_connection(config):
    """ทดสอบการเชื่อมต่อ server"""
    try:
        print(f"📡 Testing server: {config['server']}")

        if config["username"] and config["password"]:
            conn_str = (
                f"DRIVER={{{config['driver']}}};"
                f"SERVER={config['server']};"
                f"UID={config['username']};"
                f"PWD={config['password']};"
                f"TrustServerCertificate=yes;"
                f"Connection Timeout=10;"
            )
        else:
            conn_str = (
                f"DRIVER={{{config['driver']}}};"
                f"SERVER={config['server']};"
                f"Trusted_Connection=yes;"
                f"TrustServerCertificate=yes;"
                f"Connection Timeout=10;"
            )

        conn = pyodbc.connect(conn_str)
        conn.close()
        print("✅ Server connection: SUCCESS")
        return True

    except Exception as e:
        print(f"❌ Server connection: FAILED")
        print(f"   Error: {str(e)}")
        return False


def test_database_connection(config):
    """ทดสอบการเชื่อมต่อ database"""
    try:
        print(f"🗄️ Testing database: {config['database']}")

        if config["username"] and config["password"]:
            conn_str = (
                f"DRIVER={{{config['driver']}}};"
                f"SERVER={config['server']};"
                f"DATABASE={config['database']};"
                f"UID={config['username']};"
                f"PWD={config['password']};"
                f"TrustServerCertificate=yes;"
                f"Connection Timeout=10;"
            )
        else:
            conn_str = (
                f"DRIVER={{{config['driver']}}};"
                f"SERVER={config['server']};"
                f"DATABASE={config['database']};"
                f"Trusted_Connection=yes;"
                f"TrustServerCertificate=yes;"
                f"Connection Timeout=10;"
            )

        conn = pyodbc.connect(conn_str)
        conn.close()
        print("✅ Database connection: SUCCESS")
        return True

    except Exception as e:
        print(f"❌ Database connection: FAILED")
        print(f"   Error: {str(e)}")

        # แนะนำการแก้ไข
        if "database" in str(e).lower():
            print("💡 Suggestions:")
            print("   - ตรวจสอบว่า database มีอยู่จริง")
            print(
                '   - รัน: sqlcmd -S "(localdb)\\MSSQLLocalDB" -Q "CREATE DATABASE ProjectManagerDB"'
            )

        return False


def test_basic_query(config):
    """ทดสอบ query พื้นฐาน"""
    try:
        print("🔍 Testing basic query...")

        if config["username"] and config["password"]:
            conn_str = (
                f"DRIVER={{{config['driver']}}};"
                f"SERVER={config['server']};"
                f"DATABASE={config['database']};"
                f"UID={config['username']};"
                f"PWD={config['password']};"
                f"TrustServerCertificate=yes;"
            )
        else:
            conn_str = (
                f"DRIVER={{{config['driver']}}};"
                f"SERVER={config['server']};"
                f"DATABASE={config['database']};"
                f"Trusted_Connection=yes;"
                f"TrustServerCertificate=yes;"
            )

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # Test queries
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print(f"✅ SQL Server Version: {version[:50]}...")

        cursor.execute("SELECT GETDATE()")
        current_time = cursor.fetchone()[0]
        print(f"✅ Current Time: {current_time}")

        # Test table existence
        cursor.execute(
            """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
        """
        )
        tables = cursor.fetchall()

        if tables:
            print(f"✅ Found {len(tables)} tables:")
            for table in tables[:5]:  # Show first 5 tables
                print(f"   - {table[0]}")
            if len(tables) > 5:
                print(f"   ... และอีก {len(tables) - 5} tables")
        else:
            print("⚠️ No tables found - database is empty")
            print("💡 Run setup.sql to create tables")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Query test: FAILED")
        print(f"   Error: {str(e)}")
        return False


def check_odbc_drivers():
    """ตรวจสอบ ODBC drivers ที่มี"""
    print("\n🔧 Available ODBC Drivers:")
    print("-" * 30)

    try:
        drivers = pyodbc.drivers()
        sql_drivers = [d for d in drivers if "SQL Server" in d]

        if sql_drivers:
            for driver in sql_drivers:
                print(f"✅ {driver}")
        else:
            print("❌ No SQL Server ODBC drivers found!")
            print("💡 Install: ODBC Driver 17 for SQL Server")

    except Exception as e:
        print(f"❌ Error checking drivers: {e}")


def check_localdb_status():
    """ตรวจสอบสถานะ LocalDB"""
    print("\n🏠 LocalDB Status Check:")
    print("-" * 30)

    try:
        import subprocess

        # Check LocalDB instances
        result = subprocess.run(["sqllocaldb", "info"], capture_output=True, text=True)

        if result.returncode == 0:
            instances = result.stdout.strip().split("\n")
            print(f"📋 Available instances: {', '.join(instances)}")

            # Check MSSQLLocalDB specifically
            result = subprocess.run(
                ["sqllocaldb", "info", "MSSQLLocalDB"], capture_output=True, text=True
            )

            if result.returncode == 0:
                print("✅ MSSQLLocalDB instance found")
                if "Running" in result.stdout:
                    print("✅ MSSQLLocalDB is running")
                else:
                    print("⚠️ MSSQLLocalDB is stopped")
                    print("💡 Run: sqllocaldb start MSSQLLocalDB")
            else:
                print("❌ MSSQLLocalDB instance not found")
                print("💡 Run: sqllocaldb create MSSQLLocalDB")
        else:
            print("❌ sqllocaldb command not found")
            print("💡 Install SQL Server Express LocalDB")

    except Exception as e:
        print(f"❌ LocalDB check failed: {e}")


def generate_connection_commands():
    """สร้างคำสั่งเชื่อมต่อที่ใช้ได้"""
    print("\n📋 Connection Commands:")
    print("-" * 30)

    print("🔨 Create Database (LocalDB):")
    print('sqlcmd -S "(localdb)\\MSSQLLocalDB" -Q "CREATE DATABASE ProjectManagerDB"')

    print("\n🔌 Test Connection (SSMS):")
    print("Server: (localdb)\\MSSQLLocalDB")
    print("Authentication: Windows Authentication")

    print("\n🐍 Python Test:")
    print(
        """
import pyodbc
conn_str = '''
DRIVER={ODBC Driver 17 for SQL Server};
SERVER=(localdb)\\MSSQLLocalDB;
DATABASE=ProjectManagerDB;
Trusted_Connection=yes;
'''
conn = pyodbc.connect(conn_str)
print("Connected!")
conn.close()
"""
    )


if __name__ == "__main__":
    print("🚀 Starting Database Diagnostic...")

    # เรียกใช้การทดสอบทั้งหมด
    check_odbc_drivers()
    check_localdb_status()
    test_sql_server_connection()
    generate_connection_commands()

    print("\n" + "=" * 50)
    print("🎯 Diagnostic Complete!")
