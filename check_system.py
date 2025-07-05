#!/usr/bin/env python3
"""
check_system.py
ตรวจสอบระบบและเชื่อมต่อ SSMS โดยตรง
"""
import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """ตรวจสอบ Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(
            f"❌ Python {version.major}.{version.minor}.{version.micro} (ต้องการ 3.8+)"
        )
        return False


def check_files():
    """ตรวจสอบไฟล์สำคัญ"""
    files = {
        "app.py": "Main application file",
        ".streamlit/secrets.toml": "Database credentials",
        "requirements.txt": "Python dependencies",
        "config/database.py": "Database configuration",
    }

    missing = []
    for file_path, desc in files.items():
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - {desc}")
            missing.append(file_path)

    return missing


def check_directories():
    """ตรวจสอบโฟลเดอร์"""
    dirs = ["modules", "utils", "config", "logs", "data", ".streamlit"]
    missing = []

    for dir_path in dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/")
            missing.append(dir_path)

    return missing


def check_packages():
    """ตรวจสอบ Python packages"""
    packages = [
        "streamlit",
        "pyodbc",
        "pandas",
        "plotly",
        "bcrypt",
        "yaml",
        "openpyxl",
    ]

    missing = []
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"✅ {pkg}")
        except ImportError:
            print(f"❌ {pkg}")
            missing.append(pkg)

    return missing


def test_database():
    """ทดสอบการเชื่อมต่อฐานข้อมูล"""
    try:
        import pyodbc
        import toml

        if not os.path.exists(".streamlit/secrets.toml"):
            print("❌ ไม่พบ secrets.toml")
            return False

        config = toml.load(".streamlit/secrets.toml")
        db = config["database"]

        # Connection string สำหรับ LocalDB (ไม่ใช้ encryption)
        conn_str = (
            f"DRIVER={{{db['driver']}}};"
            f"SERVER={db['server']};"
            f"DATABASE={db['database']};"
            "Trusted_Connection=yes;"
        )

        print(f"🔗 เชื่อมต่อ: {db['server']}")
        print(f"🗄️ ฐานข้อมูล: {db['database']}")

        with pyodbc.connect(conn_str, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT @@SERVERNAME, DB_NAME()")
            server, database = cursor.fetchone()

            print(f"✅ เชื่อมต่อสำเร็จ")
            print(f"   Server: {server}")
            print(f"   Database: {database}")
            return True

    except ImportError:
        print("❌ ขาด pyodbc หรือ toml")
        return False
    except Exception as e:
        print(f"❌ เชื่อมต่อไม่สำเร็จ: {str(e)}")
        return False


def create_missing():
    """สร้างโฟลเดอร์และไฟล์ที่จำเป็น"""
    # สร้างโฟลเดอร์
    dirs = ["modules", "utils", "config", "logs", "data", ".streamlit"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # สร้าง __init__.py
    for init in ["modules/__init__.py", "utils/__init__.py", "config/__init__.py"]:
        if not os.path.exists(init):
            with open(init, "w") as f:
                f.write("# Package init\n")


def main():
    """Main check function"""
    print("🚀 DENSO Project Manager - System Check")
    print("=" * 45)

    # ตรวจสอบ Python
    python_ok = check_python_version()

    print("\n📁 Files & Directories:")
    missing_files = check_files()
    missing_dirs = check_directories()

    print("\n📦 Python Packages:")
    missing_packages = check_packages()

    print("\n🗄️ Database Connection:")
    db_ok = test_database()

    print("\n" + "=" * 45)
    print("📋 สรุป:")

    if python_ok:
        print("✅ Python version")
    if not missing_files:
        print("✅ Required files")
    if not missing_dirs:
        print("✅ Directory structure")
    if not missing_packages:
        print("✅ Python packages")
    if db_ok:
        print("✅ Database connection")

    # แสดงปัญหา
    issues = []
    if not python_ok:
        issues.append("Python version ต่ำเกินไป")
    if missing_files:
        issues.append(f"ขาดไฟล์: {', '.join(missing_files)}")
    if missing_dirs:
        issues.append(f"ขาดโฟลเดอร์: {', '.join(missing_dirs)}")
    if missing_packages:
        issues.append(f"ขาด packages: {', '.join(missing_packages)}")
    if not db_ok:
        issues.append("เชื่อมต่อฐานข้อมูลไม่ได้")

    if issues:
        print("\n⚠️  ปัญหาที่พบ:")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")

        print("\n🔧 แก้ไข:")
        if missing_dirs:
            print("- รัน: python check_system.py --fix")
        if missing_packages:
            print("- รัน: pip install -r requirements.txt")
        if not db_ok:
            print("- ตรวจสอบ .streamlit/secrets.toml")
            print("- ตรวจสอบ SSMS connection")
    else:
        print("\n🎉 ระบบพร้อมใช้งาน!")
        print("▶️  รัน: streamlit run app.py")


if __name__ == "__main__":
    if "--fix" in sys.argv:
        create_missing()
        print("🔧 สร้างโครงสร้างเสร็จแล้ว")
    else:
        main()
