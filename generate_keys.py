#!/usr/bin/env python3
"""
DENSO Project Manager Pro - Security Keys Generator
สคริปต์สำหรับสร้าง Secret Keys ที่ปลอดภัย
"""

import secrets
import string
from datetime import datetime


def generate_strong_key(length: int = 32) -> str:
    """สร้าง secret key ที่แข็งแกร่ง"""
    alphabet = string.ascii_letters + string.digits + "-_"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_all_keys():
    """สร้าง keys ทั้งหมดที่จำเป็น"""

    print("🔐 DENSO Project Manager Pro - Security Keys Generator")
    print("=" * 60)
    print(f"🕐 Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # สร้าง keys แบบ URL-safe
    keys = {
        "app_secret_key": secrets.token_urlsafe(32),
        "password_reset_key": secrets.token_urlsafe(32),
        "jwt_access_key": secrets.token_urlsafe(32),
        "jwt_refresh_key": secrets.token_urlsafe(32),
        "csrf_secret": secrets.token_urlsafe(24),
        "data_encryption_key": secrets.token_urlsafe(32),
        "cookie_secret": secrets.token_urlsafe(32),
    }

    print("📋 Copy these keys to your .streamlit/secrets.toml file:")
    print()

    # แสดงรูปแบบ secrets.toml
    print("# .streamlit/secrets.toml")
    print("[app]")
    print(f'secret_key = "{keys["app_secret_key"]}"')
    print()

    print("[security]")
    print(f'password_reset_key = "{keys["password_reset_key"]}"')
    print(f'jwt_access_key = "{keys["jwt_access_key"]}"')
    print(f'jwt_refresh_key = "{keys["jwt_refresh_key"]}"')
    print(f'csrf_secret = "{keys["csrf_secret"]}"')
    print(f'data_encryption_key = "{keys["data_encryption_key"]}"')
    print()

    print("# For .streamlit/config.toml")
    print("[server]")
    print(f'cookieSecret = "{keys["cookie_secret"]}"')
    print()

    print("🔧 Additional environment variables (optional):")
    print("# .env file")
    for name, key in keys.items():
        env_name = name.upper()
        print(f"{env_name}={key}")

    print()
    print("⚠️  SECURITY REMINDERS:")
    print("• Never commit secrets.toml to Git")
    print("• Store these keys safely")
    print("• Use different keys for production")
    print("• Rotate keys regularly")
    print("• Keep backups in secure location")

    return keys


def generate_production_keys():
    """สร้าง keys สำหรับ production แบบพิเศษ"""

    print("🏭 PRODUCTION KEYS - Extra Security")
    print("=" * 50)

    # สำหรับ production ใช้ความยาวที่มากกว่า
    production_keys = {
        "app_secret_key": secrets.token_urlsafe(48),
        "password_reset_key": secrets.token_urlsafe(48),
        "jwt_access_key": secrets.token_urlsafe(48),
        "jwt_refresh_key": secrets.token_urlsafe(48),
        "csrf_secret": secrets.token_urlsafe(32),
        "data_encryption_key": secrets.token_urlsafe(48),
        "database_encryption_key": secrets.token_urlsafe(48),
        "api_key": secrets.token_urlsafe(32),
        "webhook_secret": secrets.token_urlsafe(32),
    }

    for name, key in production_keys.items():
        print(f"{name}: {key}")

    return production_keys


def validate_key_strength(key: str) -> bool:
    """ตรวจสอบความแข็งแกร่งของ key"""

    if len(key) < 24:
        return False

    # ตรวจสอบความหลากหลายของตัวอักษร
    has_upper = any(c.isupper() for c in key)
    has_lower = any(c.islower() for c in key)
    has_digit = any(c.isdigit() for c in key)
    has_special = any(c in "-_" for c in key)

    return all([has_upper, has_lower, has_digit, has_special])


def check_existing_keys():
    """ตรวจสอบ keys ที่มีอยู่"""
    try:
        import streamlit as st

        print("🔍 Checking existing keys...")

        # ตรวจสอบ app secret key
        if hasattr(st.secrets, "app") and hasattr(st.secrets.app, "secret_key"):
            app_key = st.secrets.app.secret_key
            if app_key and app_key != "default-change-this":
                print(f"✅ App secret key: Set (length: {len(app_key)})")
            else:
                print("❌ App secret key: Not set or using default")

        # ตรวจสอบ security keys
        if hasattr(st.secrets, "security"):
            security_keys = [
                "password_reset_key",
                "jwt_access_key",
                "jwt_refresh_key",
                "csrf_secret",
                "data_encryption_key",
            ]

            for key_name in security_keys:
                if hasattr(st.secrets.security, key_name):
                    key_value = getattr(st.secrets.security, key_name)
                    if key_value and key_value != "default-change-this":
                        print(f"✅ {key_name}: Set (length: {len(key_value)})")
                    else:
                        print(f"❌ {key_name}: Not set or using default")
                else:
                    print(f"❌ {key_name}: Missing")

    except ImportError:
        print("⚠️ Streamlit not available - cannot check existing keys")
    except Exception as e:
        print(f"⚠️ Error checking keys: {str(e)}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "production":
            generate_production_keys()
        elif command == "check":
            check_existing_keys()
        elif command == "validate":
            if len(sys.argv) > 2:
                key_to_validate = sys.argv[2]
                is_strong = validate_key_strength(key_to_validate)
                print(f"Key strength: {'✅ Strong' if is_strong else '❌ Weak'}")
            else:
                print("Usage: python generate_keys.py validate <key>")
        else:
            print("Available commands:")
            print("  python generate_keys.py            # Generate development keys")
            print("  python generate_keys.py production # Generate production keys")
            print("  python generate_keys.py check      # Check existing keys")
            print("  python generate_keys.py validate <key> # Validate key strength")
    else:
        generate_all_keys()
