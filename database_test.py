# แก้ไข database_test.py
import pymssql

try:
    conn = pymssql.connect(
        server="10.73.148.27",
        user="TS00029",
        password="Thammaphon@TS00029",
        database="SDXProjectManager",
    )
    print("✅ Connected successfully!")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
