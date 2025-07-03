#!/usr/bin/env python3
"""
DENSO Project Manager Pro - Directory Setup Script
สคริปต์สำหรับสร้างโฟลเดอร์ที่จำเป็นทั้งหมด
"""

import os
import sys
from pathlib import Path


def create_directories():
    """สร้างโฟลเดอร์ที่จำเป็นทั้งหมด"""

    directories = [
        # Main directories
        "logs",
        "logs/errors",
        "data",
        "data/uploads",
        "data/exports",
        "data/backups",
        "config",
        "reports",
        "temp",
        # Streamlit directories
        ".streamlit",
        # Additional directories
        "static",
        "static/css",
        "static/js",
        "static/images",
        "docs",
        "tests",
    ]

    print("🏗️ DENSO Project Manager Pro - Directory Setup")
    print("=" * 50)

    created_count = 0
    existing_count = 0
    error_count = 0

    for directory in directories:
        try:
            if os.path.exists(directory):
                print(f"✅ {directory} (already exists)")
                existing_count += 1
            else:
                os.makedirs(directory, exist_ok=True)
                print(f"📁 {directory} (created)")
                created_count += 1

        except Exception as e:
            print(f"❌ {directory} (error: {str(e)})")
            error_count += 1

    print("\n" + "=" * 50)
    print(f"📊 Summary:")
    print(f"   Created: {created_count} directories")
    print(f"   Existing: {existing_count} directories")
    print(f"   Errors: {error_count} directories")
    print(f"   Total: {len(directories)} directories")

    if error_count == 0:
        print("✅ All directories setup successfully!")
    else:
        print("⚠️ Some directories could not be created.")

    return error_count == 0


def create_gitkeep_files():
    """สร้างไฟล์ .gitkeep ในโฟลเดอร์ว่าง"""

    empty_directories = [
        "logs",
        "logs/errors",
        "data/uploads",
        "data/exports",
        "data/backups",
        "temp",
        "reports",
    ]

    print("\n📄 Creating .gitkeep files...")

    for directory in empty_directories:
        try:
            gitkeep_path = os.path.join(directory, ".gitkeep")
            if not os.path.exists(gitkeep_path):
                with open(gitkeep_path, "w") as f:
                    f.write("# This file keeps the directory in Git\n")
                print(f"📝 {gitkeep_path}")
            else:
                print(f"✅ {gitkeep_path} (exists)")

        except Exception as e:
            print(f"❌ Error creating .gitkeep in {directory}: {str(e)}")


def create_sample_configs():
    """สร้างไฟล์ config ตัวอย่าง"""

    configs = {
        ".streamlit/secrets.toml.example": """# .streamlit/secrets.toml.example
# Copy this file to secrets.toml and update with your values

[database]
server = "your-server"
database = "ProjectManagerDB"
username = "your-username"
password = "your-password"
driver = "ODBC Driver 17 for SQL Server"

[app]
secret_key = "your-secret-key-here"
debug = true
session_timeout = 3600

[security]
bcrypt_rounds = 12
max_login_attempts = 5
password_min_length = 8
""",
        "config/app_config.yaml.example": """# config/app_config.yaml.example
# Copy this file to app_config.yaml and customize

app:
  app_name: 'DENSO Project Manager Pro'
  version: '2.0.0'
  debug: false
  environment: 'development'

database:
  connection_timeout: 30
  command_timeout: 60

security:
  bcrypt_rounds: 12
  max_login_attempts: 5
""",
        "README.md": """# DENSO Project Manager Pro

## Quick Start

1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
2. Update database connection details in `secrets.toml`
3. Run: `streamlit run app.py`

## Default Login
- Username: admin
- Password: admin123

⚠️ Change the default password immediately!
""",
    }

    print("\n📋 Creating sample configuration files...")

    for file_path, content in configs.items():
        try:
            if not os.path.exists(file_path):
                # สร้างโฟลเดอร์ก่อนถ้าจำเป็น
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"📝 {file_path}")
            else:
                print(f"✅ {file_path} (exists)")

        except Exception as e:
            print(f"❌ Error creating {file_path}: {str(e)}")


def main():
    """Main function"""

    # เปลี่ยน working directory ไปที่ directory ของ script
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    print(f"Working directory: {os.getcwd()}")
    print()

    # สร้างโฟลเดอร์
    success = create_directories()

    # สร้างไฟล์ .gitkeep
    create_gitkeep_files()

    # สร้างไฟล์ config ตัวอย่าง
    create_sample_configs()

    print("\n🎉 Setup completed!")

    if success:
        print("✅ Ready to run: streamlit run app.py")
    else:
        print("⚠️ Please check the errors above before running the application.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
